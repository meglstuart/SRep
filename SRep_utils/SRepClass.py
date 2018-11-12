from __future__ import division
import numpy as np
import vtk
import os, logging
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element, SubElement
from ElementTree_pretty import prettify
# logging.basicConfig(filename='SRep.log',level=logging.DEBUG)

from vtk.util import numpy_support


class SRep:
    """
    This is a python SRep class that reads and writes SALT sreps to file. It has the following fields:
        nUp                         Number of up spokes
        nDown                       Number of down spokes
        nCrest                      Number of crest spokes
        upMedialPoints              nUp x 3 array containing tail points of up
                                    spokes
        downMedialPoints            nDown x 3 array containing tail points of
                                    down spokes
        crestMedialPoints           nCrest x 3 array containing tail points of
                                    crest spokes
        upDirs                      nUp x 3 array containing up spoke
                                    directions
        downDirs                    nDown x 3 array containing down spoke
                                    directions
        crestDirs                   nCrest x 3 array containing crest spoke
                                    directions
        upLengths                   Array containing lengths of up spokes
        downLengths                 Array containing lengths of down spokes
        crestLengths                Array containing lengths of crest spokes
        __nRows
        __nCols
        __vtkUpPoly
        __vtkDownPoly
        __vtkCrestPoly

        TODO:
        upGrid         Not yet implemented: Dictionary implementation of a graph
        downGrid       Not yet implemented: Dictionary implementation of a graph
        crestLines     Not yet implemented: Dictionary implementation of a graph
    """
    def __init__(self,filename):
        self.__importSRep(filename)
        self.__getPointsFromPolys()

    def __importSRep(self,filename):
        tree = ET.parse(filename)
        upFileName = ''
        crestFileName = ''
        downFileName = ''
        self.__nCols = 0
        self.__nRows = 0
        headerFolder = os.path.dirname(filename)
        for child in tree.getroot():
            if child.tag == 'upSpoke':
                #if os.path.isabs(child.text):
                upFileName = os.path.join(headerFolder, child.text)
            elif child.tag == 'downSpoke':
                downFileName = os.path.join(headerFolder, child.text)
            elif child.tag == 'crestSpoke':
                crestFileName = os.path.join(headerFolder, child.text)
            elif child.tag == 'nRows':
                self.__nRows = (int)(child.text)
            elif child.tag == 'nCols':
                self.__nCols = (int)(child.text)
        logging.info("upSpoke file: " + upFileName)
        logging.info("downSpoke file: " + downFileName)
        logging.info("crestSpoke file: " + crestFileName)

        self.__vtkUpPoly = self.__readSpokeFile(upFileName)
        self.__vtkDownPoly = self.__readSpokeFile(downFileName)
        self.__vtkCrestPoly = self.__readSpokeFile(crestFileName)

    def __readSpokeFile(self, upFileName):
        reader = vtk.vtkXMLPolyDataReader()

        reader.SetFileName(upFileName)
        reader.Update()
        upSpokes = reader.GetOutput()

        upPointData = upSpokes.GetPointData()
        numberOfArrays = upPointData.GetNumberOfArrays()
        if numberOfArrays is 0:
            logging.warning("File: " + upFileName + " does not contain data")
        return upSpokes

    def __getPointsFromPolys(self):
        self.upLengths = numpy_support.vtk_to_numpy(self.__vtkUpPoly
                            .GetPointData().GetArray('spokeLength'))
        self.upDirs = numpy_support.vtk_to_numpy(self.__vtkUpPoly
                        .GetPointData().GetArray('spokeDirection'))
        self.nUp = self.__vtkUpPoly.GetNumberOfPoints()

        self.upMedialPoints = numpy_support.vtk_to_numpy(self.__vtkUpPoly.GetPoints().GetData())
        self.upBoundaryPoints = np.zeros([self.nUp, 3])
        for i in xrange(self.nUp):
            self.upBoundaryPoints[i] = (self.upMedialPoints[i]
                                        + self.upLengths[i]*self.upDirs[i])


        self.downLengths = numpy_support.vtk_to_numpy(self.__vtkDownPoly
                            .GetPointData().GetArray('spokeLength'))
        self.downDirs = numpy_support.vtk_to_numpy(self.__vtkDownPoly
                        .GetPointData().GetArray('spokeDirection'))
        self.nDown = self.__vtkDownPoly.GetNumberOfPoints()

        self.downMedialPoints = numpy_support.vtk_to_numpy(self.__vtkDownPoly.GetPoints().GetData())
        self.downPoints = np.zeros([2*self.nDown, 3])
        self.downBoundaryPoints = np.zeros([self.nDown, 3])
        for i in xrange(self.nDown):
            self.downBoundaryPoints[i] = (self.downMedialPoints[i]
                                        + self.downLengths[i]*self.downDirs[i])


        self.crestLengths = numpy_support.vtk_to_numpy(self.__vtkCrestPoly
                            .GetPointData().GetArray('spokeLength'))
        self.crestDirs = numpy_support.vtk_to_numpy(self.__vtkCrestPoly
                        .GetPointData().GetArray('spokeDirection'))
        self.nCrest = self.__vtkCrestPoly.GetNumberOfPoints()

        self.crestMedialPoints = numpy_support.vtk_to_numpy(self.__vtkCrestPoly.GetPoints().GetData())
        self.crestPoints = np.zeros([2*self.nCrest, 3])
        self.crestBoundaryPoints = np.zeros([self.nCrest, 3])
        for i in xrange(self.nCrest):
            self.crestBoundaryPoints[i] = (self.crestMedialPoints[i]
                                        + self.crestLengths[i]*self.crestDirs[i])


    def getUpBoundaryPt(self,i):
        return self.upMedialPoints[i] + self.upLengths[i]*self.upDirs[i]

    def getDownBoundaryPt(self,i):
        return self.downMedialPoints[i] + self.downLengths[i]*self.downDirs[i]

    def getCrestBoundaryPt(self,i):
        return self.crestMedialPoints[i] + self.crestLengths[i]*self.crestDirs[i]


    def updatePolyfromPoints(self):
        """ Assuming the new points have the same graph structure as the
        old points (i.e nobody has swapped places) """

        self.__vtkUpPoly = self.__updateSupport(self.__vtkUpPoly,self.upMedialPoints, self.upBoundaryPoints)
        self.__vtkDownPoly = self.__updateSupport(self.__vtkDownPoly,self.downMedialPoints, self.downBoundaryPoints)
        self.__vtkCrestPoly = self.__updateSupport(self.__vtkCrestPoly,self.crestMedialPoints, self.crestBoundaryPoints)



    def __updateSupport(self, origPoly, medials, boundaries):
        poly = vtk.vtkPolyData()
        poly.DeepCopy(origPoly)
        if poly.GetPointData().HasArray("spokeDirection"):
            poly.GetPointData().RemoveArray("spokeDirection")
        if poly.GetPointData().HasArray("spokeLength"):
            poly.GetPointData().RemoveArray("spokeLength")

        vtk_points = vtk.vtkPoints()

        spoke_directions = vtk.vtkDoubleArray()
        spoke_directions.SetNumberOfComponents(3)
        spoke_directions.SetName("spokeDirection")

        spoke_lengths = vtk.vtkDoubleArray()
        spoke_lengths.SetNumberOfComponents(1)
        spoke_lengths.SetName("spokeLength")

        for (x,y) in zip(medials,boundaries):
            vtk_points.InsertNextPoint(x)
            dir = np.subtract(y,x)
            length = np.linalg.norm(dir)
            dir = dir/length
            spoke_directions.InsertNextTuple(dir)
            spoke_lengths.InsertNextTuple1(length)

        poly.SetPoints(vtk_points)
        poly.GetPointData().AddArray(spoke_directions)
        poly.GetPointData().SetActiveVectors("spokeDirection")
        poly.GetPointData().AddArray(spoke_lengths)
        poly.GetPointData().SetActiveScalars("spokeLength")

        return poly


    def writeToFolder(self,foldername):
        headerFolder = os.path.abspath(foldername)

        outputUp = headerFolder + '/up.vtp'
        outputDown = headerFolder + '/down.vtp'
        outputCrest = headerFolder + '/crest.vtp'


        writer = vtk.vtkXMLPolyDataWriter()
        writer.SetDataModeToAscii()

        #-------------------------------------------------
        #               Write header.xml
        #-------------------------------------------------

        root = Element('s-rep')

        nRowsXMLElement = SubElement(root, 'nRows')
        nRowsXMLElement.text = str(self.__nRows)

        nColsXMLElement = SubElement(root, 'nCols')
        nColsXMLElement.text = str(self.__nCols)

        meshTypeXMLElement = SubElement(root, 'meshType')
        meshTypeXMLElement.text = 'Quad'

        colorXMLElement = SubElement(root, 'color')

        redXMLElement = SubElement(colorXMLElement, 'red')
        redXMLElement.text = str(0)

        greenXMLElement = SubElement(colorXMLElement, 'green')
        greenXMLElement.text = str(0.5)

        blueXMLElement = SubElement(colorXMLElement, 'blue')
        blueXMLElement.text = str(0)

        isMeanFlagXMLElement = SubElement(root, 'isMean')
        isMeanFlagXMLElement.text = 'False'

        meanStatPathXMLElement = SubElement(root, 'meanStatPath')
        meanStatPathXMLElement.text = ''

        upSpokeXMLElement = SubElement(root, 'upSpoke')
        upSpokeXMLElement.text = os.path.join(outputUp)

        downSpokeXMLElement = SubElement(root, 'downSpoke')
        downSpokeXMLElement.text = os.path.join(outputDown)

        crestSpokeXMLElement = SubElement(root, 'crestSpoke')
        crestSpokeXMLElement.text = os.path.join(outputCrest)

        file_handle = open(foldername + '/header.xml','w')
        file_handle.write(prettify(root))
        file_handle.close()

        #------------------------------------------
        #             write children
        #------------------------------------------


        writer.SetFileName(outputUp)
        writer.SetInputData(self.__vtkUpPoly)
        writer.Update()

        writer.SetFileName(outputDown)
        writer.SetInputData(self.__vtkDownPoly)
        writer.Update()

        writer.SetFileName(outputCrest)
        writer.SetInputData(self.__vtkCrestPoly)
        writer.Update()


# srep = SRep("test_objects/201295/header.xml")
# srep.updatePolyfromPoints()
# srep.writeToFolder("test_objects/testoutput")
# print(srep.crestPoints)
