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
  inptFId = 'dflt.kml'
  outpFId = '{:s}-{:s}-{:s}.xml' \
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

  global icaoSpec
  global sfixList


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
##   

  #
  # asalink format input files: fixed record text from web query
  # http://rfinder.asalink.net/free/autoroute_rtx.php
  #
  def alegFromAsalink( self, tLine):
    '''parse single fixed lgth text record record'''
    # http://rfinder.asalink.net/free/autoroute_rtx.php
    # ID      FREQ   TRK   DIST   Coords                     Name/Remarks
    # LFMN    FFF.F    0      0   N4339'55.46" E00712'53.94" NICE COTE DAZ
    tAlt = 5111
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
##   

  def addaLegd( self, tDict):
    ''' Append a sinle leg dictionary to legs list'''
    self.legL.append(tDict)
    self.legsTale += 1
##   

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
 ##   

#
  def fromARDP( self, inptFId):
    '''open and scan fixed length record text file: FAA STARDP.txt'''
    with open(inptFId, 'r', encoding="ISO-8859-1") as srceHndl:
      srceNmbr = 0
      progress = 'openFile'
      wantSubt = ''
      #stashed FAAN for matching STAR/SID to transition proc
      wantPost = ''
      currSequ = 'xnnnn'
      ##
      for srceLine in srceHndl:
        progress = 'nxtlSrce'
        srceNmbr += 1
        #dbug trap
        #        if (srceNmbr == 27051):
        #          print('ding srceNmbr: ', srceNmbr)
        # FAA proc path precedes Adap Airport Iden so run all leg lists
        # preset as unwanted, accum leg points until 'AA'
        pathGate = 'psetShut'
        # FAA Sequence number Snnnn == Star[-Tx] Dnnnn == Sid[-Tx]
        sequNmbr = srceLine[0:6]
        if (currSequ != sequNmbr):
          progress = 'anewSequ'
          currSequ = sequNmbr
          #print('currSequ: ', currSequ)
          adApIden = 'nSeqShut'
          adApGate = 'nSeqShut'
        blnkPosn = 11 + srceLine[11:].find(' ')
        faclType = srceLine[10:blnkPosn]
        #
        # 'AA' : Adapted Airport, applies back to sequ start
        if ('AA' in srceLine[10:12] ) :
          # scan current line's Iden, only save wanted Iden
          blnkPosn = 30 + srceLine[30:].find(' ')
          if ( (( srceLine[30:blnkPosn] ) in icaoSpec) | (icaoSpec == 'icaoAAll')) :
            # In case of past departure leglist, need last wpnt's fnapIden
            fnapPrev = fnapIden
            fnapIden = srceLine[30:blnkPosn]
            adApIden = fnapIden
            # maybe more than one AA recd, flag for leglist dump
            # fixme D0686 AA TIW NA BNA AA BNA , looks like preceding legList 
            pathGate = 'wantPath'
            # gate to remember for txtns
            adApGate = 'match'
        else:   
          # scan fnapIden for non incl 'AA'
          blnkPosn = 30 + srceLine[30:].find(' ')
          fnapIden = srceLine[30:blnkPosn]
        # col39: has dot: first record of a new FAA proc with pfixIden.sfixIden Name (txtn) 
        if ('.' in srceLine[38:]):
          # new proc/path may be associated with prec adAp
          progress = 'bnewProc'
          self.legL = []
          self.legsTale = 0
          #
          # 20Se15 New sequ wipes AA match ? 
          pathGate = 'ndotShut'
          #adApGate = 'ndotWipe'
          # parse procedure into preface, post and full FAA name
          stopPosn = srceLine.find('.')
          blnkPosn = stopPosn + srceLine[stopPosn:].find(' ')
          pfixIden = srceLine[38:stopPosn]
          sfixIden = srceLine[(stopPosn+1):blnkPosn]
          fullIden = srceLine[38:blnkPosn]
          fullName = srceLine[blnkPosn:]
          # cache Iden in proc first line 
          procBegl = fnapIden
          # Get proc tye from 1st char and TX string
          if ('D' in srceLine[:1]):
            if ('TRANSITION' in srceLine):
              thisType = 'Sid-Tx'
              ##11Se self.pathName = sfixIden + '.' + fnapIden
              ##11Se 
              self.pathName = fullIden
              tAlt = 4100
            else:
              thisType = 'Sid'
              # make up Sid name from first wypt and FAA procSpec
              ##20Se11
              ##11Se self.pathName = sfixIden + '.' + fnapIden
              self.pathName = fnapIden + '.' + pfixIden
              tAlt = 2123
          if ('S' in srceLine[:1]):
            # For arrival pathName is second part of FAA name
            starProc = sfixIden
            if ('TRANSITION' in srceLine):
              thisType = 'Star-Tx'
              # pathname is first wypt, stash proc part of name for matching
              ##17Je13 self.pathName = fullIden
              ##19Se02 self.pathName = sfixIden
              ##20Se11 self.pathName = sfixIden + '.' + fnapIden
              # star subTag matches its transition subtag
              txtnProc = sfixIden
              ## 19Se08  ???? maybetxtnProc = prefsfixIden
              tAlt = 4200
            else :
              thisType = 'Star'
              ##20Se11 self.pathName = sfixIden + '.' + fnapIden
              tAlt = 2500
              # stash 1st leg name to match txtn end leg
          #End processing anewSequ for first line in procedure
        ##else:
          ##20Se09 want currLegn for both begn and ff
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
        tNam = adApIden
        lDic = dict( iden = fnapIden, latN = latDec, lonE = lonDec, \
                     altF = int(tAlt), rmks='none' )
        # Do not apend Adapted Airport location to legsList
        if (not (srceLine[10:12] == 'AA') and not(srceLine[10:12] == 'NA')) :
          self.legL.append(lDic)
          self.legsTale += 1
        # Star, Star-Transitions are first in FAA input file
        if (('Star' in thisType ) & \
            ((typeSpec in thisType )|(typeSpec == 'typeAAll' ))):
          #
          if (   ('-Tx' in thisType ) ):
            # Star-txtn: txtnProc is sfixIden, match to prev proc's sfixIden
            if (('match' in adApGate ) and (fnapIden in sfixIden )) :
              #tAlt -= 150
              #print('wantStTx')
              pathGate = 'wantStTx'
          #
          if (not('-Tx' in thisType ) ):
            # waypoint list precedes AA Airport type, accum leg list 
            # Wanted if either wyptID matches last trk seg or is unspecified
            ## ((srceLine[10:12] == 'AA') & (adApIden in icaoSpec)): 20Se09
            if ( ('match' in adApGate ) & (fnapIden in sfixIden) ):
              if ((procSpec == sfixIden) | (procSpec == 'procAAll')) :
                if ((wyptSpec == self.legL[self.legsTale -1]['iden']) \
                 | (wyptSpec == 'wyptAAll')):
                 #tAlt -= 20
                 pathGate = 'wantStar'
                 # Stash STAR's beginning leg for match to Star-Tx
                 wantPost = sfixIden
        if (('Sid' in thisType ) & \
            (( typeSpec in thisType)|(typeSpec == 'typeAAll' ))):
          if ( ('-Tx' in thisType )) :
            # Sid-txtn: txtnProc is sfixIden, match to prev proc's sfixIden
            #if ((sequAdAp in  currLegn) ):
            if (('match' in adApGate ) and  (fnapIden in sfixIden )) :
              #tAlt += 1000
              #print('wantSdTx')
              pathGate = 'wantSdtx'
          else :
            # Sid non-Tx
            if (  ( 'match' in adApGate ) & (fnapIden in sfixIden) \
            ##if (  ( 'match' in adApGate ) & (fnapPrev in sfixIden) \
                & (( procSpec == sfixIden) | (procSpec == 'procAAll')) \
                & (( procBegl in wyptSpec ) | ('wyptAAll' in wyptSpec))) :
              #tAlt += 150
              pathGate = 'AAdidSid'
              # Stash STAR's beginning leg for match to Star-Tx
              wantPost = sfixIden
        if ( ( srceLine[10:12] == 'AA') & \
               ( not (( adApIden in icaoSpec) | (icaoSpec == 'icaoAAll'))))  :
          pathGate = 'dApRecd'
        if ( 'want' in pathGate ):
            tTyp = thisType
            #            print('want line: ', srceNmbr, ' tTyp: ', tTyp)
            # Arrival procedures differentiate by last wpnt's fnapIden 
            if ('S' in srceLine[:1]):
              ##20Se11 
              self.pathName = sfixIden + '.' + fnapPrev
            pDic = dict( path = self.pathName, ssid = tTyp, \
              rway = rwaySpec, legL = self.legL, tale = self.legsTale)
            #print('path at srce: ', srceNmbr, ' sequ: ', sequNmbr, ' gate: ', pathGate)
            self.pthL.append(copy.deepcopy(pDic))
            self.pthsTale += 1
            pathGate == 'pathDone'
    srceHndl.close()
