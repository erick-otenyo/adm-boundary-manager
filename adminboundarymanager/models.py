from django.contrib.gis.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from shapely import geometry, unary_union, Polygon
from wagtail.admin.forms.models import (
    WagtailAdminModelForm,
)
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.contrib.settings.models import BaseSiteSetting
from wagtail.contrib.settings.registry import register_setting
from wagtail.models import Orderable
from wagtailcache.cache import clear_cache


class AdminBoundary(models.Model):
    name_0 = models.CharField(max_length=100, blank=True, null=True)
    name_1 = models.CharField(max_length=100, blank=True, null=True)
    name_2 = models.CharField(max_length=100, blank=True, null=True)
    name_3 = models.CharField(max_length=100, blank=True, null=True)
    name_4 = models.CharField(max_length=100, blank=True, null=True)
    gid_0 = models.CharField(max_length=100, blank=True, null=True)
    gid_1 = models.CharField(max_length=100, blank=True, null=True)
    gid_2 = models.CharField(max_length=100, blank=True, null=True)
    gid_3 = models.CharField(max_length=100, blank=True, null=True)
    gid_4 = models.CharField(max_length=100, blank=True, null=True)
    level = models.IntegerField(blank=True, null=True)
    
    geom = models.MultiPolygonField(srid=4326)
    
    class Meta:
        verbose_name_plural = _("Administrative Boundaries")
    
    def __str__(self):
        level = self.level
        country_name = self.name_0
        
        prefix = f"{country_name} - Level "
        
        if level == 0:
            return f"{prefix} {level} - {self.name_0}"
        
        if level == 1:
            return f"{prefix} {level} - {self.name_1}"
        
        if level == 2:
            return f"{prefix} {level} - {self.name_2}"
        
        if level == 3:
            return f"{prefix} {level} - {self.name_3}"
        
        return f"{prefix} {level} - {self.pk}"
    
    @property
    def bbox(self):
        min_x, min_y, max_x, max_y = self.geom.envelope.extent
        bbox = [min_x, min_y, max_x, max_y]
        return bbox
    
    @property
    def info(self):
        info = {"iso": self.gid_0}
        
        if self.level == 0:
            info.update({"name": self.name_0})
        
        if self.level == 1:
            gid_1 = self.gid_1.split(".")[1].split("_")[0]
            info.update({"id1": gid_1, "name": self.name_1})
        
        if self.level == 2:
            gid_1 = self.gid_1.split(".")[1].split("_")[0]
            gid_2 = self.gid_1.split(".")[1].split("_")[1]
            info.update({"id1": gid_1, "id2": gid_2, "name": self.name_2})
        
        return info


class AdminBoundaryForm(WagtailAdminModelForm):
    def is_valid(self):
        form_is_valid = super().is_valid()
        
        if form_is_valid:
            countries_formset = self.formsets.get("countries")
            countries_cleaned_data = countries_formset.cleaned_data
            
            countries = []
            for country in countries_cleaned_data:
                to_delete = country.get("DELETE")
                
                if not to_delete:
                    country_obj = Country(country=country.get("country"))
                    countries.append(country_obj)
            
            cleaned_data = self.cleaned_data
            countries_must_share_boundaries = cleaned_data.get("countries_must_share_boundaries")
            
            if countries_must_share_boundaries and len(countries) > 1:
                bounds_polygons = []
                for country in countries:
                    if country.country_bounds_polygon:
                        bounds_polygons.append(country.country_bounds_polygon)
                
                if bounds_polygons:
                    union_polygon = bounds_polygons[0]
                    
                    for polygon in bounds_polygons[1:]:
                        union_polygon = union_polygon.union(polygon)
                    
                    connected = isinstance(union_polygon, Polygon)
                    if not connected:
                        error = _("One or more selected countries do not share boundaries. "
                                  "Please make sure all the countries are in one region and share boundaries")
                        # add error
                        self.formsets.get("countries")._non_form_errors.append(error)
                        
                        return False
        
        return form_is_valid


