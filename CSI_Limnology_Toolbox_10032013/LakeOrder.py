# Filename: LakeOrder.py
# Purpose: Assigns a lake order classification to a lake shapefile using a RivEx generated river shapefile
#          with stream order.

import os
import arcpy
import shutil

arcpy.env.overwriteOutput = "TRUE"

# User inputs:
rivex = arcpy.GetParameterAsText(0) # A shapefile of rivers that has the "Strahler" field produced by RivEx extension.
csilakes = arcpy.GetParameterAsText(1) # A shapefile of CSILakes.
nwi = arcpy.GetParameterAsText(2) # NWI shapefile
outfolder = arcpy.GetParameterAsText(3) # Location where output gets stored.

arcpy.env.parallelProcessingFactor = "100%"
arcpy.env.extent = csilakes

# Select non-artificial rivers that intersect lakes and make shapefile
exp1 = '''"FType" = 334 OR "FType" = 336 OR "FType" = 460 OR "FType" = 566'''
arcpy.MakeFeatureLayer_management(rivex, os.path.join(outfolder, "rivex.lyr"), exp1)
rivex_lyr = os.path.join(outfolder, "rivex.lyr")
arcpy.SelectLayerByLocation_management(rivex_lyr, "INTERSECT", csilakes, '', "NEW_SELECTION")
arcpy.CopyFeatures_management(rivex_lyr, os.path.join(outfolder, "int_rivers.shp"))
int_rivers = os.path.join(outfolder, "int_rivers.shp")

# Make points from the start vertices of intersecting stream segments.
arcpy.FeatureVerticesToPoints_management(int_rivers, os.path.join(outfolder, "potdrain_pts.shp"), "START")
potdrain_pts = os.path.join(outfolder, "potdrain_pts.shp")

# Select from potential drain points those that intersect lakes.
arcpy.MakeFeatureLayer_management(potdrain_pts, os.path.join(outfolder, "potdrains.lyr"))
potdrains_lyr = os.path.join(outfolder, "potdrains.lyr")
arcpy.SelectLayerByLocation_management(potdrains_lyr, "", csilakes)
arcpy.CopyFeatures_management(potdrains_lyr, os.path.join(outfolder, "drain_pts.shp"))
drain_pts = os.path.join(outfolder, "drain_pts.shp")

# Spatial join
basename = os.path.basename(csilakes)
arcpy.SpatialJoin_analysis(csilakes, drain_pts, os.path.join(outfolder, basename))
outshp = os.path.join(outfolder, basename)

# Clean up undesired fields.
dropfields = ["OBJECTID","FDate", "FDate_1", "Resoluti_1", "FlowDir", "Ftype_1", "FCode_1", "Shape_Le_1", "Enabled",\
               "Fnode", "Tnode", "Segment", "ORIG_FID", "Join_Count", "TARGET_FID", "Resolution", "Elevation","ReachCod_1"]
arcpy.DeleteField_management(outshp, dropfields)

# Assign Headwater Lakes a value of zero in the Strahler field.
hwfield = "Strahler"
cursor = arcpy.UpdateCursor(outshp, """"Connection" = 'Headwater'""")
for row in cursor:
    # Change to zero
    row.setValue(hwfield,0)
    cursor.updateRow(row)

del row
del cursor

# Assign Isolated Lakes a value of -3 in the Strahler field.
seepfield = "Strahler"
cursor = arcpy.UpdateCursor(outshp, """"Connection" = 'Isolated'""")
for row in cursor:
    # Change to neg 3
    row.setValue(seepfield,-3)
    cursor.updateRow(row)

del row
del cursor

# Select those isolated lakes that are connected to connected lakes by wetlands
arcpy.MakeFeatureLayer_management(outshp, os.path.join(outfolder, "outshp.lyr"))
outshp_lyr = os.path.join(outfolder, "outshp.lyr")
arcpy.SelectLayerByAttribute_management(outshp_lyr, "NEW_SELECTION", """"Connection" = 'Isolated'""")
arcpy.CopyFeatures_management(outshp_lyr, os.path.join(outfolder, "isolakes.shp"))
isolakes = os.path.join(outfolder, "isolakes.shp")
arcpy.SelectLayerByAttribute_management(outshp_lyr, "NEW_SELECTION", """"Connection" = 'Isolated'""")
arcpy.SelectLayerByAttribute_management(outshp_lyr, "SWITCH_SELECTION", """"Connection" = 'Isolated'""")
arcpy.CopyFeatures_management(outshp_lyr, os.path.join(outfolder, "conlakes.shp"))
conlakes = os.path.join(outfolder, "conlakes.shp")
arcpy.MakeFeatureLayer_management(nwi, os.path.join(outfolder, "nwi.lyr"))
nwi_lyr = os.path.join(outfolder, "nwi.lyr")


