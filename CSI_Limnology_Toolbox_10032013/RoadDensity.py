# Filename: RoadDensity.py
# 

import arcpy, os
from arcpy.sa import *
arcpy.CheckOutExtension('Spatial')

# User defined parameters
zones = arcpy.GetParameterAsText(0) # Polygon feature class
field = arcpy.GetParameterAsText(1) # Field w/Unique values
rds = arcpy.GetParameterAsText(2) # Roads line feature class
outfolder = arcpy.GetParameterAsText(3) # Folder for output

# Create named folder and variable for output table
name = os.path.splitext(os.path.basename(zones))[0]
if not os.path.exists(os.path.join(outfolder, name)):
    os.mkdir(os.path.join(outfolder, name))
outtable = os.path.join(outfolder, name, name + "RdDensity.dbf")




# Add ZoneHa field to polygons
try:
    arcpy.AddField_management(zones, "Hectares", "DOUBLE")
    zoneha_exp = "!shape.area@hectares!"
    arcpy.CalculateField_management(zones, "Hectares", zoneha_exp, "PYTHON")
except:
    pass

arcpy.TabulateIntersection_analysis(zones, field, rds, outtable,'', '','', "METERS")
arcpy.JoinField_management(outtable, field, zones, field, "Hectares")
arcpy.AddField_management(outtable, "RdDensity", "DOUBLE")
density_exp = '!LENGTH! / !Hectares!'
arcpy.CalculateField_management(outtable, "RdDensity", density_exp, "PYTHON")
arcpy.DeleteField_management(outtable, ['Hectares', 'PERCENTAGE'])
arcpy.AddField_management(outtable, "RdMeters", "DOUBLE")
arcpy.CalculateField_management(outtable, "RdMeters", "!LENGTH!", "PYTHON")
arcpy.DeleteField_management(outtable, 'LENGTH')


    





