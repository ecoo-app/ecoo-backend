from django.contrib.auth.models import Permission
from django.test import TestCase
from django.test.client import Client
from django.urls.base import reverse

from apps.currency.models import Currency
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
