#!/usr/bin/env python
##
# fplnMill class creates list(s) of leg dictionaries for various In, Out fmts
# a Leg is a single segment with at least: endpoint Lat, Lon
#    is stored as alegDict with keys for each of leg's (facets)
# a path is a list of legDicts comprising a single track
#    AI procs and RM 'Loads' would be created from a single path
#    RM STAR/SID file would be created from a list of multiple paths
##
import copy, getopt, sys
#
def normArgs(argv):
  global inptFId
  global outpFId
  global srceFmat
  global genrFmat
  global icaoSpec
  global procSpec
  global typeSpec
  global rwaySpec
  global wantHelp
  global wyptSpec
  global skelFId 
  global specFId 
  global sequNumb
  global targAlt
  global tRout
  global txtnSpec
# fallback values
  icaoSpec = 'icaoAAll'
  srceFmat = 'srceNDef'
  genrFmat = 'genrNDef'
  procSpec = 'procAAll'
  typeSpec = 'typeAAll'
  rwaySpec = 'rwayAAll'
  skelFId  = ''
  specFId  = ''
  wyptSpec = 'wyptAAll'
  targAlt  = 0
<<<<<<< HEAD
  inptFId = 'dflt.kml'
  outpFId = '{:s}-{:s}-{:s}.xml' \
=======
  inptFId = 'xmly-test-kmls.kml'
  outpFId = 'xmly-test-xmls/{:s}-{:s}-{:s}.xml' \
>>>>>>> 24cd8fbdbf03474d3a4b5fca45557b6e84048cfc
            .format(icaoSpec, typeSpec, procSpec)
  wantHelp = 0
  # get args
  try:
    opts, args = getopt.getopt(argv, "a:f:g:hi:k:o:n:p:r:s:t:w", \
         ["altitude=", "srcformat=", "genformat=", "inptfid=", "spec==", \
          "outpfid=","help", "icao=", "proc=",  \
          "runway=", "spec=", "type=", "waypoint="] )
  except getopt.GetoptError:
     print ('sorry, args do not make sense ')
     sys.exit(2)
  #
  for opt, arg in opts:
    if   opt in ("-f", "--srceFormat"):
      srceFmat = arg
    if   opt in ("-g", "--genFormat"):
      genrFmat  = arg
    if   opt in ("-a", "--alitude"):
      targAlt  = int(arg)
    if   opt in ("-h", "--help"):
      wantHelp = 1
    if   opt in ("-i", "--inptfid"):
      inptFId  = arg
    if   opt in ("-k", "--skel"):
      skelFId  = arg
    if   opt in ("-n", "--icao"):
      icaoSpec = arg
    if   opt in ("-o", "--outpfid"):
      outpFId  = arg
    if   opt in ("-p", "--proc"):
      procSpec = arg
    if   opt in ("-r", "--runway"):
      rwaySpec = arg
    if   opt in ("-s", "--spec"):
      specFId  = arg
    if   opt in ("-t", "--type"):
      typeSpec = arg
    if   opt in ("-w", "--waypoint"):
      wyptSpec = arg
  #
  if ( '.' in procSpec):
    procSepr = procSpec.find('.')
    txtnSpec = procSpec[:procSepr]
    procSpec = procSpec[(procSepr+1):]

#
class fplnMill:

  def __init__( self, tName):
    '''Create empty list and reset tally'''
    self.legL = []
    self.legsName = ''
    self.legsTale = 0
    self.procSpec = tName
    self.pathName = tName
    self.pthL = []
    self.pthsTale = 0
    self.specL = []
    self.specTale = 0

  #
  # asalink format input files: fixed record text from web query
  # http://rfinder.asalink.net/free/autoroute_rtx.php
  #
  def alegFromAsalink( self, tLine):
    '''parse single fixed lgth text record record'''
    # http://rfinder.asalink.net/free/autoroute_rtx.php
    # ID      FREQ   TRK   DIST   Coords                     Name/Remarks
    # LFMN    FFF.F    0      0   N4339'55.46" E00712'53.94" NICE COTE DAZ
    tAlt = 10000
    blnkPosn = tLine[:5].find(' ')
    if (blnkPosn < 1):
      blnkPosn = 5
    self._Iden = tLine[0:blnkPosn]
    self._Freq = tLine[8:14]
    if not(self._Freq == '      '):
      self._Freq = float(self._Freq)
    self._Trak = int(tLine[15:18])
    self._Dist = int(tLine[21:25])
    self._LatN = ((float(tLine[35:40])  / 60 + float(tLine[32:34]) ) / 60 + \
              float(tLine[29:31]))
    if ('S' in tLine[28:29]):
      self._LatN *= -1
    self._LonE = ((float(tLine[50:55])  / 60 + float(tLine[47:49])) / 60  +  \
              float(tLine[43:46]))
    if ('W' in tLine[42:43]):
      self._LonE *= -1
    self._Rmks = tLine[57:]
    return (dict(iden=self. _Iden, freq=self._Freq, dist=self._Dist, \
                 altF=tAlt, latN=self._LatN, lonE=self._LonE, rmks=self._Rmks))

  def addaLegd( self, tDict):
    ''' Append a sinle leg dictionary to legs list'''
    self.legL.append(tDict)
    self.legsTale += 1

  def fromASAL( self, inptFId):
    '''open a fixed length record text file pasted from rfinder.asalink.net'''
    tTyp = typeSpec
    with open(inptFId, 'r', encoding="ISO-8859-1") as srceHndl:
      for srceLine in srceHndl:
        if not('Remarks' in srceLine):
          self.addaLegd(self.alegFromAsalink(srceLine))
          #print(self.alegFromAsalink(srceLine))    
    pDic = dict( path = self.pathName, ssid = tTyp, \
      rway = rwaySpec, legL = self.legL, tale = self.legsTale)
    self.pthL.append(copy.deepcopy(pDic))
    self.pthsTale += 1
    srceHndl.close()

