#! /usr/bin/python
'''
Copyright (C) 2017-2020 Erich Heinzle a1039181@gmail.com
based on GPL HPGL export code by Aaron Spike, aaron@ekips.org

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
'''
import inkex, simpletransform, cubicsuperpath, simplestyle, cspsubdiv, random

# we only want to export simple polygons to pcb-rnd
# so we need a test that determines if a path is a simple
# polygon, i.e. a polygon with no self intersection.
# python code for intersection test based on code by Ansh Riyal

def isSimplePolygon(total_path):
        simple = True
        for i in range(0,(len(total_path)-2)):
            for j in range(i+2, (len(total_path)-2)):
                simple = simple and not foundIntersection(total_path[i], total_path[i+1], total_path[j], total_path[j+1])
        return simple

# this function tests if point B is on segment AC
def bOnSegmentAC(a, b, c):
    if ((b.x <= max(a.x, c.x)) and (b.x >= min(a.x, c.x)) and
            (b.y <= max(a.y, c.y)) and (b.y >= min(a.y, c.y))):
        return True
    return False

# this function determines the orientation of the triangle ABC
def orientation(a, b, c):
    test = (float(b.y - a.y) * (c.x - b.x)) - (float(b.x - a.x)*(c.y - b.y))
    if (test > 0):
        return 1 # CW
    if (test < 0):
        return 2 # CCW
    return 0 # colinear

# this function determines if AB intersects CD
def foundIntersection(a,b,c,d):
    o1 = orientation(a,b,c)
    o2 = orientation(a,b,d)
    o3 = orientation(c,d,a)
    o4 = orientation(c,d,b)

    if ((o1 != o2) and (o3 != o4)):
        return True
    if ((o1 == 0) and bOnSegmentAC(a,b,c)):
        return True
    if ((o2 == 0) and bOnSegmentAC(a,d,c)):
        return True
    if ((o3 == 0) and bOnSegmentAC(b,a,d)):
        return True
    if ((o4 == 0) and bOnSegmentAC(b,c,d)):
        return True
    return False

class Point:
    def __init__(self, x,y):
        self.x = x
        self.y = y

    def equals(self, P):
        return ((self.x == P.x) and (self.y == P.y))

class MyEffect(inkex.Effect):

    header = "li:pcb-rnd-subcircuit-v7 {\n ha:subc.74 {\n  ha:attributes {\n   refdes = U0\n  }\n  ha:data {\n   li:padstack_prototypes {\n   }\n   li:objects {\n   }\n   li:layers {\n"
    pre_polygon_layer_defs = '''    ha:top-sig {\n     lid=0\n     ha:type {\n      copper = 1\n      top = 1\n     }\n     li:objects {\n'''
    post_polygon_layer_defs = '''     }\n     ha:combining {\n     }\n    }\n
    ha:bottom-sig {\n     lid = 1\n     ha:type {\n      bottom = 1\n      copper = 1\n     }\n
     li:objects {\n     }\n     ha:combining {\n     }\n    }\n
    ha:top-gnd {\n     lid=2\n     ha:type {\n      copper = 1\n      top = 1\n     }\n
     li:objects {\n     }\n     ha:combining {\n     }\n    }\n
    ha:bottom-gnd {\n     lid = 3\n     ha:type {\n      bottom = 1\n      copper = 1\n     }\n
     li:objects {\n     }\n     ha:combining {\n     }\n    }\n
    ha:outline {\n     lid = 4\n     ha:type {\n      boundary = 1\n     }\n
     li:objects {\n     }\n     ha:combining {\n     }\n    }\n
    ha:bottom-silk {\n     lid = 5\n     ha:type {\n      silk = 1\n      bottom = 1\n     }\n
     li:objects {\n     }\n     ha:combining {\n     }\n    }\n
    ha:top-silk {\n     lid = 6\n     ha:type {\n      silk = 1\n      top = 1\n     }\n
     li:objects {\n'''
    prefooter = '''     }\n     ha:combining {\n     }\n    }\n
    ha:subc-aux {\n     lid = 7\n     ha:type {\n      top = 1\n      misc = 1\n      virtual = 1\n     }\n
     li:objects {\n     }\n     ha:combining {\n     }\n    }\n'''
