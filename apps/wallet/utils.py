import json
import time
import traceback

from django.conf import settings
from django.utils.timezone import now
from pytezos import pytezos
from pytezos.michelson.types.base import MichelsonType
from pytezos.operation.result import OperationResult

PAPER_WALLET_MESSAGE_STRUCTURE = {
    "prim": "pair",
    "args": [
        {"prim": "string"},
        {"prim": "nat"},
    ],
}


def create_paper_wallet_message(wallet, token_id):
    message_to_encode = {
        "prim": "Pair",
        "args": [
            {"string": wallet.wallet_id},
            {"int": token_id},
        ],
    }
    michelson_type = MichelsonType.match(PAPER_WALLET_MESSAGE_STRUCTURE)
    return michelson_type.from_micheline_value(message_to_encode).pack()


MESSAGE_STRUCTURE = {
    "prim": "pair",
    "args": [
        {"prim": "key"},
        {
            "prim": "pair",
            "args": [
                {"prim": "nat"},
                {
                    "prim": "list",
                    "args": [
                        {
                            "prim": "pair",
                            "args": [
                                {"prim": "address"},
                                {
                                    "prim": "pair",
                                    "args": [{"prim": "nat"}, {"prim": "nat"}],
                                },
                            ],
                        }
                    ],
                },
            ],
        },
    ],
}


def create_message(from_wallet, to_wallet, nonce, token_id, amount):
    message_to_encode = {
        "prim": "Pair",
        "args": [
            {"string": from_wallet.public_key},
            {
                "prim": "Pair",
                "args": [
                    {"int": nonce},
                    [
                        {
                            "prim": "Pair",
                            "args": [
                                {"string": to_wallet.address},
                                {
                                    "prim": "Pair",
                                    "args": [{"int": token_id}, {"int": amount}],
                                },
                            ],
                        }
                    ],
                ],
            },
        ],
    }

    michelson_type = MichelsonType.match(MESSAGE_STRUCTURE)
    return michelson_type.from_micheline_value(message_to_encode).pack()


def pack_meta_transaction(meta_transaction):
    message_to_encode = {
        "prim": "Pair",
        "args": [
            {"string": meta_transaction["from_public_key"]},
            {"prim": "Pair", "args": [{"int": meta_transaction["nonce"]}, []]},
        ],
    }

    for transaction in meta_transaction["txs"]:
        message_to_encode["args"][1]["args"][1].append(
            {
                "prim": "Pair",
                "args": [
                    {"string": transaction["to_"]},
                    {
                        "prim": "Pair",
                        "args": [
                            {"int": transaction["token_id"]},
                            {"int": transaction["amount"]},
                        ],
                    },
                ],
            }
        )
    michelson_type = MichelsonType.match(MESSAGE_STRUCTURE)
    return michelson_type.from_micheline_value(message_to_encode).pack()


def read_nonce_from_chain(address):
    pytezos_client = pytezos.using(
        key=settings.TEZOS_ADMIN_ACCOUNT_PRIVATE_KEY, shell=settings.TEZOS_NODE
    )
    token_contract = pytezos_client.contract(settings.TEZOS_TOKEN_CONTRACT_ADDRESS)
    try:
        return int(
            token_contract.nonce_of(
                callback="{}%receive_nonce".format(
                    settings.TEZOS_CALLBACK_CONTRACT_ADDRESS
                ),
                requests=[address],
            )
            .operation_group.sign()
            .preapply()["contents"][0]["metadata"]["internal_operation_results"][0][
                "parameters"
            ]["value"][0]["args"][0]["int"]
        )
    except:
        return 0


