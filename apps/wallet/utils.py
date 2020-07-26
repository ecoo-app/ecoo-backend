from rest_framework.pagination import CursorPagination
from pytezos import pytezos, michelson
from django.utils.timezone import now
from apps.wallet.models import Wallet, MetaTransaction, Transaction, WalletPublicKeyTransferRequest, TRANSACTION_STATES
from django.conf import settings
from django.utils.timezone import now
from pytezos import michelson, pytezos
from rest_framework.pagination import CursorPagination


class CustomCursorPagination(CursorPagination):
    ordering = 'created'


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
    open_meta_transactions = list(map(
        lambda selected_transaction: selected_transaction.to_meta_transaction_dictionary(), selected_transactions))

    if selected_transactions.exists():
        selected_transactions.update(state=TRANSACTION_STATES.PENDING.value)
        try:
            pytezos_client = pytezos.using(
                key=settings.TEZOS_ADMIN_ACCOUNT_PRIVATE_KEY, shell=settings.TEZOS_NODE)
            token_contract = pytezos_client.contract(
                settings.TEZOS_TOKEN_CONTRACT_ADDRESS)
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


def publish_open_mint_transactions_to_chain():
    open_transactions = Transaction.objects.filter(
        state=TRANSACTION_STATES.OPEN.value, from_wallet=None)
    selected_transaction_ids = set(
        open_transactions.values_list('uuid', flat=True))
    selected_transactions = Transaction.objects.filter(
        uuid__in=selected_transaction_ids)
    if selected_transactions.exists():
        selected_transactions.update(state=TRANSACTION_STATES.PENDING.value)
        try:
            pytezos_client = pytezos.using(
                key=settings.TEZOS_ADMIN_ACCOUNT_PRIVATE_KEY, shell=settings.TEZOS_NODE)
            token_contract = pytezos_client.contract(
                settings.TEZOS_TOKEN_CONTRACT_ADDRESS)
            for transaction in selected_transactions:
                operation_result = token_contract.mint(address=transaction.to_wallet.address, decimals=transaction.to_wallet.currency.decimals, name=transaction.to_wallet.currency.name, token_id=transaction.to_wallet.currency.token_id, symbol=transaction.to_wallet.currency.symbol, amount=transaction.amount).operation_group.sign().inject(
                    _async=False, preapply=True, check_result=True, num_blocks_wait=settings.TEZOS_BLOCK_WAIT_TIME)

                if operation_result['contents'][0]['metadata']['operation_result']['status'] == 'applied':
                    selected_transactions.update(
                        state=TRANSACTION_STATES.DONE.value, submitted_to_chain_at=now(), operation_hash=operation_result['hash'])
                else:
                    selected_transactions.update(
                        state=TRANSACTION_STATES.FAILED.value, submitted_to_chain_at=now())
        except Exception as error:
            selected_transactions.update(
                state=TRANSACTION_STATES.FAILED.value, submitted_to_chain_at=now())


def publish_open_transfer_transactions_to_chain():
    open_transfer_transactions = Transaction.objects.filter(
        state=TRANSACTION_STATES.OPEN.value).exclude(from_wallet=None).exclude(uuid__in=MetaTransaction.objects.all())
    selected_transaction_ids = set(
        open_transfer_transactions.values_list('uuid', flat=True))
    selected_transactions = Transaction.objects.filter(
        uuid__in=selected_transaction_ids)
    if selected_transactions.exists():
        selected_transactions.update(state=TRANSACTION_STATES.PENDING.value)
        try:
            pytezos_client = pytezos.using(
                key=settings.TEZOS_ADMIN_ACCOUNT_PRIVATE_KEY, shell=settings.TEZOS_NODE)
            token_contract = pytezos_client.contract(
                settings.TEZOS_TOKEN_CONTRACT_ADDRESS)
            last_from_wallet = None
            transfer_transaction_payloads = []
            for transaction in selected_transactions:
                if last_from_wallet != transaction.from_wallet:
                    transfer_transaction_payloads.append({
                        "from_": transaction.from_wallet.address,
                        "txs": []
                    })
                transfer_transaction_payloads[-1]['txs'].append({
                    "to_": transaction.to_wallet.address,
                    "token_id": transaction.to_wallet.currency.token_id,
                    "amount": transaction.amount
                })
                last_from_wallet = transaction.from_wallet

            operation_result = token_contract.transfer(transfer_transaction_payloads).operation_group.sign().inject(
                _async=False, preapply=True, check_result=True, num_blocks_wait=settings.TEZOS_BLOCK_WAIT_TIME)

            if operation_result['contents'][0]['metadata']['operation_result']['status'] == 'applied':
                selected_transactions.update(
                    state=TRANSACTION_STATES.DONE.value, submitted_to_chain_at=now(), operation_hash=operation_result['hash'])
            else:
                selected_transactions.update(
                    state=TRANSACTION_STATES.FAILED.value, submitted_to_chain_at=now())
        except Exception as error:
            selected_transactions.update(
                state=TRANSACTION_STATES.FAILED.value, submitted_to_chain_at=now())


