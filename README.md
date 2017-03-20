# inkscape2pcb
inkscape2pcb contains inkscape extension scripts that allow export of inkscape paths to pcb-rnd layouts (.lht) and gEDA PCB footprints (.fp)

The scripts are based on the HPGL export script that ships with inkscape.

The scripts need to be added to your local inkscape extension script directory, for example

/usr/share/inkscape/extensions

before starting up inkscape again.

On loading, inkscape will find the scripts, at which point the "Save As" menu will allow saving to pcb-rnd .lht layout formats, and also gEDA PCB footprint (.fp) formats.

Currently, the exporter only exports lines and paths as line elements.

Support for polygon export may be added in the future, if viable.

Exported gEDA PCB footprints are natively supported by gEDA PCB, pcb-rnd, and KiCad.

Licence is GPL2, or at your option, a newer GPL licence.


