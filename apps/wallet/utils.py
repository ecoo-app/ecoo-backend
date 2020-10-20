from rest_framework.pagination import CursorPagination
from pytezos import pytezos, michelson
from django.utils.timezone import now
from django.conf import settings
from django.utils.timezone import now
from pytezos.operation.result import OperationResult
import json
import traceback
import time

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


def sync_to_blockchain(is_dry_run=True, _async=False):
    print('starting sync')
    time.sleep(settings.BLOCKCHAIN_SYNC_WAIT_TIME)
    from apps.wallet.models import Wallet, MetaTransaction, Transaction, WalletPublicKeyTransferRequest, TRANSACTION_STATES

    pytezos_client = pytezos.using(
        key=settings.TEZOS_ADMIN_ACCOUNT_PRIVATE_KEY, shell=settings.TEZOS_NODE)
    token_contract = pytezos_client.contract(
        settings.TEZOS_TOKEN_CONTRACT_ADDRESS)

    funding_transactions = {}
    meta_transactions = []
    operation_groups = []

    state_update_items = []

    for transaction in Transaction.objects.exclude(state=TRANSACTION_STATES.PENDING.value).exclude(state=TRANSACTION_STATES.DONE.value).order_by('created_at'):
        state_update_items.append(transaction)
        if not transaction.from_wallet:
            operation_groups.append(token_contract.mint(address=transaction.to_wallet.address,
                                                        decimals=transaction.to_wallet.currency.decimals,
                                                        name=transaction.to_wallet.currency.name,
                                                        token_id=transaction.to_wallet.currency.token_id,
                                                        symbol=transaction.to_wallet.currency.symbol,
                                                        amount=transaction.amount).operation_group.sign())
        elif MetaTransaction.objects.filter(pk=transaction.pk).exists():
            meta_transactions.append(
                MetaTransaction.objects.get(pk=transaction))
        else:
            same_from_txs = funding_transactions.get(
                transaction.from_wallet.address, [])
            same_from_txs.append({
                "to_": transaction.to_wallet.address,
                "token_id": transaction.to_wallet.currency.token_id,
                "amount": transaction.amount
            })
            funding_transactions[transaction.from_wallet.address] = same_from_txs

    # preparing funding
    if len(funding_transactions.items()) > 0:
        funding_transaction_payloads = list(map(lambda item: {
            "from_": item[0],
            "txs": item[1]
        }, funding_transactions.items()))
        operation_groups.append(token_contract.transfer(
            funding_transaction_payloads).operation_group.sign())

    # preparing meta
    if len(meta_transactions) > 0:
        meta_transaction_payloads = list(map(
            lambda meta_transaction: meta_transaction.to_meta_transaction_dictionary(), meta_transactions))
        operation_groups.append(token_contract.meta_transfer(
            meta_transaction_payloads).operation_group.sign())

    # wallet public key transfers
    wallet_public_key_transfer_payloads = []
    wallet_public_key_transfer_requests = []
    for wallet_public_key_transfer_request in WalletPublicKeyTransferRequest.objects.exclude(state=TRANSACTION_STATES.PENDING.value).exclude(state=TRANSACTION_STATES.DONE.value).order_by('created_at'):
        if wallet_public_key_transfer_request.wallet.balance > 0 and wallet_public_key_transfer_request.wallet.public_key != wallet_public_key_transfer_request.new_public_key:
            new_address = Wallet(
                public_key=wallet_public_key_transfer_request.new_public_key).address
            state_update_items.append(wallet_public_key_transfer_request)
            wallet_public_key_transfer_requests.append(
                wallet_public_key_transfer_request)
            wallet_public_key_transfer_payloads.append({
                "from_": wallet_public_key_transfer_request.wallet.address,
                "txs": [{
                        "to_": new_address,
                        "token_id": wallet_public_key_transfer_request.wallet.currency.token_id,
                        "amount": wallet_public_key_transfer_request.wallet.balance
                        }]
            })
        else:
            wallet_public_key_transfer_request.old_public_key = wallet_public_key_transfer_request.wallet.public_key
            wallet_public_key_transfer_request.wallet.public_key = wallet_public_key_transfer_request.new_public_key
            wallet_public_key_transfer_request.wallet.save()
            wallet_public_key_transfer_request.state = TRANSACTION_STATES.DONE.value
            wallet_public_key_transfer_request.notes = "Has no balance or was recovering to same pubkey, transferred offchain"
            wallet_public_key_transfer_request.save()

    if len(wallet_public_key_transfer_payloads) > 0:
        operation_groups.append(token_contract.transfer(
            wallet_public_key_transfer_payloads).operation_group.sign())

    # merging all operations into one single group
    final_operation_group = None
    operation_counter = 0
    for operation_group in operation_groups:
        if final_operation_group == None:
            final_operation_group = operation_group
            operation_counter = int(operation_group.contents[0]['counter'])
        else:
            operation_counter += 1
            operation = operation_group.contents[0]
            operation['counter'] = str(operation_counter)
            final_operation_group = final_operation_group.operation(
                operation_group.contents[0])

    if final_operation_group != None:  # we have stuff to sync
        print(final_operation_group)
        operation_result = final_operation_group.sign().preapply()
        print(operation_result)
        if is_dry_run:
            return OperationResult.is_applied(operation_result)
        elif OperationResult.is_applied(operation_result):
            def update_sync_state(items, state=TRANSACTION_STATES.PENDING.value, notes='', operation_hash=''):
                for item in items:
                    type(item).objects.filter(pk=item.pk).update(state=state, notes=notes,
                                                                 operation_hash=operation_hash, submitted_to_chain_at=now())
            update_sync_state(state_update_items)
            try:
                is_confirmed_in_chain = False
                try:
                    operation_inject_result = final_operation_group.sign().inject(
                        _async=_async, preapply=True, check_result=True, num_blocks_wait=settings.TEZOS_BLOCK_WAIT_TIME)
                    is_operation_applied = OperationResult.is_applied(
                        operation_inject_result)
                    is_confirmed_in_chain = True
                except AssertionError:
                    # here we assume that the operation was applied even if we know the assertion failed
                    is_operation_applied = True

                if is_operation_applied:
                    for wallet_public_key_transfer_request in wallet_public_key_transfer_requests:
                        wallet_public_key_transfer_request.old_public_key = wallet_public_key_transfer_request.wallet.public_key
                        wallet_public_key_transfer_request.wallet.public_key = wallet_public_key_transfer_request.new_public_key
                        wallet_public_key_transfer_request.wallet.save()
                        wallet_public_key_transfer_request.state = TRANSACTION_STATES.DONE.value
                        wallet_public_key_transfer_request.save()
                    if is_confirmed_in_chain:
                        update_sync_state(state_update_items, TRANSACTION_STATES.DONE.value, json.dumps(
                            operation_inject_result), operation_inject_result['hash'])
                    else:
                        update_sync_state(state_update_items, TRANSACTION_STATES.DONE.value, json.dumps(
                            operation_result), "*")
                else:
                    if operation_inject_result is None:
                        update_sync_state(state_update_items, TRANSACTION_STATES.FAILED.value, 'Error during sync: {}'.format(
                            json.dumps(operation_result)))
                    else:
                        update_sync_state(state_update_items, TRANSACTION_STATES.FAILED.value, 'Error during sync: {}'.format(
                            json.dumps(operation_inject_result)))
                return is_operation_applied
            except Exception as error:
                update_sync_state(state_update_items, TRANSACTION_STATES.FAILED.value,
                                  'Exception during sync: {}\nTraceback: {}'.format(repr(error), traceback.format_exc()))
                return False
        else:
            return OperationResult.is_applied(operation_result)


def create_claim_transaction(wallet):
    from apps.wallet.models import Wallet, MetaTransaction, Transaction, WalletPublicKeyTransferRequest, TRANSACTION_STATES

    Transaction.objects.create(from_wallet=wallet.currency.owner_wallet,
                               to_wallet=wallet, amount=wallet.currency.starting_capital)
    wallet.notify_owner_receiving_money(
        from_wallet_id=wallet.currency.owner_wallet, amount=wallet.currency.starting_capital)
