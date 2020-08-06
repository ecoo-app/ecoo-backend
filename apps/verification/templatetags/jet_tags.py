from django import template
from django.conf import settings
register = template.Library()

# @register.filter
# def sort_apps(apps):
#     apps.sort(
#         key = lambda x:
#         settings.APP_ORDER.index(x['app_label'])
#         if x['app_label'] in settings.APP_ORDER
#         else len(apps)
#     )
#     print([x['app_label'] for x in apps])
#     return apps

# @register.filter
# def put_it_first(value, arg):
#     print('bla')
#     request = context['request']
#     menu = get_menu_items(context)
#     verification_menu = next((m for m in menu if m['app_label'] == 'verification' and m['has_perms']), None)
#     if verification_menu is not None:
#         extra_items = []
#         extra_items.append({
#                     'url': reverse('admin:user_import'),
#                     'url_blank': False,
#                     'name': 'user_import',
#                     'object_name': 'Import Users',
#                     'label': 'Import Users',
#                     'has_perms': request.user.is_superuser,
#                     'current': False
#             }
#         )    
#         extra_items.append({
#                     'url': reverse('admin:company_import'),
#                     'url_blank': False,
#                     'name': 'company_import',
#                     'object_name': 'Import Companies',
#                     'label': 'Import Companies',
#                     'has_perms': request.user.is_superuser,
#                     'current': False
#             }
#         )            
#         verification_menu['items'] += extra_items

#     return menu