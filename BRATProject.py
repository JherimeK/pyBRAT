# -------------------------------------------------------------------------------
# Name:        BRAT Project Builder
# Purpose:     Gathers and structures the inputs for a BRAT project
#
# Author:      Jordan Gilbert
#
# Created:     09/25/2015
# Latest Update: 02/08/2017
# Copyright:   (c) Jordan Gilbert 2017
# Licence:     This work is licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International
#              License. To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/4.0/.
# -------------------------------------------------------------------------------

# import modules
import os
import arcpy
import sys
from SupportingFunctions import make_folder, make_layer
reload(make_layer)
reload(make_folder)


def main(projPath, ex_veg, hist_veg, network, DEM, landuse, valley, road, rr, canal, ownership):
    """Create a BRAT project and populate the inputs"""
    arcpy.env.overwriteOutput = True
    arcpy.env.workspace = projPath

    if not os.path.exists(projPath):
        os.mkdir(projPath)

    inputsFolder = make_folder(projPath, "Inputs")

    vegetationFolder = make_folder(inputsFolder, "01_Vegetation")
    networkFolder = make_folder(inputsFolder, "02_Network")
    topoFolder = make_folder(inputsFolder, "03_Topography")
    anthropogenicFolder = make_folder(inputsFolder, "04_Anthropogenic")

    exVegFolder = make_folder(vegetationFolder, "01_ExistingVegetation")
    histVegFolder = make_folder(vegetationFolder, "02_HistoricVegetation")

    valleyBottomFolder = make_folder(anthropogenicFolder, "01_ValleyBottom")
    roadFolder = make_folder(anthropogenicFolder, "02_Roads")
    railroadFolder = make_folder(anthropogenicFolder, "03_Railroads")
    canalsFolder = make_folder(anthropogenicFolder, "04_Canals")
    landUseFolder = make_folder(anthropogenicFolder, "05_LandUse")
    landOwnershipFolder = make_folder(anthropogenicFolder, "06_LandOwnership")

    sourceCodeFolder = os.path.dirname(os.path.abspath(__file__))
    symbologyFolder = os.path.join(sourceCodeFolder, 'BRATSymbology')

    # Gets all of our symbology variables set up
    exVegSuitabilitySymbology = os.path.join(symbologyFolder, "Existing_Veg_Suitability.lyr")
    exVegRiparianSymbology = os.path.join(symbologyFolder, "Existing_Veg_Riparian.lyr")
    exVegEVTTypeSymbology = os.path.join(symbologyFolder, "Existing_Veg_EVT_Type.lyr")
    exVegEVTClassSymbology = os.path.join(symbologyFolder, "Existing_Veg_EVT_Class.lyr")
    exVegClassNameSymbology = os.path.join(symbologyFolder, "Existing_Veg_ClassName.lyr")

    histVegGroupSymbology = os.path.join(symbologyFolder, "Historic_Veg_BPS_Type.lyr")
    histVegBPSNameSymbology = os.path.join(symbologyFolder, "Historic_Veg_BPS_Name.lyr")
    histVegSuitabilitySymbology = os.path.join(symbologyFolder, "Historic_Veg_Suitability.lyr")
    histVegRiparianSymbology = os.path.join(symbologyFolder, "Historic_Veg_Riparian.lyr")

    networkSymbology = os.path.join(symbologyFolder, "Network.lyr")
    landuseSymbology = os.path.join(symbologyFolder, "Land_Use_Raster.lyr")
    landOwnershipSymbology = os.path.join(symbologyFolder, "SurfaceManagementAgency.lyr")
    canalsSymbology = os.path.join(symbologyFolder, "Canals.lyr")
    roadsSymbology = os.path.join(symbologyFolder, "Roads.lyr")
    railroadsSymbology = os.path.join(symbologyFolder, "Railroads.lyr")
    valleyBottomSymbology = os.path.join(symbologyFolder, "ValleyBottom.lyr")
    valleyBottomOutlineSymbology = os.path.join(symbologyFolder, "ValleyBottom_Outline.lyr")
    flowDirectionSymbology = os.path.join(symbologyFolder, "Network_FlowDirection.lyr")

    # add the existing veg inputs to project
    exVegDestinations = copyMultiInputToFolder(exVegFolder, ex_veg, "Ex_Veg", isRaster=True)
    makeInputLayers(exVegDestinations, "Existing Vegetation Suitability for Beaver Dam Building", symbologyLayer=exVegSuitabilitySymbology, isRaster=True, fileName="ExVegSuitability")
    makeInputLayers(exVegDestinations, "Existing Riparian", symbologyLayer=exVegRiparianSymbology, isRaster=True, checkField="EVT_PHYS")
    makeInputLayers(exVegDestinations, "Veg Type - EVT Type", symbologyLayer=exVegEVTTypeSymbology, isRaster=True, checkField="EVT_PHYS")
    makeInputLayers(exVegDestinations, "Veg Type - EVT Class", symbologyLayer=exVegEVTClassSymbology, isRaster=True)
    makeInputLayers(exVegDestinations, "Veg Type - EVT Class Name", symbologyLayer=exVegClassNameSymbology, isRaster=True)


    # add the historic veg inputs to project
    histVegDestinations = copyMultiInputToFolder(histVegFolder, hist_veg, "Hist_Veg", isRaster=True)
    makeInputLayers(histVegDestinations, "Historic Vegetation Suitability for Beaver Dam Building", symbologyLayer=histVegSuitabilitySymbology, isRaster=True, fileName="HistVegSuitability")
    makeInputLayers(histVegDestinations, "Veg Type - BPS Type", symbologyLayer=histVegGroupSymbology, isRaster=True, checkField="GROUPVEG")
    makeInputLayers(histVegDestinations, "Veg Type - BPS Name", symbologyLayer=histVegBPSNameSymbology, isRaster=True)
    makeInputLayers(histVegDestinations, "Historic Riparian", symbologyLayer=histVegRiparianSymbology, isRaster=True, checkField="GROUPVEG")


    # add the network inputs to project
    networkDestinations = copyMultiInputToFolder(networkFolder, network, "Network", isRaster=False)
    makeInputLayers(networkDestinations, "Network", symbologyLayer=networkSymbology, isRaster=False)
    makeInputLayers(networkDestinations, "Flow Direction", symbologyLayer=flowDirectionSymbology, isRaster=False)

    # add the DEM inputs to the project
    copyMultiInputToFolder(topoFolder, DEM, "DEM", isRaster=True)
    makeTopoLayers(topoFolder)

    # add landuse raster to the project
    if landuse is not None:
        landuseDestinations = copyMultiInputToFolder(landUseFolder, landuse, "Land_Use", isRaster=True)
        makeInputLayers(landuseDestinations, "Land Use Raster", symbologyLayer=landuseSymbology, isRaster=True)

    # add the conflict inputs to the project
    if valley is not None:
        vallyBottomDestinations = copyMultiInputToFolder(valleyBottomFolder, valley, "Valley", isRaster=False)
        makeInputLayers(vallyBottomDestinations, "Valley Bottom Fill", symbologyLayer=valleyBottomSymbology, isRaster=False)
        makeInputLayers(vallyBottomDestinations, "Valley Bottom Outline", symbologyLayer=valleyBottomOutlineSymbology, isRaster=False)

    # add road layers to the project
    if road is not None:
        roadDestinations = copyMultiInputToFolder(roadFolder, road, "Roads", isRaster=False)
        makeInputLayers(roadDestinations, "Roads", symbologyLayer=roadsSymbology, isRaster=False)

    # add railroad layers to the project
    if rr is not None:
        rrDestinations = copyMultiInputToFolder(railroadFolder, rr, "Railroads", isRaster=False)
        makeInputLayers(rrDestinations, "Railroads", symbologyLayer=railroadsSymbology, isRaster=False)

    # add canal layers to the project
    if canal is not None:
        canalDestinations = copyMultiInputToFolder(canalsFolder, canal, "Canals", isRaster=False)
        makeInputLayers(canalDestinations, "Canals", symbologyLayer=canalsSymbology, isRaster=False)

    # add land ownership layers to the project
    if ownership is not None:
        ownershipDestinations = copyMultiInputToFolder(landOwnershipFolder, ownership, "Land Ownership", isRaster=False)
        makeInputLayers(ownershipDestinations, "Land Ownership", symbologyLayer=landOwnershipSymbology, isRaster=False)