def publish_wallet_recovery_transfer_balance():
    open_wallet_public_key_transfer_requests = WalletPublicKeyTransferRequest.objects.filter(
        state=TRANSACTION_STATES.OPEN.value)
    selected_wallet_public_key_transfer_request_ids = set(
        open_wallet_public_key_transfer_requests.values_list('uuid', flat=True))

    selected_wallet_public_key_transfer_requests = WalletPublicKeyTransferRequest.objects.filter(
        uuid__in=selected_wallet_public_key_transfer_request_ids)

    pytezos_client = pytezos.using(
        key=settings.TEZOS_ADMIN_ACCOUNT_PRIVATE_KEY, shell=settings.TEZOS_NODE)
    token_contract = pytezos_client.contract(
        settings.TEZOS_TOKEN_CONTRACT_ADDRESS)

    transfer_transaction_payloads = []
    allowed_wallet_public_key_transfer_requests = []
    if selected_wallet_public_key_transfer_requests.exists():
        for selected_wallet_public_key_transfer_request in selected_wallet_public_key_transfer_requests:
            if selected_wallet_public_key_transfer_request.wallet.to_transactions.exclude(
                    state=TRANSACTION_STATES.DONE.value).exists() or selected_wallet_public_key_transfer_request.wallet.from_transactions.exclude(
                    state=TRANSACTION_STATES.DONE.value).exists():
                pass  # unsynchronized stuff is available cannot process transfer
            else:
                selected_wallet_public_key_transfer_request.state = TRANSACTION_STATES.PENDING.value
                selected_wallet_public_key_transfer_request.old_public_key = selected_wallet_public_key_transfer_request.wallet.public_key
                new_address = Wallet(
                    public_key=selected_wallet_public_key_transfer_request.new_public_key).address
                transfer_transaction_payloads.append({
                    "from_": selected_wallet_public_key_transfer_request.wallet.address,
                    "txs": [{
                        "to_": new_address,
                        "token_id": selected_wallet_public_key_transfer_request.wallet.currency.token_id,
                        "amount": selected_wallet_public_key_transfer_request.wallet.balance
                    }]
                })
                selected_wallet_public_key_transfer_request.save()
                allowed_wallet_public_key_transfer_requests.append(
                    selected_wallet_public_key_transfer_request)
        try:
            operation_result = token_contract.transfer(transfer_transaction_payloads).operation_group.sign().inject(
                _async=False, preapply=True, check_result=True, num_blocks_wait=settings.TEZOS_BLOCK_WAIT_TIME)

            if operation_result['contents'][0]['metadata']['operation_result']['status'] == 'applied':
                for allowed_wallet_public_key_transfer_request in allowed_wallet_public_key_transfer_requests:
                    allowed_wallet_public_key_transfer_request.wallet.public_key = allowed_wallet_public_key_transfer_request.new_public_key
                    allowed_wallet_public_key_transfer_request.wallet.save()
                    allowed_wallet_public_key_transfer_request.state = TRANSACTION_STATES.DONE.value
                    allowed_wallet_public_key_transfer_request.submitted_to_chain_at = now()
                    allowed_wallet_public_key_transfer_request.operation_hash = operation_result[
                        'hash']
                    allowed_wallet_public_key_transfer_request.save()
            else:
                for allowed_wallet_public_key_transfer_request in allowed_wallet_public_key_transfer_requests:
                    allowed_wallet_public_key_transfer_request.state = TRANSACTION_STATES.FAILED.value
                    allowed_wallet_public_key_transfer_request.save()
        except Exception as error:
            for allowed_wallet_public_key_transfer_request in allowed_wallet_public_key_transfer_requests:
                allowed_wallet_public_key_transfer_request.state = TRANSACTION_STATES.FAILED.value
                allowed_wallet_public_key_transfer_request.save()


def create_claim_transaction(wallet):
    Transaction.objects.create(from_wallet=wallet.currency.owner_wallet,
                               to_wallet=wallet, amount=wallet.currency.starting_capital)
