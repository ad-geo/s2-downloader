import os
import traceback
from collections import defaultdict
from datetime import date

import arcpy
import requests
from arcpy import management
from osgeo import gdal
from requests.adapters import HTTPAdapter, Retry

# STACK API info
stac_url = "https://earth-search.aws.element84.com/v1/search"
stac_collections = ["sentinel-2-l2a"]


def get_iso_date(date_str: date) -> str:
    """Convert date to ISO format yyyy-mm-dd"""
    try:
        return date_str.strftime('%Y-%m-%d')
    except Exception as e:
        arcpy.AddError(f"Error converting date to ISO format: {traceback.format_exc()}")
        raise


def buffer_extent(extent_poly, buffer: float) -> tuple:
    """Buffer polygon extent with the given buffer in metres and return WGS84 bounding box and polygon."""
    try:
        # ensure the polygon is in WGS84 (EPSG:4326)
        if int(extent_poly.spatialReference.factoryCode) != 4326:
            extent_poly_wgs84 = extent_poly.projectAs(arcpy.SpatialReference(4326))
        else:
            extent_poly_wgs84 = extent_poly

        # calculate buffer in degrees. this will be used as search extent
        buffer_dd = buffer / 100000  # 100 km = 1 degree (approx)
        x_min = extent_poly_wgs84.extent.XMin - buffer_dd
        x_max = extent_poly_wgs84.extent.XMax + buffer_dd
        y_min = extent_poly_wgs84.extent.YMin - buffer_dd
        y_max = extent_poly_wgs84.extent.YMax + buffer_dd

        # create buffered bounding box string
        buff_bb_wgs84 = f"{x_min},{y_min},{x_max},{y_max}"

        # construct buffered polygon. this will be used as clip fc
        poly_array = arcpy.Array([
            arcpy.Point(x_min, y_min),
            arcpy.Point(x_min, y_max),
            arcpy.Point(x_max, y_max),
            arcpy.Point(x_max, y_min),
            arcpy.Point(x_min, y_min)
        ])
        buff_poly_wgs84 = arcpy.Polygon(poly_array, spatial_reference=arcpy.SpatialReference(4326))

        return buff_bb_wgs84, buff_poly_wgs84

    except Exception as e:
        arcpy.AddError(f"Error creating buffered extent: {traceback.format_exc()}")
        raise


def get_session() -> requests.Session:
    """Create a session with retries for HTTP requests."""
    try:
        # set session and retry
        session = requests.Session()
        retries = Retry(
            total=5,
            backoff_factor=0.1,
            status_forcelist=[500, 502, 503, 504]
        )
        session.mount("https://", HTTPAdapter(max_retries=retries))

        return session

    except requests.exceptions.RequestException as e:
        arcpy.AddError(f"Error creating session: {traceback.format_exc()}")
        raise


def search_stac(url: str, b_box: str, start_date: str, end_date: str, collections: list) -> dict:
    """Search the STAC database for scenes within the specified bounding box and date range."""
    try:
        scene_info = defaultdict(list)
        request_count = 1
        limit = 50
        matched = -9999
        returned = -9999

        params = {
            "bbox": b_box,
            "datetime": f"{start_date}T00:00:00Z/{end_date}T23:59:59Z",
            "collections": collections,
            "limit": limit,
            "sortby": "+properties.datetime",
        }

        # set session and retry
        session = get_session()

        while returned != 0:
            if request_count == 1:
                response = session.get(url=url, params=params)
            else:
                response = session.get(url=url)

            if response.status_code != 200:
                arcpy.AddError(f"Error in request: {response.status_code}")
                break

            response_json = response.json()

            matched = int(response_json.get("context", {}).get("matched", {}))
            returned = int(response_json.get("context", {}).get("returned", {}))
            arcpy.AddMessage(f"limit : {limit}, matched : {matched}, returned : {returned})")

            for link in response_json.get("links", {}):
                if link.get("rel", {}) == "next":
                    url = link.get("href", {})

            for feature in response_json.get("features", {}):
                sc_info = {
                    "scene_datetime": feature.get("properties", {}).get("datetime", {}),
                    "scene_id": feature.get("id", {}),
                    "scene_uri": feature.get("properties", {}).get("s2:product_uri", {}),
                    "ql_url": feature.get("assets", {}).get("thumbnail", {}).get("href", {}),
                    "vis_url": feature.get("assets", {}).get("visual", {}).get("href", {}),
                    "mtd_url": feature.get("assets", {}).get("granule_metadata", {}).get("href", {}),
                    "cloud_cover": feature.get("properties", {}).get("eo:cloud_cover", {}),
                    "epsg_code": feature.get("properties", {}).get("proj:epsg", {}),
                    "bbox": feature.get("bbox", {})
                }
                scene_info["scenes"].append(sc_info)
            request_count += 1

        return scene_info

    except requests.exceptions.RequestException as e:
        arcpy.AddError(f"Error while searching STAC: {traceback.format_exc()}")
        raise


