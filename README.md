
 xmly.py generates route files for simulation
  used by flightgear Route Manager or AI Aircraft )       
       by OpenRadar or ATC-pie for SID/STAR path outlines  
          ATC Pie support lags 
      
Source Format may be one of these: 
  -f ARDP   Fixed Lgth text file (US Only) from: ..
https://www.faa.gov/air_traffic/flight_info/aeronav/aero_data/NASR_Subscription/ 
  -f ASAL  Text file pasted from the Route Output section  of : ..  
  http://rfinder.asalink.net/free/ 
  -f LEVD  Level-D format SID/STAR data file by subscription to ..  
  https://www.navigraph.com/FmsData.aspx  
  -f PATH  KML Places File with an image overlay and paths section  
    Deprecated: Use -i PMKS with Overlay and Waypoints as Placemarks
  -f PMKS  KML Places file with Image Overlay and Placemark paths   
                                                                    
 Specification file, associates SID/STAR with runway ID             
  -k --skel path/to/skelFId  generates spec file, edit, add rwys    
  -s --spec path/to/specFId                                         
  Fields in skel, spec file have: ICAO, "Sid|Star", path.desc, RWYID
  leaving  eg:  KIAD, Sid, pfixIden.firstLegn, 08L                  
  arriving eg:  KIAD, Star, sfixIden.lastLegN, 08R                  
    N.B Sinle space only after comma separators                     
                                                                    
Outut format may be one of these:
  -g ATPI  ATC Pie for display on ATCPI radar 
    .. save in ATC-pie data path                                    
  -g FGAI  FlightGgear AI Flightplan for fgdata/AI/FlightPlans      
    .. useful for creating e.g local AI SID/STAR traffic            
  -g FGLD  FlightGear pseudo Level-D for Route Manager SID/STAR     
    .. does not support all tags found in Paid-For navigraph data  
    .. but can create useful SID/STAR paths from FAA/KML files      
  -g KMLS  Generate individual KML waypoint/track files for SID/STAR 
    .. Use gpxsee application to preview KML before flying RMV2 file
  -g ORDR  Open Radar for display on OpenRadar 
    .. save in  /OpenRadar/data/routes/ICAO/ICAO.procedures.xml     
  -g RMV2  Flightgear Route Manager Load format   
    .. Use FG Route Manager Load button to open the route 
                                                                    
Filter on data in out may be :
  -n --icao     NAME limit output to routes to/from icao NAME           
  -o            some/path/AUTO will construct an appropriate FGLD, FGAI, ORDR  
                formatted fileID and create the output file in some/path dir 
  -p --proc     PROCID :limit output to specific named STAR/SIDs        
  -r --runway   RWID Applies that runway ID into output xml tags      
  -t --type     TYPE limits output to STAR / SID procedure type         
  -w --waypoint WPID Limits output generated to paths ending WPID   
                                                                    
