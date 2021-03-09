import pytezos
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls.base import reverse

from apps.wallet.models import (
    CashOutRequest,
    MetaTransaction,
    PaperWallet,
    Transaction,
    Wallet,
    WalletPublicKeyTransferRequest,
)
from project.utils_testing import EcouponTestCaseMixin


class WalletAdminTestCase(EcouponTestCaseMixin, TestCase):
    def test_only_staff_see_wallet_admin(self):
        self.client.force_login(self.user)
        url = reverse("admin:wallet_wallet_changelist")
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.startswith("/admin/login"))
        self.user.user_permissions.add(Permission.objects.get(codename="view_wallet"))
        self.user.user_permissions.add(
            Permission.objects.get(codename="can_view_all_currencies")
        )
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.startswith("/admin/login"))

        self.client.force_login(self.staff_user)
        self.staff_user.user_permissions.add(
            Permission.objects.get(codename="view_wallet")
        )
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_see_correct_wallets(self):
        url = reverse("admin:wallet_wallet_changelist")
        self.staff_user.user_permissions.add(
            Permission.objects.get(codename="view_wallet")
        )
        self.client.force_login(self.staff_user)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            list(resp.context_data["cl"].queryset),
            [],
        )

        self.currency.users.add(self.staff_user)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            sorted(list(resp.context_data["cl"].queryset), key=lambda x: x.wallet_id),
            sorted(
                list(Wallet.objects.filter(currency=self.currency)),
                key=lambda x: x.wallet_id,
            ),
        )

        self.staff_user.user_permissions.add(
            Permission.objects.get(codename="can_view_all_currencies")
        )

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            sorted(list(resp.context_data["cl"].queryset), key=lambda x: x.wallet_id),
            sorted(list(Wallet.objects.all()), key=lambda x: x.wallet_id),
        )


class PaperWalletAdminTestCase(EcouponTestCaseMixin, TestCase):
    # TODO: FIXME: add test for admin actions
    def test_only_staff_see_wallet_admin(self):
        self.client.force_login(self.user)
        url = reverse("admin:wallet_paperwallet_changelist")
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.startswith("/admin/login"))
        self.user.user_permissions.add(
            Permission.objects.get(codename="view_paperwallet")
        )
        self.user.user_permissions.add(
            Permission.objects.get(codename="can_view_all_currencies")
        )
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.startswith("/admin/login"))

        self.client.force_login(self.staff_user)
        self.staff_user.user_permissions.add(
            Permission.objects.get(codename="view_paperwallet")
        )
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_see_correct_wallets(self):
        url = reverse("admin:wallet_paperwallet_changelist")
        self.staff_user.user_permissions.add(
            Permission.objects.get(codename="view_paperwallet")
        )
        self.client.force_login(self.staff_user)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            list(resp.context_data["cl"].queryset),
            [],
        )

        self.currency.users.add(self.staff_user)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            sorted(list(resp.context_data["cl"].queryset), key=lambda x: x.wallet_id),
            sorted(
                list(PaperWallet.objects.filter(currency=self.currency)),
                key=lambda x: x.wallet_id,
            ),
        )

        self.staff_user.user_permissions.add(
            Permission.objects.get(codename="can_view_all_currencies")
        )

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            sorted(list(resp.context_data["cl"].queryset), key=lambda x: x.wallet_id),
            sorted(list(PaperWallet.objects.all()), key=lambda x: x.wallet_id),
        )


