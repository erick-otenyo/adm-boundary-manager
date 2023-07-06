from django import forms

from django.utils.translation import gettext_lazy as _


class CodAbsBoundaryUploadForm(forms.Form):
    LEVEL_CHOICES = (
        ("0", _("Level 0")),
        ("1", _("Level 1")),
        ("2", _("Level 2")),
        ("3", _("Level 3")),
        ("4", _("Level 4")),
    )
    country = forms.ChoiceField(required=True, label=_("Country"))
    level = forms.ChoiceField(required=True, choices=LEVEL_CHOICES, label=_("Admin Boundary Level"))
    shp_zip = forms.FileField(required=True, label=_("Country Shapefile ZIP"),
                              widget=forms.FileInput(attrs={'accept': '.zip'}))

    def __init__(self, country_choices=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # set country options
        if country_choices:
            self.fields['country'].choices = [(country.code, country.name) for country in country_choices]
