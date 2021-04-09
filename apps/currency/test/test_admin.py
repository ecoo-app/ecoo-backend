from django.contrib.auth.models import Permission
from django.test import TestCase
from django.test.client import Client
from django.urls.base import reverse

from apps.currency.models import Currency
from apps.wallet.models import PaperWallet
from project.utils_testing import BaseEcouponApiTestCase, EcouponTestCaseMixin


class CurrencyTestCase(BaseEcouponApiTestCase):
    pass


class CurrencyAdminTestCase(EcouponTestCaseMixin, TestCase):
    def test_normaluser_view(self):
        self.client.force_login(self.user)
        url = reverse("admin:currency_currency_changelist")
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.startswith("/admin/login"))
        self.staff_user.user_permissions.add(
            Permission.objects.get(codename="view_currency")
        )
        self.user.user_permissions.add(
            Permission.objects.get(codename="can_view_all_currencies")
        )
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.startswith("/admin/login"))

    def test_staffuser_view_all(self):

        self.staff_user.user_permissions.add(
            Permission.objects.get(codename="view_currency")
        )
        self.staff_user.save()
        self.currency.users.add(self.staff_user)
        self.currency.save()
        self.staff_user.refresh_from_db()

        self.client = Client()
        self.client.force_login(self.staff_user)
        url = reverse("admin:currency_currency_changelist")
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            list(resp.context_data["cl"].queryset),
            list(Currency.objects.filter(pk=self.currency.pk)),
        )

        self.staff_user.user_permissions.add(
            Permission.objects.get(codename="can_view_all_currencies")
        )
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            sorted(list(resp.context_data["cl"].queryset), key=lambda x: x.name),
            sorted(list(Currency.objects.all()), key=lambda x: x.name),
        )

    def test_create_paper_wallet_consumer(self):
        self.client.force_login(self.staff_user)
        self.staff_user.is_superuser = True
        self.staff_user.save()
        self.staff_user.refresh_from_db()

        url = reverse("admin:currency_currency_changelist")
        data = {
            "action": "generate_paper_wallet_consumer",
            "_selected_action": [str(self.currency.pk)],
        }

        paper_wallet_count = PaperWallet.objects.count()

        response = self.client.post(url, data, follow=True)

        self.assertTrue(paper_wallet_count + 1, PaperWallet.objects.count())
        self.assertTrue(response.status_code, 200)

        paper_wallet = PaperWallet.objects.get(pk=response.context_data["object_id"])
        self.assertEqual(paper_wallet.balance, self.currency.starting_capital)

    def test_create_paper_wallet_company(self):
        self.client.force_login(self.staff_user)
        self.staff_user.is_superuser = True
        self.staff_user.save()
        self.staff_user.refresh_from_db()
        paper_wallet_count = PaperWallet.objects.count()
        url = reverse("admin:currency_currency_changelist")
        data = {
            "action": "generate_paper_wallet_company",
            "_selected_action": [str(self.currency.pk)],
        }

        paper_wallet_count = PaperWallet.objects.count()

        response = self.client.post(url, data, follow=True)

        self.assertTrue(paper_wallet_count + 1, PaperWallet.objects.count())
        self.assertTrue(response.status_code, 200)

        paper_wallet = PaperWallet.objects.get(pk=response.context_data["object_id"])
        self.assertEqual(paper_wallet.balance, 0)
