from wagtail_modeladmin.options import modeladmin_register

from adminboundarymanager.wagtail_hooks import AdminBoundaryManagerAdminGroup

modeladmin_register(AdminBoundaryManagerAdminGroup)
