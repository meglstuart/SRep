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

#We can get up, down, and crest boundary points as follows:
for i in xrange(srep.nUp):
    print(srep.getUpBoundaryPt(i))

#Let's make the up spokes twice as long:
srep.upLengths = 2.0*srep.upLengths
print(srep.upLengths)

# now, we update the vtk data structure based on our change.
srep.updatePoly()


# Then write to file. Note, this function also calls self.updatePoly(),
# so it's not strictly neccessary to updatePoly by hand before

srep.writeToFolder(outputpath)