def sync_to_blockchain(is_dry_run=True, _async=False):
    print("starting sync")
    time.sleep(settings.BLOCKCHAIN_SYNC_WAIT_TIME)
    from apps.wallet.models import (
        TRANSACTION_STATES,
        MetaTransaction,
        Transaction,
        Wallet,
        WalletPublicKeyTransferRequest,
    )

    pytezos_client = pytezos.using(
        key=settings.TEZOS_ADMIN_ACCOUNT_PRIVATE_KEY, shell=settings.TEZOS_NODE
    )
    token_contract = pytezos_client.contract(settings.TEZOS_TOKEN_CONTRACT_ADDRESS)

    funding_transactions = {}
    meta_transactions = []
    operation_groups = []

    state_update_items = []

    for transaction in (
        Transaction.objects.exclude(state=TRANSACTION_STATES.PENDING.value)
        .exclude(state=TRANSACTION_STATES.DONE.value)
        .order_by("created_at")
    ):
        if not transaction.from_wallet:
            operation_groups.append(
                token_contract.mint(
                    address=transaction.to_wallet.address,
                    decimals=transaction.to_wallet.currency.decimals,
                    name=transaction.to_wallet.currency.name,
                    token_id=transaction.to_wallet.currency.token_id,
                    symbol=transaction.to_wallet.currency.symbol,
                    amount=transaction.amount,
                ).operation_group.sign()
            )
            state_update_items.append(transaction)
        elif MetaTransaction.objects.filter(pk=transaction.pk).exists():
            meta_transactions.append(MetaTransaction.objects.get(pk=transaction))
            state_update_items.append(transaction)
        elif (
            transaction.to_wallet.from_transactions.count()
            > 0 | transaction.to_wallet.transfer_requests.count()
            > 0
        ):
            same_from_txs = funding_transactions.get(
                transaction.from_wallet.address, []
            )
            same_from_txs.append(
                {
                    "to_": transaction.to_wallet.address,
                    "token_id": transaction.to_wallet.currency.token_id,
                    "amount": transaction.amount,
                }
            )
            funding_transactions[transaction.from_wallet.address] = same_from_txs
            state_update_items.append(transaction)

    # preparing funding
    if len(funding_transactions.items()) > 0:
        funding_transaction_payloads = list(
            map(
                lambda item: {"from_": item[0], "txs": item[1]},
                funding_transactions.items(),
            )
        )
        operation_groups.append(
            token_contract.transfer(funding_transaction_payloads).operation_group.sign()
        )

    # preparing meta
    if len(meta_transactions) > 0:
        meta_transaction_payloads = list(
            map(
                lambda meta_transaction: meta_transaction.to_meta_transaction_dictionary(),
                meta_transactions,
            )
        )
        operation_groups.append(
            token_contract.meta_transfer(
                meta_transaction_payloads
            ).operation_group.sign()
        )

    # wallet public key transfers
    wallet_public_key_transfer_payloads = []
    wallet_public_key_transfer_requests = []
    for wallet_public_key_transfer_request in (
        WalletPublicKeyTransferRequest.objects.exclude(
            state=TRANSACTION_STATES.PENDING.value
        )
        .exclude(state=TRANSACTION_STATES.DONE.value)
        .order_by("created_at")
    ):
        if (
            wallet_public_key_transfer_request.wallet.balance > 0
            and wallet_public_key_transfer_request.wallet.public_key
            != wallet_public_key_transfer_request.new_public_key
        ):
            new_address = Wallet(
                public_key=wallet_public_key_transfer_request.new_public_key
            ).address
            state_update_items.append(wallet_public_key_transfer_request)
            wallet_public_key_transfer_requests.append(
                wallet_public_key_transfer_request
            )
            wallet_public_key_transfer_payloads.append(
                {
                    "from_": wallet_public_key_transfer_request.wallet.address,
                    "txs": [
                        {
                            "to_": new_address,
                            "token_id": wallet_public_key_transfer_request.wallet.currency.token_id,
                            "amount": wallet_public_key_transfer_request.wallet.balance,
                        }
                    ],
                }
            )
        else:
            wallet_public_key_transfer_request.old_public_key = (
                wallet_public_key_transfer_request.wallet.public_key
            )
            wallet_public_key_transfer_request.wallet.public_key = (
                wallet_public_key_transfer_request.new_public_key
            )
            wallet_public_key_transfer_request.wallet.save()
            wallet_public_key_transfer_request.state = TRANSACTION_STATES.DONE.value
            wallet_public_key_transfer_request.notes = (
                "Has no balance or was recovering to same pubkey, transferred offchain"
            )
            wallet_public_key_transfer_request.save()
            wallet_public_key_transfer_request.wallet.notify_owner_transfer_request_done()

    if len(wallet_public_key_transfer_payloads) > 0:
        operation_groups.append(
            token_contract.transfer(
                wallet_public_key_transfer_payloads
            ).operation_group.sign()
        )

    # merging all operations into one single group
    final_operation_group = None
    operation_counter = 0
    for operation_group in operation_groups:
        if final_operation_group is None:
            final_operation_group = operation_group
            operation_counter = int(operation_group.contents[0]["counter"])
        else:
            operation_counter += 1
            operation = operation_group.contents[0]
            operation["counter"] = str(operation_counter)
            final_operation_group = final_operation_group.operation(
                operation_group.contents[0]
            )

    if final_operation_group is not None:  # we have stuff to sync
        print(final_operation_group)
        operation_result = final_operation_group.sign().preapply()
        print(operation_result)
        if is_dry_run:
            return OperationResult.is_applied(operation_result)
        elif OperationResult.is_applied(operation_result):

            def update_sync_state(
                items,
                state=TRANSACTION_STATES.PENDING.value,
                notes="",
                operation_hash="",
            ):
                for item in items:
                    type(item).objects.filter(pk=item.pk).update(
                        state=state,
                        notes=notes,
                        operation_hash=operation_hash,
                        submitted_to_chain_at=now(),
                    )

            update_sync_state(state_update_items)
            try:
                is_confirmed_in_chain = False
                try:
                    operation_inject_result = final_operation_group.sign().inject(
                        _async=_async,
                        preapply=True,
                        check_result=True,
                        num_blocks_wait=settings.TEZOS_BLOCK_WAIT_TIME,
                    )
                    is_operation_applied = OperationResult.is_applied(
                        operation_inject_result
                    )
                    is_confirmed_in_chain = True
                except AssertionError:
                    # here we assume that the operation was applied even if we know the assertion failed
                    is_operation_applied = True

                if is_operation_applied:
                    for (
                        wallet_public_key_transfer_request
                    ) in wallet_public_key_transfer_requests:
                        wallet_public_key_transfer_request.old_public_key = (
                            wallet_public_key_transfer_request.wallet.public_key
                        )
                        wallet_public_key_transfer_request.wallet.public_key = (
                            wallet_public_key_transfer_request.new_public_key
                        )
                        wallet_public_key_transfer_request.wallet.save()
                        wallet_public_key_transfer_request.state = (
                            TRANSACTION_STATES.DONE.value
                        )
                        wallet_public_key_transfer_request.save()
                        wallet_public_key_transfer_request.wallet.notify_owner_transfer_request_done()

                    if is_confirmed_in_chain:
                        update_sync_state(
                            state_update_items,
                            TRANSACTION_STATES.DONE.value,
                            json.dumps(operation_inject_result),
                            operation_inject_result["hash"],
                        )
                    else:
                        update_sync_state(
                            state_update_items,
                            TRANSACTION_STATES.DONE.value,
                            json.dumps(operation_result),
                            "*",
                        )
                else:
                    if operation_inject_result is None:
                        update_sync_state(
                            state_update_items,
                            TRANSACTION_STATES.FAILED.value,
                            "Error during sync: {}".format(
                                json.dumps(operation_result)
                            ),
                        )
                    else:
                        update_sync_state(
                            state_update_items,
                            TRANSACTION_STATES.FAILED.value,
                            "Error during sync: {}".format(
                                json.dumps(operation_inject_result)
                            ),
                        )
                return is_operation_applied
            except Exception as error:
                update_sync_state(
                    state_update_items,
                    TRANSACTION_STATES.FAILED.value,
                    "Exception during sync: {}\nTraceback: {}".format(
                        repr(error), traceback.format_exc()
                    ),
                )
                return False
        else:
            return OperationResult.is_applied(operation_result)