##

  #
  # gpx input format: gpx path created e.g. by exporting from skyvector.com
  #   Each path is a set of legs between aypoints
  def fromGPX( self, inptFId):
    '''open a gpx waypoint list, append to prcs'''
    global icaoSpec
    tTyp = typeSpec
    with open(inptFId, 'r') as srceHndl:
      #
      progress = 'justOpnd'
      leglTale = 0
      pathTale = 0
      srceTale = 0
      pathOpen = 0
      leglOpen = 0
      tAlt = 1234
      tNam = ''
      tIdx = 0
      for srceLine in srceHndl:
        srceTale += 1
        # Find end of Image Overlay section: Sid/Star peths follow
        if ('<rte>' in srceLine) :
          #print('fromGPX()-<rte>')
          # Clean Legs for each new path
          pDic = {}
          self.legL = []
          self.legsTale = 0
          pathTale += 1
          pathOpen = 1
        #Each folder segment after GroundOverlay: new Sid/Star path
        if (pathOpen):
          if (('<name>' in srceLine) and (leglOpen == 0)):
            begnPosn = srceLine.find('<name>') + 6
            endnPosn = srceLine.find('</name>')
            self.pathName = srceLine[begnPosn:endnPosn]
            icaoSpec  = self.pathName
            #print('pathName: ', self.pathName)
          if (('<name>' in srceLine) & (  leglOpen)):
            begnPosn = srceLine.find('<name>') + 6
            endnPosn = srceLine.find('</name>')
            adApIden = srceLine[begnPosn:endnPosn]
            tNam = adApIden
            #print('leglName: ', tNam)
          if (('<rtept' in srceLine)):
            #print('rtept')
            leglOpen = 1
          if (leglOpen):
            if (('lat=' in srceLine) & (  leglOpen)):
              begnPosn = srceLine.find('lat=') + 5
              endnPosn = srceLine.find('"', begnPosn)
              tLat =float(srceLine[begnPosn:endnPosn])
              print('line: ', srceTale, ' lat begn:', begnPosn, ' endn: ', endnPosn, ' Lat: ', tLat)
            if (('lon=' in srceLine) & (  leglOpen)):
              begnPosn = srceLine.find('lon=') + 5
              endnPosn = srceLine.find('"', begnPosn)
              tLon =float(srceLine[begnPosn:endnPosn])
              print('line: ', srceTale, ' lon begn:', begnPosn, ' endn: ', endnPosn, ' Lon: ', tLon)
            if (('</rtept>' in srceLine)):
              #
              #print('/rtept: ', srceTale, ' lat begn:', begnPosn, ' endn: ', endnPosn)
              lDic = dict( iden = tNam, latN = tLat, lonE = tLon, \
                           altF = int(tAlt) + 500 * tIdx )
              self.legL.append(lDic)
              self.legsTale += 1
              leglOpen = 0
              leglTale += 1
          if (('</rte>' in srceLine)):
            #print('/rte: ', srceTale, ' leglTale:', leglTale, ' pathTale: ', pathTale)
            pDic = dict( path = self.pathName, rway = rwaySpec, ssid = tTyp, \
                         legL = self.legL, tale = self.legsTale, rmks = 'none')
            self.pthL.append(copy.deepcopy(pDic))
            self.pthsTale += 1
            pathTale += 1
            pathopen = 0
    srceHndl.close()
