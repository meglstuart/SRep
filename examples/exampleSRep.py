import numpy as np
import sys
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
from SRep_utils import SRep
# from ..SRep_utils import SRep

headerpath = 'test_object/201295/header.xml'
outputpath = 'test_object/testoutput'

srep = SRep(headerpath)
print(srep.nUp)
# print(srep.upBoundaryPoints)

# now you can edit the boundary and medial points

#let's make each of the spokes on the up side twice as long
for i in xrange(srep.nUp):
    srep.upBoundaryPoints[i] = (srep.upMedialPoints[i]
                                + 2*srep.upLengths[i]*srep.upDirs[i])

# We updated the boundary points, but that has not updated the radii.
# Soon, I will implement updating the whole srep class when changes are made to points

# now, we update the vtk data structure based on our change.
srep.updatePolyfromPoints()
