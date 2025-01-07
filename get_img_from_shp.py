import getpass
import os
import traceback

import arcpy

from utils import get_iso_date, buffer_extent, stac_url, stac_collections, search_stac, get_data


class GetImgFromShp(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Get Sentinel2 Image From Shapefile"
        self.description = "Get Sentinel2 Image From  Shapefile"
        self.canRunInBackground = True

    def getParameterInfo(self):
        """Define parameter definitions"""
        params = []

        start_date = arcpy.Parameter(
            displayName="Start Date for Search (UTC)",
            name="start_date",
            datatype="GPDate",
            parameterType="Required",
            direction="Input"
        )
        params.append(start_date)

        end_date = arcpy.Parameter(
            displayName="End Date for Search (UTC)",
            name="end_date",
            datatype="GPDate",
            parameterType="Required",
            direction="Input"
        )
        params.append(end_date)

        buffer_val = 250
        buffer = arcpy.Parameter(
            displayName=f"Buffer Distance (Meters)",
            name="buffer",
            datatype="GPLong",
            parameterType="Required",
            direction="Input"
        )
        buffer.value = buffer_val
        params.append(buffer)

        in_fc = arcpy.Parameter(
            displayName="Input Shapefile or Feature Class",
            name="in_fc",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input"
        )
        in_fc.filter.list = ["Polygon"]
        params.append(in_fc)

        out_prefix_field = arcpy.Parameter(
            displayName="Field for Prefix",
            name="out_prefix_field",
            datatype="Field",
            parameterType="Required",
            direction="Input"
        )
        out_prefix_field.parameterDependencies = [in_fc.name]
        params.append(out_prefix_field)

        out_dir = arcpy.Parameter(
            displayName="Output Directory",
            name="out_dir",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input"
        )
        params.append(out_dir)

        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        try:
            # get parameters
            start_date = parameters[0].value
            end_date = parameters[1].value
            buffer = float(parameters[2].valueAsText)  # convert buffer to float
            in_fc = parameters[3].valueAsText
            out_prefix_field = parameters[4].valueAsText
            out_dir = parameters[5].valueAsText

            # print user and parameters
            user_param = (
                    f"\n============{self.label}============\n" +
                    f"User: {getpass.getuser()}\n" +
                    f"Start Date: {start_date}\n" +
                    f"End Date: {end_date}\n" +
                    f"Buffer Distance (Meters): {buffer}\n" +
                    f"Input Shapefile or Feature Class: {in_fc}\n" +
                    f"Field for Prefix: {out_prefix_field}\n" +
                    f"Output Directory: {out_dir}\n\n"
            )
            arcpy.AddMessage(user_param)

            # create necessary folder
            temp_dir = os.path.join(out_dir, "temp")
            for _dir in [out_dir, temp_dir]:
                if not os.path.exists(_dir):
                    os.makedirs(_dir)
                    arcpy.AddMessage(f"created {_dir}")

            # loop for each polygon
            start_date_iso = get_iso_date(start_date)
            end_date_iso = get_iso_date(end_date)
            with arcpy.da.SearchCursor(in_fc, field_names=[out_prefix_field, "SHAPE@"]) as cursor:
                for row in cursor:
                    out_prefix = row[0]
                    poly_extent = row[1]

                    arcpy.AddMessage(f"Processing {out_prefix_field}: {out_prefix}")

                    # get buffered bounding box and polygon in WGS84
                    buff_bb_wgs84, buff_poly_wgs84 = buffer_extent(extent_poly=poly_extent, buffer=buffer)

                    # search for scene info from STAC API
                    scene_info = search_stac(url=stac_url, b_box=buff_bb_wgs84, start_date=start_date_iso,
                                             end_date=end_date_iso, collections=stac_collections)

                    # download image and metadata
                    get_data(scene_info=scene_info, out_prefix=out_prefix, out_dir=out_dir, temp_dir=temp_dir,
                             clip_extent=buff_poly_wgs84)

                    arcpy.AddMessage(f"Completed {out_prefix_field}: {out_prefix}")

            return

        except Exception as e:
            arcpy.AddError(f"Error executing tool: {traceback.format_exc()}")
            raise

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return