# Select isolated lakes connected to connected lakes by wetlands. Calc as -2
arcpy.SelectLayerByLocation_management(nwi_lyr, "INTERSECT", isolakes, '', "NEW_SELECTION")
arcpy.SelectLayerByAttribute_management(nwi_lyr, "SUBSET_SELECTION", """"WETLAND_TY" = 'Freshwater Emergent Wetland' OR "WETLAND_TY" = 'Freshwater Forested/Shrub Wetland' OR "WETLAND_TY" = 'Other'""")
arcpy.SelectLayerByLocation_management(nwi_lyr, "INTERSECT", conlakes, '', "SUBSET_SELECTION")
arcpy.CopyFeatures_management(nwi_lyr, os.path.join(outfolder, "conwetlands_lk.shp"))
conwetlands = os.path.join(outfolder, "conwetlands_lk.shp")
arcpy.SelectLayerByLocation_management(outshp_lyr, "INTERSECT", conwetlands, '', "NEW_SELECTION")
arcpy.SelectLayerByAttribute_management(outshp_lyr, "SUBSET_SELECTION", """"Connection" = 'Isolated'""")
arcpy.CalculateField_management(outshp_lyr, "Strahler", "-2", "VB")

# Select isolated lakes connected to streams by wetlands. Calc as -2
arcpy.SelectLayerByLocation_management(nwi_lyr, "INTERSECT", isolakes, '', "NEW_SELECTION")
arcpy.SelectLayerByAttribute_management(nwi_lyr, "SUBSET_SELECTION", """"WETLAND_TY" = 'Freshwater Emergent Wetland' OR "WETLAND_TY" = 'Freshwater Forested/Shrub Wetland' OR "WETLAND_TY" = 'Other'""")
arcpy.SelectLayerByLocation_management(nwi_lyr, "INTERSECT", rivex, '', "SUBSET_SELECTION")
arcpy.Dissolve_management(nwi_lyr, os.path.join(outfolder, "conwetlands_st.shp"))
conwetlands2 = os.path.join(outfolder, "conwetlands_st.shp")
arcpy.SelectLayerByLocation_management(outshp_lyr, "INTERSECT", conwetlands2, '', "NEW_SELECTION")
arcpy.SelectLayerByAttribute_management(outshp_lyr, "SUBSET_SELECTION", """"Connection" = 'Isolated'""")
arcpy.CalculateField_management(outshp_lyr, "Strahler", "-2", "VB")
arcpy.SelectLayerByAttribute_management(outshp_lyr, "CLEAR_SELECTION")
arcpy.CopyFeatures_management(outshp_lyr, os.path.join(outfolder, "preLakeOrder1.shp"))
lakeorder1 = os.path.join(outfolder, "preLakeOrder1.shp")

# Classify lakes from LakeOrder1 that are only intersected by intermittent streams.
arcpy.MakeFeatureLayer_management(rivex, os.path.join(outfolder, "perennial.lyr"), """"FCode" = 46000 OR "FCode" = 46006 OR "FCode" = 33600 OR "FCode" = 33400 OR "FCode" = 33601""")
perennial = os.path.join(outfolder, "perennial.lyr")
arcpy.MakeFeatureLayer_management(lakeorder1, os.path.join(outfolder, "poslakeorder.lyr"))
poslakeorder = os.path.join(outfolder, "poslakeorder.lyr")
arcpy.SelectLayerByLocation_management(poslakeorder, "INTERSECT", perennial, '', "NEW_SELECTION")
arcpy.SelectLayerByLocation_management(poslakeorder, "INTERSECT", perennial, '', "SWITCH_SELECTION")
arcpy.SelectLayerByAttribute_management(poslakeorder, "SUBSET_SELECTION", """"Strahler" >= 0""")
arcpy.CalculateField_management(poslakeorder, "Strahler", "-1", "VB")
arcpy.CopyFeatures_management(poslakeorder, os.path.join(outfolder, "LakeOrder.shp"))                                          