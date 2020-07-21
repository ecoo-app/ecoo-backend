from rest_framework.pagination import CursorPagination
from pytezos import pytezos, michelson
from django.utils.timezone import now
from apps.wallet.models import MetaTransaction, TRANSACTION_STATES
from django.conf import settings


class CustomCursorPagination(CursorPagination):
    ordering = 'created'


def getBalanceForWallet(wallet):
    # TODO: implement!!
    # TODO: get balance of account on blockchain & apply the transactions stored but not commited
    # entry point get_balance -> move function to utils

    return 10400


MESSAGE_STRUCTURE = {
    "prim": "pair",
            "args": [
                {
                    "prim": "key"
                },
                {
                    "prim": "pair",
                    "args": [
                        {
                            "prim": "nat"
                        },
                        {
                            "prim": "list",
                            "args": [
                                {
                                    "prim": "pair",
                                    "args": [
                                        {"prim": "address"},
                                        {
                                            "prim": "pair",
                                            "args": [
                                                {"prim": "nat"},
                                                {"prim": "nat"}
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
}


def create_message(from_wallet, to_wallet, nonce, token_id, amount):
    message_to_encode = {
        "prim": "Pair",
        "args": [
                {
                    "string": from_wallet.public_key
                },
            {
                    "prim": "Pair",
                    "args": [
                        {
                            'int': nonce
                        },
                        [
                            {
                                "prim": "Pair",
                                "args": [
                                    {
                                        "string": to_wallet.address
                                    },
                                    {
                                        "prim": "Pair",
                                        "args": [
                                            {
                                                "int": token_id
                                            },
                                            {
                                                'int': amount
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    ]
                    }
        ]
    }
    return michelson.pack.pack(message_to_encode, MESSAGE_STRUCTURE)


def pack_meta_transaction(meta_transaction):
    message_to_encode = {
        "prim": "Pair",
        "args": [
            {
                "string": meta_transaction['from_public_key']
            },
            {
                "prim": "Pair",
                "args": [
                    {
                        'int': meta_transaction['nonce']
                    },
                    []
                ]
            }
        ]
    }

    for transaction in meta_transaction['txs']:
        message_to_encode['args'][1]['args'][1].append({
            "prim": "Pair",
            "args": [
                {
                    "string": transaction['to_']
                },
                {
                    "prim": "Pair",
                    "args": [
                        {
                            "int": transaction['token_id']
                        },
                        {
                            'int': transaction['amount']
                        }
                    ]
                }
            ]
        })

    return michelson.pack.pack(message_to_encode, MESSAGE_STRUCTURE)


def read_nonce_from_chain(address):
    pytezos_client = pytezos.using(
        key=settings.TEZOS_ADMIN_ACCOUNT_PRIVATE_KEY, shell=settings.TEZOS_NODE)
    token_contract = pytezos_client.contract(
        settings.TEZOS_TOKEN_CONTRACT_ADDRESS)
    try:
        return int(token_contract.nonce_of(callback='{}%receive_nonce'.format(settings.TEZOS_CALLBACK_CONTRACT_ADDRESS), requests=[address]).operation_group.sign().preapply()['contents'][0]['metadata']['internal_operation_results'][0]['parameters']['value'][0]['args'][0]['int'])
    except:
        return 0


def publish_open_meta_transactions_to_chain():
    open_transactions = MetaTransaction.objects.filter(
        state=TRANSACTION_STATES.OPEN.value)
    selected_transaction_ids = set(
        open_transactions.values_list('uuid', flat=True))
    selected_transactions = MetaTransaction.objects.filter(
        uuid__in=selected_transaction_ids)
    pytezos_client = pytezos.using(
        key=settings.TEZOS_ADMIN_ACCOUNT_PRIVATE_KEY, shell=settings.TEZOS_NODE)
    token_contract = pytezos_client.contract(
        settings.TEZOS_TOKEN_CONTRACT_ADDRESS)
    open_meta_transactions = list(map(
        lambda selected_transaction: selected_transaction.to_meta_transaction_dictionary(), selected_transactions))
    selected_transactions.update(state=TRANSACTION_STATES.PENDING.value)
    try:
        operation_result = token_contract.meta_transfer(open_meta_transactions).operation_group.sign().inject(
            _async=False, preapply=True, check_result=True, num_blocks_wait=settings.TEZOS_BLOCK_WAIT_TIME)

        if operation_result['contents'][0]['metadata']['operation_result']['status'] == 'applied':
            selected_transactions.update(
                state=TRANSACTION_STATES.DONE.value, submitted_to_chain_at=now(), operation_hash=operation_result['hash'])
        else:
            selected_transactions.update(
                state=TRANSACTION_STATES.FAILED.value, submitted_to_chain_at=now())
    except Exception as error:
        print(error)
        selected_transactions.update(
            state=TRANSACTION_STATES.FAILED.value, submitted_to_chain_at=now())