#
  def fromARDP( self, inptFId):
    '''open and scan fixed length record text file: FAA STARDP.txt'''
    with open(inptFId, 'r', encoding="ISO-8859-1") as srceHndl:
      currSequ = '     '
      progress = 'openFile'
      wantSubt = ''
      #stashed FAAN for matching STAR/SID to transition proc
      wantPost = ''
      srceNmbr = 0
      for srceLine in srceHndl:
        srceNmbr += 1  
        # segment name for all srceLines starts at col 30
        blnkPosn = 30 + srceLine[30:].find(' ')
        tsegName = srceLine[30:blnkPosn]
        # col39: FAA Name NNN.NNN name is in first record of a proc path
        if ('.' in srceLine[38:]):
          progress = 'anewSequ'
          self.legL = []
          self.legsTale = 0
          # parse procedure into preface, post and full FAA name
          stopPosn = srceLine.find('.')
          blnkPosn = stopPosn + srceLine[stopPosn:].find(' ')
          prefFAAN = srceLine[38:stopPosn]
          postFAAN = srceLine[(stopPosn+1):blnkPosn]
          fullFAAN = srceLine[38:blnkPosn]
          procBegl = tsegName
          # Get proc tye from 1st char and TX string
          if ('D' in srceLine[:1]):
            if ('TRANSITION' in srceLine):
              thisType = 'Sid-Txtn'
              self.pathName = fullFAAN
              tAlt = 5000
            else:
              thisType = 'Sid'
              # make up Sid name from first wypt and FAA procSpec
              self.pathName = tsegName + '.' + prefFAAN
              tAlt = 250
          if ('S' in srceLine[:1]):
            # For arrival pathName is second part of FAA name
            starProc = postFAAN
            if ('TRANSITION' in srceLine):
              thisType = 'Star-Txtn'
              # pathname is first wypt, stash proc part of name for matching
              ##17Je13 self.pathName = fullFAAN
              ##19Se02 self.pathName = postFAAN
              self.pathName = prefFAAN + '.' + postFAAN
              # star subTag matches its transition subtag
              txtnProc = postFAAN
              ## 19Se08  ???? maybetxtnProc = prefpostFAAN
              tAlt = 10000
            else :
              thisType = 'Star'
              self.pathName = postFAAN
              tAlt = 5000
              # stash 1st leg name to match txtn end leg
          #End processing for first line in procedure
        else:
          blnkPosn = 30 + srceLine[30:].find(' ')
          currLegn = srceLine[30:blnkPosn]
          # not a segment start, parse current leg name
        # scan All srceLines for position info, legDict may be discarded
        latNS    = srceLine[13:14]
        latDD    = float(srceLine[14:16])
        latMM    = float(srceLine[16:18])
        latSS    = float(srceLine[18:20])
        latSD    = float(srceLine[20:21])
        lonEW    = srceLine[21:22]
        lonDD    = float(srceLine[22:25])
        lonMM    = float(srceLine[25:27])
        lonSS    = float(srceLine[27:29])
        lonSD    = float(srceLine[29:30])
        latDec   = latDD + latMM/60 + latSS/3600 + latSD/36000
        lonDec   = lonDD + lonMM/60 + lonSS/3600 + lonSD/36000
        if ( latNS == 'S' ):
          latDec = latDec * -1
        if ( lonEW == 'W' ):
          lonDec = lonDec * -1
        tNam = tsegName
        lDic = dict( iden = tsegName, latN = latDec, lonE = lonDec, \
                     altF = int(tAlt), rmks='none' )
        # Do not apend Adapted Airport location to legsList
        if not (srceLine[10:12] == 'AA') :
          self.legL.append(lDic)
          self.legsTale += 1
        # preset as unwanted, adjust alts anyway, then decide if wanted
        progress = 'dontWant'
        if (('Star' in thisType ) & \
            ((typeSpec in thisType )|(typeSpec == 'typeAAll' ))):
          tAlt -= 500
          # Star-Transitions follow Star in FAA input file, do Star first
          if (not('Txtn' in thisType ) ):
            # Wanted if either wyptID matches last trk seg or is unspecified
            if ((srceLine[10:12] == 'AA') & (tsegName in icaoSpec)):
              if ((procSpec == postFAAN) | (procSpec == 'procAAll')) :
                if ((wyptSpec == self.legL[self.legsTale -1]['iden']) \
                 | (wyptSpec == 'wyptAAll')):
                  progress = 'wantThis'
                  # Stash STAR's beginning leg for match to Star-Txtn
                  wantPost = postFAAN
          if (   ('Txtn' in thisType ) ):
             # Star-txtn: txtnProc is postFAAN, match to prev proc's postFAAN
            ##if ((wantPost != '') & (tsegName in postFAAN)):
            ##19Se03 if ((wantPost != '') & (wantPost in postFAAN)) & (tsegName in postFAAN)):
              if ((wantPost != '') & (wantPost in postFAAN) & (tsegName in postFAAN)):
                progress = 'wantThis'
        if (('Sid' in thisType ) & \
            (( typeSpec in thisType)|(typeSpec == 'typeAAll' ))):
          tAlt += 500
          # Sid-Transitions follow Star in FAA input file, do Star first
          if ( not('Txtn' in thisType )) :
            if ((srceLine[10:12] == 'AA') & (tsegName in icaoSpec)):
              if ( ( procSpec == postFAAN) | (procSpec == 'procAAll')) :
                # Wanted if either wyptID matches first trk seg or unspecified
                if ((wyptSpec == procBegl) | (wyptSpec == 'wyptAAll')):
                  progress = 'wantThis'
                  # Stash STAR's beginning leg for match to Star-Txtn
                  wantPost = postFAAN
          else :
            # Sid-txtn: txtnProc is postFAAN, match to prev proc's postFAAN
            if (wantPost in postFAAN):
              progress = 'wantThis'
        if (progress == 'wantThis'):
            #print('want line: ', srceNmbr) 
            tTyp = thisType
            pDic = dict( path = self.pathName, ssid = tTyp, \
              rway = rwaySpec, legL = self.legL, tale = self.legsTale)
            self.pthL.append(copy.deepcopy(pDic))
            self.pthsTale += 1
    srceHndl.close()

  #
  # kml input format: kml path created at https://flightplandatabase.com 'Save KML' 
  def fromKML ( self, inptFId):
    '''open a flightplandatabase kml track file, append to prcs'''
    procSpec = (icaoSpec + '-' + typeSpec)
    tTyp = typeSpec
    with open(inptFId, 'r') as srceHndl:
      cordFlag = 0
      procSpec = ''
      for srceLine in srceHndl:
        # Flag to terminate track segment
        if ('</coordinates>' in srceLine):
          cordFlag = 0
        # first Line after Placemark: get procedure name, cancel flag
        if ('</name>' in srceLine):
          begnPosn = srceLine.find('<name>') + 6
          endnPosn = srceLine.find('</name>')
          tsegName = self.pathName = srceLine[begnPosn:endnPosn]
        # Flag start of track segment coordinate list
        if ('<coordinates>' in srceLine):
          cordFlag = 1
          pDic = {}
          self.legL = []
        # extract track coordinates list, first coords may include the tag itself 
        if (cordFlag == 1 ):
          self.legsName = tsegName
          self.legsTale = 0
          tSrc = (srceLine.replace('<coordinates>', ''))
          tSrc = (tSrc.lstrip().rstrip())
          tMrk = 0
          tIdx = 0
          while ((tSrc != '') & (tMrk >= 0)):
            tIdx += 1
            tMrk = tSrc.find(',')
            tLon = float(tSrc[:tMrk])
            tSrc = tSrc[tMrk+1:]
            tMrk = tSrc.find(',')
            tLat = float(tSrc[:tMrk])
            tSrc = tSrc[tMrk+1:]
            # alt fileds precede ' ' except last on coord line
            tMrk = tSrc.find(' ')
            if (tMrk < 0):
              tAlt = tSrc
            else:
              tAlt = tSrc[:tMrk]
            tSrc = tSrc[tMrk+1:]
            tNam = tsegName + '-' + str(tIdx)
            lDic = dict( iden = tNam, latN = tLat, \
                         lonE = tLon, \
                         altF = int(tAlt) + 500 * tIdx, rmks = 'none' )
            self.legL.append(lDic)
            self.legsTale += 1
          pDic = dict( path = self.pathName, rway = rwaySpec, ssid = tTyp, \
                           legL = self.legL, tale = self.legsTale)
          self.pthL.append(copy.deepcopy(pDic))
          #self.pthL.append(dict( path = self.pathName, rway = rwaySpec, \
          #                 legL = lDic, tale = self.legsTale))
          self.pthsTale += 1
    srceHndl.close()

  #
  # Level-D input format: xml file from navigraph subscription
  #   Each named procedure is a list of placemarks
  def fromLEVD( self, inptFId):
    wpntIndx = tNam = tTyp = tLat = tLon = tAlt =''
    '''open a Level-D xml file, create dictionary of path legs'''
    with open(inptFId, 'r') as srceHndl:
      # LevD has only one ICAO id per file, end tag depends on proc type
      progress = 'seekICAO'
      ssidEnds = 'noEndYet'
      for srceLine in srceHndl:
        if (( progress == 'seekICAO') & ('<Airport ICAOcode="' in srceLine)) :
          begnPosn = (srceLine.find('<Airport ICAOcode="') + 19 )
          endnPosn = (srceLine.find('">') )
          icaoSpec = srceLine[begnPosn:endnPosn]
          progress = 'seekNextPath'
        if ((progress == 'seekNextPath') & (' Name="' in srceLine)):
          begnPosn = srceLine.find('<') + 1
          endnPosn = (srceLine[begnPosn:].find(' ')) + begnPosn
          ssidType = srceLine[begnPosn:endnPosn]
          ssidEnds = '</' + ssidType + '>'
          if ( ssidType == 'Star_Transition'):
            ssidEnds = '</StarTr_Waypoint>'
          # advance begnPosn to first "
          begnPosn = srceLine.find('Name="') + 6
          endnPosn = srceLine[begnPosn + 1 :].find('"') + begnPosn + 1
          self.pathName = srceLine[begnPosn:endnPosn]
          rwayCurr = ''
          if (( ssidType == 'Sid') | ( ssidType == 'Star')) :
            begnPosn = srceLine.find('Runways="') + 9
            endnPosn = srceLine.find('">')
            rwayCurr = srceLine[begnPosn:endnPosn]
          # Clean Legs for each new path
          pDic = {}
          self.legL = []
          self.legsTale = 0
          wpntIndx = tNam = tTyp = tLat = tLon = tAlt =''
          progress = 'seekNextWpnt'
        # Leg elements are on multi lines collected later
        # _Waypoint in ending tag indicates all elements collected
        if ((progress == 'seekNextWpnt') & ('_Waypoint ID="' in srceLine)):
          begnPosn = srceLine.find('_Waypoint ID="') + 14
          endnPosn = srceLine[begnPosn:].find('"')
          wpntIndx = srceLine[begnPosn:endnPosn]
          progress = 'doinWpnt'
        if (( progress == 'doinWpnt') & ('</' in srceLine) & \
                                ('_Waypoint>' in srceLine)) :
          # skip invalid LatLon and fill Leg Dict and append to path list
          if ( (tLat != 0) & (tLon != 0) ):
            lDic = dict( iden = tNam, type = tTyp, latN = tLat, lonE = tLon, \
                          altF = tAlt, indx = wpntIndx, rmks = 'none')
            self.legL.append(lDic)
            self.legsTale += 1
          progress = 'seekNextWpnt'
        if ( ((progress == 'seekNextWpnt') & (ssidEnds  in srceLine)) \
            |(tTyp == '(VECTORS)') ):
          if ( (typeSpec != 'typeAAll') & (ssidType != typeSpec)):
            progress = 'dontWant'
          if ( (rwaySpec != 'rwayAAll') & (rwayCurr != rwaySpec)):
            progress = 'dontWant'
          if (progress != 'dontWant'):
            pDic = dict( path = self.pathName, rway = rwayCurr, ssid = ssidType, \
                         legL = self.legL, tale = self.legsTale)
            self.pthL.append(copy.deepcopy(pDic))
            self.pthsTale += 1
          progress = 'seekNextPath'
        if (( progress == 'doinWpnt') & ('<Name>' in srceLine)):
          begnPosn = srceLine.find('<Name>') + 6
          endnPosn = srceLine.find('</Name>')
          tNam = srceLine[begnPosn:endnPosn]
        if (( progress == 'doinWpnt') & ('<Type>' in srceLine)):
          begnPosn = srceLine.find('<Type>') + 6
          endnPosn = srceLine.find('</Type>')
          tTyp = srceLine[begnPosn:endnPosn]
          typeFlag = tTyp
        if (( progress == 'doinWpnt') & ('<Latitude>' in srceLine)):
          begnPosn = srceLine.find('<Latitude>') + 10
          endnPosn = srceLine.find('</Latitude>')
          tLat = float(srceLine[begnPosn:endnPosn])
        if (( progress == 'doinWpnt') & ('<Longitude>' in srceLine)):
          begnPosn = srceLine.find('<Longitude>') + 11
          endnPosn = srceLine.find('</Longitude>')
          tLon = float(srceLine[begnPosn:endnPosn])
        if (( progress == 'doinWpnt') & ('<Altitude>' in srceLine)):
          begnPosn = srceLine.find('<Altitude>') + 10
          endnPosn = srceLine.find('</Altitude>')
          tAlt = int(srceLine[begnPosn:endnPosn])
    srceHndl.close()


  # OpenRadar input: an optional list of name points then xml path specs
  def fromORDR( self, inptFId):
    # must stash list of named points with lat, lon
    self.pntsList = []
    self.pntsTale = 0
    with open(inptFId, 'r') as srceHndl:
      for srceLine in srceHndl:
        # for all 'addPoint lines save name, lat, lon in pntsList
        if ( '<addPoint code=' in srceLine):
          begnPosn = srceLine.find( '<addPoint code="')  + 16
          endnPosn = srceLine[begnPosn:].find( '"') + begnPosn
          pntsName = srceLine[begnPosn:endnPosn]
          begnPosn = srceLine.find( 'point="')      + 7
          endnPosn = srceLine[begnPosn:].find( '"/>') + begnPosn
          sstrLlon = srceLine[begnPosn:endnPosn]
          begnPosn = sstrLlon.find(',')
          pntsLati = sstrLlon[:begnPosn]
          pntsLong = sstrLlon[(begnPosn+1):]
          pntsItem = dict( iden = pntsName, latS = pntsLati, lonS = pntsLong)
          # Named points hould contain no duplcate, do not test for dups
          self.pntsList.append(copy.deepcopy(pntsItem))
          self.pntsTale += 1
        # at 'route name' tag parse fields
        if ( '<route' in srceLine):
          begnPosn = srceLine.find( ' name="')  + 7
          endnPosn = srceLine[begnPosn:].find( '"') + begnPosn
          self.pathName = srceLine[begnPosn:endnPosn]
          begnPosn = srceLine.find( 'displayMode="')  + 13
          endnPosn = srceLine[begnPosn:].find( '"') + begnPosn
          ssidType = srceLine[begnPosn:endnPosn]
          begnPosn = srceLine.find( 'color="')  + 7
          endnPosn = srceLine[begnPosn:].find( '"') + begnPosn
          tRGB     = srceLine[begnPosn:endnPosn]
          self.legL = []
          self.legsTale = 0
        # at 'runway' tag parse fields
        if ( '<activeLan' in srceLine):
          begnPosn = srceLine.find( '<activeLandingRunways>')  + 22
          endnPosn = srceLine[begnPosn:].find( '</active') + begnPosn
          rwaySpec = srceLine[begnPosn:endnPosn]
        if ( '<activeSta' in srceLine):
          begnPosn = srceLine.find( '<activeStartRunways>')  + 20
          endnPosn = srceLine[begnPosn:].find( '</active') + begnPosn
          rwaySpec = srceLine[begnPosn:endnPosn]
        # at 'line start' tag parse and create leg
        if ( '<line start' in srceLine):
          begnPosn = srceLine.find( '<line start="')  + 13
          endnPosn = srceLine[begnPosn:].find( '"') + begnPosn
          begnLegn = srceLine[begnPosn:endnPosn]
          # OR line segments dup begn name with prev endn name
          begnPosn = srceLine.find( 'end="')  + 5
          endnPosn = srceLine[begnPosn:].find( '"') + begnPosn
          endnLegn = srceLine[begnPosn:endnPosn]
          # parse any tesxt field as 'remarks'
          self.rmks = ''
          if ( 'text=' in srceLine):
            begnPosn = srceLine.find( 'text="')  + 6
            endnPosn = srceLine[begnPosn:].find( '"') + begnPosn
            self.rmks = srceLine[begnPosn:endnPosn]
          else:
            self.rmks = 'none'
          # match an 'added-point' with lat, lon from list
          addnPntn = 0
          for p in range(self.pntsTale):
            if (self.pntsList[p]['iden'] == begnLegn):
              latDec = float(self.pntsList[p]['latS'])
              lonDec = float(self.pntsList[p]['lonS'])
              lDic   = dict( iden = begnLegn, latN = latDec, lonE = lonDec, \
                             altF = float(0),  rmks = self.rmks)
              self.legL.append(lDic)
              self.legsTale += 1
              addnPntn = 1
          if (addnPntn == 0):
            # not addpoint: save as waypoint name with bogus lat, lon
            latDec =  99
            lonDec = 199
            lDic   = dict( iden = begnLegn, latN = latDec,   lonE = lonDec, \
                           altF = float(0), rmks = self.rmks )
            self.legL.append(lDic)
            self.legsTale += 1
        # after last leg segment, use stashed endn name as last leg
        if ( '</route>' in srceLine):
          addnPntn = 0
          for p in range(self.pntsTale):
            if (self.pntsList[p]['iden'] == endnLegn):
              latDec = float(self.pntsList[p]['latS'])
              lonDec = float(self.pntsList[p]['lonS'])
              lDic   = dict( iden = begnLegn, latN = latDec,   lonE = lonDec, \
                             altF = float(0), rmks = self.rmks )
              self.legL.append(lDic)
              self.legsTale += 1
              addnPntn = 1
          if (addnPntn == 0):
            # not addpoint: save as waypoint name with bogus lat, lon
            latDec =  99
            lonDec = 199
            lDic = dict( iden = begnLegn, latN = latDec,   lonE = lonDec, \
                         altF = float(0), rmks = self.rmks )
            self.legL.append(lDic)
            self.legsTale += 1
          # leg list complete, append as new path
          pDic = dict( path = self.pathName, rway = rwaySpec, ssid = ssidType, \
                       legL = self.legL, tale = self.legsTale)
          self.pthL.append(copy.deepcopy(pDic))
          self.pthsTale += 1
    srceHndl.close()

  #
  # kml overlay input format: kml path created from tracing a GE Image Overlay
  #   Deprecated: works for GE paths .. uwse fromKmlPmrk instead
  def fromPATH( self, inptFId):
    '''open a GE kml image olay + track lists file, append to prcs'''
    procSpec = (icaoSpec + '-' + typeSpec)
    tTyp = typeSpec
    with open(inptFId, 'r') as srceHndl:
      procFlag = 0
      olayFlag = 0
      cordFlag = 0
      procSpec = ''
      for srceLine in srceHndl:
        # Flag to terminate track segment
        if ((olayFlag == 1 ) & ('</coordinates>' in srceLine)):
          cordFlag = 0
        # Flag end of Image Overlay section: Placemarks follw
        if ('</GroundOverlay' in srceLine) :
          olayFlag = 1
        # first Line after Placemark: get procedure name, cancel flag
        if ((olayFlag == 1 ) & (procFlag == 1 )):
          begnPosn = srceLine.find('<name>') + 6
          endnPosn = srceLine.find('</name>')
          self.pathName = srceLine[begnPosn:endnPosn]
          procFlag = 0
        #
        if ((olayFlag == 1 ) & ('<Placemark>' in srceLine)):
          procFlag = 1
        # Find <name> field and extract name of track segment
        if ((olayFlag == 1 ) & (cordFlag == 0 ) & ('<name>' in srceLine)):
          begnPosn = srceLine.find('<name>') + 6
          endnPosn = srceLine.find('</name>')
          tsegName = srceLine[begnPosn:endnPosn]
        # Flag start of track segment coordinate list
        if ((olayFlag == 1 ) & ('<coordinates>' in srceLine)):
          cordFlag = 1
          pDic = {}
          self.legL = []
        # extract track coordinates list
        if ((cordFlag == 1 ) & ~('<' in srceLine)):
          self.legsName = tsegName
          self.legsTale = 0
          tSrc = (srceLine.lstrip().rstrip())
          tMrk = 0
          tIdx = 0
          while ((tSrc != '') & (tMrk >= 0)):
            tIdx += 1
            tMrk = tSrc.find(',')
            tLon = float(tSrc[:tMrk])
            tSrc = tSrc[tMrk+1:]
            tMrk = tSrc.find(',')
            tLat = float(tSrc[:tMrk])
            tSrc = tSrc[tMrk+1:]
            # alt fileds precede ' ' except last on coord line
            tMrk = tSrc.find(' ')
            if (tMrk < 0):
              tAlt = tSrc
            else:
              tAlt = tSrc[:tMrk]
            tSrc = tSrc[tMrk+1:]
            tNam = tsegName + '-' + str(tIdx)
            lDic = dict( iden = tNam, latN = tLat, \
                         lonE = tLon, \
                         altF = int(tAlt) + 500 * tIdx, rmks = 'none' )
            self.legL.append(lDic)
            self.legsTale += 1
          pDic = dict( path = self.pathName, rway = rwaySpec, ssid = tTyp, \
                           legL = self.legL, tale = self.legsTale)
          self.pthL.append(copy.deepcopy(pDic))
          #self.pthL.append(dict( path = self.pathName, rway = rwaySpec, \
          #                 legL = lDic, tale = self.legsTale))
          self.pthsTale += 1
    srceHndl.close()

  #
  # kml overlay input format: kml path created from tracing a GE Image Overlay
  #   Each path is a separate named GE folder containingplacemarks
  #   Star/Sid image overlay with 'GroundOverlay' precedes Sid/Star paths
  def fromPMKS( self, inptFId):
    '''open a GE kml image olay + Placemark list, append to prcs'''
    procSpec = (icaoSpec + '-' + typeSpec)
    tTyp = typeSpec
    with open(inptFId, 'r') as srceHndl:
      progress = 'seekImag'

      pastImag = 0  # ==1 after </GroundOverlay> tag at end: Image Overlay
      pathFldr = 0  # ==1 pastImag & 1st <Folder> until path's <name> tag
      legsFlag = 0  # ==1 after path's name until </Folder>

      pmrkFlag = 0
      procFlag = 0
      procSpec = ''
      for srceLine in srceHndl:
        # Find end of Image Overlay section: Sid/Star peths follow
        if (( progress == 'seekImag') & ('</GroundOverlay' in srceLine)) :
          progress = 'seekNextPath'
        #Each folder segment after GroundOverlay: new Sid/Star path
        if ((progress == 'seekNextPath') & ('<Folder>' in srceLine)):
          progress = 'seekPathName'
        # <name> tag after <Folder> tag: get Sid/Star path name, cancel flag
        if (( progress == 'seekPathName' ) & ('<name>' in srceLine)):
          begnPosn = srceLine.find('<name>') + 6
          endnPosn = srceLine.find('</name>')
          self.pathName = srceLine[begnPosn:endnPosn]
          # Clean Legs for each new path
          pDic = {}
          self.legL = []
          self.legsTale = 0
          progress = 'seekNextPmrk'
        if (( progress == 'seekNextPmrk' ) & ('<Placemark>' in srceLine)):
          progress = 'doinPmrk'
        if (( progress == 'doinPmrk' ) & ('<name>' in srceLine)):
          # Find <name> field and extract name of track segment
          begnPosn = srceLine.find('<name>') + 6
          endnPosn = srceLine.find('</name>')
          tsegName = srceLine[begnPosn:endnPosn]
          self.legsName = tsegName
        if (( progress == 'doinPmrk' ) & ('<coordinates>' in srceLine)):
          tSrc = (srceLine.lstrip().rstrip())
          tMrk = 0
          tIdx = 0
          tIdx += 1
          #find first comma after Lon
          tMrk = tSrc.find(',')
          # offset '<coordinates>' tag
          tLon = float(tSrc[13:tMrk])
          #strip head of srceLine
          tSrc = tSrc[tMrk+1:]
          # second comma after Lat
          tMrk = tSrc.find(',')
          tLat = float(tSrc[:tMrk])
          # strip Lat field
          tSrc = tSrc[tMrk+1:]
          # '<.coor' after Alt
          tMrk = tSrc.find('</coor')
          tAlt = float(tSrc[:tMrk])
          #tNam = tsegName + '-' + str(tIdx)
          tNam = tsegName
          lDic = dict( iden = tNam, latN = tLat, \
                       lonE = tLon, \
                       altF = int(tAlt) + 500 * tIdx )
          self.legL.append(lDic)
          self.legsTale += 1
        if (( progress == 'doinPmrk' ) & ('</Placemark>' in srceLine)):
          progress = 'seekNextPmrk'
        if (( progress == 'seekNextPmrk' ) & ('</Folder>' in srceLine)):
          pDic = dict( path = self.pathName, rway = rwaySpec, ssid = tTyp, \
                       legL = self.legL, tale = self.legsTale, rmks = 'none')
          self.pthL.append(copy.deepcopy(pDic))
          self.pthsTale += 1
          progress = 'seekNextPath'
    srceHndl.close()

  def fromSpec( self, inptFId):
    '''open a comma-space file matching  Sid-Star wypt name to rway in use '''
    self.specTale = 0
    with open(inptFId, 'r') as specHndl:
      for specLine in specHndl:
        if ( specLine[0] != '#'):
          posn = specLine.find(', ')
          if (specLine[:posn] == icaoSpec):
            sIcao = icaoSpec
            # discard icao
            specLine = specLine[(posn + 2):]
            posn = specLine.find(', ')
            sType = specLine[:posn]
            # discard Sid/Star type  
            specLine = specLine[(posn + 2):]

            ## 19Se05 was plain waypoint now is 
            #    Star: procName.Waypoint  Sid: wpnt.ProcName
            posn = specLine.find('.')
            if ( sType == 'Star'):
              # discard 'procNname.'
              specLine = specLine[(posn+1):]
              posn = specLine.find(', ')
              sWypt = specLine[:posn]
              # discard wpnt 
            if ( sType == 'Sid'):
              sWypt = specLine[:posn]
              #print(sWypt)
              posn = specLine.find(', ')
            # both Star, Sid discard wpnt portion   
            specLine = specLine[(posn + 2):]
            #print (specLine)
            posn = specLine.find(', ')
            ##sRway = specLine[:posn]
            sRway = specLine[:posn]
            sDic = dict(icao = sIcao, type = sType, wypt = sWypt, rway = sRway)
            #print (sDic)
            self.specL.append(copy.deepcopy(sDic))
            self.specTale += 1
    specHndl.close()

  #
  # ATC-pie output format: for creating path displays
  #
  # There is no header, no tail in ATC-pie drawn files

  def toATPIPath( self, outpFId, p, rway):
    ''' call from toATPIBody with hndl, pathIndx to write single path '''
    # Create eight different line styles and seven different colors
    depClrs = ['#F03434',  '#F03470',  '#F034AC',  '#F034E8', \
               '#F07034',  '#F07070',  '#F070AC',  '#F070E8', \
               '#F0AC34',  '#F0AC70',  '#F0ACAC',  '#F0ACEC'  ]
    arrClrs = ['#3434F0',  '#3470F0',  '#34ACF0',  '#34E8F0', \
               '#7034F0',  '#7070F0',  '#70ACF0',  '#70E8F0', \
               '#AC34F0',  '#AC70F0',  '#ACACF0',  '#ACE8F0'  ]
    tSsid = (self.pthL[p]['ssid']).lower()
    # construct output fileID from outpFId and pathname / number
    pathSfix = self.pthL[p]['path']
    if (pathSfix == ''):
      pathSfix = p
    pathFId = outpFId + '{:s}-{:s}.txt'.format( pathSfix, rway)
    outpHndl  = open(pathFId, 'w', 0)
    # remove '-Txtn' suffixes from route types
    if (tSsid == 'Sid-Txtn') :
      tSsid = 'sid'
    if (tSsid == 'Star-Txtn') :
      tSsid = 'star'
    if (tSsid == 'sid') :
      # pink shift for departing wpts
      oL = '\n {:s}'.format(depClrs[(p%12)])
    else:
      # skyblue shift for approach wpts
      oL = '\n {:s}'.format(arrClrs[(p%12)])
    outpHndl.write(oL)
    # Write line segments
    for l in range(self.pthL[p]['tale']-1):
      latN = '{:f}'.format(self.pthL[p]['legL'][l]['latN'])
      lonE = '{:f}'.format(self.pthL[p]['legL'][l]['lonE'])
      # if bogus lat, lon then output by name, else numeric lat, lon
      if ((float(latN) > 90) & (float(lonE) > 180)):
        oL = '\n{:s} '.format(self.pthL[p]['legL'][l]['iden'])
      else:
        oL = '\n{:s},{:s}'.format(latN, lonE)
      # pull 'remarks' field, if blank make up begin-end labels
      self.rmks =   self.pthL[p]['legL'][l]['rmks']
      if (self.rmks == 'none'):
        self.rmks = ''
        # Arrival first line append proc name
        if(tSsid == 'star'):
          if (l == 0):
            self.rmks = self.pthL[p]['path']
          #Arrival last line append rwy ID
          if(l == (self.pthL[p]['tale']-2)):
            self.rmks = rway
          ## intermediate legs suggest alt in 100's ft
          #if( (l != (self.pthL[p]['tale']-2)) & (l != 0)):
          #  self.rmks = str(int(self.pthL[p]['legL'][l]['altF'] / 100))
        if(tSsid == 'sid'):
          # Sid first leg: identify rway
          if (l == 0):
            self.rmks = rway
          if (l == (self.pthL[p]['tale']-2)):
            #Sid last leg append proc name
            self.rmks = self.pthL[p]['path']
          ## intermediate legs suggest alt in 100's ft
          #if( (l != (self.pthL[p]['tale']-2)) & (l != 0)):
          #  self.rmks = str(int(self.pthL[p]['legL'][l]['altF'] / 100))
      oL = oL + ' ' + self.rmks
      outpHndl.write(oL)
    # Close route segme
    outpHndl.write('  \n')
    # Construct refeence line for list file
    self.listLine = pathFId + ' DRAW ' + pathSfix + '-' + rway + '\n'
    self.listHndl.write(self.listLine)
    outpHndl.flush
    outpHndl.close

  def toATPIBody( self, outpFId):
    ''' given open file ID write ATC-pie dwng  body from legs lists '''
    # create and open list file holding refs to all path files created
    self.listFId   = outpFId + icaoSpec + '.lst'
    self.listHndl  = open(self.listFId, 'w', 0)
    for p in range(self.pthsTale):
      # Each path may apply to more than one rway according to rwaySpec entry
      if ( specFId  == '' ):
        # no runway spec file called, output path
        tRout.toATPIPath( outpFId, p, self.pthL[p]['rway'] )
      else:
        for s in range(self.specTale):
          if (icaoSpec in self.specL[s]['icao'] ):
            if (self.pthL[p]['ssid'] in self.specL[s]['type'] ):
              if ('Star' in self.specL[s]['type']):
                # Arr list needs to match last wypt
                l = self.pthL[p]['tale']
                print((self.specL[s]['type'], self.specL[s]['wypt'], \
                        self.pthL[p]['legL'][l-1]['iden']))
                if (self.specL[s]['wypt'] == self.pthL[p]['legL'][l-1]['iden']):
                  # call output path with rway inserted from specfile
                  specRway = self.specL[s]['rway']
                  tRout.toATPIPath( outpFId, p, specRway  )
              if ('Sid' in self.specL[s]['type']):
                # Dep list needs to match first wypt
                if (self.specL[s]['wypt'] == self.pthL[p]['legL'][0]['iden']):
                  # call output path with rway inserted from specfile
                  specRway = self.specL[s]['rway']
                  tRout.toATPIPath( outpFId, p, specRway  )
    self.listHndl.flush
    self.listHndl.close

  #
  # FlightGear AI Scenario 1 Output format: for AI/FlightPlans directory
  #
  def toFGAIHead( self, outpHndl):
    ''' given open file Handle:  write fgfs RM xml procedure headlines '''
    deptName = self.legL[0]['iden']
    destName = self.legL[self.legsTale-1]['iden']
    outpHndl.write('<?xml version="1.0"?>\n\n')
    oL = '<!-- ** NOT FOR NAVIGATION ** FOR SIMULATION PUROSES ONLY ** -->\n'
    outpHndl.write(oL)
    oL = '<!-- **  IMAGINARY DATA NOT FOR USE IN REAL SITUATIONS    ** -->\n'
    outpHndl.write(oL)
    oL = '<!-- FGAI FlightGear AI Scenario file generated by xmly.py   -->\n'
    outpHndl.write(oL)
    oL = '<!--   AI/FlightPlans/{:s}-{:s}.xml file       -->\n\n' \
    .format(icaoSpec, procSpec)
    outpHndl.write(oL)
    oL = '<!-- Manually edit if multiple Dept/Destn Routes are present  -->\n'
    outpHndl.write(oL)
    oL = '<!--  and proper alt/crossat/ktas/flaps/gear/on-ground tags   -->\n'
    outpHndl.write(oL)
    outpHndl.write('\n<PropertyList>\n')
    outpHndl.write('  <flightplan>\n')


  def toFGAIBody( self, outpHndl):
    ''' given open file Handle:  write fgfs RM xml body from legs list '''
    for p in range(self.pthsTale):
      ktas = 200
      oL = '\n    <!-- {:s} {:s}:{:s} Rw:{:s} Wp:{:s} -->\n' \
           .format(icaoSpec, self.pthL[p]['ssid'], self.pthL[p]['path'], \
                   rwaySpec, wyptSpec )
      outpHndl.write(oL)
      for l in range(self.pthL[p]['tale']):
        outpHndl.write('    <wpt>\n')
        #oL = '      <name>{:s}-{:d}</name>\n' \
        #     .format( self.pthL[p]['legL'][l]['iden'], (l+1) )
        oL = '      <name>{:s}</name>\n' \
             .format( self.pthL[p]['legL'][l]['iden'] )
        outpHndl.write(oL)
        oL = '      <lat type="double">{:07f}</lat>\n' \
             .format(self.pthL[p]['legL'][l]['latN'])
        outpHndl.write(oL)
        oL = '      <lon type="double">{:08f}</lon>\n' \
             .format(self.pthL[p]['legL'][l]['lonE'])
        outpHndl.write(oL)
        if ((self.pthL[p]['legL'][l]['altF']) > 0) :
          oL = '      <crossat>{:d}</crossat>\n' \
             .format(self.pthL[p]['legL'][l]['altF'])
          outpHndl.write(oL)
        oL = '      <ktas>{:d}</ktas>\n'.format(ktas)
        outpHndl.write(oL)
        outpHndl.write('      <flaps-down>false</flaps-down>\n')
        outpHndl.write('      <gear-down>false</gear-down>\n')
        outpHndl.write('      <on-ground>false</on-ground>\n')
        outpHndl.write('    </wpt>\n\n')
      oL = '    <!-- END {:s}    {:s} -->\n\n' \
           .format(icaoSpec, self.pthL[p]['path'])
      outpHndl.write(oL)

  def toFGAITail( self, outpHndl):
    ''' given open file Handle:  write fgfs RM xml tail lines '''
    outpHndl.write('\n  </flightplan>\n')
    outpHndl.write('</PropertyList>\n')

  #
  # FlightGear level-D output format: for Sid Star files for RM SID/STAR cmd
  #
  def toFGLDHead( self, outpHndl):
    ''' given open file Handle:  write fgfs LevD xml procedure headlines '''
    outpHndl.write('<?xml version="1.0"?>\n\n')
    oL = '<!-- ** NOT FOR NAVIGATION ** FOR SIMULATION PUROSES ONLY ** -->\n'
    outpHndl.write(oL)
    oL = '<!-- **  IMAGINARY DATA NOT FOR USE IN REAL SITUATIONS    ** -->\n'
    outpHndl.write(oL)
    oL = '<!-- FGLD FlightGear RouteManager file generated by xmly.py  -->\n'
    outpHndl.write(oL)
    oL = '<!-- Scenery/Airports/{:s}/{:s}/{:s}/{:s}.procedure file     -->\n\n' \
    .format(icaoSpec[0:1], icaoSpec[1:2], icaoSpec[2:3], icaoSpec)
    outpHndl.write(oL)
    outpHndl.write('<ProceduresDB version="FGLD by xmlly.py">\n')
    oL = '  <Airport ICAOcode="{:s}">\n'.format(icaoSpec)
    outpHndl.write(oL)

  def toFGLDBody( self, outpHndl):
    ''' given open file Handle:  write fgfs RM xml body from legs lists '''
    for p in range(self.pthsTale):
      oL = '\n    <{:s} Name="{:s}" Runways="{:s}">' \
           .format(self.pthL[p]['ssid'], self.pthL[p]['path'], \
                   self.pthL[p]['rway'])
      outpHndl.write(oL)
      # Many Sid's have a Heading to Alt at start
      if ( self.pthL[p]['ssid'] == 'Sid') :
        outpHndl.write('\n      <!-- Un-Comment for Heading To Alt Leg -->\n')
        outpHndl.write('      <!-- Sid_Waypoint ID="1"-->\n')
        outpHndl.write('      <!-- Name>(520)</Name-->\n')
        outpHndl.write('      <!-- Type>ConstHdgtoAlt</Type-->\n')
        outpHndl.write('      <!-- Latitude>0.000000</Latitude-->\n')
        outpHndl.write('      <!-- Longitude>0.000000</Longitude-->\n')
        outpHndl.write('      <!-- Speed>0</Speed-->\n')
        outpHndl.write('      <!-- Altitude>520</Altitude-->\n')
        outpHndl.write('      <!-- AltitudeCons>0</AltitudeCons-->\n')
        outpHndl.write('      <!-- AltitudeRestriction>above</AltitudeRestriction-->\n')
        outpHndl.write('      <!-- Hdg_Crs>1</Hdg_Crs-->\n')
        outpHndl.write('      <!-- Hdg_Crs_value>104</Hdg_Crs_value-->\n')
        outpHndl.write('      <!-- Flytype>Fly-by</Flytype-->\n')
        outpHndl.write('      <!-- BankLimit>25</BankLimit-->\n')
        outpHndl.write('      <!-- Sp_Turn>Auto</Sp_Turn-->\n')
        outpHndl.write('      <!-- /Sid_Waypoint ID="1"-->\n')

      for l in range(self.pthL[p]['tale']):
        wyptDecl = self.pthL[p]['ssid'] + '_Waypoint'
        if ( 'Star-Txtn' in self.pthL[p]['ssid']) :
          wyptDecl = 'StarTr_Waypoint'
        if ( 'Sid-Txtn' in self.pthL[p]['ssid']) :
          wyptDecl = 'SidTr_Waypoint'
        oL = '\n      <{:s} ID="{:d}">\n' \
             .format(wyptDecl, l+2)
        outpHndl.write(oL)
        oL = '        <Name>{:s}</Name>\n' \
             .format(self.pthL[p]['legL'][l]['iden'])
        outpHndl.write(oL)
        outpHndl.write('        <Type>Normal</Type>\n')
        oL = '        <Latitude>{:07f}</Latitude>\n' \
             .format(self.pthL[p]['legL'][l]['latN'])
        outpHndl.write(oL)
        oL = '        <Longitude>{:08f}</Longitude>\n' \
             .format(self.pthL[p]['legL'][l]['lonE'])
        outpHndl.write(oL)
        if ( 'Sid' in self.pthL[p]['ssid']) :
          outpHndl.write('        <Speed>0</Speed>\n')
        oL = '        <Altitude>{:d}</Altitude>\n' \
             .format(self.pthL[p]['legL'][l]['altF'])
        outpHndl.write(oL)
        altiRstr = 'above'
        if ( 'Sid' in self.pthL[p]['ssid']) :
          outpHndl.write('        <AltitudeCons>0</AltitudeCons>\n')
          altiRstr = 'at'
        oL = '        <AltitudeRestriction>{:s}</AltitudeRestriction>\n' \
             .format( altiRstr)
        outpHndl.write(oL)
        outpHndl.write('        <Flytype>Fly-by</Flytype>\n')
        outpHndl.write('        <BankLimit>25</BankLimit>\n')
        outpHndl.write('        <Sp_Turn>Auto</Sp_Turn>\n')
        oL = '      </{:s}>\n'.format(wyptDecl)
        outpHndl.write(oL)
      oL = '    </{:s}>\n'.format(self.pthL[p]['ssid'])
      outpHndl.write(oL)

  def toFGLDTail( self, outpHndl):
    ''' given open file Handle:  write fgfs RM xml tail lines '''
    outpHndl.write('  </Airport>\n')
    outpHndl.write('\n</ProceduresDB>\n')

  #
  # OpenRadar output format: for creating OR path displays
  #
  def toORDRHead( self, outpHndl):
    ''' given open file Handle:  write fgfs LevD xml procedure headlines '''
    outpHndl.write('<?xml version="1.0"?>\n\n')
    oL = '<!-- ** NOT FOR NAVIGATION ** ** FOR SIMULATION PUROSES ONLY ** -->\n'
    outpHndl.write(oL)
    oL = '<!-- FG OpenRadar Procedure generated by xmly.py -->\n'
    outpHndl.write(oL)
    oL = '<!-- {:s} {:s} for {:s} -->\n'.format(procSpec, typeSpec, icaoSpec)
    outpHndl.write(oL)
    oL = '<!-- cmdl: {:s} -->\n'.format(str(sys.argv[1:]) )
    outpHndl.write(oL)

  def toORDRPath( self, outpHndl, p, rway):
    ''' call from toORDRBody with hndl, pathIndx, rway to write single path '''
    # Create eight different line styles and seven different colors
    stks = ['1-8-2-1', '1-7-2-2', '1-6-2-3', '1-5-2-4', \
            '1-4-2-5', '1-3-2-6', '1-2-2-7', '1-1-2-8' ]
    depClrs = ['240,20,20',  '240,20,80',  '240,20,140',  '240,20,200', \
               '240,80,20',  '240,80,80',  '240,80,140',  '240,80,200', \
              '240,140,20', '240,220,80', '240,140,140', '240,140,200'   ]
    arrClrs = ['20,20,240',  '20,80,240',  '20,140,240',  '20,200,240', \
               '80,20,240',  '80,80,240',  '80,140,240',  '80,200,240', \
              '140,20,240', '140,80,240', '140,140,240', '140,200,240'   ]
    txtnClrs = ['50,50,20',   '100,50,20',    '150,50,20',    '200,100,20', \
               '100,100,20',  '150,100,20',   '200,150,20',  '250,100,20', \
              '250,50,10',   '250,100,10',  '150,150,10',  '200,200,10'   ]
    tSsid = (self.pthL[p]['ssid']).lower()
    # remove '-Txtn' suffixes from route types
    ## 19Se04  conditions never met: tSsid was lowercased 
    #if (tSsid == 'Sid-Txtn') :
    #  tSsid = 'sid'
    #if (tSsid == 'Star-Txtn') :
    #  tSsid = 'star'
    oL = '\n  <route name="{:s}" displayMode="{:s}" ' \
         .format(self.pthL[p]['path'], tSsid)
    # Bigger zoom number means more miles on screen 
    if (tSsid == 'sid-txtn') :
      # brown   tint for transition wpts
      oL = oL + 'zoomMin="8" zoomMax="500" color="140,80,40">\n'
    if (tSsid == 'sid') :
      # pink    tint for departing wpts
      oL = oL + 'zoomMin="6" zoomMax="300" color="240,200,160">\n'
    if (tSsid == 'star-txtn') :
      # skyblue tint for approach wpts
      oL = oL + 'zoomMin="8" zoomMax="500" color="160,200,240">\n'
    if (tSsid == 'star') :
      # skyblue tint for approach wpts
      oL = oL + 'zoomMin="6" zoomMax="300" color="160,200,240">\n'
    outpHndl.write(oL)
    if (tSsid == 'sid'):
      oL = '    <activeStartRunways>{:s}' \
           .format(rway)
      outpHndl.write(oL)
      outpHndl.write('</activeStartRunways>\n')
    if (tSsid == 'star'):
      oL = '    <activeLandingRunways>{:s}' \
           .format(rway)
      outpHndl.write(oL)
      outpHndl.write('</activeLandingRunways>\n')
    outpHndl.write('    <navaids>')
    for l in range(self.pthL[p]['tale']):
      oL = '{:s}'.format(self.pthL[p]['legL'][l]['iden'])
      outpHndl.write(oL)
      r = list(range(self.pthL[p]['tale']))
      if ( l < (r[-1])):
        outpHndl.write(',')
    outpHndl.write('</navaids>\n')
    # Write line segments
    for l in range(self.pthL[p]['tale']-1):
      begName = '{:s}'.format(self.pthL[p]['legL'][l]['iden'])
      endName = '{:s}'.format(self.pthL[p]['legL'][l+1]['iden'])
      segStke = stks[(p%8)]
      if (tSsid == 'sid-txtn'):
        segColr = txtnClrs[(p%12)]
      if (tSsid == 'sid'):
        segColr = depClrs[(p%12)]
      if (tSsid == 'star-txtn'):
        segColr = txtnClrs[(p%12)]
      if (tSsid == 'star'):
        segColr = arrClrs[(p%12)]
      oL = '    <line start="{:s}" end="{:s}" arrows="end"' \
           .format(begName, endName)
      outpHndl.write(oL)
      oL = ' stroke="{:s}" color="{:s}" />\n' \
           .format(segStke, segColr)
      outpHndl.write(oL)
    # Close route segment
    outpHndl.write('  </route>\n')

  def toORDRBody( self, outpHndl):
    ''' given open file Handle:  write fgfs RM xml body from legs lists '''
    outpHndl.write('\n<routes>\n\n')
    # before route defns define, once, all waypoint name used in all paths
    onceList = []
    for p in range(self.pthsTale):
      # stash values for skeleton spec file, first wp for sid, last for star
      skelLegn = ''
      skelSsid = (self.pthL[p]['ssid'])
      for l in range(self.pthL[p]['tale']):
        thisName = self.pthL[p]['legL'][l]['iden']
        if ( thisName not in onceList):
          onceList.append(thisName)
          oL = '  <addPoint code="{:s}" point="{:07f},{:08f}"/>\n' \
                   .format((self.pthL[p]['legL'][l]['iden']), \
                           (self.pthL[p]['legL'][l]['latN']),
                           (self.pthL[p]['legL'][l]['lonE']))
          outpHndl.write(oL)
      if (( skelFId  != '' ) & (skelSsid == 'Sid') ):
        #Sid uses first legName in legList and Sid title == Path name 
        skelLegn = (self.pthL[p]['path'])
      if (( skelFId  != '' ) & (skelSsid == 'Star') ):
        #LastFirst legName in legList, save it 
        #skelLegn = (self.pthL[p]['legL'][l]['iden'])
        skelLegn = '{:s}.{:s}'.format ((self.pthL[p]['path']), \
                                       (self.pthL[p]['legL'][l]['iden']))
      if (( skelFId  != '' ) & ((skelSsid == 'Star') | (skelSsid == 'Sid'))) :
        # write line to skeleton spec file
        oL = '{:s}, {:s}, {:s}, Rwy\n'.format((icaoSpec), \
                                          (skelSsid), (skelLegn))
        skelHndl.write(oL)
    # iterate thru each path
    for p in range(self.pthsTale):
      # Each path may apply to more than one rway according to rwaySpec entry
      #print (self.pthL[p]['ssid'])
      if (( specFId  == '' ) | ('-Txtn' in self.pthL[p]['ssid'])) :
        # no runway spec file or -Txtn in path type : output path
        tRout.toORDRPath( outpHndl, p, self.pthL[p]['rway'] )
      else:
        for s in range(self.specTale):
          if (icaoSpec in self.specL[s]['icao'] ):
            #            print ( (self.pthL[p]['path']))
            # 
            skelLegn = '{:s}'.format ((self.pthL[p]['path']) )
            print(skelLegn)
            if (self.specL[s]['type'] == self.pthL[p]['ssid']):
              if ('Star' in self.specL[s]['type']):
                # Arr list needs to match last wypt
                l = self.pthL[p]['tale']
                if (self.specL[s]['wypt'] == self.pthL[p]['legL'][l-1]['iden']):
                  # call output path with rway inserted from specfile
                  specRway = self.specL[s]['rway']
                  tRout.toORDRPath( outpHndl, p, specRway )
              if ('Sid' in self.specL[s]['type']):
                # Dep list needs to match first wypt
                if (self.specL[s]['wypt'] == self.pthL[p]['legL'][0]['iden']):
                  # call output path with rway inserted from specfile
                  specRway = self.specL[s]['rway']
                  tRout.toORDRPath( outpHndl, p, specRway )

  def toORDRTail( self, outpHndl):
    ''' given open file Handle:  write fgfs RM xml tail lines '''
    outpHndl.write('\n</routes>\n')

  #
  # FlightGear Route Manager Version 2 Output format: for RM 'Load' cmd
  #
  def toRMV2Head( self, outpHndl):
    ''' given open file Handle:  write fgfs RM xml procedure headlines '''
    deptName = self.legL[0]['iden']
    destName = self.legL[self.legsTale-1]['iden']
    oL = '    <airport type="string">{:s}</airport>\n'.format(deptName)
    outpHndl.write('<?xml version="1.0"?>\n\n')
    oL = '<!-- ** NOT FOR NAVIGATION *** FOR SIMULATION PUROSES ONLY ** -->\n'
    outpHndl.write(oL)
    oL = '<!--        FG RM V2 Procedure(s) generated by xmly.py        -->\n'
    outpHndl.write(oL)
    oL = '<!-- Manually edit if multiple Dept/Destn Routes are present  -->\n'
    outpHndl.write(oL)
    oL = '<!--     and for proper Dept/Destn Runway, ICAO names         -->\n'
    outpHndl.write(oL)
    oL = '<!-- cmdl: {:s} -->\n'.format(str(sys.argv[1:]))
    outpHndl.write(oL)
    outpHndl.write('\n<PropertyList>\n')
    outpHndl.write('  <version type="int">2</version>\n')


  def toRMV2Body( self, outpHndl):
    ''' given open file Handle:  write fgfs RM xml body from legs list '''
    for p in range(self.pthsTale):
      deptName = icaoSpec
      bodySsid = (self.pthL[p]['ssid'])
      destIndx = self.pthL[p]['tale']-1
      destName = self.pthL[p]['legL'][destIndx]['iden']
      # Star: parse path to outFId if dotted else iden dot path      
      scanPath = self.pthL[p]['path']
      if ('.' in scanPath ):
        pathProc = scanPath
      else : 
        pathProc = self.pthL[p]['legL'][destIndx]['iden'] + '.' + scanPath
      #pathOFId = icaoSpec + '-' +  bodySsid + '-' + pathProc + '-rm.xml'
      pathOFId = icaoSpec + '-' +  bodySsid.upper() + '-' + pathProc + '-rm.xml'
      print(pathOFId)
      pathOHdl = open( pathOFId, 'w', 1)
      oL = '    <airport type="string">{:s}</airport>\n'.format(deptName)
      pathOHdl.write('<?xml version="1.0"?>\n\n')
      oL = '<!-- ** NOT FOR NAVIGATION *** FOR SIMULATION PUROSES ONLY ** -->\n'
      pathOHdl.write(oL)
      oL = '<!--        FG RM V2 Procedure(s) generated by xmly.py        -->\n'
      pathOHdl.write(oL)
      oL = '<!-- Manually review and edit all entries for validity        -->\n'
      pathOHdl.write(oL)
      oL = '<!--     and for proper Dept/Destn Runway, ICAO names         -->\n'
      pathOHdl.write(oL)
      oL = '<!-- cmdl: {:s} -->\n'.format(str(sys.argv[1:]))
      pathOHdl.write(oL)
      pathOHdl.write('\n<PropertyList>\n')
      pathOHdl.write('  <version type="int">2</version>\n')
      ##if ('id' in bodySsid):
        ##outpHndl.write('\n  <departure>\n')
        ##oL = '    <airport type="string">{:s}</airport>\n'\
        ##   .format(deptName)
        ##outpHndl.write(oL)
        ##oL = '    <runway type="string">{:s}</runway>\n' \
        ##   .format( self.pthL[p]['rway'])
        ##outpHndl.write(oL)
        ##outpHndl.write('  </departure>\n')
        
      ##if ('tar' in bodySsid):
        ##outpHndl.write('  <destination>\n')
        ##oL = '    <airport type="string">{:s}</airport>\n'\
        ##     .format(deptName)
        ##outpHndl.write(oL)
        ##oL = '    <runway type="string">{:s}</runway>\n' \
        ##     .format( self.pthL[p]['rway'])
        ##outpHndl.write(oL)
        ##outpHndl.write('  </destination>\n')
      pathOHdl.write('\n  <route>\n')
      ## 19Se09 do not want an a/p rway record in route
      ##outpHndl.write('    <wp>\n')
      ##outpHndl.write('      <type type="string">runway</type>\n')
      ##outpHndl.write('      <departure type="bool">true</departure>\n')
      ##oL = '      <ident type="string">{:s}</ident>\n' \
      ##     .format( self.pthL[p]['rway'])
      ##outpHndl.write(oL)
      ##oL = '      <icao type="string">{:s}</icao>\n' \
      ##     .format( icaoSpec)
      ##outpHndl.write(oL)
      ##outpHndl.write('    </wp>\n')
      for l in range(self.pthL[p]['tale']):
        ##oL = '    <wp n="{:d}">\n'.format(l+1)
        oL = '    <wp>\n'
        pathOHdl.write(oL)
        pathOHdl.write('      <type type="string">navaid</type>\n')
        oL = '      <ident type="string">{:s}</ident>\n' \
             .format(self.pthL[p]['legL'][l]['iden'])
        pathOHdl.write(oL)
        oL = '      <lat type="double">{:07f}</lat>\n' \
             .format(self.pthL[p]['legL'][l]['latN'])
        pathOHdl.write(oL)
        oL = '      <lon type="double">{:08f}</lon>\n' \
             .format(self.pthL[p]['legL'][l]['lonE'])
        pathOHdl.write(oL)
        if ((self.pthL[p]['legL'][l]['altF']) > 0) :
          oL = '      <alt-restrict type="string">at</alt-restrict>\n'
          pathOHdl.write(oL)
          oL = '      <altitude-ft type="double">{:d}</altitude-ft>\n' \
               .format(self.pthL[p]['legL'][l]['altF'])
          pathOHdl.write(oL)
        pathOHdl.write('    </wp>\n')
      ##outpHndl.write('    <wp>\n')
      ##outpHndl.write('      <type type="string">runway</type>\n')
      ##outpHndl.write('      <departure type="bool">true</departure>\n')
      ##oL = '      <ident type="string">{:s}</ident>\n' \
      ##     .format( self.pthL[p]['rway'])
      ##outpHndl.write(oL)
      ##oL = '      <ident type="string">{:s}</ident>\n' \
      ##     .format( destName)
      ##outpHndl.write(oL)
      ##outpHndl.write('    </wp>\n')
      pathOHdl.write('  </route>\n')
      pathOHdl.write('</PropertyList>\n')
      pathOHdl.flush
      pathOHdl.close

  def toRMV2Tail( self, outpHndl):
    ''' given open file Handle:  write fgfs RM xml tail lines '''
    #outpHndl.write('\n  </route>\n')
    outpHndl.write('</PropertyList>\n')