class TransactionAdminTestCase(EcouponTestCaseMixin, TestCase):
    # TODO: FIXME: add test for admin actions

    def test_only_staff_see_transaction_admin(self):
        self.client.force_login(self.user)
        url = reverse("admin:wallet_transaction_changelist")
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.startswith("/admin/login"))
        self.user.user_permissions.add(
            Permission.objects.get(codename="view_transaction")
        )
        self.user.user_permissions.add(
            Permission.objects.get(codename="can_view_all_currencies")
        )
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.startswith("/admin/login"))

        self.client.force_login(self.staff_user)
        self.staff_user.user_permissions.add(
            Permission.objects.get(codename="view_transaction")
        )
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_see_correct_transactions(self):
        url = reverse("admin:wallet_transaction_changelist")

        def sorting_fun(x):
            if x.to_wallet:
                return x.to_wallet.wallet_id
            else:
                return x.amount

        self.staff_user.user_permissions.add(
            Permission.objects.get(codename="view_transaction")
        )
        self.client.force_login(self.staff_user)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            list(resp.context_data["cl"].queryset),
            [],
        )

        self.currency.users.add(self.staff_user)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            sorted(
                list(resp.context_data["cl"].queryset),
                key=sorting_fun,
            ),
            sorted(
                list(Transaction.objects.filter(to_wallet__currency=self.currency)),
                key=sorting_fun,
            ),
        )

        self.staff_user.user_permissions.add(
            Permission.objects.get(codename="can_view_all_currencies")
        )

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            sorted(
                list(resp.context_data["cl"].queryset),
                key=sorting_fun,
            ),
            sorted(list(Transaction.objects.all()), key=sorting_fun),
        )


class MetaTransactionAdminTestCase(EcouponTestCaseMixin, TestCase):
    def test_only_staff_see_transaction_admin(self):
        self.client.force_login(self.user)
        url = reverse("admin:wallet_metatransaction_changelist")
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.startswith("/admin/login"))
        self.user.user_permissions.add(
            Permission.objects.get(codename="view_metatransaction")
        )
        self.user.user_permissions.add(
            Permission.objects.get(codename="can_view_all_currencies")
        )
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.startswith("/admin/login"))

        self.client.force_login(self.staff_user)
        self.staff_user.user_permissions.add(
            Permission.objects.get(codename="view_metatransaction")
        )
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_see_correct_transactions(self):
        url = reverse("admin:wallet_metatransaction_changelist")

        def sorting_fun(x):
            if x.to_wallet:
                return x.to_wallet.wallet_id
            else:
                return x.amount

        self.staff_user.user_permissions.add(
            Permission.objects.get(codename="view_metatransaction")
        )
        self.client.force_login(self.staff_user)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            list(resp.context_data["cl"].queryset),
            [],
        )

        self.currency.users.add(self.staff_user)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            sorted(
                list(resp.context_data["cl"].queryset),
                key=sorting_fun,
            ),
            sorted(
                list(MetaTransaction.objects.filter(to_wallet__currency=self.currency)),
                key=sorting_fun,
            ),
        )

        self.staff_user.user_permissions.add(
            Permission.objects.get(codename="can_view_all_currencies")
        )

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            sorted(
                list(resp.context_data["cl"].queryset),
                key=sorting_fun,
            ),
            sorted(list(MetaTransaction.objects.all()), key=sorting_fun),
        )


