import tempfile

from django.core.cache import cache
from django.db import connection, close_old_connections
from django.http import Http404, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.generics import ListAPIView, RetrieveAPIView
from wagtail.admin import messages
from wagtail.admin.auth import user_passes_test, user_has_any_page_permission

from .boundary_loader import load_cod_abs_boundary
from .forms import CodAbsBoundaryUploadForm
from .models import AdminBoundarySettings, AdminBoundary
from .serializers import AdminBoundarySerializer


@user_passes_test(user_has_any_page_permission)
def load_boundary(request):
    template = "adminboundarymanager/boundary_loader.html"

    abm_settings = AdminBoundarySettings.for_request(request)
    countries = [obj.country for obj in abm_settings.countries.all()]
    context = {}

    settings_url = reverse(
        "wagtailsettings:edit",
        args=[AdminBoundarySettings._meta.app_label, AdminBoundarySettings._meta.model_name, ],
    )

    context.update({"settings_url": settings_url})

    FormClass = CodAbsBoundaryUploadForm

    if request.POST:
        form = FormClass(countries, request.POST, request.FILES)

        if form.is_valid():
            shp_zip = form.cleaned_data.get("shp_zip")
            country = form.cleaned_data.get("country")
            level = form.cleaned_data.get("level")
            remove_existing = form.cleaned_data.get("remove_existing")

            if not country:
                form.add_error(None, "Please select a country in layer manager settings and try again")

            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{shp_zip.name}") as temp_file:
                for chunk in shp_zip.chunks():
                    temp_file.write(chunk)

                try:
                    load_cod_abs_boundary(shp_zip_path=temp_file.name,
                                          country_iso=country,
                                          level=int(level),
                                          remove_existing=remove_existing)
                except Exception as e:
                    form.add_error(None, str(e))
                    context.update({"form": form, "has_error": True})
                    countries = AdminBoundary.objects.filter(level=0)

                    if countries.exists():
                        context.update({"existing_countries": countries})

                    return render(request, template_name=template, context=context)

            messages.success(request, "Boundary data loaded successfully")

            # clear any existing vector tiles cache
            cache.clear()

            return redirect(reverse("adminboundarymanager_preview_boundary"))
        else:
            context.update({"form": form})
            return render(request, template_name=template, context=context)
    else:
        form = FormClass(countries)
        context["form"] = form

        return render(request, template_name=template, context=context)


@user_passes_test(user_has_any_page_permission)
def preview_boundary(request):
    template = "adminboundarymanager/boundary_preview.html"

    abm_settings = AdminBoundarySettings.for_request(request)
    countries = abm_settings.countries.all()

    boundary_tiles_url = abm_settings.boundary_tiles_url

    boundary_tiles_url = request.scheme + '://' + request.get_host() + boundary_tiles_url

    context = {
        "mapConfig": {
            "boundaryTilesUrl": boundary_tiles_url,
            "combinedBbox": abm_settings.combined_countries_bounds
        },
        "countries": countries,
        "load_boundary_url": reverse("adminboundarymanager_load_boundary")
    }

    return render(request, template, context=context)


class AdminBoundaryVectorTileView(View):
    table_name = "adminboundarymanager_adminboundary"

    def get(self, request, z, x, y):
        gid_0 = request.GET.get("gid_0")
        boundary_filter = ""

        if gid_0:
            boundary_filter = f"AND t.gid_0='{gid_0}'"

        sql = f"""WITH
            bounds AS (
              SELECT ST_TileEnvelope({z}, {x}, {y}) AS geom
            ),
            mvtgeom AS (
              SELECT ST_AsMVTGeom(ST_Transform(t.geom, 3857), bounds.geom) AS geom,
                *
              FROM {self.table_name} t, bounds
              WHERE ST_Intersects(ST_Transform(t.geom, 4326), ST_Transform(bounds.geom, 4326)) {boundary_filter}
            )
            SELECT ST_AsMVT(mvtgeom, 'default') FROM mvtgeom;
            """
        close_old_connections()
        with connection.cursor() as cursor:
            cursor.execute(sql)
            tile = cursor.fetchone()[0]
            if not len(tile):
                raise Http404()

        return HttpResponse(tile, content_type="application/x-protobuf")


class AdminBoundaryListView(ListAPIView):
    queryset = AdminBoundary.objects.all()
    serializer_class = AdminBoundarySerializer
    filter_backends = [SearchFilter, DjangoFilterBackend]
    filterset_fields = ["level", "id"]
    search_fields = ["name_0", "name_1", "name_2", "name_3", "name_4"]


class AdminBoundaryRetrieveView(RetrieveAPIView):
    queryset = AdminBoundary.objects.all()
    serializer_class = AdminBoundarySerializer