#

  def toKMLSBody( self, outpHndl):
    ''' given open file Handle:  write fgfs RM xml body from legs list '''
    for p in range(self.pthsTale):
      deptName = icaoSpec
      bodySsid = (self.pthL[p]['ssid'])
      destIndx = self.pthL[p]['tale']-1
      destName = self.pthL[p]['legL'][destIndx]['iden']
      # Star: parse path to outFId if dotted else iden dot path      
      scanPath = self.pthL[p]['path']
      if ('.' in scanPath ):
        pathProc = scanPath
      else : 
        pathProc = self.pthL[p]['legL'][destIndx]['iden'] + '.' + scanPath
      #pathOFId = icaoSpec + '-' +  bodySsid + '-' + pathProc + '.kml'
      pathOFId = icaoSpec + '-' +  bodySsid.upper() + '-' + pathProc + '.kml'
      print('icaoSpec: ', icaoSpec + '-' +  bodySsid.upper() + '-' + pathProc + '.kml')
      print('bodySsid.upper(): ', bodySsid.upper())
      print('pathProc', pathProc)
      print('pathOFId',pathOFId)
      pathOHdl = open( pathOFId, 'w', 1)
      oL = '    <airport type="string">{:s}</airport>\n'.format(deptName)
      pathOHdl.write('<?xml version="1.0" encoding="UTF-8"?>\n')
      pathOHdl.write('<kml xmlns="http://www.opengis.net/kml/2.2">\n')
      oL = '<!-- ** NOT FOR NAVIGATION *** FOR SIMULATION PUROSES ONLY ** -->\n'
      pathOHdl.write(oL)
      oL = '<!--        FG KML   Paths        generated by xmly.py        -->\n'
      pathOHdl.write(oL)
      oL = '<!-- Manually review and edit all entries for validity        -->\n'
      pathOHdl.write(oL)
      oL = '<!--     and for proper Dept/Destn Runway, ICAO names         -->\n'
      pathOHdl.write(oL)
      oL = '<!-- cmdl: {:s} -->\n'.format(str(sys.argv[1:]) )
      pathOHdl.write(oL)
      #
      pathOHdl.write('<Document>\n')
      pathOHdl.write('\n')
      pathOHdl.write('  <Style id="airplane">\n')
      pathOHdl.write('    <IconStyle>\n')
      pathOHdl.write('      <Scale>0.2</Scale>\n')
      pathOHdl.write('      <Icon>\n')
      pathOHdl.write('        <href>http://maps.google.com/mapfiles/kml/pal3/icon53.png</href>\n')
      pathOHdl.write('      </Icon>\n')
      pathOHdl.write('    </IconStyle>\n')
      pathOHdl.write('  </Style>\n')
      pathOHdl.write('\n')
      #
      pathOHdl.write('  <Style id="navaid">\n')
      pathOHdl.write('    <IconStyle>\n')
      pathOHdl.write('      <Icon><href>http://maps.google.com/mapfiles/kml/pal3/icon53.png</href></Icon>\n')
      pathOHdl.write('    </IconStyle>\n')
      pathOHdl.write('  </Style>\n')
      pathOHdl.write('\n')
      #
      pathOHdl.write('  <Style id="rangering">\n')
      pathOHdl.write('    <LineStyle>\n')
      pathOHdl.write('      <color>9f4f4faf</color>\n')
      pathOHdl.write('      <width>2</width>\n')
      pathOHdl.write('    </LineStyle>\n')
      pathOHdl.write('  </Style>\n')
      pathOHdl.write('\n')
      #
      pathOHdl.write('  <Style id="track">\n')
      pathOHdl.write('    <LineStyle>\n')
      pathOHdl.write('      <color>5fff8f8f</color>\n')
      pathOHdl.write('      <width>4</width>\n')
      pathOHdl.write('    </LineStyle>\n')
      pathOHdl.write('  </Style>\n')
      pathOHdl.write('\n')
      #
      pathOHdl.write('<Style id="waypoint">\n')
      pathOHdl.write('  <IconStyle>\n')
      pathOHdl.write('    <scale>0.5</scale>\n')
      pathOHdl.write('    <Icon>\n')
      pathOHdl.write('      <href>http://maps.google.com/mapfiles/kml/pal3/icon53.png</href>\n')
      pathOHdl.write('    </Icon>\n')
      pathOHdl.write('  </IconStyle>\n')
      pathOHdl.write('</Style>\n')
      pathOHdl.write('\n')
      #
      pathOHdl.write('  <Folder>\n')
      pathOHdl.write('    <name>{:s} Tracks</name>\n'.format(pathProc))
      pathOHdl.write('    <open>0</open>\n')
      #
      ## Nv20 pathOHdl.write('\n  <route>\n')
      ## 19Se09 do not want an a/p rway record in route
      ##outpHndl.write('    <Placemark>\n')
      ##outpHndl.write('      <type type="string">runway</type>\n')
      ##outpHndl.write('      <departure type="bool">true</departure>\n')
      ##oL = '      <ident type="string">{:s}</ident>\n' \
      ##     .format( self.pthL[p]['rway'])
      ##outpHndl.write(oL)
      ##oL = '      <icao type="string">{:s}</icao>\n' \
      ##     .format( icaoSpec)
      ##outpHndl.write(oL)
      ##outpHndl.write('    </Placemark>\n')
      #
      for l in range(self.pthL[p]['tale']):
        ##oL = '    <wp n="{:d}">\n'.format(l+1)
        oL = '    <Placemark>\n'
        pathOHdl.write(oL)
        pathOHdl.write('      <styleUrl>#waypoint</styleUrl>\n')
        oL = '      <name>{:s}</name>\n' \
             .format(self.pthL[p]['legL'][l]['iden'])
        pathOHdl.write(oL)
        
        oL = '      <Point>\n'
        pathOHdl.write(oL)
        oL = '        <coordinates> {:07f},{:07f},4000 </coordinates> \n' \
        .format(self.pthL[p]['legL'][l]['lonE'], (self.pthL[p]['legL'][l]['latN']))
        pathOHdl.write(oL)
        oL = '      </Point>\n'
        pathOHdl.write(oL)
        
        ##Nv 20 if ((self.pthL[p]['legL'][l]['altF']) > 0) :
        if (0) :
          oL = '      <alt-restrict type="string">at</alt-restrict>\n'
          pathOHdl.write(oL)
          oL = '      <altitude-ft type="double">{:d}</altitude-ft>\n' \
               .format(self.pthL[p]['legL'][l]['altF'])
          pathOHdl.write(oL)
        pathOHdl.write('    </Placemark>\n')
        
        
        
      ##outpHndl.write('    <Placemark>\n')
      ##outpHndl.write('      <type type="string">runway</type>\n')
      ##outpHndl.write('      <departure type="bool">true</departure>\n')
      ##oL = '      <ident type="string">{:s}</ident>\n' \
      ##     .format( self.pthL[p]['rway'])
      ##outpHndl.write(oL)
      ##oL = '      <ident type="string">{:s}</ident>\n' \
      ##     .format( destName)
      ##outpHndl.write(oL)
      ##outpHndl.write('    </Placemark>\n')
      ##Nv20 pathOHdl.write('  </route>\n')

      pathOHdl.write('    <Placemark>\n')
      pathOHdl.write('      <styleUrl>#track</styleUrl>\n')
      pathOHdl.write('      <LineString>\n')
      pathOHdl.write('        <coordinates>\n')
      for l in range(self.pthL[p]['tale']):
        oL = '          {:07f},{:07f},4000\n' \
             .format(self.pthL[p]['legL'][l]['lonE'], (self.pthL[p]['legL'][l]['latN']))
        pathOHdl.write(oL)
      pathOHdl.write('        </coordinates>\n')
      pathOHdl.write('      </LineString>\n')
      pathOHdl.write('    </Placemark>\n')

      pathOHdl.write('  </Folder>\n')
      pathOHdl.write('</Document>\n')
      pathOHdl.write('</kml>\n')
      pathOHdl.flush
      pathOHdl.close

  #
  # Debug
  #
  def dbugPrnt(self):
    #for elem in self.pthL:
    #  print(elem)
    print((self.pthL))