##   

  #
  # kml input format: kml path created at https://flightplandatabase.com 'Save KML'
  def fromKML ( self, inptFId):
    '''open a flightplandatabase kml track file, append to prcs'''
    tTyp = typeSpec
    with open(inptFId, 'r') as srceHndl:
      cordFlag = 0
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
##   

  #
  # FG Airport threshold.xml file 
  #   Each named procedure is a list of placemarks
  def fromAIRP( self, inptFId):
    wpntIndx = tNam = tTyp = tLat = tLon = tAlt =''
    '''open a Level-D xml file, create dictionary of path legs'''
    with open(inptFId, 'r') as srceHndl:
      # 
      progress = 'seekRway'
      ssidEnds = 'noEndYet'
      for srceLine in srceHndl:
        if (( progress == 'seekRway') & ('<runway>' in srceLine)) :
          progress = 'seekThresh'
        if ((progress == 'seekThresh') & ('threshold' in srceLine)):
          progress = 'seekGuts'
        if ((progress == 'seekGuts') & ('<lon>' in srceLine)):
          begnPosn = (srceLine.find('<lon>') + 5 )
          endnPosn = (srceLine.find('"</lon>') )
          tLon = srceLine[begnPosn:endnPosn]
        if ((progress == 'seekGuts') & ('<lat>' in srceLine)):
          begnPosn = (srceLine.find('<lat>') + 5 )
          endnPosn = (srceLine.find('"</lat>') )
          tLat = srceLine[begnPosn:endnPosn]
        if ((progress == 'seekGuts') & ('<rwy>' in srceLine)):
          begnPosn = (srceLine.find('<rwy>') + 5 )
          endnPosn = (srceLine.find('"</rwy>') )
          tNam = srceLine[begnPosn:endnPosn]
        if ((progress == 'seekGuts') & ('/<threshold>' in srceLine)):
          progress = 'endsThresh'
          # skip invalid LatLon and fill Leg Dict and append to path list
          if ( (tLat != 0) & (tLon != 0) ):
            lDic = dict( iden = tNam, latN = tLat, lonE = tLon , rmks = 'none')
            self.legL.append(lDic)
            self.legsTale += 1
        if ((progress == 'seekGuts') & ('/<runway>' in srceLine)):
          progress = 'endsRway'
          pDic = dict( path = tNam, rway = tNam, legL = self.legL, tale = self.legsTale)
          self.pthL.append(copy.deepcopy(pDic))
          self.pthsTale += 1
    srceHndl.close()
