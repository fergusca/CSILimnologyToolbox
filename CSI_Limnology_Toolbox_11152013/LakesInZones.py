# Name:JoinZones2Lakes.py
# Purpose: Gives a count and area of all, 4ha, 10ha and 4-10ha lakes by zone.
# Author: Scott Stopyak
# Created: 19/11/2013
# Copyright:(c) Scott Stopyak 2013
# Licence: Distributed under the terms of GNU GPL
#_______________________________________________________________________________

import arcpy, os

# Parameters
infolder = arcpy.GetParameterAsText(0) # Workspace with zone feature classes
lakes = arcpy.GetParameterAsText(1) # Lake polygon feature class
topoutfolder = arcpy.GetParameterAsText(2) # Output folder

# Create output geodatabase in outfolder
try:
    arcpy.CreateFileGDB_management(topoutfolder, "LakesByZone")
except:
    pass
outfolder = os.path.join(topoutfolder, "LakesByZone.gdb")

# Add LakeHa field if it doesn't exist
try:
    arcpy.AddField_management(lakes, "LakeHa", "DOUBLE")
    expha = "!shape.area@hectares!"
    arcpy.CalculateField_management(lakes, "LakeHa", expha, "PYTHON")
except:
    pass

# Set in memory as workspace. Intermediate output will be held in RAM.
mem = "in_memory"
arcpy.env.workspace = mem
arcpy.env.overwriteOutput = True

# Make 4, 10, and 4-10 hectare lake layers in memory.
exp4 = """"LakeHa" >= 4"""
arcpy.Select_analysis(lakes, "fourha", exp4)
exp10 = """"LakeHa" >= 10"""
arcpy.Select_analysis("fourha", "tenha", exp10)
exp4to10 = """"LakeHa" < 10"""
arcpy.Select_analysis("fourha", "four2tenha", exp4to10)

# List extent feature classes
fcs = []
for root, dirs, files in arcpy.da.Walk(infolder):
    for file in files:
        fcs.append(os.path.join(root,file))

# Spatial Join the 1,4,10 and 4-10 hectare lakes to each extent
for fc in fcs:
    name = os.path.basename(fc)
    fms = arcpy.FieldMappings()
    fmid = arcpy.FieldMap()
    fmha = arcpy.FieldMap()
    fmid.addInputField(fc, "Zone")
    fmha.addInputField(lakes, "LakeHa")
    fmha.mergeRule = 'Sum'
    fms.addFieldMap(fmid)
    fms.addFieldMap(fmha)
    arcpy.SpatialJoin_analysis(fc, lakes, os.path.join(outfolder,\
     "Table_" + name + "_1haLakes"),'','',fms)

for fc in fcs:
    name = os.path.basename(fc)
    fms = arcpy.FieldMappings()
    fmid = arcpy.FieldMap()
    fmha = arcpy.FieldMap()
    fmid.addInputField(fc, "Zone")
    fmha.addInputField("fourha", "LakeHa")
    fmha.mergeRule = 'Sum'
    fms.addFieldMap(fmid)
    fms.addFieldMap(fmha)
    arcpy.SpatialJoin_analysis(fc, "fourha", os.path.join(outfolder,\
     "Table_" + name + "_4haLakes"),'','',fms)

for fc in fcs:
    name = os.path.basename(fc)
    fms = arcpy.FieldMappings()
    fmid = arcpy.FieldMap()
    fmha = arcpy.FieldMap()
    fmid.addInputField(fc, "Zone")
    fmha.addInputField("tenha", "LakeHa")
    fmha.mergeRule = 'Sum'
    fms.addFieldMap(fmid)
    fms.addFieldMap(fmha)
    arcpy.SpatialJoin_analysis(fc, "tenha", os.path.join(outfolder,\
     "Table_" + name + "_10haLakes"),'','',fms)

for fc in fcs:
    name = os.path.basename(fc)
    fms = arcpy.FieldMappings()
    fmid = arcpy.FieldMap()
    fmha = arcpy.FieldMap()
    fmid.addInputField(fc, "Zone")
    fmha.addInputField("four2tenha", "LakeHa")
    fmha.mergeRule = 'Sum'
    fms.addFieldMap(fmid)
    fms.addFieldMap(fmha)
    arcpy.SpatialJoin_analysis(fc, "four2tenha", os.path.join(outfolder,\
     "Table_" + name + "_4to10haLakes"),'','',fms)

# Export feature classes to dbfs
outlist = []
for root, dirs, files in arcpy.da.Walk(outfolder):
    for file in files:
        outlist.append(os.path.join(root,file))
for f in outlist:
    arcpy.TableToDBASE_conversion(f,topoutfolder)

