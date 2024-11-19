import tempfile

from django.db import connection, close_old_connections
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.generics import ListAPIView, RetrieveAPIView
from wagtail.admin import messages
from wagtail.admin.auth import user_passes_test, user_has_any_page_permission
from wagtailcache.cache import cache_page
from wagtailcache.cache import clear_cache

from .forms import CodAbsBoundaryUploadForm, GADMBoundaryUploadForm, GenericBoundaryUploadForm
from .loaders import load_cod_abs_boundary, load_gadm_boundary, load_generic_boundary, data_sources
from .models import AdminBoundarySettings, AdminBoundary, Country
from .serializers import AdminBoundarySerializer


@user_passes_test(user_has_any_page_permission)
def load_boundary(request):
    template = "adminboundarymanager/boundary_loader.html"

    context = {}
    settings_url = reverse(
        "wagtailsettings:edit",
        args=[AdminBoundarySettings._meta.app_label, AdminBoundarySettings._meta.model_name, ],
    )
    context.update({"settings_url": settings_url})

    abm_settings = AdminBoundarySettings.for_request(request)

    context.update({"data_source": data_sources.get(abm_settings.data_source)})

    if abm_settings.data_source == "codabs":
        form_class = CodAbsBoundaryUploadForm
        loader_fn = load_cod_abs_boundary
    elif abm_settings.data_source == "gadm41":
        form_class = GADMBoundaryUploadForm
        loader_fn = load_gadm_boundary
    else:
        form_class = GenericBoundaryUploadForm
        loader_fn = load_generic_boundary

    countries = [obj.country for obj in abm_settings.countries.all()]

    if request.POST:
        form = form_class(countries, request.POST, request.FILES)

        if form.is_valid():
            file = form.cleaned_data.get("file")
            country_code = form.cleaned_data.get("country")
            language_suffix = form.cleaned_data.get("language_suffix")
            requires_language_suffix = False

            level = None

            if abm_settings.data_source != "gadm41":
                level = int(form.cleaned_data.get("level"))

            if abm_settings.data_source == "codabs":
                requires_language_suffix = True

            if not country_code:
                form.add_error(None, "Please select a country in layer manager settings and try again")

            country_option = Country.objects.get(country=country_code)

            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.name}") as temp_file:
                for chunk in file.chunks():
                    temp_file.write(chunk)

                try:
                    if requires_language_suffix and language_suffix:
                        loader_fn(temp_file.name, country=country_option.country, level=level,
                                  lang_suffix=language_suffix)
                    else:
                        loader_fn(temp_file.name, country=country_option.country, level=level, )
                except Exception as e:
                    form.add_error(None, str(e))
                    context.update({"form": form, "has_error": True})
                    countries = AdminBoundary.objects.filter(level=0)

                    if countries.exists():
                        context.update({"existing_countries": countries})

                    return render(request, template_name=template, context=context)

            messages.success(request, "Boundary data loaded successfully")

            # clear wagtail cache
            clear_cache()

            return redirect(reverse("adminboundarymanager_preview_boundary"))
        else:
            context.update({"form": form})
            return render(request, template_name=template, context=context)
    else:
        form = form_class(countries)
        context["form"] = form

        return render(request, template_name=template, context=context)


@user_passes_test(user_has_any_page_permission)
def preview_boundary(request):
    template = "adminboundarymanager/boundary_preview.html"

    abm_settings = AdminBoundarySettings.for_request(request)
    countries = abm_settings.countries.all()
    boundary_data_source = abm_settings.data_source

    boundary_tiles_url = abm_settings.boundary_tiles_url

    boundary_tiles_url = request.scheme + '://' + request.get_host() + boundary_tiles_url

    settings_url = reverse(
        "wagtailsettings:edit",
        args=[AdminBoundarySettings._meta.app_label, AdminBoundarySettings._meta.model_name, ],
    )

    context = {
        "mapConfig": {
            "boundaryTilesUrl": boundary_tiles_url,
            "combinedBbox": abm_settings.combined_countries_bounds
        },
        "countries": countries,
        "use_country_alpha3": boundary_data_source == "gadm41",
        "load_boundary_url": reverse("adminboundarymanager_load_boundary"),
        "settings_url": settings_url
    }

    return render(request, template, context=context)


@method_decorator(cache_page, name='get')
class AdminBoundaryVectorTileView(View):
    table_name = "adminboundarymanager_adminboundary"

    def get(self, request, z, x, y):
        abm_settings = AdminBoundarySettings.for_request(request)
        country_list = abm_settings.countries_list
        codes = [item for country in country_list for item in (country.get("code"), country.get("alpha3"))]
        boundary_filter = f"AND gid_0 IN {tuple(codes)}"

        gid_0 = request.GET.get("gid_0")
        if gid_0 and gid_0 in codes:
            boundary_filter = f"AND gid_0 = '{gid_0}'"

        sql = f"""WITH
            bounds AS (
              SELECT ST_TileEnvelope({z}, {x}, {y}) AS geom
            ),
            mvtgeom AS (
              SELECT ST_AsMVTGeom(ST_Transform(t.geom, 3857), bounds.geom) AS geom,
               t.id, t.name_0, t.name_1, t.name_2, t.name_3, t.name_4, t.gid_0, t.gid_1, t.gid_2, t.gid_3, t.gid_4, t.level
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


def get_boundary_info(request):
    context = {}

    abm_settings = AdminBoundarySettings.for_request(request)

    if not abm_settings.countries.exists():
        return JsonResponse({})

    site = abm_settings.site
    boundary_tiles_url = abm_settings.boundary_tiles_url
    boundary_tiles_url = site.root_url + boundary_tiles_url

    boundary_detail_url = reverse("admin_boundary_detail", args=[0]).replace("/0", "")
    boundary_detail_url = site.root_url + boundary_detail_url

    context.update({
        "tiles_url": boundary_tiles_url,
        "detail_url": boundary_detail_url,
        "country_bounds": abm_settings.combined_countries_bounds
    })

    return JsonResponse(context)