##   

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
##   


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
            lonDec =  99
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
##   

  #
  # kml overlay input format: kml path created from tracing a GE Image Overlay
  #   Deprecated: works for GE paths .. uwse fromKmlPmrk instead
  def fromPATH( self, inptFId):
    '''open a GE kml image olay + track lists file, append to prcs'''
    tTyp = typeSpec
    with open(inptFId, 'r') as srceHndl:
      procFlag = 0
      olayFlag = 0
      cordFlag = 0
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
##   

  # kml overlay input format: kml path created from tracing a GE Image Overlay
  #   Each path is a separate named GE folder containingplacemarks
  #   Star/Sid image overlay with 'GroundOverlay' precedes Sid/Star paths
  def fromPMKS( self, inptFId):
    '''open a GE kml image olay + Placemark list, append to prcs'''
    tTyp = typeSpec
    with open(inptFId, 'r') as srceHndl:
      progress = 'seekImag'

      pastImag = 0  # ==1 after </GroundOverlay> tag at end: Image Overlay
      pathFldr = 0  # ==1 pastImag & 1st <Folder> until path's <name> tag
      legsFlag = 0  # ==1 after path's name until </Folder>

      pmrkFlag = 0
      procFlag = 0
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
##   

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
  ##   

  #
  # ATC-pie output format: for creating path displays
  #  There is no header, no tail in ATC-pie drawn files. The <icao>.lst 
  #    sb copied into CONFIG/bg-img and the paths in folder <icao> 
  #
  def toATPIPath( self, tOutpFId, p, rway):
    ''' call from toATPIBody with hndl, pathIndx to write single path '''
    # Create eight different line styles and seven different colors
    # 20Oc13 ATCPi seems to need no hashmark      
    #depClrs = ['#F03434',  '#F03470',  '#F034AC',  '#F034E8', \
    #           '#F07034',  '#F07070',  '#F070AC',  '#F070E8', \
    #           '#F0AC34',  '#F0AC70',  '#F0ACAC',  '#F0ACEC'  ]
    #arrClrs = ['#3434F0',  '#3470F0',  '#34ACF0',  '#34E8F0', \
    #           '#7034F0',  '#7070F0',  '#70ACF0',  '#70E8F0', \
    #           '#AC34F0',  '#AC70F0',  '#ACACF0',  '#ACE8F0'  ]
    #           
    depClrs = ['C86020',  'D08040',  'E0A468',  'F0C088', \
               'C86020',  'D08040',  'E0A068',  'F0C088', \
               'C86C20',  'D08C40',  'E0AC68',  'F0C08C'  ]
    arrClrs = ['34A8F8',  '34A8F8',  '34A8F8',  '34A8F8', \
               '70C8F8',  '70C8F8',  '70C8F8',  '70C8F8', \
               'ACE8F8',  'ACE8F8',  'ACE8F8',  'ACE8F8'  ]
    lSsid = (self.pthL[p]['ssid']).lower()
    # construct output fileID from tOutpFId and pathname / number
    pathSfix = self.pthL[p]['path']
    if (pathSfix == ''):
      pathSfix = p
    # File ID of each path files, stored in ATPI, copy to 'ICAO' folder
    pathFId = icaoSpec + '/ATPI/' + icaoSpec
    pathFId = pathFId + '-{:s}-{:s}-{}.txt' \
                        .format((self.pthL[p]['ssid']), pathSfix, p)
    outpHndl  = open(pathFId, 'w', 1)
    if ('sid' in lSsid ) :
      # pink shift for departing wpts
      oL = '{:s}\n'.format(depClrs[(p%12)])
    else:
      # skyblue shift for approach wpts
      oL = '{:s}\n'.format(arrClrs[(p%12)])
    outpHndl.write(oL)
    # Write line segments
    legsTale = (self.pthL[p]['tale'])
    for l in range (legsTale ):
      latN = '{:f}'.format(self.pthL[p]['legL'][l]['latN'])
      lonE = '{:f}'.format(self.pthL[p]['legL'][l]['lonE'])
      # if bogus lat, lon then output by name, else numeric lat, lon
      if ((float(latN) > 90) & (float(lonE) > 180)):
        oL = '{:s}'.format(self.pthL[p]['legL'][l]['iden'])
      else:
        oL = '{:s},{:s}'.format(latN, lonE)
      # pull 'remarks' field, if blank make up begin-end labels
      self.rmks =   self.pthL[p]['legL'][l]['rmks']
      if (self.rmks == 'none'):
        ## options to label as path.endpt etc 
        #self.rmks = ''
        # Arrival first line append proc name
        #if( 'star' in lSsid ):
          #if (l == 0):
            #self.rmks = self.pthL[p]['path']
            #Arrival last line append rwy ID
            #f(l == (self.pthL[p]['tale']-2)):
              #elf.rmks = rway
            ## intermediate legs
            #if( (l != (self.pthL[p]['tale']-2)) & (l != 0)):
            #if(                                   (l != 0)):
              #self.rmks = self.pthL[p]['legL'][l]['iden']
        #if('sid' in lSsid ):
          # Sid first leg: identify rway
          #if (l == 0):
            #self.rmks = rway
          #if (l == (self.pthL[p]['tale']-2)):
            #Sid last leg append proc name
            #self.rmks = self.pthL[p]['path']
          ## intermediate legs
          #if( (l != (self.pthL[p]['tale']-2)) & (l != 0)):
          #if( (l != (self.pthL[p]['tale']-2)) ):
        self.rmks = self.pthL[p]['legL'][l]['iden']
      oL = oL + ' ' + self.rmks + '\n'
      #if ( 'AARCH' in self.pthL[p]['legL'][l]['iden']) :
      #  trapFlag = 1
        #print('trapppFlag: ', trapFlag)
      outpHndl.write(oL)
    # Close route segment
    outpHndl.write('  \n')
    outpHndl.flush
    outpHndl.close
    #  Reference list: one line for eachg path file created 
    #    filter out duped paths of same type
    dupeMask = ( pathSfix + '-' + (self.pthL[p]['ssid']))
    if not ( dupeMask in self.sfixList) :
      # Construct reference line for list file
      self.listLine = icaoSpec + '/' + icaoSpec
      self.listLine = self.listLine + '-{:s}-{:s}-{}.txt ' \
                          .format((self.pthL[p]['ssid']),  pathSfix, p)
      self.listLine = self.listLine  + ' DRAW ' + pathSfix + '\n'
      #self.listLine = icaoSpec + '/' + pathFId + ' DRAW ' + pathSfix + '\n'
      #self.listLine =                  pathFId + ' DRAW ' + pathSfix + '\n'
      #print(              self.listLine)
      self.listHndl.write(self.listLine)
      self.sfixList.append( dupeMask )
      # print(self.sfixList)
##   

  def toATPIBody( self, tOutpFId):
    ''' given open file ID write ATC-pie dwng  body from legs lists '''
    # Reference list file ID: create and open list file holding refs to all path files created
    #  
    self.listFId = icaoSpec + '/' + icaoSpec + '.lst'
    #    self.listFId =                       icaoSpec + '.lst'
    self.listHndl  = open(self.listFId, 'w', 1)
    self.sfixList = []
    for p in range(self.pthsTale):
      # Each path may apply to more than one rway according to rwaySpec entry
      if ( specFId  == '' ):
        # no runway spec file called, output path
        tRout.toATPIPath( tOutpFId, p, self.pthL[p]['rway'] )
      else:
        for s in range(self.specTale):
          if (icaoSpec in self.specL[s]['icao'] ):
            if (self.pthL[p]['ssid'] in self.specL[s]['type'] ):
              if ('Star' in self.specL[s]['type']):
                # Arr list needs to match last wypt
                l = self.pthL[p]['tale']
                #print((self.specL[s]['type'], self.specL[s]['wypt'], \
                #        self.pthL[p]['legL'][l-1]['iden']))
                if (self.specL[s]['wypt'] == self.pthL[p]['legL'][l-1]['iden']):
                  # call output path with rway inserted from specfile
                  specRway = self.specL[s]['rway']
                  tRout.toATPIPath( tOutpFId, p, specRway  )
              if ('Sid' in self.specL[s]['type']):
                # Dep list needs to match first wypt
                if (self.specL[s]['wypt'] == self.pthL[p]['legL'][0]['iden']):
                  # call output path with rway inserted from specfile
                  specRway = self.specL[s]['rway']
                  tRout.toATPIPath( tOutpFId, p, specRway  )
    self.listHndl.flush
    self.listHndl.close
##   

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
    oL = '<!--  flightplans are in AIFP folder -->\n'
    outpHndl.write(oL)
    oL = '<!--  scenarios   are in SCEN folder -->\n'
    outpHndl.write(oL)
    oL = '<!--   copy to fgdata/AI/FlightPlans/ fgdata/AI -->\n'
    outpHndl.write(oL)
    oL = '<!-- Paste from below into defaults.xml AI section -->\n\n' \
    .format(icaoSpec)
    outpHndl.write(oL)
    oL = '<!-- Manually edit if multiple Dept/Destn Routes are present  -->\n'
    outpHndl.write(oL)
    oL = '<!--  and proper alt/crossat/ktas/flaps/gear/on-ground tags   -->\n'
    outpHndl.write(oL)
    outpHndl.write('\n<!-- use xmly Export fgai scenarios with config arg -->\n')
    outpHndl.write('\n<PropertyList>\n')
    outpHndl.write('  <sim>\n')
    outpHndl.write('    <ai>\n')
    outpHndl.write('      <scenarios-enabled type="bool" userarchive="y">true</scenarios-enabled>\n')