def printHelp():
  print('\n xmly.py is a utility for generating various format route files   ')
  print('           used by flightgear ( Route Manager / AI Aircraft )       ')
  print('            and by OpenRadar or ATC-pie for SID/STAR path outlines  ')
  print('                                                                    ')
  print('\npython xmly.py -i --inputfid    /path/to/InpFile                  ')
  print('                 -o --outputfid   /path/to/{OutFile|"AUTO"}         ')
  print('                 -f --srceformat  -g --genformat                    ')
  print(' [-a --altitude ] [-h --help ] [-k --skel ][-n --icao] [-p --proc]  ')
  print(' [-r rway][-s --spec] [-t --type {"Sid"|"Star"}] [-w --waypoint]   ')
  print('                                                                    ')
  print('Source Format may be one of these: ')
  print('  -f ARDP   Fixed Lgth text file (US Only) from: ..')
  print('https://www.faa.gov/air_traffic/flight_info/aeronav/aero_data/NASR_Subscription/ ')
  print('  -f ASAL  Text file pasted from the Route Output section  of : ..  ')
  print('  http://rfinder.asalink.net/free/ ')
  print('  -f LEVD  Level-D format SID/STAR data file by subscription to ..  ')
  print('  https://www.navigraph.com/FmsData.aspx  ')
  print('  -f PATH  KML Places File with an image overlay and paths section  ')
  print('    Deprecated: Use -i PMKS with Overlay and Waypoints as Placemarks')
  print('  -f PMKS  KML Places file with Image Overlay and Placemark paths   ')
  print('                                                                    ')
  print(' Specification file, associates SID/STAR with runway ID             ')
  print('  -k --skel path/to/skelFId  generates spec file, edit, add rwys    ')
  print('  -s --spec path/to/specFId                                         ')
  print('  Fields in skel, spec file have: ICAO, "Sid|Star", path.desc, RWYID')
  print('  leaving  eg:  KIAD, Sid, prefFAAN.firstLegn, 08L                  ')
  print('  arriving eg:  KIAD, Star, postFAAN.lastLegN, 08R                  ')
  print('    N.B Sinle space only after comma separators                     ')
  print('                                                                    ')
  print('Outut format may be one of these:')
  print('  -g ATPI  ATC Pie for display on ATCPI radar ')
  print('    .. save in ATC-pie data path                                    ')
  print('  -g FGAI  FlightGgear AI Flightplan for fgdata/AI/FlightPlans      ')
  print('    .. useful for creating e.g local AI SID/STAR traffic            ')
  print('  -g FGLD  FlightGear pseudo Level-D for Route Manager SID/STAR     ')
  print('    .. does not support all tags foound in Paid-For navigraph data  ')
  print('    .. but can create useful SID/STAR paths from FAA/KML files      ')
  print('  -g KMLS  Generate individual KML waypoint/track files for SID/STAR ')
  print('    .. Use gpxsee application to preview KML before flying RMV2 file')
  print('  -g ORDR  Open Radar for display on OpenRadar ')
  print('    .. save in  /OpenRadar/data/routes/ICAO/ICAO.procedures.xml     ')
  print('  -g RMV2  Flightgear Route Manager Load format   ')
  print('    .. Use FG Route Manager Load button to open the route ')