def check_sync_state():
    from apps.wallet.models import Wallet

    pytezos_client = pytezos.using(
        key=settings.TEZOS_ADMIN_ACCOUNT_PRIVATE_KEY, shell=settings.TEZOS_NODE
    )
    token_contract = pytezos_client.contract(settings.TEZOS_TOKEN_CONTRACT_ADDRESS)
    fail_message = ""
    for wallet in Wallet.objects.all():
        try:
            on_chain_balance = token_contract.big_map_get(
                "ledger/{}::{}".format(wallet.address, wallet.currency.token_id)
            )
            if wallet.balance != on_chain_balance:

                fail_message += "{} has {} onchain balance but on system {}\n".format(
                    wallet.wallet_id, on_chain_balance, wallet.balance
                )
        except:
            if wallet.balance > 0:
                fail_message += "{} has 0 onchain balance but on system {}\n".format(
                    wallet.wallet_id, wallet.balance
                )
    if len(fail_message) > 0:
        raise Exception(fail_message)
        return False
    else:
        return True


def fix_sync_state(payback_address):
    from apps.wallet.models import Wallet

    pytezos_client = pytezos.using(
        key=settings.TEZOS_ADMIN_ACCOUNT_PRIVATE_KEY, shell=settings.TEZOS_NODE
    )
    token_contract = pytezos_client.contract(settings.TEZOS_TOKEN_CONTRACT_ADDRESS)
    transfer_transaction_payloads = []
    total_amount = 0
    for wallet in Wallet.objects.all():
        try:
            on_chain_balance = token_contract.big_map_get(
                "ledger/{}::{}".format(wallet.address, wallet.currency.token_id)
            )
            if wallet.balance < on_chain_balance:
                transfer_transaction_payloads.append(
                    {
                        "from_": wallet.address,
                        "txs": [
                            {
                                "to_": payback_address,
                                "token_id": wallet.currency.token_id,
                                "amount": on_chain_balance - wallet.balance,
                            }
                        ],
                    }
                )
                total_amount += on_chain_balance - wallet.balance
        except Exception as error:
            if wallet.balance > 0:
                print("wallet {} had some issues: {}".format(wallet.wallet_id, error))
    print(
        "going to transfer {} from {} wallets to {}".format(
            total_amount, len(transfer_transaction_payloads), payback_address
        )
    )
    token_contract.transfer(
        transfer_transaction_payloads
    ).operation_group.sign().inject(
        _async=False,
        preapply=True,
        check_result=True,
        num_blocks_wait=settings.TEZOS_BLOCK_WAIT_TIME,
    )


def create_claim_transaction(wallet):
    from apps.wallet.models import Transaction

    Transaction.objects.create(
        from_wallet=wallet.currency.owner_wallet,
        to_wallet=wallet,
        amount=wallet.currency.starting_capital,
    )
    wallet.notify_owner_receiving_money(
        from_wallet_id=wallet.currency.owner_wallet,
        amount=wallet.currency.starting_capital,
    )
