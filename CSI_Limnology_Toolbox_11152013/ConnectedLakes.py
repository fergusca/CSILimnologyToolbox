# ConnectedLakes.py

import arcpy, os

nwi = arcpy.GetParameterAsText(0)
nhd = arcpy.GetParameterAsText(1)
outfc = arcpy.GetParameterAsText(2)

arcpy.env.overwriteOutput = True
arcpy.env.parallelProcessingFactor = "100%"
arcpy.env.extent = nwi

cs = arcpy.SpatialReference()
cs.factoryCode = 102039
cs.create()
arcpy.env.outputCoordinateSystem = cs

fms = arcpy.FieldMappings()
fms.addTable(nwi)

arcpy.SpatialJoin_analysis(nwi, nhd, outfc, '', '', fms, '', "30 meters")