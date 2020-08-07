from django.contrib.admin import AdminSite
from django.urls import reverse


class MyAdminSite(AdminSite):
    def get_app_list(self, request):
        app_list = super(MyAdminSite, self).get_app_list(request)

        wallet_menu = next(
            (m for m in app_list if m['app_label'] == 'wallet' and m['has_module_perms']), None)
        if wallet_menu is not None:
            extra_items = []
            extra_items.append(
                {
                    "name": "Generate Wallets",
                    "admin_url": '/admin/wallet/paperwallet/generate-wallets/',
                    'perms': {'add': False, 'change': False, 'delete': False, 'view': True}
                }
            )
            wallet_menu['models'] += extra_items

        verification_menu = next(
            (m for m in app_list if m['app_label'] == 'verification' and m['has_module_perms']), None)
        if verification_menu is not None:
            extra_items = []
            extra_items.append(
                {
                    "name": "Import Users",
                    "admin_url": reverse('admin:user_import')
                }
            )
            extra_items.append(
                {
                    "name": "Import Companies",
                    "admin_url": reverse('admin:company_import')
                }
            )
            verification_menu['models'] += extra_items
        return app_list
# http://localhost:8000/admin/wallet/paperwallet/generate-wallets/