# we create a unique ID consistent with pcb-rnd uid expectations  
    uid_text = ''.join(random.choice("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ") for i in range(19))
    footer = prefooter + "   }\n  }\n  uid = " + uid_text + "AAAAB\n  ha:flags {\n  }\n }\n ha:pixmaps {\n }\n}\n"
    lineCount = 1
    polygonCount = 1
    
    def __init__(self):
        inkex.Effect.__init__(self)
        self.OptionParser.add_option("-f", "--flatness",
                        action="store", type="float", 
                        dest="flat", default=0.2,
                        help="Minimum flatness of the subdivided curves")
        self.OptionParser.add_option("-m", "--mirror",
                        action="store", type="inkbool", 
                        dest="mirror", default="TRUE",
                        help="Mirror Y-Axis")
        self.OptionParser.add_option("-x", "--xOrigin",
                        action="store", type="float", 
                        dest="xOrigin", default=0.0,
                        help="X Origin (pixels)")
        self.OptionParser.add_option("-y", "--yOrigin",
                        action="store", type="float", 
                        dest="yOrigin", default=0.0,
                        help="Y Origin (pixels)")
        self.OptionParser.add_option("-r", "--resolution",
                        action="store", type="int", 
                        dest="resolution", default=1000,
                        help="Resolution (dpi)")
        self.OptionParser.add_option("-t", "--thickness",
                        action="store", type="int",
                        dest="thickness", default=8,
                        help="Line thickness")
        self.OptionParser.add_option("-p", "--plotInvisibleLayers",
                        action="store", type="inkbool", 
                        dest="plotInvisibleLayers", default="FALSE",
                        help="Plot invisible layers")

    def output(self):
        print ''.join(self.lht)

    def export_polygon(self, total_path):
        self.polygons.append('        ha:polygon.%d {\n' % (self.polygonCount))
        self.polygons.append('         li:geometry {\n')
        self.polygons.append('           ta:contour {\n')
        for i in range(0, (len(total_path)-1)):
            self.polygons.append('            { %dmil; %dmil }\n' % (total_path[i].x/100.0, total_path[i].y/100.0))
        self.polygons.append('           }\n')
        self.polygons.append('         }\n')
        self.polygons.append('         clearance=40.0mil;\n')
        self.polygons.append('         ha:flags {\n')
        self.polygons.append('          clearpoly=1\n')
        self.polygons.append('         }\n')
        self.polygons.append('        }\n')
        self.polygonCount = self.polygonCount + 1

# here we process a cubic super path, and export it as lines on the top silk layer
    def process_path(self, node, mat):
        d = node.get('d')
        total_path = []
        if d:
            p = cubicsuperpath.parsePath(d)
            trans = node.get('transform')
            if trans:
                mat = simpletransform.composeTransform(mat, simpletransform.parseTransform(trans))
            simpletransform.applyTransformToPath(mat, p)
            cspsubdiv.cspsubdiv(p, self.options.flat)
            for sp in p:
                first = True
		X = -1
		Y = -1
                for csp in sp:
                    X = csp[1][0]
                    Y = csp[1][1]
                    total_path.append(Point(X, Y))
                    if not first:
                        self.lines.append('        ha:line.%d {\n' % (self.lineCount))
			self.lineCount = self.lineCount + 1
                        self.lines.append('         x1=%dmil; y1=%dmil; x2=%dmil; y2=%dmil; thickness=%dmil; clearance=40.0mil;\n' % (Xlast/100.0, Ylast/100.0, X/100.0, Y/100.0, self.options.thickness))
                        self.lines.append('         ha:flags {\n          clearline=1\n         }\n        }\n')

                    Xlast = X
                    Ylast = Y
                    first = False
        # here, we test if the path we just processed defines a simple polygon, i.e. one with no
        # self intersections. If so, we export it as a polygon as well, on the top copper layer.
        if isSimplePolygon(total_path):
            self.export_polygon(total_path)

    def process_group(self, group):
        style = group.get('style')
        if style:
            style = simplestyle.parseStyle(style)
            if style.has_key('display'):
                if style['display']=='none':
                    if not self.options.plotInvisibleLayers:
                        return
        trans = group.get('transform')
        if trans:
            self.groupmat.append(simpletransform.composeTransform(self.groupmat[-1], simpletransform.parseTransform(trans)))
        for node in group:
            if node.tag == inkex.addNS('path','svg'):
                self.process_path(node, self.groupmat[-1])
            if node.tag == inkex.addNS('g','svg'):
                self.process_group(node)
        if trans:
            self.groupmat.pop()

    def effect(self):
        self.lht = ['# pcb-rnd v7 subcircuit exported from Inkscape\n']
        self.lht.append(self.header)
        self.lht.append(self.pre_polygon_layer_defs)
        self.lines = ['']
        self.polygons = ['']
        x0 = self.options.xOrigin
        y0 = self.options.yOrigin
        scale = float(self.options.resolution)/10
        self.options.flat *= scale
        mirror = 1.0
        if self.options.mirror:
            mirror = -1.0
            if inkex.unittouu(self.document.getroot().xpath('@height', namespaces=inkex.NSS)[0]):
                y0 -= float(inkex.unittouu(self.document.getroot().xpath('@height', namespaces=inkex.NSS)[0]))
        self.groupmat = [[[scale, 0.0, -x0*scale], [0.0, mirror*scale, -y0*scale]]]
        doc = self.document.getroot()
        self.process_group(doc)
        self.lht.append(''.join(self.polygons))
        self.lht.append(self.post_polygon_layer_defs)
        self.lht.append(''.join(self.lines))
        self.lht.append(self.footer)
        self.lht.append('# here endeth the lihata')

if __name__ == '__main__':   #pragma: no cover
    e = MyEffect()
    e.affect()


# vim: expandtab shiftwidth=4 tabstop=8 softtabstop=4 encoding=utf-8 textwidth=99