<<<<<<< HEAD
  print('                                                                    ')
  print('Filter on data in out may be :')
=======
  print('Filter according to input keys:                                                                    ')
>>>>>>> 24cd8fbdbf03474d3a4b5fca45557b6e84048cfc
  print('  -n --icao NAME limit output to routes to/from icao NAME           ')
  print('  -o some/path/AUTO will construct an appropriate FGLD, FGAI, ORDR  ')
  print('       formatted fileID and create the output file in some/path dir ')
  print('  -p --proc PROCID :limit output to specific named STAR/SIDs        ')
  print('  -r --runway RWID Applies that runway ID into output xml tags      ')
  print('  -t --type TYPE limits output to STAR / SID procedure type         ')
  print('  -w --waypoint WPID Limits output generated to paths ending WPID   ')
  print('                                                                    ')
  print('Some editing of the output files may be needed                  ')
  print('  e.g. Correct Altitude, gear, flaps, on-ground fields  ')
  print('                                                                    ')
  print('Open Radar paths are blueish for SID departing,')
  print('             are pink-red  for STAR arriving,  ')
  print('             are blueish for SID/STAR Transition routes ')
  print('                                                                    ')
  print('  -f ARDP -g ORDR  Auto generation options from FAA ARDP (US Covge) ')
  print('  Run Once with tag -k pathTo/KDFW-skelSpec.txt  to create spec file')
  print('    Edit spekSpec, save as sped.txt block change Rwy to a few Rnmbrs')
  print('  Run againwith tag -s pathTo/KDFW-spec.txt  to apply spec file      ')
  print('                                                                    ')
  print(' To create KDFW.procedures.xml, using edited spec file, all procs   ')
  print('python xmly.py -i pathto/FAAData/STARDP.txt  -f ARDP -g ORDR        ')
  print('               -o pathto/wkar/KDFW.procedures.xml -n KDFW           ')
  print('               [-k pathto/wkar/KDFW-skel.txt]                       ')
  print(' first run use above, save skel, edit as spec, second time use below')
  print('               [-s pathto/wkar/KDFW-spec.txt]                       ')
  print('                                                                    ')
  print(' third times a refined spec.txt from after viewing sid/star pdfs    ')
  print('python xmly.py -i pathto/FAAData/STARDP.txt  -f ARDP -g ORDR        ')
  print('               -o pathto/wkar/KDFW.procedures.xml -n KDFW           ')
  print('               [-s pathto/wkar/KDFW-InnerDeps-spec.txt]                       ')
  print('                                                                    ')
  print('./samp directory contains sample source files, Example calls: ')
  print('                                                                    ')
  print('python xmly.py -i ./samp/LIME-Sids.kml -o ./test/LIME-Sids-ORDR.xml \
  -f PMKS -g ORDR -n LIME -r 24 -t Sid')
  print('                                                                    ')
  print(' To create KSFO.procedures.xml, all SIDs + STARs, all labelled R28L ')
  print('python xmly.py -i pathto/FAAData/STARDP.txt pathto/myprocs/AUTO \
      -f ARDP -g FGAI -n KSFO -r 28L ')
  print('                                                                   ')
  print(' To create KDEN.procedures.xml, SIDs only,  labelled R35L')
  print('python xmly.py -i pathto/FAAData/STARDP.txt pathto/myprocs/AUTO \
      -f ARDP -g FGAI -n KDEN  -t Sid -r 28L ')
  print('                                                                   ')
  print(' To create KBOS.procedures.xml, STAR ROBUC1 ending JOBEE R04R      ')
  print('python xmly.py -i pathto/FAAData/STARDP.txt pathto/myprocs/AUTO \
      -f ARDP -g FGAI -n KBOS -p ROBUC1 -t Star -r 04R -w JOBEE             ')
  print('')

