# Filename: IntraLake58.py

import os, arcpy, shutil
arcpy.env.overwriteOutput = "TRUE"

nhd = arcpy.GetParameterAsText(0)
watersheds = arcpy.GetParameterAsText(1)
outfolder = arcpy.GetParameterAsText(2)
filterlakes = arcpy.GetParameterAsText(3)

# Projections:
nad83 = arcpy.SpatialReference()
nad83.factoryCode = 4269
nad83.create()
albers = arcpy.SpatialReference()
albers.factoryCode = 102039
albers.create()

# NHD variables:
flowline = os.path.join(nhd, "Hydrography", "NHDFlowline")
waterbody = os.path.join(nhd, "Hydrography", "NHDWaterbody")
network = os.path.join(nhd, "Hydrography", "HYDRO_NET")
junction = os.path.join(nhd, "Hydrography", "HYDRO_NET_Junctions")

# Project watersheds to NAD83
arcpy.Project_management(watersheds, os.path.join(outfolder, "watersheds.shp"), nad83, '', albers)
watersheds = os.path.join(outfolder, "watersheds.shp")

# Make shapefiles for one hectare and ten hectare lakes that intersect flowlines.
arcpy.FeatureClassToShapefile_conversion(waterbody, outfolder)
waterbodyshp = os.path.join(outfolder, "NHDWaterbody.shp")
arcpy.MakeFeatureLayer_management(waterbodyshp, os.path.join(outfolder, "waterbody.lyr"))
waterbody_lyr = os.path.join(outfolder, "waterbody.lyr")
arcpy.SelectLayerByAttribute_management(waterbody_lyr, "NEW_SELECTION", '''"AreaSqKm">=0.01''')
arcpy.SelectLayerByAttribute_management(waterbody_lyr, "SUBSET_SELECTION", '''"FType" = 390 OR "FType" = 436''')
arcpy.SelectLayerByLocation_management(waterbody_lyr, "INTERSECT", flowline, "", "SUBSET_SELECTION")
try:
    arcpy.Project_management(filterlakes, os.path.join(outfolder, "filter.shp"),nad83,'',albers)
    filter = os.path.join(outfolder, "filter.shp")
    arcpy.SelectLayerByLocation_management(waterbody_lyr, "INTERSECT", filter, '', "SUBSET_SELECTION")

except:
    pass
arcpy.CopyFeatures_management(waterbody_lyr, os.path.join(outfolder, "oneha.shp"))
oneha = os.path.join(outfolder, "oneha.shp")
arcpy.MakeFeatureLayer_management(oneha, os.path.join(outfolder, "oneha.lyr"))
oneha_lyr = os.path.join(outfolder, "oneha.lyr")
arcpy.SelectLayerByAttribute_management(oneha_lyr, "NEW_SELECTION", '''"AreaSqKm">=0.1''')
arcpy.CopyFeatures_management(oneha_lyr, os.path.join(outfolder, "tenha.shp"))
tenha = os.path.join(outfolder, "tenha.shp")

# Make shapefiles of junctions that intersect one hectare and ten hectare lakes.
arcpy.MakeFeatureLayer_management(junction, os.path.join(outfolder, "junction.lyr"))
junction_lyr = os.path.join(outfolder, "junction.lyr")
arcpy.SelectLayerByLocation_management(junction_lyr, "INTERSECT", oneha, '', "NEW_SELECTION")
arcpy.CopyFeatures_management(junction_lyr, os.path.join(outfolder, "onehajunction.shp"))
onehajunction = os.path.join(outfolder, "onehajunction.shp")
arcpy.SelectLayerByLocation_management(junction_lyr, "INTERSECT", tenha, '', "NEW_SELECTION")
arcpy.CopyFeatures_management(junction_lyr, os.path.join(outfolder, "tenhajunction.shp"))
tenhajunction = os.path.join(outfolder, "tenhajunction.shp")

# Split lakes.
arcpy.AddField_management(oneha, "ID", "TEXT")
arcpy.CalculateField_management(oneha, "ID", '''"%s" % (!FID!)''', "PYTHON")
if not os.path.exists(os.path.join(outfolder, "lakes")):
    os.mkdir(os.path.join(outfolder, "lakes"))

lakes = os.path.join(outfolder, "lakes")    
arcpy.Split_analysis(oneha, oneha, "ID", lakes)

# Iterate tracing.
arcpy.env.workspace = lakes
arcpy.MakeFeatureLayer_management(watersheds, os.path.join(outfolder, "watersheds.lyr"))
watersheds_lyr = os.path.join(outfolder, "watersheds.lyr")
fcs = arcpy.ListFeatureClasses()
arcpy.MakeFeatureLayer_management(onehajunction, os.path.join(outfolder, "onehajunction.lyr"))
onehajunction_lyr = os.path.join(outfolder, "onehajunction.lyr")

for fc in fcs:
    name = os.path.splitext(fc)[0]
    arcpy.SelectLayerByLocation_management(onehajunction_lyr, "INTERSECT", fc, '', "NEW_SELECTION")
    arcpy.CopyFeatures_management(onehajunction_lyr, os.path.join(lakes, name + "junctions.shp"))
    lakejunction = os.path.join(lakes, name + "junctions.shp")
    arcpy.TraceGeometricNetwork_management(network, os.path.join(lakes, name + "trace.lyr"), lakejunction, "TRACE_UPSTREAM", tenhajunction)
    trace = os.path.join(lakes, name + "trace.lyr", "NHDFlowline")
    arcpy.CopyFeatures_management(trace, os.path.join(lakes, name + "trace.shp"))
    traceshp = os.path.join(lakes, name + "trace.shp")
    arcpy.FeatureVerticesToPoints_management(traceshp, os.path.join(lakes, name + "tracemid.shp"), "MID")
    tracemid = os.path.join(lakes, name + "tracemid.shp")
    arcpy.SelectLayerByLocation_management(watersheds_lyr, "INTERSECT", tracemid, '', "NEW_SELECTION")
    arcpy.CopyFeatures_management(watersheds_lyr, os.path.join(lakes, name + "sheds.shp"))
    sheds = os.path.join(lakes, name + "sheds.shp")
    arcpy.AddField_management(sheds, "Dissolve", "TEXT")
    arcpy.CalculateField_management(sheds, "Dissolve", "1", "VB")
    arcpy.Dissolve_management(sheds, os.path.join(lakes, name + "dissolve.shp"), "Dissolve")
    dissolve = os.path.join(lakes, name + "dissolve.shp")
    arcpy.SpatialJoin_analysis(dissolve, waterbodyshp, os.path.join(lakes, name + "intralakeshed.shp"))








