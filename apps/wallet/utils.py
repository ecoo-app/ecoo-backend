from rest_framework.pagination import CursorPagination

class CustomCursorPagination(CursorPagination):
    ordering = 'created'


def getBalanceForWallet(wallet):
    # TODO: implement!!
    # TODO: get balance of account on blockchain & apply the transactions stored but not commited
    # entry point get_balance -> move function to utils

    return 104.0