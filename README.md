## ArcGIS Pro Sentinel-2 Downloader

The ArcGIS Pro Sentinel-2 Downloader is a Python toolbox for ArcGIS Pro, enabling users to search and download Sentinel-2
data via the Earth Search STAC API. [Earth Search](https://www.element84.com/earth-search/) is a STAC-compliant search
and discovery API developed by Element84.

This toolbox includes two primary tools:

1. Get Sentinel2 Image From Screen
2. Get Sentinel2 Image From Shapefile

### Prerequisites

1. Familiarity with ArcGIS Pro.
2. The toolbox was designed and tested in ArcGIS Pro version 3.1.2.

### 1. Get Sentinel2 Image From Screen

This tool retrieves Sentinel-2 imagery by using the extent from an active map in ArcGIS Pro. The tool utilises the Earth
Search STAC API to search, download, and clip both the image and metadata.

#### How to Use "Get Sentinel2 Image From Screen":

1. Open or create a new map in ArcGIS Pro.
2. Zoom into your Area of Interest (AOI). This AOI will serve as the search extent.
3. In the **Catalog Pane**, navigate to the **s2-downloader** folder and expand the **s2_downloader.pyt** toolbox.
4. Open the **Get Sentinel2 Image From Screen** tool, and configure the following parameters:
    - **Start Date for Search (UTC)**: The start date for Sentinel-2 data search.
    - **End Date for Search (UTC)**: The end date for the Sentinel-2 data search.
    - **Buffer Distance**: The buffer distance around the AOI, in meters (default is 250 meters, customisable).
    - **Prefix for Output Files**: An alphanumeric identifier for the output image and metadata (e.g., ABC123).
    - **Output Directory**: The full path to the output directory where the files will be saved. The directory must
      exist
      before running the tool.
5. Click **Run**. The tool will create:
    - Clipped True Color (TCI) images.
    - Corresponding metadata files.

### 2. Get Sentinel2 Image From Shapefile

This tool allows users to specify a shapefile as the source of one or more polygons. Each polygon will be used as a
search extent for retrieving Sentinel-2 imagery and metadata.

#### How to Use "Get Sentinel2 Image From Shapefile":

1. In the **Catalog Pane**, navigate to the **s2-Downloader** folder and expand the **s2_downloader.pyt** toolbox.
2. Open the **Get Sentinel2 Image From Shapefile** tool, and configure the following parameters:
    - **Start Date for Search (UTC)**: The start date for Sentinel-2 data search.
    - **End Date for Search (UTC)**: The end date for the Sentinel-2 data search.
    - **Buffer Distance**: The buffer distance around each shapefile polygon, in meters (default is 250 meters,
      customisable).
    - **Input Shapefile or Feature Class**: Shapefile containing one or more polygons used to define search extents.
    - **Field for Prefix**: The field in the shapefile whose values will be used as identifiers for the output image and
      metadata (alphanumeric characters only, e.g., ABC123).
    - **Output Directory**: The full path to the output directory where the files will be saved. The directory must
      exist
      before running the tool.
3. Click **Run**. The tool will create:
    - Clipped True Color (TCI) images.
    - Corresponding metadata files.

### Output Naming Convention

The naming convention for the output files is as follows:

- **PREFIX_S2#_#####_YYYYMMDD_SEQ_L2A_TCI.tif**
- **PREFIX_S2#_#####_YYYYMMDD_SEQ_L2A_metadata.xml**

Where:

- **PREFIX** = Prefix (as defined by the user)
- **S2#** = Satellite ID (e.g., S2A or S2B)
- **#####** = Scene ID
- **YYYYMMDD** = Acquisition date in year-month-day format
- **SEQ** = Sequence e.g. 0 - in most cases there will be only one image per day. In case there are more (in northern
  latitudes), the following images will be 1,2,...
- **L2A** = Processing level (Level 2A)
- **TCI** = True Color Image file
- **metadata** = Metadata file in XML format

### Troubleshooting and Support

- If you encounter issues or need assistance, please check the ArcGIS Pro logs for detailed error messages.
- For further support, consult the [Earth Search](https://www.element84.com/earth-search/) documentation.