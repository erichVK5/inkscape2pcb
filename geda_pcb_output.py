#! /usr/bin/python
'''
Copyright (C) 2017 Erich Heinzle a1039181@gmail.com
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
import inkex, simpletransform, cubicsuperpath, simplestyle, cspsubdiv

class MyEffect(inkex.Effect):

    header = "Element[\"\" \"InkscapeExportedElement\" \"\" \"\" 0 0 -10000 -10000 0 100 \"\"] # header stub\n(\n"
    footer = ") # footer stub\n"

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
                        help="Line thickness (mil/thou)")
        self.OptionParser.add_option("-p", "--plotInvisibleLayers",
                        action="store", type="inkbool", 
                        dest="plotInvisibleLayers", default="FALSE",
                        help="Plot invisible layers")

    def output(self):
        print ''.join(self.fp)

    def process_path(self, node, mat):
        d = node.get('d')
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
                    if not first:
                        self.fp.append('\tElementLine(%d %d %d %d %d)\n' % (Xlast,Ylast,X,Y,self.options.thickness))
                    Xlast = X
                    Ylast = Y
                    first = False

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
        self.fp = ['# gEDA PCB footprint exported from Inkscape\n']
        self.fp.append(self.header)
        x0 = self.options.xOrigin
        y0 = self.options.yOrigin
        scale = float(self.options.resolution)/100
        self.options.flat *= scale
        mirror = 1.0
        if self.options.mirror:
            mirror = -1.0
            if inkex.unittouu(self.document.getroot().xpath('@height', namespaces=inkex.NSS)[0]):
                y0 -= float(inkex.unittouu(self.document.getroot().xpath('@height', namespaces=inkex.NSS)[0]))
        self.groupmat = [[[scale, 0.0, -x0*scale], [0.0, mirror*scale, -y0*scale]]]
        doc = self.document.getroot()
        self.process_group(doc)
        self.fp.append(self.footer)

if __name__ == '__main__':   #pragma: no cover
    e = MyEffect()
    e.affect()


# vim: expandtab shiftwidth=4 tabstop=8 softtabstop=4 encoding=utf-8 textwidth=99
