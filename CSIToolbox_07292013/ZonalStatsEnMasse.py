# Filename: ZonalStatsEnMasse.py
# Purpose: Get zonal stats for raster data into a new field in polygons.

# Import modules
import os, arcpy
from arcpy.sa import *

# Check out the ArcGIS Spatial Analyst extension license
arcpy.CheckOutExtension("Spatial")

infolder = arcpy.GetParameterAsText(0) # Workspace/folder with rasters
poly = arcpy.GetParameterAsText(1) # Polygons feature class
zone = arcpy.GetParameterAsText(2) # Polygon feature class unique ID for zones e.g. "OBJECTID"
if not os.path.exists(os.path.join(infolder, "zonalstats")):
    os.mkdir(os.path.join(infolder, "zonalstats"))

outfolder = os.path.join(infolder, "zonalstats")    

# Set environment settings
arcpy.ResetEnvironments()
arcpy.env.workspace = infolder
arcpy.env.overwriteOutput = "TRUE"

# Get zonal stats for each raster
rasters = arcpy.ListRasters("*")

for raster in rasters:
    basename = os.path.basename(raster)
    table = os.path.splitext(basename)[0]
    stats = ZonalStatisticsAsTable(poly, zone, raster, os.path.join(outfolder, table + "_ZonalStats.dbf"), "DATA", "ALL")
    