@register_setting
class AdminBoundarySettings(BaseSiteSetting, ClusterableModel):
    base_form_class = AdminBoundaryForm
    
    DATA_SOURCE_CHOICES = (
        ("codabs", "OCHA Administrative Boundary Common Operational Datasets (COD-ABS)"),
        ("gadm41", "Global Administrative Areas 4.1 (GADM)"),
        ("generic", "Generic Data Source")
    )
    
    data_source = models.CharField(max_length=100, choices=DATA_SOURCE_CHOICES, default="codabs",
                                   verbose_name=_("Boundary Data Source"), help_text="Source of the boundaries data")
    countries_must_share_boundaries = models.BooleanField(default=True,
                                                          verbose_name=_(
                                                              "Countries must share boundaries - If more than one"),
                                                          help_text=_(
                                                              "Validation to ensure that the selected countries share "
                                                              "boundaries with each other. Used if two or more "
                                                              "countries are set."))
    
    panels = [
        FieldPanel("data_source"),
        FieldPanel("countries_must_share_boundaries"),
        InlinePanel("countries", heading=_("Countries"), label=_("Country Detail")),
    ]
    
    @cached_property
    def countries_list(self):
        countries = []
        for country in self.countries.all():
            countries.append({
                "name": country.country.name,
                "code": country.country.code,
                "alpha3": country.country.alpha3,
                "bbox": country.country.geo_extent
            })
        return countries
    
    @cached_property
    def combined_countries_bounds(self):
        bounds_polygons = self.get_country_bounds_polygons()
        if not bounds_polygons:
            return None
        combined_polygon = unary_union(bounds_polygons)
        return list(combined_polygon.bounds)
    
    def get_country_bounds_polygons(self):
        bounds_polygons = []
        for country in self.countries_list:
            if country.get("bbox"):
                bbox = country.get("bbox")
                polygon = geometry.box(*bbox, ccw=True)
                bounds_polygons.append(polygon)
        return bounds_polygons
    
    @cached_property
    def boundary_tiles_url(self):
        return reverse("admin_boundary_tiles", args=[0, 0, 0]).replace("/0/0/0", r"/{z}/{x}/{y}")


class Country(Orderable):
    objects = None
    parent = ParentalKey(AdminBoundarySettings, on_delete=models.CASCADE, related_name='countries')
    country = CountryField(blank_label=_("Select Country"), verbose_name=_("country"), unique=True)
    
    panels = [
        FieldPanel("country", widget=CountrySelectWidget()),
    ]
    
    @cached_property
    def country_bounds_polygon(self):
        bbox = self.country.geo_extent
        if not bbox:
            return None
        polygon = geometry.box(*bbox, ccw=True)
        return polygon


@receiver(post_save, sender=AdminBoundarySettings)
def handle_post_save_settings(sender, instance, **kwargs):
    # clear cache after saving boundary settings
    clear_cache()


# delete any existing country boundaries after deleting a country
@receiver(post_delete, sender=Country)
def after_country_delete(sender, instance, **kwargs):
    country = instance.country
    country_codes_to_delete = [country.code, country.alpha3]
    
    # delete admin boundaries for countries in list
    AdminBoundary.objects.filter(gid_0__in=country_codes_to_delete).delete()


@receiver(post_save, sender=Country)
def after_country_save(sender, instance, created, **kwargs):
    # get countries
    setting_countries = instance.parent.countries.all()
    
    ready = True
    codes_not_to_delete = []
    
    # check that all countries have been saved
    for country in setting_countries:
        # check if the country has been saved to db
        if not country.id:
            ready = False
    
    if ready:
        for c in setting_countries:
            codes_not_to_delete.append(c.country.code)
            codes_not_to_delete.append(c.country.alpha3)
        
        # all countries
        all_countries = Country.objects.all()
        for country in all_countries:
            codes_not_to_delete.append(country.country.code)
            codes_not_to_delete.append(country.country.alpha3)
        
        # delete all boundaries not for set countries
        AdminBoundary.objects.exclude(gid_0__in=codes_not_to_delete).delete()


from django.db import models
from django.utils.translation import gettext_lazy as _


class BoundaryMenuPermission(models.Model):
    class Meta:
        verbose_name = _('Admin Boundary Menu Permission')
        verbose_name_plural = _('Admin Boundary Menu Permissions')
        default_permissions = ([])
        
        permissions = (
            ('can_view_adm_boundary_menu)', 'Can view Admin Boundary Menu'),
        )
