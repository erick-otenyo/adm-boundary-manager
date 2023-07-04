import glob
import os
from zipfile import ZipFile

from adminboundarymanager.errors import NoShpFound, NoShxFound, NoDbfFound


def extract_zipped_shapefile(shp_zip_path, out_dir):
    # unzip file
    with ZipFile(shp_zip_path, 'r') as zip_obj:
        for filename in zip_obj.namelist():
            # ignore __macosx files
            if not filename.startswith('__MACOSX/'):
                zip_obj.extract(filename, out_dir)

    # Use the first available shp
    shp = glob.glob(f"{out_dir}/*.shp") or glob.glob(f"{out_dir}/*/*.shp")

    if not shp:
        raise NoShpFound("No shapefile found in provided zip file")

    shp_fn = os.path.splitext(shp[0])[0]
    shp_dir = os.path.dirname(shp_fn)

    files = [os.path.join(shp_dir, f) for f in os.listdir(shp_dir)]

    # check for .shx
    if f"{shp_fn}.shx" not in files:
        raise NoShxFound("No .shx file found in provided zip file")

    # check for .dbf
    if f"{shp_fn}.dbf" not in files:
        raise NoDbfFound("No .dbf file found in provided zip file")

    # return first shp path
    return shp[0]