def get_fname_from_url(scene_id: str, file_url: str, file_prefix: str, file_suffix: str) -> str:
    """
    Create standard file name
    """
    try:
        file_ext = os.path.splitext(file_url)[1]
        fname = f"{file_prefix}_{scene_id}_{file_suffix}{file_ext}"

        return fname

    except Exception as e:
        arcpy.AddError(f"Error getting filename for {scene_id}: {traceback.format_exc()}")
        raise


def download_img(scene_id: str, in_url: str, in_lyr: str, in_clip_fc, out_file: str) -> None:
    """Download and clip image from a URL."""
    try:
        if os.path.exists(out_file):
            arcpy.AddMessage(f"Image for {scene_id} already exists at {out_file}")
            return

        if in_url is None:
            arcpy.AddMessage(f"Warning: Image for {scene_id} is not available.")
            return

        # set processing extent
        arcpy.env.extent = "MINOF"

        # read url into vrt
        cog_url = in_url
        if not cog_url.startswith("/vsicurl/"):
            cog_url = f"/vsicurl/{cog_url}"

        ds = gdal.OpenEx(cog_url)
        if ds is None:
            arcpy.AddError(f"Failed to open dataset for {scene_id}")
            return

        # download and clip
        gdal.Translate(in_lyr, ds)
        arcpy.management.Clip(in_raster=in_lyr, out_raster=out_file, in_template_dataset=in_clip_fc,
                              clipping_geometry="NONE", maintain_clipping_extent="NO_MAINTAIN_EXTENT")
        arcpy.AddMessage(f"saved image for {scene_id} in {out_file}")

        return

    except Exception as e:
        arcpy.AddError(f"Error downloading image for {scene_id}: {traceback.format_exc()}")
        raise


def download_mtd(session: requests.Session, scene_id: str, in_url: str, out_file: str) -> None:
    """Download image metadata from a URL."""
    try:
        if os.path.exists(out_file):
            arcpy.AddMessage(f"metadata for {scene_id} exists in {out_file}")
            return

        if in_url is None:
            arcpy.AddMessage(f"WARNING metadata for {scene_id} is not available")
            return

        with open(out_file, "w") as f:
            response = session.get(url=in_url)
            if response.status_code == 200:
                f.write(response.text)
                arcpy.AddMessage(f"saved metadata for {scene_id} in {out_file}")

        return

    except Exception as e:
        arcpy.AddError(f"Error downloading metadata for {scene_id}: {traceback.format_exc()}")
        raise


def get_data(scene_info: dict, out_prefix: str, out_dir: str, temp_dir: str, clip_extent) -> None:
    """Download image and metadata for each scene"""
    try:
        # set session and retry
        session = get_session()

        count_download = 0
        total_download = len(scene_info.get("scenes", {}))

        for item in scene_info.get("scenes", {}):
            scene_id = item.get("scene_id")
            vis_url = item.get("vis_url")
            mtd_url = item.get("mtd_url")
            epsg_code = item.get("epsg_code")

            vis_fname = get_fname_from_url(scene_id=scene_id, file_url=vis_url, file_prefix=out_prefix,
                                           file_suffix="TCI")
            mtd_fname = get_fname_from_url(scene_id=scene_id, file_url=mtd_url, file_prefix=out_prefix,
                                           file_suffix="metadata")
            vrt_fname = f"{scene_id}_TCI.vrt"

            vis_file = os.path.join(out_dir, vis_fname)
            mtd_file = os.path.join(out_dir, mtd_fname)
            vrt_lyr = os.path.join(temp_dir, vrt_fname)

            # project clip extent polygon
            clip_extent_proj = clip_extent.projectAs(arcpy.SpatialReference(epsg_code))

            # download image
            download_img(scene_id=scene_id, in_url=vis_url, in_lyr=vrt_lyr, in_clip_fc=clip_extent_proj,
                         out_file=vis_file)

            # download metadata
            download_mtd(scene_id=scene_id, session=session, in_url=mtd_url, out_file=mtd_file)

            count_download += 1
            arcpy.AddMessage(f"downloaded {count_download} of {total_download} images")

        return

    except Exception as e:
        arcpy.AddError(f"Error getting data: {traceback.format_exc()}")
        raise
