import numpy as np
from SRepClass import SRep

headerpath = 'test_objects/201295/header.xml'
outputpath = 'test_objects/testoutput'

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
