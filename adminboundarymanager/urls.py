from django.urls import path

from adminboundarymanager.views import (
    AdminBoundaryListView,
    AdminBoundaryVectorTileView,
    AdminBoundaryRetrieveView,
    get_boundary_info
)

urlpatterns = [
    path(r'api/admin-boundary/info', get_boundary_info, name="admin_boundary_info"),
    path(r'api/admin-boundary/search', AdminBoundaryListView.as_view(), name="admin_boundary_search"),
    path(r'api/admin-boundary/<pk>', AdminBoundaryRetrieveView.as_view(), name="admin_boundary_detail"),
    path(r'api/admin-boundary/tiles/<int:z>/<int:x>/<int:y>', AdminBoundaryVectorTileView.as_view(),
         name="admin_boundary_tiles"),
]
