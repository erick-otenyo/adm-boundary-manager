import glob
import os
import re
from zipfile import ZipFile

from adminboundarymanager.errors import NoShpFound, NoShxFound, NoDbfFound


def _pick_shapefile(shp_paths, level=None):
    """The shapefile for `level` when a zip holds several, else the first (sorted).

    COD-AB packages put every level in one zip (som_admin0.shp, som_admin1.shp, ...),
    with edge-matched (_em), lines and points variants beside them.
    """
    shp_paths = sorted(shp_paths)
    if level is None or len(shp_paths) == 1:
        return shp_paths[0]
    matching = [s for s in shp_paths if re.search(rf"adm(?:in)?{int(level)}(?![0-9])", os.path.basename(s), re.I)]
    plain = [s for s in matching if not re.search(r"_em|lines|points", os.path.basename(s), re.I)]
    return (plain or matching or shp_paths)[0]


def extract_zipped_shapefile(shp_zip_path, out_dir, level=None):
    # unzip file
    with ZipFile(shp_zip_path, 'r') as zip_obj:
        for filename in zip_obj.namelist():
            # ignore __macosx files
            if not filename.startswith('__MACOSX/'):
                zip_obj.extract(filename, out_dir)

    shp = glob.glob(f"{out_dir}/*.shp") or glob.glob(f"{out_dir}/*/*.shp")

    if not shp:
        raise NoShpFound("No shapefile found in provided zip file")

    shp_path = _pick_shapefile(shp, level)
    shp_fn = os.path.splitext(shp_path)[0]
    shp_dir = os.path.dirname(shp_fn)

    files = [os.path.join(shp_dir, f) for f in os.listdir(shp_dir)]

    # check for .shx
    if f"{shp_fn}.shx" not in files:
        raise NoShxFound("No .shx file found in provided zip file")

    # check for .dbf
    if f"{shp_fn}.dbf" not in files:
        raise NoDbfFound("No .dbf file found in provided zip file")

    return shp_path
