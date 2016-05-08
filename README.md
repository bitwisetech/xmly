# xmly.py

xmly.py is a Python2 utility for generating various format route files used by
Flightgear (Route Manager / AI Aircraft) and by OpenRadar or ATC-pie
for SID/STAR path outlines.

## Usage

```
python xmly.py -i --inputfid /path/to/InpFile -o --outputfid /path/to/{OutFile|"AUTO"}
               -f --srceformat  -g --genformat
```

with options:


```
  [-a --altitude ] [-h --help ] [-n --icao] [-p --proc] [-r rway]
  [-s --spec] [-t --type {"Sid"|"Star"}] [-w --waypoint]
```

## Source formats

Source Format may be one of these:
-  -f ARDP  Fixed Lgth text file (US Only) from: https://nfdc.faa.gov/xwiki/bin/view/NFDC/56+Day+NASR+Subscription
-  -f ASAL  Text file pasted from the Route Output section of: http://rfinder.asalink.net/free/
-  -f LEVD  Level-D format SID/STAR data file by subscription to https://www.navigraph.com/FmsData.aspx
-  -f PATH  KML Places File with an image overlay and paths section (**Deprecated**: Use -i PMKS with Overlay and Waypoints as Placemarks)
-  -f PMKS  KML Places file with Image Overlay and Placemark paths

Or use a specification file, manually generated, associating SID/STAR and Rwy with `-s --spec path/to/specFile`.
Fields in spec file have: ICAO, "Sid|Star", WYPTID, RWYID
- eg:  KIAD, Star, BARIN, 30
- eg:  KIAD, Sid, TIICE, 19L

## Output formats

Output format may be one of these:

- -g FGAI  FlightGgear AI Flightplan for fgdata/AI/FlightPlans
  - useful for creating e.g local AI SID/STAR traffic
- -g FGLD  FlightGear pseudo Level-D for Route Manager SID/STAR
  - does not support all tags foound in Paid-For navigraph data
  - but can create useful SID/STAR paths from FAA/KML files
- -g ORDR  Open Radar for display on OpenRadar
  - Save in  /OpenRadar/data/routes/ICAO/ICAO.procedures.xml
- -g RMV1  Flightgear Route Manager Load format
  - Use FG Route Manager Load button to open the route
- -g ATPI  ATC-Pie DRAW format
  - Use the generated ICAO.lst file to load the routes

Available options controling output:

- -o some/path/AUTO will construct an appropriate FGLD, FGAI, ORDR
       formatted fileID and create the output file in some/path dir
- -p --proc PROCID :limit output to specific named STAR/SIDs
- -r --runway RWID Applies that runway ID into output xml tags
- -t --type TYPE limits output to STAR / SID procedure type
- -w --waypoint WPID Limits output generated to paths ending WPID

Some editing of the output files may be needed e.g. Correct Altitude, gear, flaps, on-ground fields.

Open Radar segments tinted blueish for STAR paths, reddish for SIDs you may wish to add labels, etc and customize Runway ID numbering `./samp` directory contains sample source files.

## Example calls

```
python xmly.py -i ./samp/LIME-Sids.kml -o ./test/LIME-Sids-ORDR.xml -f PMKS -g ORDR -n LIME -r 24 -t Sid
```
To create KSFO.procedures.xml, all SIDs + STARs, all labelled R28L:
```
python xmly.py -i pathto/FAAData/STARDP.txt pathto/myprocs/AUTO -f ARDP -g FGAI -n KSFO -r 28L
```

To create KDEN.procedures.xml, SIDs only, labelled R35L:
```
python xmly.py -i pathto/FAAData/STARDP.txt pathto/myprocs/AUTO -f ARDP -g FGAI -n KDEN -t Sid -r 28L
```

To create KBOS.procedures.xml, STAR ROBUC1 ending JOBEE R04R:
```
python xmly.py -i pathto/FAAData/STARDP.txt pathto/myprocs/AUTO -f ARDP -g FGAI -n KBOS -p ROBUC1 -t Star -r 04R -w JOBEE
```

