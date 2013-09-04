# Filename: WetlandOrder.py
# Purpose: Assigns a numerical class to wetlands based on their connectivity to the landscape.
# Classes:
    # 0 = Headwater wetlands no inlets but have an outlet
    # 1 or greater by highest strahler order of connecting streams
    # -1 Wetlands that are isolated from streams

import os
import arcpy
import shutil
from arcpy.da import *

arcpy.CheckOutExtension("DataInteroperability")
arcpy.env.overwriteOutput = "TRUE"

# User input parameters:
rivex = arcpy.GetParameterAsText(0) # A shapefile of rivers that has the "Strahler" field produced by RivEx extension.
nwi = arcpy.GetParameterAsText(1) # NWI feature class
outfolder = arcpy.GetParameterAsText(2) # Location where output gets stored.
ram = "in_memory"

# Environmental Settings
arcpy.ResetEnvironments()
arcpy.env.extent = rivex
arcpy.env.parallelProcessingFactor = "100%"
arcpy.env.workspace = ram
albers = arcpy.SpatialReference()
albers.factoryCode = 102039
albers.create()
arcpy.env.outputCoordinateSystem = albers

# Make a fc of selected wetlands
nwifilter = """ "ATTRIBUTE" LIKE 'P%' """
arcpy.MakeFeatureLayer_management(nwi, "nwi_lyr")
arcpy.SelectLayerByAttribute_management("nwi_lyr", "NEW_SELECTION", nwifilter)
arcpy.CopyFeatures_management("nwi_lyr", "allwetpre")

# Add field for hectares and calculate
arcpy.AddField_management("allwetpre", "WetHa", "DOUBLE")


# Buffer a donut around selected wetland polys 30m
arcpy.Buffer_analysis("allwetpre", "allwet", "30 meters", "OUTSIDE_ONLY")

# Add wetland order field for connected wetlands
arcpy.AddField_management("allwet","WetOrder", "TEXT")

# Spatial join connected wetlands and streams
##################Field Maps########################
fms = arcpy.FieldMappings()
fm_strahlermax = arcpy.FieldMap()
fm_strahlersum = arcpy.FieldMap()
fm_wetorder = arcpy.FieldMap()
fm_wetha = arcpy.FieldMap()
fm_attribute = arcpy.FieldMap()
fm_lengthkm = arcpy.FieldMap()

fm_strahlermax.addInputField(rivex, "Strahler")
fm_strahlersum.addInputField(rivex, "Strahler")
fm_wetorder.addInputField("allwet", "WetOrder")
fm_wetha.addInputField("allwet", "WetHa")
fm_attribute.addInputField("allwet", "ATTRIBUTE")
fm_lengthkm.addInputField(rivex, "LengthKm")

fm_lengthkm.mergeRule = 'Sum'
fm_strahlermax.mergeRule = 'Max'
fm_strahlersum.mergeRule = 'Sum'

lengthkm_name = fm_lengthkm.outputField
lengthkm_name.name = 'StreamKm'
lengthkm_name.aliasName = 'StreamKm'
fm_lengthkm.outputField = lengthkm_name

strahlermax_name = fm_strahlermax.outputField
strahlermax_name.name = 'StrOrdMax'
strahlermax_name.aliasName = 'StrOrdMax'
fm_strahlermax.outputField = strahlermax_name

strahlersum_name = fm_strahlersum.outputField
strahlersum_name.name = 'StrOrdSum'
strahlersum_name.aliasName = 'StrOrdSum'
fm_strahlersum.outputField = strahlersum_name

fms.addFieldMap(fm_strahlermax)
fms.addFieldMap(fm_strahlersum)
fms.addFieldMap(fm_wetorder)
fms.addFieldMap(fm_wetha)
fms.addFieldMap(fm_attribute)
fms.addFieldMap(fm_lengthkm)
#####################################################

arcpy.SpatialJoin_analysis("allwet", rivex, "conwetorder", '', '', fms)

# Calculate fields
arcpy.AddField_management("conwetorder", "StreamCnt", "LONG")
arcpy.CalculateField_management("conwetorder","StreamCnt", "!Join_Count!", "PYTHON")
arcpy.DeleteField_management("conwetorder", "Join_Count")

# Create output feature class in a file geodatabase
arcpy.CreateFileGDB_management(outfolder, "WetlandOrder")
outgdb = os.path.join(outfolder, "WetlandOrder.gdb")
arcpy.FeatureClassToFeatureClass_conversion("conwetorder", outgdb, "WetlandOrder")
outfc = os.path.join(outgdb, "WetlandOrder")
try:
    arcpy.DeleteField_management(outfc, "BUFF_DIST")
    arcpy.DeleteField_management(outfc, "ACRES")
    arcpy.DeleteField_management(outfc, "Target_FID")
    arcpy.DeleteField_management(outfc, "Shape_Length")
except:
    pass


# Create Veg field
arcpy.AddField_management(outfc, "Veg", "TEXT")
arcpy.CalculateField_management(outfc, "Veg", "!ATTRIBUTE![:3]", "PYTHON")

# Calculate Veg Field
arcpy.AddField_management(outfc, "VegType", "TEXT")

with arcpy.da.UpdateCursor(outfc, ["Veg", "VegType"]) as cursor:
    for row in cursor:
        if row[0] == "PEM":
            row[1] = "PEMorPAB"
        elif row[0] == "PAB":
            row[1] = "PEMorPAB"
        elif row[0] == "PFO":
            row[1] = "PFO"
        elif row[0] == "PSS":
            row[1] = "PSS"
        else:
            row[1] = "Other"
        cursor.updateRow(row)

del cursor

# Calculate WetOrder from StrOrdSum
with arcpy.da.UpdateCursor(outfc, ["StrOrdSum", "WetOrder"]) as cursor:
    for row in cursor:
        if row[0] == 0:
            row[1] = "Isolated"
        elif row[0] == 1:
            row[1] = "Single"
        elif row[0] == None:
            row[1] = "Isolated"
        else:
            row[1] = "Connected"
        cursor.updateRow(row)

# Delete intermediate veg field
arcpy.DeleteField_management(outfc, "Veg")
try:
    arcpy.DeleteField_management(outfc, "Shape_Length")
    arcpy.DeleteField_management(outfc, "Shape_Area")
except:
    pass

# Calculate geometry for wetland hectares.
arcpy.CalculateField_management(outfc, "WetHa", "!shape.area@hectares!", "PYTHON")

# Write table to csv file.
def TableToCSV(fc,CSVFile):
    
    fields = [f.name for f in arcpy.ListFields(fc) if f.type <> 'Geometry']
    with open(CSVFile, 'w') as f:
        f.write(','.join(fields)+'\n') # csv headers
        with arcpy.da.SearchCursor(fc, fields) as cursor:
            for row in cursor:
                f.write(','.join([str(r) for r in row])+'\n')
    
if __name__ == '__main__':

    fc = os.path.join(outgdb,"WetlandOrder")
    csv = os.path.join(outfolder,"WetlandOrder.csv")
    TableToCSV(fc,csv)



    


        
            
                

















