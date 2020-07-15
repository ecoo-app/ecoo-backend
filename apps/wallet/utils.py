from rest_framework.pagination import CursorPagination
import pytezos

class CustomCursorPagination(CursorPagination):
    ordering = 'created'


def getBalanceForWallet(wallet):
    # TODO: implement!!
    # TODO: get balance of account on blockchain & apply the transactions stored but not commited
    # entry point get_balance -> move function to utils

    return 104.0



MESSAGE_STRUCTURE = {
    "prim": "pair",
            "args": [
                {
                    "prim": "bytes"
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
                                        {"prim": "bytes"},
                                        {
                                            "prim": "pair",
                                            "args": [
                                                {"prim": "int"},
                                                {"prim": "int"}
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

def createMessage(from_address, to_address, nonce, token_id, amount):
    message_to_encode = {
            "prim": "Pair",
            "args": [
                {
                    "string": from_address.pub_key
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
                                        "string": to_address.address
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
    return pytezos.michelson.pack.pack(message_to_encode, MESSAGE_STRUCTURE)