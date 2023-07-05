from django.urls import path
from django.views.decorators.cache import cache_page

from adminboundarymanager.views import AdminBoundaryListView, AdminBoundaryVectorTileView, AdminBoundaryRetrieveView

urlpatterns = [
    path(r'api/admin-boundary/search', AdminBoundaryListView.as_view(), name="admin_boundary_search"),
    path(r'api/admin-boundary/<pk>', AdminBoundaryRetrieveView.as_view(), name="admin_boundary_detail"),
    path(r'api/admin-boundary/tiles/<int:z>/<int:x>/<int:y>', cache_page(3600)(AdminBoundaryVectorTileView.as_view()),
         name="admin_boundary_tiles"),
]
