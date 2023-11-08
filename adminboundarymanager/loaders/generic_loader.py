import os
import tempfile

import geopandas as gpd
from django.contrib.gis.utils import LayerMapping
from django.db import transaction

from adminboundarymanager.errors import (
    MissingBoundaryField,
    NoMatchingBoundaryData,
    InvalidBoundaryGeomType,
    UnsupportedBoundaryLevel
)
from adminboundarymanager.models import AdminBoundary
from adminboundarymanager.utils import extract_zipped_shapefile

COMMON_FIELDS = {
    "level": "LEVEL"
}

LEVEL0_BOUNDARY_FIELDS = {
    "name_0": "NAME_0",
    "gid_0": "GID_0",
}
LEVEL1_BOUNDARY_FIELDS = {
    **LEVEL0_BOUNDARY_FIELDS,
    "name_1": "NAME_1",
    "gid_1": "GID_1",
}

LEVEL2_BOUNDARY_FIELDS = {
    **LEVEL1_BOUNDARY_FIELDS,
    "name_2": "NAME_2",
    "gid_2": "GID_2",
}

LEVEL3_BOUNDARY_FIELDS = {
    **LEVEL2_BOUNDARY_FIELDS,
    "name_3": "NAME_3",
    "gid_3": "GID_3",
}

LEVEL4_BOUNDARY_FIELDS = {
    **LEVEL3_BOUNDARY_FIELDS,
    "name_4": "NAME_4",
    "gid_4": "GID_4",
}

GEOM_FIELD = {
    "geom": "MULTIPOLYGON",
}

VALID_GEOM_TYPES = ["Polygon", "MultiPolygon"]

GENERIC_FIELDS = {
    "level_0": LEVEL0_BOUNDARY_FIELDS,
    "level_1": LEVEL1_BOUNDARY_FIELDS,
    "level_2": LEVEL2_BOUNDARY_FIELDS,
    "level_3": LEVEL3_BOUNDARY_FIELDS,
}


@transaction.atomic
def check_and_load_boundaries(shp_path, country, level, remove_existing=True):
    # set required layermapping fields
    if level == 0:
        required_fields = LEVEL0_BOUNDARY_FIELDS
    elif level == 1:
        required_fields = LEVEL1_BOUNDARY_FIELDS
    elif level == 2:
        required_fields = LEVEL2_BOUNDARY_FIELDS
    elif level == 3:
        required_fields = LEVEL3_BOUNDARY_FIELDS
    elif level == 4:
        required_fields = LEVEL4_BOUNDARY_FIELDS
    else:
        raise UnsupportedBoundaryLevel(
            f"Unsupported admin boundary level : '{level}'. Supported levels are 0, 1, 2, 3 and 4.")

    required_fields.update({**COMMON_FIELDS})

    # read shapefile first layer
    gdf = gpd.read_file(shp_path, layer=0)

    # format columns to upper
    columns_rename_dict = {}
    for column in list(gdf.columns):
        columns_rename_dict[column] = column.upper()
    gdf.rename(columns=columns_rename_dict)

    # assign level
    gdf = gdf.assign(LEVEL=level)

    # get geom types
    geom_types = gdf.geometry.geom_type.unique()

    # validate expected geom types
    for geom_type in geom_types:
        if geom_type not in VALID_GEOM_TYPES:
            raise InvalidBoundaryGeomType(
                f"Invalid geometry type. Expected one of {VALID_GEOM_TYPES}. Not {geom_type}")

    # get shapefile fields
    layer_fields = list(gdf.columns)

    # check that all required fields exist
    for col in required_fields.values():
        if col not in layer_fields:
            compulsory_fields = required_fields.copy()
            compulsory_fields.pop("level")
            raise MissingBoundaryField(
                f"The shapefile does not contain all the required fields. "
                f"All of the following fields must be present: {', '.join(compulsory_fields.values())} ")

    # gdf should not be empty
    if gdf.empty:
        raise NoMatchingBoundaryData(
            "No matching boundary data. "
            "Please check the selected country and make sure it exists in the provided shapefile")

    # save gdf to temporary shapefile
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_shapefile_path = os.path.join(tmpdir, f'boundary_shapefile.shp')
        # Save the filtered data to a new Shapefile
        gdf.to_file(temp_shapefile_path, driver='ESRI Shapefile')

        layer_mapping_fields = {
            **required_fields,
            **GEOM_FIELD,
        }

        if remove_existing:
            # delete existing boundary data for given country iso and level
            AdminBoundary.objects.filter(gid_0=country.code, level=level).delete()
            AdminBoundary.objects.filter(gid_0=country.alpha3, level=level).delete()

        # do layermapping and save
        lm = LayerMapping(AdminBoundary, temp_shapefile_path, layer_mapping_fields)
        lm.save(verbose=True)


def load_generic_boundary(shp_zip_path, country, level=1, remove_existing=True, **kwargs):
    with tempfile.TemporaryDirectory() as tmpdir:
        # extract shapefile to get .shp file
        shp_path = extract_zipped_shapefile(shp_zip_path, tmpdir)
        # load boundaries
        check_and_load_boundaries(shp_path, country, level, remove_existing=remove_existing)
