from .cod_abs_loader import load_cod_abs_boundary
from .gadm_loader import load_gadm_boundary
from .generic_loader import load_generic_boundary, GENERIC_FIELDS

data_sources = {
    "codabs": {
        "title": "OCHA Administrative Boundary Common Operational Datasets (COD-ABS)",
        "description": "Administrative Boundary CODs are baseline geographical datasets that are used by humanitarian "
                       "agencies during preparedness and response activities. They are preferably sourced from "
                       "official government boundaries but when these are unavailable the IM network must develop and "
                       "agree to a process to develop an alternate dataset.",
        "data_detail_urls": [
            {
                "label": "About Administrative Boundary CODs (COD-AB)",
                "url": "https://humanitarian.atlassian.net/wiki/spaces/codtsp/pages/41973316/Administrative+Boundary+CODs+COD-AB"
            },
            {
                "label": "More about OCHA CODs",
                "url": "https://storymaps.arcgis.com/stories/dcf6135fc0e943a9b77823bb069e2578"
            }
        ],
        "data_download_url": "https://data.humdata.org/dashboards/cod?cod_level=cod-standard&cod_level=cod-enhanced"
                             "&dataseries_name=COD%20-%20Subnational%20Administrative%20Boundaries&q=&sort=if(gt("
                             "last_modified%2Creview_date)%2Clast_modified%2Creview_date)%20desc",
        "levels": []
    },
    "gadm41": {
        "title": "Global Administrative Areas 4.1 (GADM)",
        "description": "GADM is a database of the location of the world's administrative areas (boundaries). "
                       "Administrative areas in this database include: countries, counties, districts, "
                       "etc. and cover every country in the world. For each area it provides some attributes, "
                       "foremost being the name and in some cases variant names.",
        "data_detail_urls": [
            {
                "label": "Learn More ",
                "url": "https://gadm.org/"
            }
        ],
        "data_download_url": "https://gadm.org/data.html"
    },
    "generic": {
        "title": "Generic Data Source",
        "description": "Load boundaries data from other sources, that follow the defined data model",
        "data_source_url": None,
        "levels": [
            {"level": 0, "fields": GENERIC_FIELDS.get("level_0")},
            {"level": 1, "fields": GENERIC_FIELDS.get("level_1")},
            {"level": 2, "fields": GENERIC_FIELDS.get("level_1")},
            {"level": 3, "fields": GENERIC_FIELDS.get("level_1")},
        ],
    }
}
