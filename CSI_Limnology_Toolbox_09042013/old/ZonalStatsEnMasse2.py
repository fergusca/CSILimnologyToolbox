# Filename: ZonalStatsEnMasse.py
# Purpose: Get zonal stats for raster data into a new field in polygons.

# Import modules
import os, arcpy
from arcpy.sa import *



# Check out the ArcGIS Spatial Analyst extension license
arcpy.CheckOutExtension("Spatial")

# Input parameters:
infolder = arcpy.GetParameterAsText(0) # Workspace/folder with rasters
polys = arcpy.GetParameterAsText(1) # geodatabase with just extent polygons in it.
id = "OBJECTID"
arcpy.env.workspace = infolder

rasters = []
for root, dirs, files in arcpy.da.Walk(infolder):
    for file in files:
        if file.endswith(".tif"):
            rasters.append(os.path.join(root, file))
        

# Set environment settings
arcpy.ResetEnvironments()
arcpy.env.workspace = polys
arcpy.env.overwriteOutput = "TRUE"
arcpy.env.parallelProcessingFactor = "100%"

# List polygons in the geodatabase
arcpy.env.workspace = polys
fcs = arcpy.ListFeatureClasses()
print fcs

for fc in fcs:
    if not os.path.exists(os.path.join(infolder, fc + "stats")):
        os.mkdir(os.path.join(infolder, fc + "stats"))

    outfolder = os.path.join(infolder, fc + "stats")    
    # Add an ID field
    try:
        arcpy.AddField_management(fc, "ID", "TEXT")
        arcpy.CalculateField_management(fc, "ID", "!OBJECTID!", "PYTHON")
    except:
        continue
    # Get zonal stats for each raster
   
    
    for raster in rasters:
        basename = os.path.basename(raster)
        table = os.path.splitext(basename)[0]
        stats = ZonalStatisticsAsTable(fc, "ID", raster, os.path.join(outfolder, table + ".dbf"), "DATA", "ALL")
    
    