from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls.base import reverse

from apps.wallet.models import MetaTransaction, Transaction, Wallet
from project.utils_testing import EcouponTestCaseMixin

# TODO: add test for paperwallet admin actions


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


class TransactionAdminTestCase(EcouponTestCaseMixin, TestCase):
    def setUp(self):
        super().setUp()
        Transaction.objects.create(to_wallet=self.wallet_1, amount=20)
        Transaction.objects.create(to_wallet=self.wallet_1_2, amount=20)
        Transaction.objects.create(to_wallet=self.wallet_1_2_2, amount=20)
        Transaction.objects.create(to_wallet=self.wallet_2, amount=20)

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