def copyMultiInputToFolder(folderPath, multiInput, subFolderName, isRaster):
    """
    Copies multi input ArcGIS inputs into the folder that we want them in
    :param folderPath: The root folder, where we'll put a bunch of sub folders
    :param multiInput: A string, with paths to the inputs seperated by semicolons
    :param subFolderName: The name for each subfolder (will have a number after it)
    :param isRaster: Tells us if the thing is a raster or not
    :return:
    """
    splitInput = multiInput.split(";")
    i = 1
    destinations = []
    for inputPath in splitInput:
        newSubFolder = make_folder(folderPath, subFolderName + "_" + str(i))
        destinationPath = os.path.join(newSubFolder, os.path.basename(inputPath))

        if isRaster:
            arcpy.CopyRaster_management(inputPath, destinationPath)
        else:
            arcpy.Copy_management(inputPath, destinationPath)
        destinations.append(destinationPath)
        i += 1
    return destinations


def makeTopoLayers(topoFolder):
    """
    Writes the layers
    :param topoFolder: We want to make layers for the stuff in this folder
    :return:
    """
    sourceCodeFolder = os.path.dirname(os.path.abspath(__file__))
    symbologyFolder = os.path.join(sourceCodeFolder, 'BRATSymbology')
    demSymbology = os.path.join(symbologyFolder, "DEM.lyr")
    slopeSymbology = os.path.join(symbologyFolder, "Slope.lyr")
    hillshadeSymbology = os.path.join(symbologyFolder, "Hillshade.lyr")

    for folder in os.listdir(topoFolder):
        demFolderPath = os.path.join(topoFolder, folder)
        demFile = None
        for fileName in os.listdir(demFolderPath):
            if fileName.endswith(".tif"):
                demFile = os.path.join(demFolderPath, fileName)
                make_layer(demFolderPath, demFile, "DEM", demSymbology, is_raster=True)

        hillshadeFolder = make_folder(demFolderPath, "Hillshade")
        hillshadeFile = os.path.join(hillshadeFolder, "Hillshade.tif")
        arcpy.HillShade_3d(demFile, hillshadeFile)
        make_layer(hillshadeFolder, hillshadeFile, "Hillshade", hillshadeSymbology, is_raster=True)

        slopeFolder = make_folder(demFolderPath, "Slope")
        slopeFile = os.path.join(slopeFolder, "Slope.tif")
        outSlope = arcpy.sa.Slope(demFile)
        outSlope.save(slopeFile)
        make_layer(slopeFolder, slopeFile, "Slope", slopeSymbology, is_raster=True)


def makeInputLayers(destinations, layerName, isRaster, symbologyLayer=None, fileName=None, checkField=None):
    """
    Makes the layers for everything in the folder
    :param destinations: A list of paths to our input
    :param layerName: The name of the layer
    :param isRaster: Whether or not it's a raster
    :param symbologyLayer: The base for the symbology
    :param fileName: The name for the file (if it's different from the layerName)
    :param checkField: The name of the field that the symbology is based on
    :return:
    """
    if fileName == None:
        fileName = layerName
    for destination in destinations:
        destDirName = os.path.dirname(destination)
        if checkField:
            fields = [f.name for f in arcpy.ListFields(destination)]
            if checkField not in fields:
                # Stop execution if the field we're checking for is not in the layer base
                return
        make_layer(destDirName, destination, layerName, symbology_layer=symbologyLayer, is_raster=isRaster, file_name=fileName)


if __name__ == '__main__':
    main(
        sys.argv[1],
        sys.argv[2],
        sys.argv[3],
        sys.argv[4],
        sys.argv[5],
        sys.argv[6],
        sys.argv[7],
        sys.argv[8],
        sys.argv[9],
        sys.argv[10],
        sys.argv[11])
