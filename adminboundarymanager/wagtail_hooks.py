from django.contrib.auth.models import Permission
from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.menu import MenuItem, Menu
from wagtail_modeladmin.menus import GroupMenuItem
from wagtail_modeladmin.options import ModelAdminGroup, ModelAdmin

from .models import AdminBoundarySettings, AdminBoundary
from .views import load_boundary, preview_boundary


@hooks.register('register_admin_urls')
def urlconf_boundarymanager():
    return [
        path('load-boundary/', load_boundary, name='adminboundarymanager_load_boundary'),
        path('preview-boundary/', preview_boundary, name='adminboundarymanager_preview_boundary'),
    ]


class ModelAdminCanHide(ModelAdmin):
    hidden = False


class ModelAdminGroupWithHiddenItems(ModelAdminGroup):
    def get_submenu_items(self):
        menu_items = []
        item_order = 1
        for model_admin in self.modeladmin_instances:
            if not model_admin.hidden:
                menu_items.append(model_admin.get_menu_item(order=item_order))
                item_order += 1
        return menu_items


class AdminBoundaryModelAdmin(ModelAdminCanHide):
    model = AdminBoundary
    hidden = True


class AdminBoundaryMenuGroupAdminMenuItem(GroupMenuItem):
    def is_shown(self, request):
        return request.user.has_perm("adminboundarymanager.can_view_adm_boundary_menu")


class AdminBoundaryManagerAdminGroup(ModelAdminGroupWithHiddenItems):
    menu_label = _('Boundary Manager')
    menu_order = 700
    items = (AdminBoundaryModelAdmin,)
    
    def get_menu_item(self, order=None):
        if self.modeladmin_instances:
            submenu = Menu(items=self.get_submenu_items())
            return AdminBoundaryMenuGroupAdminMenuItem(self, self.get_menu_order(), submenu)
    
    def get_submenu_items(self):
        menu_items = super().get_submenu_items()
        
        boundary_loader = MenuItem(label=_("Boundary Data"), url=reverse("adminboundarymanager_preview_boundary"),
                                   icon_name="snippet")
        menu_items.append(boundary_loader)
        
        try:
            settings_url = reverse(
                "wagtailsettings:edit",
                args=[AdminBoundarySettings._meta.app_label, AdminBoundarySettings._meta.model_name, ],
            )
            abm_settings_menu = MenuItem(label=_("Admin Boundary Settings"), url=settings_url, icon_name="cog")
            menu_items.append(abm_settings_menu)
        except Exception:
            pass
        
        return menu_items


@hooks.register("register_permissions")
def register_permissions():
    return Permission.objects.filter(content_type__app_label="adminboundarymanager")
