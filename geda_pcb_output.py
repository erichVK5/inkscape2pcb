#! /usr/bin/python
'''
Copyright (C) 2017, 2022 Erich Heinzle a1039181@gmail.com
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
import inkex
from inkex.paths import CubicSuperPath, Path
from inkex.transforms import Transform
from inkex.bezier import cspsubdiv

class MyEffect(inkex.EffectExtension):

    header = "Element[\"\" \"InkscapeExportedElement\" \"\" \"\" 0 0 -10000 -10000 0 100 \"\"] # header stub\n(\n"
    footer = ") # footer stub\n"

    def add_arguments(self, pars):
        pars.add_argument("--flatness",
                        dest="flat",
                        type=float, 
                        default=0.2,
                        help="Minimum flatness of the subdivided curves")
        pars.add_argument("-m", "--mirror",
                        type=inkex.Boolean, 
                        dest="mirror", default="FALSE",
                        help="Mirror Y-Axis")
        pars.add_argument("-x", "--xOrigin",
                        type=float, 
                        dest="xOrigin", default=0.0,
                        help="X Origin (pixels)")
        pars.add_argument("-y", "--yOrigin",
                        type=float, 
                        dest="yOrigin", default=0.0,
                        help="Y Origin (pixels)")
        pars.add_argument("-s", "--scaling",
                        type=int, 
                        dest="scaling", default=1.0,
                        help="Scaling")
        pars.add_argument("-t", "--thickness",
                        type=int,
                        dest="thickness", default=8,
                        help="Line thickness (mil/thou)")
        pars.add_argument("-p", "--plotInvisibleLayers",
                        type=inkex.Boolean, 
                        dest="plotInvisibleLayers", default="FALSE",
                        help="Plot invisible layers")

    def process_path(self, node, transform):
        path = node.path.to_absolute()\
                   .transform(node.composed_transform())\
                   .transform(transform)\
                   .to_superpath()
        if path:
            cspsubdiv(path, self.options.flat)
            # path to HPGL commands
            first = True
            oldPosX = -1
            oldPosY = -1
            for singlePath in path:
                for singlePathPoint in singlePath:
                    posX, posY = singlePathPoint[1]
                    # check if point is repeating, if so, ignore
                    if not first:
                        self.fp.append('\tElementLine(%d %d %d %d %d)\n' % (oldPosX,oldPosY,posX,posY,self.options.thickness))
                    oldPosX = posX
                    oldPosY = posY
                    first = False

    def process_group(self, group):
        """flatten layers and groups to avoid recursion"""
        for child in group:
            if not isinstance(child, inkex.ShapeElement):
                continue
            if child.is_visible():
                if isinstance(child, inkex.Group):
                    self.process_group(child)
                elif isinstance(child, inkex.PathElement):
                    self.process_path(child, Transform(self.groupmat))

    def save(self, stream):
        stream.write(''.join(self.fp).encode('utf-8'))

    def effect(self):
        self.fp = ['# gEDA PCB footprint exported from Inkscape\n']
        self.fp.append(self.header)
        x0 = self.options.xOrigin
        y0 = self.options.yOrigin
        scale = float(self.options.scaling)
        self.options.flat *= scale
        mirror = 1.0
        if self.options.mirror:
            mirror = -1.0
            if self.svg.unittouu(self.document.getroot().xpath('@height', namespaces=inkex.NSS)[0]):
                y0 -= float(self.svg.unittouu(self.document.getroot().xpath('@height', namespaces=inkex.NSS)[0]))
        self.groupmat = [[scale, 0.0, 0.0], [0.0, mirror*scale, 0.0]]
        doc = self.document.getroot()
        self.process_group(doc)
        self.fp.append(self.footer)

if __name__ == '__main__':   #pragma: no cover
    MyEffect().run()

# vim: expandtab shiftwidth=4 tabstop=8 softtabstop=4 encoding=utf-8 textwidth=99
