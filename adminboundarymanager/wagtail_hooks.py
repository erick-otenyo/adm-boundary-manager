from django.contrib.auth.models import Permission
from django.urls import path, reverse
from django.utils.functional import cached_property
from wagtail import hooks
from wagtail.admin.viewsets import ViewSetGroup
from wagtail.admin.viewsets.base import ViewSet

from .models import AdminBoundarySettings
from .views import load_boundary, preview_boundary


@hooks.register('register_admin_urls')
def urlconf_boundarymanager():
    return [
        path('load-boundary/', load_boundary, name='adminboundarymanager_load_boundary'),
        path('preview-boundary/', preview_boundary, name='adminboundarymanager_preview_boundary'),
    ]


class BoundaryLoaderViewSet(ViewSet):
    menu_label = "Boundary Data"
    icon = "upload"
    name = "boundary-loader"
    
    def get_urlpatterns(self):
        return [
            path('', preview_boundary, name='boundary_loader_index'),
        ]


class BoundarySettingsViewSet(ViewSet):
    menu_label = "Boundary Settings"
    icon = "cog"
    name = "boundary-settings"
    
    @cached_property
    def menu_url(self):
        settings_url = reverse(
            "wagtailsettings:edit",
            args=[AdminBoundarySettings._meta.app_label, AdminBoundarySettings._meta.model_name, ],
        )
        return settings_url


class AdminBoundaryViewSetGroup(ViewSetGroup):
    menu_label = "Boundaries"
    menu_icon = "snippet"
    add_to_admin_menu = True
    
    items = [
        BoundaryLoaderViewSet(),
        BoundarySettingsViewSet(),
    ]


@hooks.register("register_permissions")
def register_permissions():
    return Permission.objects.filter(content_type__app_label="adminboundarymanager")
