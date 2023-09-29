from django import forms

from django.utils.translation import gettext_lazy as _


class GenericBoundaryUploadForm(forms.Form):
    LEVEL_CHOICES = (
        ("0", _("Level 0")),
        ("1", _("Level 1")),
        ("2", _("Level 2")),
        ("3", _("Level 3")),
        ("4", _("Level 4")),
    )

    country = forms.ChoiceField(required=True, label=_("Country"))
    level = forms.ChoiceField(required=True, choices=LEVEL_CHOICES, label=_("Admin Boundary Level"))
    file = forms.FileField(required=True, label=_("Country Shapefile ZIP"),
                           widget=forms.FileInput(attrs={'accept': '.zip'}))

    def __init__(self, country_choices=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # set country options
        if country_choices:
            self.fields['country'].choices = [(country.code, country.name) for country in country_choices]


class CodAbsBoundaryUploadForm(GenericBoundaryUploadForm):
    LANGUAGE_CHOICES = (
        ("EN", "EN"),
        ("FR", "FR"),
    )
    language_suffix = forms.ChoiceField(required=True, choices=LANGUAGE_CHOICES, label=_("Language suffix"))


class GADMBoundaryUploadForm(forms.Form):
    country = forms.ChoiceField(required=True, label=_("Country"))
    file = forms.FileField(required=True, label=_("GADM Country Geopackage"),
                           help_text=_("The uploaded file should be a geopackage, "
                                       "downloaded from https://gadm.org/download_country.html"),
                           widget=forms.FileInput(attrs={'accept': '.gpkg'}))

    def __init__(self, country_choices=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # set country options
        if country_choices:
            self.fields['country'].choices = [(country.code, country.name) for country in country_choices]