class WalletPublickeyRequestAdminTestCase(EcouponTestCaseMixin, TestCase):
    def setUp(self):
        super().setUp()

        new_key = pytezos.crypto.key.Key.generate()
        WalletPublicKeyTransferRequest.objects.create(
            wallet=self.wallet_1,
            old_public_key=self.wallet_1.public_key,
            new_public_key=new_key.public_key(),
        )

        new_key = pytezos.crypto.key.Key.generate()
        WalletPublicKeyTransferRequest.objects.create(
            wallet=self.wallet_1_2_2,
            old_public_key=self.wallet_1_2_2.public_key,
            new_public_key=new_key.public_key(),
        )

    def test_only_staff_see_walletpublickeytransferrequest_admin(self):
        self.client.force_login(self.user)
        url = reverse("admin:wallet_walletpublickeytransferrequest_changelist")
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.startswith("/admin/login"))
        self.user.user_permissions.add(
            Permission.objects.get(codename="view_walletpublickeytransferrequest")
        )
        self.user.user_permissions.add(
            Permission.objects.get(codename="can_view_all_currencies")
        )
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.startswith("/admin/login"))

        self.client.force_login(self.staff_user)
        self.staff_user.user_permissions.add(
            Permission.objects.get(codename="view_walletpublickeytransferrequest")
        )
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_see_correct_walletpublickeytransferrequest(self):
        url = reverse("admin:wallet_walletpublickeytransferrequest_changelist")

        def sorting_fun(x):
            return x.wallet.wallet_id

        self.staff_user.user_permissions.add(
            Permission.objects.get(codename="view_walletpublickeytransferrequest")
        )
        self.client.force_login(self.staff_user)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            list(resp.context_data["cl"].queryset),
            [],
        )

        self.currency.users.add(self.staff_user)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            sorted(
                list(resp.context_data["cl"].queryset),
                key=sorting_fun,
            ),
            sorted(
                list(
                    WalletPublicKeyTransferRequest.objects.filter(
                        wallet__currency=self.currency
                    )
                ),
                key=sorting_fun,
            ),
        )

        self.staff_user.user_permissions.add(
            Permission.objects.get(codename="can_view_all_currencies")
        )

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            sorted(
                list(resp.context_data["cl"].queryset),
                key=sorting_fun,
            ),
            sorted(list(WalletPublicKeyTransferRequest.objects.all()), key=sorting_fun),
        )


class CashOutRequestAdminTestCase(EcouponTestCaseMixin, TestCase):
    # TODO: FIXME: add test for admin action

    def setUp(self):
        super().setUp()
        tx1 = Transaction.objects.create(
            from_wallet=self.wallet_1, to_wallet=self.currency.owner_wallet, amount=5
        )
        CashOutRequest.objects.create(
            transaction=tx1,
            beneficiary_name="baba",
            beneficiary_iban="CH93 0076 2011 6238 5295 7",
        )

        tx2 = Transaction.objects.create(
            from_wallet=self.wallet_2_2,
            to_wallet=self.currency_2.owner_wallet,
            amount=5,
        )
        CashOutRequest.objects.create(
            transaction=tx2,
            beneficiary_name="baba",
            beneficiary_iban="CH93 0076 2011 6238 5295 7",
        )

    def test_only_staff_see_cashoutrequest_admin(self):
        self.client.force_login(self.user)

        url = reverse("admin:wallet_cashoutrequest_changelist")
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.startswith("/admin/login"))
        self.user.user_permissions.add(
            Permission.objects.get(codename="view_cashoutrequest")
        )
        self.user.user_permissions.add(
            Permission.objects.get(codename="can_view_all_currencies")
        )
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.startswith("/admin/login"))

        self.client.force_login(self.staff_user)
        self.staff_user.user_permissions.add(
            Permission.objects.get(codename="view_cashoutrequest")
        )
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_see_correct_cashoutrequest(self):
        url = reverse("admin:wallet_cashoutrequest_changelist")

        def sorting_fun(x):
            return x.transaction.from_wallet.wallet_id

        self.staff_user.user_permissions.add(
            Permission.objects.get(codename="view_cashoutrequest")
        )
        self.client.force_login(self.staff_user)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            list(resp.context_data["cl"].queryset),
            [],
        )

        self.currency.users.add(self.staff_user)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            sorted(
                list(resp.context_data["cl"].queryset),
                key=sorting_fun,
            ),
            sorted(
                list(
                    CashOutRequest.objects.filter(
                        transaction__from_wallet__currency=self.currency
                    )
                ),
                key=sorting_fun,
            ),
        )

        self.staff_user.user_permissions.add(
            Permission.objects.get(codename="can_view_all_currencies")
        )

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            sorted(
                list(resp.context_data["cl"].queryset),
                key=sorting_fun,
            ),
            sorted(list(CashOutRequest.objects.all()), key=sorting_fun),
        )