##   

  def toFGAIBody( self, outpHndl):
    ''' given open file Handle:  write fgfs RM xml body from legs list '''
    pathNumb = 0
    pfixList = []
    sfixList = []
    for p in range(self.pthsTale):
      pathNumb += 1
      ##
      pathSsid = self.pthL[p]['ssid']
      scanPath = self.pthL[p]['path']
      if ('.' in scanPath ):
        pathProc = scanPath
      else :
        pathProc = self.pthL[p]['legL'][destIndx]['iden'] + '.' + scanPath
      ##
      scenOFId = icaoSpec + '/SCEN/' + icaoSpec + '-' + pathSsid + '-' +  pathProc \
                                     +  '-ai.xml'
      scenOHdl = open( scenOFId, 'w', 1)
      ##
      # ndupGate open for either pfixIden or sfixIden not seen before
      dupeMask = ( pathProc[pathProc.find('.'):] + '-' + (self.pthL[p]['ssid']))
      ndupGate = 'psetShut'
      if not (dupeMask in pfixList) :
        pfixList.append (dupeMask)
        ndupGate = 'pfixNdup'
      if not (dupeMask in sfixList) : 
        sfixList.append ( dupeMask )
        ndupGate = 'pfixNdup'
      if ('Ndup' in ndupGate):
        #print('ndup')
        oL = '      <scenario>{:s}-{:s}-{:s}-ai.xml</scenario>\n'. \
                      format(icaoSpec,pathSsid, scanPath)
        outpHndl.write(oL)
      else:                   
        #print('dupe')
        oL = '      <!--scenario>{:s}-{:s}-{:s}-ai.xml</scenario-->\n'. \
                      format(icaoSpec,pathSsid, scanPath)
        outpHndl.write(oL)
      ##
      scenOHdl.write('<?xml version="1.0"?>\n')
      scenOHdl.write('<PropertyList>\n')
      scenOHdl.write('  <scenario>\n')
      scenOHdl.write('\n')
      oL =           '    <name>{:s}-{:s}-{:s}-ai</name>\n'\
                       .format( icaoSpec, pathSsid, scanPath)
      scenOHdl.write(oL)
      scenOHdl.write('    <description>\n')
      oL =           '      {:s}-{:s}\n'.format(pathSsid, scanPath)
      scenOHdl.write(oL)
      scenOHdl.write('      FG AI Scenario by xmly \n')
      scenOHdl.write('    </description>\n')
      scenOHdl.write('    <entry>\n')
      oL =           '      <callsign>{:s}-ai</callsign>\n'.format(pathProc)
      scenOHdl.write(oL)
      scenOHdl.write('      <type>aircraft</type>\n')
      scenOHdl.write('      <class>jet_transport</class>\n')
      scenOHdl.write('      <model>AI/Aircraft/747/744-Delta.xml</model>\n')
      oL =           '      <flightplan>{:s}-{:s}-{:s}-fp.xml</flightplan>\n' \
                              .format( icaoSpec, pathSsid, scanPath)
      scenOHdl.write(oL)
      scenOHdl.write('      <repeat>1</repeat>\n')
      scenOHdl.write('    </entry>\n')
      scenOHdl.write('  </scenario>\n')
      scenOHdl.write('</PropertyList>\n')
      scenOHdl.close
      ##
      aifpOFId = icaoSpec + '/AIFP/' + icaoSpec + '-' + pathSsid + '-' \
                                     + scanPath + '-fp.xml'
      aifpOHdl = open( aifpOFId, 'w', 1)
      ##
      aifpOHdl.write('<?xml version="1.0"?>\n\n')
      oL =           '<!--{:s}-{:d}-->\n'.format( icaoSpec, pathNumb)
      aifpOHdl.write(oL)
      aifpOHdl.write('<PropertyList>\n')
      aifpOHdl.write('  <flightplan>\n')
      aifpOHdl.write('\n')
      ##
      ktas = 165
      oL = '    <!-- i:{:s} s:{:s} p:{:s} r:{:s} w:{:s} -->\n' \
           .format(icaoSpec, pathSsid, scanPath, \
                   rwaySpec, wyptSpec )
      aifpOHdl.write(oL)
      for l in range(self.pthL[p]['tale']):
        aifpOHdl.write('    <wpt>\n')
        #oL = '      <name>{:s}-{:d}</name>\n' \
        #     .format( self.pthL[p]['legL'][l]['iden'], (l+1) )
        oL = '      <name>{:s}</name>\n' \
             .format( self.pthL[p]['legL'][l]['iden'] )
        aifpOHdl.write(oL)
        lastLatN = self.pthL[p]['legL'][l]['latN']
        oL = '      <lat type="double">{:07f}</lat>\n' \
             .format(self.pthL[p]['legL'][l]['latN'])
        aifpOHdl.write(oL)
        lastLonE = self.pthL[p]['legL'][l]['lonE']
        oL = '      <lon type="double">{:08f}</lon>\n' \
             .format(self.pthL[p]['legL'][l]['lonE'])
        aifpOHdl.write(oL)
        if ((self.pthL[p]['legL'][l]['altF']) > 0) :
          oL = '      <alt>{:d}</alt>\n' \
             .format(self.pthL[p]['legL'][l]['altF'])
          aifpOHdl.write(oL)
        oL = '      <ktas>{:d}</ktas>\n'.format(ktas)
        aifpOHdl.write(oL)
        aifpOHdl.write('      <flaps-down>true</flaps-down>\n')
        aifpOHdl.write('      <gear-down>true</gear-down>\n')
        aifpOHdl.write('      <on-ground>false</on-ground>\n')
        aifpOHdl.write('    </wpt>\n\n')
      # Append wp named END
      aifpOHdl.write('    <wpt>\n')
      oL = '      <name>END</name>\n'
      aifpOHdl.write(oL)
      oL = '      <lat type="double">{:07f}</lat>\n' \
           .format(lastLatN)
      aifpOHdl.write(oL)
      oL = '      <lon type="double">{:08f}</lon>\n' \
           .format(lastLonE)
      aifpOHdl.write(oL)
      aifpOHdl.write('    </wpt>\n')
      oL = '    <!-- END {:s}    {:s} -->\n\n' \
           .format(icaoSpec, scanPath)
      aifpOHdl.write(oL)
      aifpOHdl.write('\n')
      aifpOHdl.write('  </flightplan>\n')
      aifpOHdl.write('</PropertyList>\n')
      aifpOHdl.close
      
