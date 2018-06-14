# -------------------------------------------------------------------------------
# Name:        BRAT Validation
# Purpose:     Tests the output of BRAT against a shape file of beaver dams
#
# Author:      Braden Anderson
#
# Created:     05/2018
# -------------------------------------------------------------------------------

import os
import arcpy

def main(bratOutput, dams, outputName):
    """
    The main function
    :param bratOutput: The output of BRAT (a polyline shapefile)
    :param dams: A shapefile containing a point for each dam
    :param outputName: The name of the output shape file
    :param layerPackageName: The name for the layer package
    :return:
    """
    arcpy.env.overwriteOutput = True
    if outputName.endswith('.shp'):
        outNetwork = os.path.join(os.path.dirname(bratOutput), outputName)
    else:
        outNetwork = os.path.join(os.path.dirname(bratOutput), outputName + ".shp")
    arcpy.Delete_management(outNetwork)

    damFields = ['e_DamCt', 'e_DamDens', 'e_DamPcC']
    otherFields = ['Ex_Categor', 'Pt_Categor', 'mCC_EX_Ct', 'mCC_PT_Ct', 'mCC_EXtoPT']
    newFields = damFields + otherFields

    inputFields = ['SHAPE@LENGTH', 'oCC_EX', 'oCC_PT']

    if dams:
        arcpy.AddMessage("Adding fields that need dam input...")
        setDamAttributes(bratOutput, outNetwork, dams, damFields + ['Join_Count'] + inputFields, newFields)
    else:
        arcpy.CopyFeatures_management(bratOutput, outNetwork)
        addFields(outNetwork, otherFields)

    arcpy.AddMessage("Adding fields that don't need dam input...")
    setOtherAttributes(outNetwork, otherFields + inputFields)

    if dams:
        cleanUpFields(bratOutput, outNetwork, newFields)

    makeLayers(outNetwork)


def setDamAttributes(bratOutput, outputPath, dams, reqFields, newFields):
    """
    Sets all the dam info and updates the output file with that data
    :param bratOutput: The polyline we're basing our stuff off of
    :param outputPath: The polyline shapefile with BRAT output
    :param dams: The points shapefile of observed dams
    :param damFields: The fields we want to update for dam attributes
    :return:
    """
    arcpy.Snap_edit(dams, [[bratOutput, 'EDGE', '30 Meters']])
    arcpy.SpatialJoin_analysis(bratOutput,
                               dams,
                               outputPath,
                               join_operation='JOIN_ONE_TO_ONE',
                               join_type='KEEP_ALL',
                               match_option='INTERSECT')
    addFields(outputPath, newFields)

    with arcpy.da.UpdateCursor(outputPath, reqFields) as cursor:
        for row in cursor:
            damNum = row[-4]        # fourth to last attribute
            segLength = row[-3]   # third to last attribute
            oCC_EX = row[-2]        # second to last attribute
            oCC_PT = row[-1]        # last attribute

            row[0] = damNum
            row[1] = damNum / segLength * 1000
            try:
                row[2] = damNum / oCC_PT
            except ZeroDivisionError:
                row[2] = 0

            cursor.updateRow(row)

    arcpy.DeleteField_management(outputPath, ["Join_Count", "TARGET_FID"])



def addFields(outputPath, newFields):
    """
    Adds the fields we want to our output shape file
    :param outputPath: Our output shape file
    :param newFields: All the fields we want to add
    :return:
    """
    textFields = ['Ex_Categor', 'Pt_Categor']
    for field in newFields:
        if field in textFields:
            arcpy.AddField_management(outputPath, field, field_type="TEXT", field_length=50)
        else: # we assume that the default is doubles
            arcpy.AddField_management(outputPath, field, field_type="DOUBLE", field_precision=0, field_scale=0)


