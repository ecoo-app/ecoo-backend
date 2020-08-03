from django.urls import reverse
from jet.templatetags.jet_tags import register
from jet.utils import get_menu_items

@register.simple_tag(takes_context=True)
def jet_get_menu(context):
    request = context['request']
    menu = get_menu_items(context)
    verification_menu = next((m for m in menu if m['app_label'] == 'verification' and m['has_perms']), None)
    if verification_menu is not None:
        extra_items = []
        extra_items.append({
                    'url': reverse('admin:user_import'),
                    'url_blank': False,
                    'name': 'user_import',
                    'object_name': 'Import Users',
                    'label': 'Import Users',
                    'has_perms': request.user.is_superuser,
                    'current': False
            }
        )    
        extra_items.append({
                    'url': reverse('admin:company_import'),
                    'url_blank': False,
                    'name': 'company_import',
                    'object_name': 'Import Companies',
                    'label': 'Import Companies',
                    'has_perms': request.user.is_superuser,
                    'current': False
            }
        )            
        verification_menu['items'] += extra_items

    return menu