##   
  def toFGAIPBdy( self, outpHndl):
    ''' given open file Handle:  write fgfs RM xml body from legs list '''
    for p in range(self.pthsTale):
      ktas = 145
      oL = '\n    <!-- i:{:s} s:{:s} p:{:s} r:{:s} w:{:s} -->\n' \
           .format(icaoSpec, pathSsid, self.pthL[p]['path'], \
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
          oL = '      <alt>{:d}</alt>\n' \
             .format(self.pthL[p]['legL'][l]['altF'])
          outpHndl.write(oL)
        oL = '      <ktas>{:d}</ktas>\n'.format(ktas)
        outpHndl.write(oL)
        outpHndl.write('      <flaps-down>true</flaps-down>\n')
        outpHndl.write('      <gear-down>false</gear-down>\n')
        outpHndl.write('      <on-ground>false</on-ground>\n')
        outpHndl.write('    </wpt>\n\n')
      # Append wp named END
      outpHndl.write('    <wpt>\n')
      oL = '      <name>END</name>\n'
      outpHndl.write(oL)
      oL = '      <lat type="double">{:07f}</lat>\n' \
           .format(self.pthL[p]['legL'][l]['latN'])
      outpHndl.write(oL)
      oL = '      <lon type="double">{:08f}</lon>\n' \
           .format(self.pthL[p]['legL'][l]['lonE'])
      outpHndl.write(oL)
      outpHndl.write('    </wpt>\n')
      oL = '    <!-- END {:s}    {:s} -->\n\n' \
           .format(icaoSpec, self.pthL[p]['path'])
      outpHndl.write(oL)

##   
  def toFGAITail( self, outpHndl):
    ''' given open file Handle:  write fgfs RM xml tail lines '''
    outpHndl.write('    </ai>\n')
    outpHndl.write('  </sim>\n')
    outpHndl.write('</PropertyList>\n')

##
  def toFGLDHead( self, outpHndl):
    ''' given open file Handle:  write fgfs RM xml tail lines '''
    outpHndl.write('<PropertyList>\n\n')
    #outpHndl.write('  <Airport>\n')
    #oL = '    <Name>{:s}</Name>\n'.format(icaoSpec)
    #outpHndl.write(oL)
    outpHndl.write('\n<!-- Start FGLD -->\n')

##   
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
        if ( 'Star-Tx' in self.pthL[p]['ssid']) :
          wyptDecl = 'StarTr_Waypoint'
        if ( 'Sid-Tx' in self.pthL[p]['ssid']) :
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
##   

  def toFGLDTail( self, outpHndl):
    ''' given open file Handle:  write fgfs RM xml tail lines '''
    outpHndl.write('\n<!-- End FGLD -->\n')
    #outpHndl.write('\n  </Airport>\n')
    outpHndl.write('\n</PropertyList>\n')
    
##   
  def toKMLSBody( self, outpHndl):
    ''' given open file Handle:  write kml files from paths  '''
    outpHndl.write(' Files are in ./KMLS folder\n')
    outpHndl.write('  gpxsee app recommended\n')
    pathNumb = 0
    pfixList = []
    sfixList = []
    for p in range(self.pthsTale):
      pathNumb += 1
      deptName = icaoSpec
      pathSsid = (self.pthL[p]['ssid'])
      destIndx = self.pthL[p]['tale']-1
      if ( destIndx > 0 ) :
        destName = self.pthL[p]['legL'][destIndx]['iden']
        # Star: parse path to outFId if dotted else iden dot path
        scanPath = self.pthL[p]['path']
        if ('.' in scanPath ):
          pathProc = scanPath
        else :
          pathProc = self.pthL[p]['legL'][destIndx]['iden'] + '.' + scanPath
        ##
        # ndupGate open for either pfixIden or sfixIden not seen before
        ndupGate = 'psetShut'
        ndupFlag = 'dupe'
        if not (pathProc[:pathProc.find('.')] in pfixList):
          pfixList.append (pathProc[:pathProc.find('.')])
          ndupGate = 'pfixNdup'
          ndupFlag = 'ndup'
        if not (pathProc[pathProc.find('.'):] in sfixList) : 
          sfixList.append (pathProc[pathProc.find('.'):])
          ndupGate = 'sfixNdup'
          ndupFlag = 'ndup'
        if ('Ndup' in ndupGate):
          oL = '<!-- ndup pathProc: {:s}-{:s}-{:s}-{} -->\n'.format(icaoSpec, \
                               pathSsid, scanPath, p)
          outpHndl.write(oL)
        else :
          oL = '<!-- dupe pathProc: {:s}-{:s}-{:s}-{} -->\n'.format(icaoSpec, \
                               pathSsid, scanPath, p)
          outpHndl.write(oL)
        ##
        pathOFId = icaoSpec + '/KMLS/' + icaoSpec + '-' + pathSsid + '-' \
                            + ndupFlag + '-' + pathProc + '-' + str(p) + '.kml'
        #      print('KMLS: ', pathOFId)
        ##
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
##   

  def toORDRPath( self, outpHndl, p, rway):
    ''' call from toORDRBody with hndl, pathIndx, rway to write single path '''
    # Create varied line styles, color reddish departt blueish arrive
    stks = ['1-8-2-1', '1-7-2-2', '1-6-2-3', '1-5-2-4', \
            '1-4-2-5', '1-3-2-6', '1-2-2-7', '1-1-2-8' ]
    depClrs =  ['240,20,20',  '240,20,80',   '240,20,140',  '240,20,200', \
                '240,80,20',  '240,80,80',   '240,80,140',  '240,80,200', \
                '240,140,20', '240,220,80',  '240,140,140', '240,140,200'   ]
    arrClrs =  ['20,20,240',  '20,80,240',   '20,140,240',  '20,200,240', \
                '80,20,240',  '80,80,240',   '80,140,240',  '80,200,240', \
                '140,20,240', '140,80,240',  '140,140,240', '140,200,240'   ]
    txtnClrs = ['50,50,20',   '100,50,20',   '150,50,20',   '200,100,20', \
                '100,100,20', '150,100,20', '200,150,20',  '250,100,20', \
                '250,50,10',  '250,100,10', '150,150,10',  '200,200,10'   ]
    stxrClrs = ['50,150,200',  '100,175,200', '150,180,200',    '200,190,200', \
                '100,100,210','150,110,210', '200,120,210',  '250,130,210', \
                '250,200,220', '250,210,220', '150,220,220',  '200,230,220'   ]
    lSsid = (self.pthL[p]['ssid']).lower()
    oL = '\n  <route name="{:s}" displayMode="{:s}" ' \
         .format(self.pthL[p]['path'], lSsid)
    # Bigger zoom number means more miles on screen
    if (lSsid == 'sid-tx') :
      # brown   tint for transition wpts
      oL = oL + 'zoomMin="8" zoomMax="500" color="140,80,40">\n'
    if (lSsid == 'sid') :
      # pink    tint for departing wpts
      oL = oL + 'zoomMin="6" zoomMax="300" color="240,200,160">\n'
    if (lSsid == 'star-tx') :
      # skyblue tint for approach wpts
      oL = oL + 'zoomMin="8" zoomMax="500" color="160,200,240">\n'
    if (lSsid == 'star') :
      # skyblue tint for approach wpts
      oL = oL + 'zoomMin="6" zoomMax="300" color="160,200,240">\n'
    outpHndl.write(oL)
    if (lSsid == 'sid'):
      oL = '    <activeStartRunways>{:s}' \
           .format(rway)
      outpHndl.write(oL)
      outpHndl.write('</activeStartRunways>\n')
    if (lSsid == 'star'):
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
      if (lSsid == 'sid-tx'):
        segColr = txtnClrs[(p%12)]
      if (lSsid == 'sid'):
        segColr = depClrs[(p%12)]
      if (lSsid == 'star-tx'):
        segColr = stxrClrs[(p%12)]
      if (lSsid == 'star'):
        segColr = arrClrs[(p%12)]
      oL = '    <line start="{:s}" end="{:s}" arrows="end"' \
           .format(begName, endName)
      outpHndl.write(oL)
      oL = ' stroke="{:s}" color="{:s}" />\n' \
           .format(segStke, segColr)
      outpHndl.write(oL)
    # Close route segment
    outpHndl.write('  </route>\n')
##   

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
      ##if (( skelFId  != '' ) & (skelSsid == 'Sid') ):
      if (( skelFId  != '' ) & ( 'Sid' in skelSsid  ) ):
        #Sid uses first legName in legList and Sid title == Path name
        #skelLegn = (self.pthL[p]['legL'][l]['iden'])
        #
        skelLegn = (self.pthL[p]['path'])
      ##if (( skelFId  != '' ) & (skelSsid == 'Sid') ):
      if (( skelFId  != '' ) & ('Star' in skelSsid ) ):
        #LastFirst legName in legList, save it
        #        skelLegn = (self.pthL[p]['legL'][l]['iden'])
        #
        skelLegn = '{:s}'.format ((self.pthL[p]['path']) )
      if (( skelFId  != '' ) & (( 'Star' in skelSsid ) | ( 'Sid' in skelSsid ))) :
        # write line to skeleton spec file
        oL = '{:s}, {:s}, {:s}, Rwy\n'.format((icaoSpec), \
                                          (skelSsid), (skelLegn))
        skelHndl.write(oL)
    # iterate thru each path
    for p in range(self.pthsTale):
      # Each path may apply to more than one rway according to rwaySpec entry
      #      print ('@p: ', p, self.pthL[p]['path'])
      #if ( 'BLV' in self.pthL[p]['path']) :
      #  trapFlag = 1
        #        print('ding trapFlag: ', trapFlag)
      if (( specFId  == '' ) | ('-Tx' in self.pthL[p]['ssid'])) :
        # no runway spec file or -Tx in path type : output path
        tRout.toORDRPath( outpHndl, p, self.pthL[p]['rway'] )
      else:
        for s in range(self.specTale):
          if (icaoSpec in self.specL[s]['icao'] ):
            #            print ( (self.pthL[p]['path']))
            #
            skelLegn = '{:s}'.format ((self.pthL[p]['path']) )
            #print(skelLegn)
            if ( (self.specL[s]['type'] == self.pthL[p]['ssid']) \
             and (self.pthL[p]['tale'] > 0)):
              if ('Star' in self.specL[s]['type']):
                # Arr list needs to match last wypt
                l = self.pthL[p]['tale']
                if (self.specL[s]['wypt'] == self.pthL[p]['legL'][l-1]['iden']):
                  # call output path with rway inserted from specfile
                  specRway = self.specL[s]['rway']
                  tRout.toORDRPath( outpHndl, p, specRway )
              if ('Sid' in self.specL[s]['type']):
                # Dep list needs to match first wypt
                #print (self.specL[s]['wypt']) 
                #print (self.pthL[p]['legL'][0]['iden'])
                if (self.specL[s]['wypt'] == self.pthL[p]['legL'][0]['iden']):
                  specRway = self.specL[s]['rway']
                  tRout.toORDRPath( outpHndl, p, specRway )
##   

  def toORDRTail( self, outpHndl):
    ''' given open file Handle:  write fgfs RM xml tail lines '''
    outpHndl.write('\n</routes>\n')
##   

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
    outpHndl.write('  <!--  Files are in RMV2 folder -->\n')
##   

  def toRMV2Body( self, outpHndl):
    ''' given open file Handle:  write fgfs RM xml body from legs list '''
    pathNumb = 0
    pfixList = []
    sfixList = []
    for p in range(self.pthsTale):
      pathNumb += 1
      deptName = icaoSpec
      pathSsid = (self.pthL[p]['ssid'])
      destIndx = (self.pthL[p]['tale']-1)
      if ( destIndx > 0 ) :
        destName = self.pthL[p]['legL'][destIndx]['iden']
        # Star: parse path to outFId if dotted else iden dot path
        scanPath = self.pthL[p]['path']
        if ('.' in scanPath ):
          pathProc = scanPath
        else :
          pathProc = self.pthL[p]['legL'][destIndx]['iden'] + '.' + scanPath
        ##
        ndupFlag = 'dupe'
        if not (pathProc[:pathProc.find('.')] in pfixList):
          pfixList.append (pathProc[:pathProc.find('.')])
          ndupFlag = 'ndup'
        if not (pathProc[pathProc.find('.'):] in sfixList) : 
          sfixList.append (pathProc[pathProc.find('.'):])
          ndupGate = 'sfixNdup'
          ndupFlag = 'ndup'
        pathOFId = icaoSpec + '/RMV2/' + icaoSpec + '-' + pathSsid + '-' + ndupFlag \
                                                  + '-' + pathProc + '-rm.xml'
        #print('RMV2: ', pathOFId)
        pathOHdl = open( pathOFId, 'w', 1)
        ##
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
        pathOHdl.write('\n  <route>\n')
        ##if ('id' in pathSsid):
          ##outpHndl.write('\n  <departure>\n')
          ##oL = '    <airport type="string">{:s}</airport>\n'\
          ##   .format(deptName)
          ##outpHndl.write(oL)
          ##oL = '    <runway type="string">{:s}</runway>\n' \
          ##   .format( self.pthL[p]['rway'])
          ##outpHndl.write(oL)
          ##outpHndl.write('  </departure>\n')

        ##if ('tar' in pathSsid):
          ##outpHndl.write('  <destination>\n')
          ##oL = '    <airport type="string">{:s}</airport>\n'\
          ##     .format(deptName)
          ##outpHndl.write(oL)
          ##oL = '    <runway type="string">{:s}</runway>\n' \
          ##     .format( self.pthL[p]['rway'])
          ##outpHndl.write(oL)
          ##outpHndl.write('  </destination>\n')
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
##   

  def toRMV2Tail( self, outpHndl):
    ''' given open file Handle:  write fgfs RM xml tail lines '''
    #outpHndl.write('\n  </route>\n')
    outpHndl.write('</PropertyList>\n')
##   

##   

  #
  # Debug
  #
  def dbugPrnt(self):
    #for elem in self.pthL:
    #  print(elem)
    print((self.pthL))
##   

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
  print('  leaving  eg:  KIAD, Sid, pfixIden.firstLegn, 08L                  ')
  print('  arriving eg:  KIAD, Star, sfixIden.lastLegN, 08R                  ')
  print('    N.B Sinle space only after comma separators                     ')
  print('                                                                    ')
  print('Outut format may be one of these:')
  print('  -g ATPI  ATC Pie for display on ATCPI radar ')
  print('    .. save in ATC-pie data path                                    ')
  print('  -g FGAI  FlightGgear AI Flightplan for fgdata/AI/FlightPlans      ')
  print('    .. useful for creating e.g local AI SID/STAR traffic            ')
  print('  -g FGLD  FlightGear pseudo Level-D for Route Manager SID/STAR     ')
  print('    .. does not support all tags found in Paid-For navigraph data  ')
  print('    .. but can create useful SID/STAR paths from FAA/KML files      ')
  print('  -g KMLS  Generate individual KML waypoint/track files for SID/STAR ')
  print('    .. Use gpxsee application to preview KML before flying RMV2 file')
  print('  -g ORDR  Open Radar for display on OpenRadar ')
  print('    .. save in  /OpenRadar/data/routes/ICAO/ICAO.procedures.xml     ')
  print('  -g RMV2  Flightgear Route Manager Load format   ')
  print('    .. Use FG Route Manager Load button to open the route ')
  print('                                                                    ')
  print('Filter on data in out may be :')
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
##   

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
    tRout = fplnMill(icaoSpec + '-' + typeSpec)
    # run input file scanner
    if ('AIRP' in srceFmat.upper()):
      tRout.fromAIRP(inptFId)
    if ('ARDP' in srceFmat.upper()):
      tRout.fromARDP(inptFId)
    if ('ASAL' in srceFmat.upper()):
      tRout.fromASAL(inptFId)
    if ('GPX' in srceFmat.upper()):
      tRout.fromGPX(inptFId)
    if ('KML' in srceFmat.upper()):
      tRout.fromKML(inptFId)
    if ('LEVD' in srceFmat.upper()):
      tRout.fromLEVD(inptFId)
      #tRout.dbugPrnt()
    if ('ORDR' in srceFmat.upper()):
      tRout.fromORDR(inptFId)
    if ('PATH' in srceFmat.upper()):
      tRout.fromPATH(inptFId)
    print('Route created for icao <=> type: ', (icaoSpec + ' <=> ' + typeSpec) )
    # run output formatter
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
    if ('KMLS' in genrFmat.upper()):
      # open output file
      outpHndl  = open(outpFId, 'w', 1)
      tRout.toKMLSBody( outpHndl)
      outpHndl.flush
    # close output file
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
##   
