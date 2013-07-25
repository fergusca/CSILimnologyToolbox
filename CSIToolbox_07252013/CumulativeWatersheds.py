# Filename: CumulativeWatersheds.py
# Purpose: Creates a watershed for each lake & cumulative upstream, connected watersheds.

import os, arcpy, shutil
arcpy.env.overwriteOutput = "TRUE"
arcpy.ResetEnvironments()


nhd = arcpy.GetParameterAsText(0)
watersheds = arcpy.GetParameterAsText(1)
topoutfolder = arcpy.GetParameterAsText(2)
filterlakes = arcpy.GetParameterAsText(3)

# Naming Convention
subregion_number = os.path.basename(nhd)
subregion = subregion_number[4:8]
if not os.path.exists(os.path.join(topoutfolder, subregion + "CWS")):
    os.mkdir(os.path.join(topoutfolder, subregion + "CWS"))

outfolder = os.path.join(topoutfolder, subregion + "CWS")
# Create folder for final output
if not os.path.exists(os.path.join(outfolder, "CWS")):
    os.mkdir(os.path.join(outfolder, "CWS"))

intws = os.path.join(outfolder, "CWS")
 
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
arcpy.env.extent = waterbody

# Make shapefiles for one hectare and ten hectare lakes that intersect flowlines.
arcpy.FeatureClassToShapefile_conversion(waterbody, outfolder)
waterbodyshp = os.path.join(outfolder, "NHDWaterbody.shp")
arcpy.MakeFeatureLayer_management(waterbodyshp, os.path.join(outfolder, "waterbody.lyr"))
waterbody_lyr = os.path.join(outfolder, "waterbody.lyr")
arcpy.SelectLayerByAttribute_management(waterbody_lyr, "NEW_SELECTION", '''"AreaSqKm">=0.04''')
arcpy.SelectLayerByAttribute_management(waterbody_lyr, "SUBSET_SELECTION", '''"AreaSqKm" >=0.04 AND ("FCode" = 39000 OR "FCode" = 39004 OR "FCode" = 39009 OR "FCode" = 39010 OR "FCode" = 39011 OR "FCode" = 39012 OR "FCode" = 43600 OR "FCode" = 43613 OR "FCode" = 43615 OR "FCode" = 43617 OR "FCode" = 43618 OR "FCode" = 43619 OR "FCode" = 43621)''')
arcpy.SelectLayerByLocation_management(waterbody_lyr, "INTERSECT", flowline, "", "SUBSET_SELECTION")
try:
    arcpy.Project_management(filterlakes, os.path.join(outfolder, "filter.shp"),nad83,'',albers)
    filter = os.path.join(outfolder, "filter.shp")
    arcpy.SelectLayerByLocation_management(waterbody_lyr, "INTERSECT", filter, '', "SUBSET_SELECTION")

except:
    pass
arcpy.CopyFeatures_management(waterbody_lyr, os.path.join(outfolder, "fourha.shp"))
fourha = os.path.join(outfolder, "fourha.shp")
arcpy.MakeFeatureLayer_management(fourha, os.path.join(outfolder, "fourha.lyr"))
fourha_lyr = os.path.join(outfolder, "fourha.lyr")

# Make shapefiles of junctions that intersect one hectare and ten hectare lakes.
arcpy.MakeFeatureLayer_management(junction, os.path.join(outfolder, "junction.lyr"))
junction_lyr = os.path.join(outfolder, "junction.lyr")
arcpy.SelectLayerByLocation_management(junction_lyr, "INTERSECT", fourha, '', "NEW_SELECTION")
arcpy.CopyFeatures_management(junction_lyr, os.path.join(outfolder, "fourhajunction.shp"))
fourhajunction = os.path.join(outfolder, "fourhajunction.shp")

# Split lakes.
arcpy.AddField_management(fourha, "ID", "TEXT")
arcpy.CalculateField_management(fourha, "ID", '''"%s" % (!FID!)''', "PYTHON")
if not os.path.exists(os.path.join(outfolder, "lakes")):
    os.mkdir(os.path.join(outfolder, "lakes"))

lakes = os.path.join(outfolder, "lakes")    
arcpy.Split_analysis(fourha, fourha, "ID", lakes)

# Iterate tracing.
arcpy.env.workspace = lakes
arcpy.MakeFeatureLayer_management(watersheds, os.path.join(outfolder, "watersheds.lyr"))
watersheds_lyr = os.path.join(outfolder, "watersheds.lyr")
fcs = arcpy.ListFeatureClasses()
arcpy.MakeFeatureLayer_management(fourhajunction, os.path.join(outfolder, "fourhajunction.lyr"))
fourhajunction_lyr = os.path.join(outfolder, "fourhajunction.lyr")

arcpy.AddMessage("Starting iteration.")