#
# main
#
if __name__ == "__main__":
  global inptFId
  global outpFId
  global srceFmat
  global genrFmat
  global icaoSpec
  global procSpec
  global typeSpec
  global rwaySpec
  global wantHelp
  global wyptSpec
  global specFId 
  global sequNumb
  global targAlt
  global tRout
  global txtnSpec
  # work command line args
  normArgs(sys.argv[1:])
  if (wantHelp > 0):
    printHelp()
  else:
    # make up output fileID if 'AUTO' in spec
    if ( 'AUTO' in outpFId ) :
      subsPosn = outpFId.find('AUTO')
      outpFId  = outpFId[:subsPosn] + icaoSpec + '-' + procSpec + '.xml'
      if ( 'FGAI' in genrFmat.upper()):
        outpFId  = outpFId[:subsPosn] + icaoSpec + '-' \
        + typeSpec + '-' +  procSpec  + '-' +  rwaySpec + '-FGAI.xml'
      if ( 'FGLD' in genrFmat.upper()):
        outpFId  = outpFId[:subsPosn] + icaoSpec[0:1] + '/'  \
        + icaoSpec[1:2] + '/'+ icaoSpec[2:3] + '/'+ icaoSpec \
        + '.procedures.xml'
      if (( 'ATPI' in genrFmat.upper()) | ( 'ORDR' in genrFmat.upper())):
        outpFId  = outpFId[:subsPosn] + icaoSpec + '-' + typeSpec + '-' \
        +  procSpec  + '-' + wyptSpec + '-' + rwaySpec + '-ORDR.xml'
      if ( 'RMV2' in genrFmat.upper()):
        outpFId  = outpFId[:subsPosn] + icaoSpec + '-' \
        + typeSpec + '-' +  procSpec  + '-' +  rwaySpec + '-RMV2.xml'
      print(('Auto outpFId: ' + outpFId))
    # create flightPLanMill
    print('tRout on:', (icaoSpec + '-' + typeSpec) )
    tRout = fplnMill(icaoSpec + '-' + typeSpec)
    # run input file scanner
    if ('ARDP' in srceFmat.upper()):
      tRout.fromARDP(inptFId)
    if ('ASAL' in srceFmat.upper()):
      tRout.fromASAL(inptFId)
    if ('KML' in srceFmat.upper()):
      tRout.fromKML(inptFId)
    if ('LEVD' in srceFmat.upper()):
      tRout.fromLEVD(inptFId)
      #tRout.dbugPrnt()
    if ('ORDR' in srceFmat.upper()):
      tRout.fromORDR(inptFId)
    if ('PATH' in srceFmat.upper()):
      tRout.fromPATH(inptFId)
    if ('PMKS' in srceFmat.upper()):
      tRout.fromPMKS(inptFId)
    # run output frmatter
    #to ATPI creates multiple files: FId is passed, not handle
    if ('ATPI' in genrFmat.upper()):
      if ( specFId  != ''):
        tRout.fromSpec( specFId )
      #tRout.dbugPrnt()
      tRout.toATPIBody(outpFId)
    if ( 'FGAI' in genrFmat.upper()):
      # open output file
      outpHndl  = open(outpFId, 'w', 1)
      tRout.toFGAIHead(outpHndl)
      tRout.toFGAIBody(outpHndl)
      tRout.toFGAITail(outpHndl)
      outpHndl.flush
      outpHndl.close
    if ( 'FGLD' in genrFmat.upper()):
      # open output file
      outpHndl  = open(outpFId, 'w', 1)
      tRout.toFGLDHead(outpHndl)
      tRout.toFGLDBody(outpHndl)
      tRout.toFGLDTail(outpHndl)
      outpHndl.flush
      outpHndl.close
    if ('ORDR' in genrFmat.upper()):
      # open output file
      outpHndl  = open(outpFId, 'w', 1)
      if ( skelFId  != ''):
        # open skeleton spec file for writing star/sid ID's 
        skelHndl  = open(skelFId, 'w', 1)
      if ( specFId  != ''):
        tRout.fromSpec( specFId )
      #tRout.dbgPrnt()
      tRout.toORDRHead(outpHndl)
      tRout.toORDRBody(outpHndl)
      tRout.toORDRTail(outpHndl)
      if ( skelFId  != ''):
        skelHndl.flush
        skelHndl.close
      outpHndl.flush
      outpHndl.close
    if ('RMV2' in genrFmat.upper()):
      # open output file
      outpHndl  = open(outpFId, 'w', 1)
      tRout.toRMV2Head( outpHndl)
      tRout.toRMV2Body( outpHndl)
      tRout.toRMV2Tail( outpHndl)
      outpHndl.flush
      outpHndl.close
    if ('KMLS' in genrFmat.upper()):
      # open output file
      outpHndl  = open(outpFId, 'w', 1)
      tRout.toKMLSBody( outpHndl)
      outpHndl.flush
      outpHndl.close
    # close output file