def setOtherAttributes(outputPath, fields):
    """
    Sets the attributes of all other things we want to do
    :param outputPath: The polyline shapefile with BRAT output
    :param fields: The fields we want to update
    :return:
    """
    with arcpy.da.UpdateCursor(outputPath, fields) as cursor:
        for row in cursor:
            segLength = row[-3] # third to last attribute
            oCC_EX = row[-2] # second to last attribute
            oCC_PT = row[-1] # last attribute

            # Handles Ex_Categor
            row[0] = handleCategory(oCC_EX)

            # Handles Pt_Categor
            row[1] = handleCategory(oCC_PT)

            # Handles mCC_EX_Ct
            row[2] = (oCC_EX * segLength) / 1000

            # Handles mCC_PT_Ct
            row[3] = (oCC_PT * segLength) / 1000

            # Handles mCC_EXtoPT
            if oCC_PT != 0:
                row[4] = oCC_EX / oCC_PT
            else:
                row[4] = 0

            cursor.updateRow(row)


def handleCategory(oCCVariable):
    """
    Returns a string based on the oCC value given to it
    :param oCCVariable: A number
    :return: String
    """
    if oCCVariable == 0:
        return "None"
    elif 0 < oCCVariable <= 1:
        return "Rare"
    elif 1 < oCCVariable <= 5:
        return "Occasional"
    elif 5 < oCCVariable <= 15:
        return "Frequent"
    elif 15 < oCCVariable <= 40:
        return "Pervasive"
    else:
        return "UNDEFINED"


def cleanUpFields(bratNetwork, outNetwork, newFields):
    """
    Removes unnecessary fields
    :param bratNetwork: The original, unmodified stream network
    :param outNetwork: The output network
    :param newFields: All the fields we added
    :return:
    """
    originalFields = [field.baseName for field in arcpy.ListFields(bratNetwork)]
    desiredFields = originalFields + newFields
    outputFields = [field.baseName for field in arcpy.ListFields(outNetwork)]

    removeFields = []
    for field in outputFields:
        if field not in desiredFields:
            removeFields.append(field)

    if len(removeFields) > 0:
        arcpy.DeleteField_management(outNetwork, removeFields)


def makeLayers(out_network):
    """
    Writes the layers
    :param out_network: The output network, which we want to make into a layer
    :return:
    """
    arcpy.AddMessage("Making layers...")
    output_folder = os.path.dirname(out_network)

    tribCodeFolder = os.path.dirname(os.path.abspath(__file__))
    symbologyFolder = os.path.join(tribCodeFolder, 'BRATSymbology')
    conflictLayer = os.path.join(symbologyFolder, "Conflict.lyr")
    managementLayer = os.path.join(symbologyFolder, "Management_Zones.lyr")

    makeLayer(output_folder, out_network, "Conflict_Potential", conflictLayer, isRaster=False)
    makeLayer(output_folder, out_network, "Beaver_Management_Zones", managementLayer, isRaster=False)


def makeLayer(output_folder, layer_base, new_layer_name, symbology_layer, isRaster, description="Made Up Description"):
    """
    Creates a layer and applies a symbology to it
    :param output_folder: Where we want to put the folder
    :param layer_base: What we should base the layer off of
    :param new_layer_name: What the layer should be called
    :param symbology_layer: The symbology that we will import
    :param isRaster: Tells us if it's a raster or not
    :param description: The discription to give to the layer file
    :return: The path to the new layer
    """
    new_layer = new_layer_name + "_lyr"
    new_layer_save = os.path.join(output_folder, new_layer_name + ".lyr")

    if isRaster:
        arcpy.MakeRasterLayer_management(layer_base, new_layer)
    else:
        arcpy.MakeFeatureLayer_management(layer_base, new_layer)

    arcpy.ApplySymbologyFromLayer_management(new_layer, symbology_layer)
    arcpy.SaveToLayerFile_management(new_layer, new_layer_save)
    new_layer_instance = arcpy.mapping.Layer(new_layer_save)
    new_layer_instance.description = description
    new_layer_instance.save()
    return new_layer_save