for fc in fcs:
    try:
        name = os.path.splitext(fc)[0]
        arcpy.AddMessage("Processing " + name + ".")
        # Sets the output to in memory:
        lakes = "in_memory"
        # Repair the lake geometery if needed.
        arcpy.RepairGeometry_management(fc)
        # Select 4 hectare lake junctions that do intersect it.
        arcpy.SelectLayerByLocation_management(fourhajunction_lyr, "INTERSECT", fc, '', "NEW_SELECTION")
        # Copy junctions
        arcpy.CopyFeatures_management(fourhajunction_lyr, os.path.join(lakes, "junct" + name))
        lakejunction = os.path.join(lakes, "junct" + name)
        # Trace the network upstream from the junctions from above
        arcpy.TraceGeometricNetwork_management(network, os.path.join(lakes, "im" + name + "tracelyr"), lakejunction, "TRACE_UPSTREAM")
        trace = os.path.join(lakes, "im" + name + "tracelyr", "NHDFlowline")
        # Write the trace
        arcpy.CopyFeatures_management(trace, os.path.join(lakes, "im" + name + "trace"))
        traceshp = os.path.join(lakes, "im" + name + "trace")
        # Make a layer from the trace
        arcpy.MakeFeatureLayer_management(traceshp, os.path.join(lakes, "im" + name + "tracesellyr"))
        tracesel = os.path.join(lakes, "im" + name + "tracesellyr")
        # Select from the trace lines those that don't have their midpoint in the lake
        arcpy.SelectLayerByLocation_management(tracesel, "HAVE_THEIR_CENTER_IN", fc, '', "NEW_SELECTION")
        arcpy.SelectLayerByLocation_management(tracesel, "HAVE_THEIR_CENTER_IN", fc, '', "SWITCH_SELECTION")
        # Select watersheds that intersect the trace
        arcpy.SelectLayerByLocation_management(watersheds_lyr, "INTERSECT", tracesel, '', "NEW_SELECTION")
        arcpy.CopyFeatures_management(watersheds_lyr, os.path.join(lakes, "im" + name + "sheds"))
        sheds = os.path.join(lakes, "im" + name + "sheds")
        arcpy.MakeFeatureLayer_management(sheds, os.path.join(lakes, "im" + name + "shedslyr"))
        sheds_lyr = os.path.join(lakes, "im" + name + "shedslyr")
        # Make sure the lake's own watershed gets added (merged) back in to the final aggregated watershed:
        # Make a centroid for the lake, then intersect it with watersheds, then merge it with the previous sheds made above.
        arcpy.FeatureToPoint_management(fc, os.path.join(lakes, "center" + name))
        center = os.path.join(lakes, "center" + name)
        arcpy.SelectLayerByLocation_management(watersheds_lyr, "INTERSECT", center, '', "NEW_SELECTION")
        arcpy.CopyFeatures_management(watersheds_lyr, os.path.join(lakes, "sheds2" + name))
        sheds2 = os.path.join(lakes, "sheds2" + name)
        arcpy.Merge_management([sheds,sheds2], os.path.join(lakes, "sheds3" + name))
        sheds3 = os.path.join(lakes, "sheds3" + name)
        # Dissolve the aggregate watershed if it has more than one polygon and do a spatial join to give it the right ID.
        polynumber = int(arcpy.GetCount_management(sheds3).getOutput(0))
        if polynumber > 1:
            try:
                arcpy.AddField_management(sheds3, "Dissolve", "TEXT")
                arcpy.CalculateField_management(sheds3, "Dissolve", "1", "VB")
                arcpy.Dissolve_management(sheds3, os.path.join(lakes, "dis" + name))
                dissolve = os.path.join(lakes, "dis" + name)
                arcpy.SpatialJoin_analysis(dissolve, fc, os.path.join(lakes, "pre" + name))
            except:
                pass
        else:
            arcpy.SpatialJoin_analysis(sheds3, fc, os.path.join(lakes, "pre" + name))

        pre = os.path.join(lakes, "pre" + name)
        arcpy.Erase_analysis(pre,fc, os.path.join(intws, "IWS" + name + ".shp"))
        arcpy.Delete_management(lakejunction)
        arcpy.Delete_management(trace)
        arcpy.Delete_management(traceshp)
        arcpy.Delete_management(tracesel)
        arcpy.Delete_management(sheds)
        arcpy.Delete_management(sheds_lyr)
        arcpy.Delete_management(center)
        arcpy.Delete_management(sheds2)
        arcpy.Delete_management(sheds3)
        del polynumber
        
    except:
        print "Something's went wrong with" + str(fc) 
        continue


            
arcpy.env.workspace = intws
shedlist = arcpy.ListFeatureClasses("*IWS*")
arcpy.Merge_management(shedlist, os.path.join(intws, "IWS" + subregion + ".shp"))




    
        








