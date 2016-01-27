#!/usr/bin/env python

#######################
#Robert MS, June 2015##
##Modified October 2015 for S wave tomography##

#################################################
#Uses obspyDMC to download data for use with a tomography project. Will produce useful graphs if asked to
#################################################

#####
#ObspyDMC requests sometimes take a long time. When fetching data, you should run this process in screen
#####

print "\nDid you call >antsrc ? If not, stop the program and do so: Otherwise it won't make antelope databases!\n"

import os
import sys 
import glob
import argparse

print 'Importing Obspy modules...'
from obspy.fdsn import Client
import obspy
from obspy import read
import obspy.signal 
import pylab as plt
from obspy.taup.taup import getTravelTimes
from obspy.core.util.geodetics.base import gps2DistAzimuth
from obspy.core.util import locations2degrees
from obspy import UTCDateTime
FDSNclient = Client('IRIS')
from collections import Counter
print 'Done imports'


parser = argparse.ArgumentParser()

parser.add_argument('-params',action='store',dest='inputfile',help='Input the name of the paramter file if you want to use this to get data')

parser.add_argument('-plot',action='store',default=False,dest='plotraypath',help='Append this if you want to produce a .pdf plot of the raypaths in your request. Give the full file path')

parser.add_argument('-prep',action='store',dest='inputpath',help='The full file path to the data you want to prepare for a tomography project')

parser.add_argument('-phase',action='store',dest='phase',help='The seismic phase you are intersted in: This determines which SAC files are accessed and what the final output is. Choose from S or P')

parser.add_argument('-Tcheck',action='store_true',default=False,dest='tcheck',help='Append to check the data directory for timing problems, and report the suspect files')

parser.add_argument('-Tcorrect',action='store_true',default=False,dest='tcorrect',help='Append to correct suspect times')

parser.add_argument('-autoP',action='store_true',default=False,dest='autop',help='Append to run the Baer autopicker on the data and add the P picked times to the header. This is experimental')

results = parser.parse_args()

if results.autop:
  print 'Setting up autopicker'
  from obspy.signal.trigger import pkBaer

##########################
#Read input parameter file
##########################

def readparamfile(infile):
	'''Reads parameter file and creates variables for input into ObspyDMC'''

	paramfile = open(infile,'r')
	lines = paramfile.readlines()
	paramfile.close()

	#only read input from lines not beginning with a #
	inputlist = []
	for line in lines:
		if line[0] != '#':
			inputlist.append(line.strip())

	return inputlist 
	
##########################
#Get data using obspyDMC [to test if this is installed correctly, run >obspyDMT --tour]
##########################

def call_obspyDMC(inputlist):
  '''Check if values in inputlist are correct, and call obspyDMC to get the data and make the required dir structure'''

  cwd = os.getcwd()

  Datadir = inputlist[0]
  minmag = inputlist[1]
  maxmag = inputlist[2]
  mintime = inputlist[3]
  maxtime = inputlist[4]
  network = inputlist[5]
  station = inputlist[6].strip()
  channel = inputlist[7]
  stationbounds = inputlist[8]
  eventboundsbox = inputlist[9]
  eventboundscicle = inputlist[10]
  correction = inputlist[11]
  time = inputlist[12]

  try:
   minmag = float(minmag)
   maxmag = float(maxmag)
   time = float(time)
  except:
   print 'Magnitudes and time must be numbers'
   sys.exit(1)

  if station == '*':
    print 'WARNING: Requesting all stations for network %s' %network

    #constract a list of available stations
    station = constuctTAstationlist(network,mintime,maxtime,stationbounds)

  if eventboundsbox == '-':
     request_str = "obspyDMT --datapath %s --min_date %s --max_date %s --min_mag %g --max_mag %g --cha %s --station_rect %s --net %s --sta %s --corr_unit=%s --event_circle %s --offset=%g --fdsn_bulk" %(Datadir,mintime,maxtime,minmag,maxmag,channel,stationbounds,network,station,correction,eventboundscicle,time)

     print 'Input parameters look good: calling obspyDMT to fetch data'
     print request_str

#This command does the data fetching
########################################
     os.system('%s' %request_str)
  ########################################
    
    #Graphical options [don't work on dna user]
    ########################################
	#os.chdir('%s' %Datadir)
	#datadirectory = os.getcwd()
	#os.chdir(cwd)
	#plot_raypaths(datadirectory)


def constuctTAstationlist(network,starttime,endtime,stationbounds):
  '''When downloading TA station data, construct a string that contains all the stations of interest'''

  stationcoors = stationbounds.split('/')

  print stationcoors

  inventory = FDSNclient.get_stations(network=network,station=None,level='station',starttime=starttime,endtime=endtime,minlongitude=stationcoors[0],minlatitude=stationcoors[2],maxlongitude=stationcoors[1],maxlatitude=stationcoors[3])
  print inventory

  stationstring = []
  for station in inventory[0]:
    stationcode = str(station).split(' ')[1].strip()

    #we don't want to donwload multiple records for stations that have more than one instrument
    if '01' not in stationcode:
      stationstring.append(stationcode)

  stationstring = ','.join(stationstring)

  return stationstring
	

##########################
#Look at the station names in a dir and return a list of them: Necessary when we're grouping E and N for rotation
##########################

def findstationnames():
  '''Look at the station names in a directory and return a list of the names. This is important as the list is then used to locate BHE,BHN and BHE files'''
  
  filenames = []
  os.system('rm *FID*') #remove station FID, because the data from this are consistently messed up
  sacfiles = glob.glob('*.BHZ')
  for sacfile in sacfiles:
    sacfilenameparts = sacfile.split('.')
    filename = sacfilenameparts[2]

    if filename not in filenames:
      filenames.append(filename)
      
  return filenames
  
##########################
#Processing loop for S wave tomography: Append useful information to SAC header and rotate to GCP; make antelope database from the T component only
##########################
  
def ProcessLoopS(filepath,stationnames):
    '''File processing loop for S tomography: Take the components and convert to RTZ, and delte the E and N comps'''

    saceditscript = '/data/dna/rmartin/ALASKA/prep_for_tomo/SAC_operations_S.sh'
    
    p = os.getcwd()
    
    for station in stationnames:
        print 'Dealing with %s' %station
    
        Rstream = obspy.Stream()

        #Get all SAC files associated with that station
        sacfiles = list(reversed(sorted(glob.glob('*.%s..*' %station))))
        saccount = 0
        
        for sacfile in sacfiles:
           trace = read(sacfile)
           
           #Only determine the distance and back-azimuth once: This is what the saccount variable is here for
           if saccount == 0:
           
             evlat = trace[0].stats.sac.evla
             evlon = trace[0].stats.sac.evlo
             evdep = trace[0].stats.sac.evdp
             stlat = trace[0].stats.sac.stla
             stlon = trace[0].stats.sac.stlo
           
             dist = locations2degrees(evlat,evlon,stlat,stlon) #find distance from the quake to the station (in degrees)

             arcs = gps2DistAzimuth(lat1=stlat,lon1=stlon,lat2=evlat,lon2=evlon)

             baz = arcs[1] #This is station-event
             az = arcs[2] #This is event-station
             
             if evdep > 1e3:
                evdep = evdep/1000.0;
                
             traveltimes = getTravelTimes(dist,evdep, model='iasp91')
             
             P = 0
             S = 0

             for element in traveltimes:
               phaseinfo = element['phase_name']
               if phaseinfo == 'P':
                  Ptime = element['time']
                  P = 1
               if phaseinfo == 'S':
                  Stime = element['time']
                  S = 1
               if (P==1 and S ==1):
                  break

             try:
               P = Ptime
             except:
               Ptime = 0
             try:
               S = Stime
             except:
               Stime = 0             
            
           #Set the P and S times, and other SAC header data
           trace[0].stats.sac.az = float(az)
           trace[0].stats.sac.baz = float(baz)

           trace[0].stats.sac.o = 0.0 #add origin time

           #For some reason, these obspy signal processing steps can be very slow. Using SAC for now. 
           #trace[0].resample(20) #resample the trace - this sample rate is needed for the cross correlation code
           #trace[0].detrend('demean')

           if Ptime > 0:
            trace[0].stats.sac.user1 = Ptime
           if Stime > 0:
            trace[0].stats.sac.user2 = Stime

           trace[0].stats.sac.evdp = evdep*1000 #dbpick wants depth to be in meters

           trace.write(sacfile,format='SAC')

           saccount += 1

        try: 

          Zfile = sacfiles[0]
          Nfile = sacfiles[1]
          Efile = sacfiles[2]

          #Set the component orientations of the files

          traceE = read(Efile)
          traceE[0].stats.sac.cmpinc = 90.0
          traceE[0].stats.sac.cmpaz = 90.0
          traceE.write(Efile,format='SAC')

          traceN = read(Nfile)
          traceN[0].stats.sac.cmpinc = 90.0
          traceN.write(Nfile,format='SAC')

          #Strict test to ensure the files are read in the correct order

          if ('BHE' not in Efile) or ('BHN' not in Nfile) or ('BHZ' not in Zfile):

            if ('BHR' in Zfile):
              print 'Skipping: ZRT files already present'
            else:
              print 'Components not recognized'

          else:

            basefilename = Efile[:-4]

            #Rotate to GCP (using SAC)
            os.system('%s %s %s %s' %(saceditscript,Nfile,Efile,basefilename))

            #Save space by removing the N and E comps
            os.system('rm %s %s' %(Nfile,Efile))

        except:
          print 'Sacfile list: %s does not contain three component data' %str(sacfiles) 
          continue

        #sys.exit(1)
           
    #create antelope database - just for S waves, which are picked on the traverse.
    os.system('sac2db *.BHT T')
    
##########################
#Processing loop for P wave tomography: Append useful information to SAC header, make antelope database from the T component only (very similar stages to the S loop; shared code could be made into a 
#new function
##########################

def ProcessLoopP(filepath):
    '''The file processing loop associated with P wave tomography: Just deal with the BHZ files to save time'''

    sacfiles = glob.glob('*.BHZ')

    #Check to see if there is more than one location for a given station
    stationnames = []
    for sacfile in sorted(sacfiles):
      sacfilenameparts = sacfile.split('.')
      stationname = sacfilenameparts[2]

      if stationname not in stationnames:
        stationnames.append(stationname)

        trace = read(sacfile)

        evlat = trace[0].stats.sac.evla
        evlon = trace[0].stats.sac.evlo
        evdep = trace[0].stats.sac.evdp
        stlat = trace[0].stats.sac.stla
        stlon = trace[0].stats.sac.stlo

        dist = locations2degrees(evlat,evlon,stlat,stlon) #find distance from the quake to the station (in degrees)

        arcs = gps2DistAzimuth(lat1=stlat,lon1=stlon,lat2=evlat,lon2=evlon)

        baz = arcs[1] #This is station-event
        az = arcs[2] #This is event-station

        #If we're running this code twice in a row, need to correct the evdep accordingly. The evdep that comes from obspy will be in km, but needs
        #to be in the SAC header in meters. If the depth is already in meters in the SACfile, then it will almost certainly be >1000. This if statement check for 
        #this, and converts to km if necessary

        if evdep > 1e3:
          evdep = evdep/1000.0

        traveltimes = getTravelTimes(dist,evdep, model='iasp91')
        
        P = 0
        S = 0

        for element in traveltimes:
            phaseinfo = element['phase_name']
            if phaseinfo == 'P':
               Ptime = element['time']
               P = 1
            if phaseinfo == 'S':
               Stime = element['time']
               S = 1
            if (P==1 and S==1):
               break

        try:
            P = Ptime
        except:
            Ptime = 0
        try:
            S = Stime
        except:
            Stime = 0

        #Set the P and S times
        trace[0].stats.sac.az = float(az)
        trace[0].stats.sac.baz = float(baz)
        trace[0].stats.sac.o = 0.0 #add origin time
        
        if Ptime > 0:
          trace[0].stats.sac.user1 = Ptime
        if Stime > 0:
          trace[0].stats.sac.user1 = Stime

        trace[0].stats.sac.evdp = evdep*1000 #dbpick wants depth to be in meters

        #other operations
        trace[0].detrend('demean')

        #THE CROSS CORRELATION CODE ASSUMES A SAMPLING RATE OF 0.05 (20 SAMPLES/SECOND). IT WILL NOT WORK
        #OTHERWISE!!!

        trace[0].resample(20)

        #Experimental setup: attempts to automatically pick the P arrivals: In my experience this doesn't work very well

        if results.autop:

          tracestreamP = trace.copy()

          df = tracestreamP[0].stats.sampling_rate
          filter1 = 0.02
          filter2 = 0.1
          tracestreamP.filter("bandpass",freqmin=filter1,freqmax=filter2,corners=2)
          tracestreamP.taper(max_percentage=0.05, type='cosine')

          p_pick, phase_info = pkBaer(tracestreamP[0].data,df,10,2,2,10,20,6) #output from this is in samples.

          autoPtime = p_pick/df

          #Append the autopicker's time to the 
          if abs(Ptime-autoPtime) < 20:
            print 'Autopick accepted!'
            trace[0].stats.sac.t3 = autoPtime
           
        #Important - must write to the SAC file!
        trace.write(sacfile,format='SAC')
           
        print 'Appended P arrivals to %s' %sacfile

      else:
        print 'Found multiple instruments at station %s. Removing all but 1' %(stationname)
        os.system('rm %s' %sacfile)


    #create antelope database for P arrivals
    os.system('sac2db *.BHZ Z')


#########################
#Try to locate timing mismatches. For some reason certain event/station combinations have issues with timing, and this messes up antelope's dbpick
#Here, we try to find the suspect files and make a list of them
#########################
def Suspecttimes(filepath):
  '''Looks at all the SACfiles within each event directory and checks they have the same origin time. If not, the outlier files are noted'''

  os.chdir(filepath)

  timesfile = open('Suspect_timing_files.dat','wa')

  eventdirs = glob.glob('20*')

  upperdir = os.getcwd()

  for eventdir in eventdirs:
    #outfile.write(eventdir)

    os.chdir(eventdir)
    os.chdir('BH_VEL')
    print 'In event %s' %eventdir

    timesfile.write('> %s\n' %eventdir)

    starttimes = [] #Keep track of start times

    sacfiles = glob.glob('*BH*') #Deals with all components - should all have the same starttime

    for sacfile in sacfiles:
       print 'Looking at %s' %sacfile
       trace = read(sacfile)
       time = trace[0].stats.starttime
       starttimes.append(str(time))

    #Find most common element in the startttimes list (we can assume that this is the 'correct' time)
    count = Counter(starttimes)
    most_common = count.most_common()
    print most_common
    for time in most_common:
      timesfile.write('Quaketime: %s, Number of files: %i\n' %(time[0],time[1]))
    os.chdir(upperdir)
  
  timesfile.close()

#########################
#Correct suspect times, either by just changing the starttime of the suspect events, or by deleting the suspect SAC files in extreme cases
#This step is not strictly necessary, but it ensures that the antelope .origins database files only have one event origin per event directory
#########################
def Correctsuspecttimes(filepath):
  '''Correct the suspect times found in the associated file'''

  os.chdir(filepath)

  if os.path.isfile('Suspect_timing_files.dat'):
    print 'Found suspect times file in %s' %filepath
  else:
    print 'No suspect times file found. Run this script with a -Tcheck first to generate it'
    sys.exit(1)

  infile = open('Suspect_timing_files.dat','r')
  lines = infile.readlines()
  infile.close()

  eventsdic = {}
  for line in lines:
    vals = line.split()

    if vals[0] == '>':
      event = vals[1].strip()
      eventsdic[event] = []
    else:
      time = vals[1][:-1]
      eventsdic[event].append(time)

  cwd=os.getcwd()

  for event in eventsdic:
    print 'In event %s' %event
    if len(eventsdic[event]) > 1:

      #maintime is the most common time; aka the correct time. We loop though all the files and remove those whose starttimes are wrong by a very 
      #large number

      maintime = eventsdic[event][0]
      maintimeUTC = UTCDateTime(maintime)

      os.chdir(event)
      os.chdir('BH_VEL')
      allfiles = glob.glob('*BH*')

      for sacfile in allfiles:
        trace = read(sacfile)
        tracetime = UTCDateTime(trace[0].stats.starttime)
        tdiff = abs(maintimeUTC-tracetime)

        if tdiff < 0.1:
          trace[0].stats.starttime = maintime
          print 'file %s has a negligible time difference of %g. Correcting header' %(sacfile,tdiff)
          trace.write(sacfile,format='SAC')
        else:
          print 'file %s has time difference < 0.5. Deleting file' %sacfile
          os.system('rm %s' %sacfile)

    os.chdir(cwd)



##########################
#Plop raypath map. Doesn't work on the DNA user because we don't have PIL. We are NOOBS! 
##########################

def plot_raypaths(filepath):
	'''Call this to make a .pdf of the raypaths associated with an event-station collection'''

	filepathparts=filepath.split('/')
	datadir = filepathparts[-1]
	starttime = str(datadir.split('_')[0])

	plot_command = "obspyDMT --plot_dir %s --min_date %s --plot_sta --plot_ev --plot_ray --plot_format 'pdf'" %(filepath,starttime)
	os.system('%s' %plot_command)

##########################
#Function that actually enters the event directories and does the processing. The comments are outdated and refer to a SAC macro that was originally used to do the processing
#Now we only use obspy, and the data is kept at its original frequency
##########################

def prepare_files_for_tomo(filepath,filter=True):
    '''Prepares SAC files obtained via obspy to a format necessary for the tomography program. Filepath should be the same as that given to plot_raypaths
    See the example below
   
    This consists of the following steps:
   
    > Check to see if multiple location codes for given station. Use the first one and delete the other.
    > XX IF ASKED FOR XX Filter the data to a given band (this is for P wave tomography - the value can be changed in SAC_operations.csh)
    > Resample everything to delta = 0.05
    > Create an antelope database associated with each station 
    > Remove data that has not undergone instrument correction
   
    This runs the functions 'process loop P' or 'process loop S' depending on what the user has asked for
    '''
   
    cwd = os.getcwd()
    
    try:
      os.chdir(filepath)
    except:
      print 'Specified filepath %s does not appear to exist' %filepath
      sys.exit(1)
    
    events = list(sorted(glob.glob('20*'))) #list of all the event directories

    for eventdir in events:
    
        os.chdir(eventdir)
       
        currenteventdir = os.getcwd()
       
        #Not really necessary, but saves space: obspyDMC saves both the raw and instrument-corrected data, but we don't need the former
        if os.path.isdir('BH_RAW'):
           os.system('rm -r BH_RAW')
           
        
        ####################################
        #Decide if we're doing P or S wave tomography
        ####################################
        
        
        if os.path.exists('BH_VEL'):
           os.chdir('BH_VEL')
        
        filepathdata = os.getcwd()
        
        if results.phase == 'P':
           #P-wave tomo processing function
           ProcessLoopP(filepathdata)
        if results.phase == 'S':

           print eventdir
           stations = findstationnames()

           ProcessLoopS(filepathdata,stations)
        
        os.chdir(filepath)
              

if __name__ == '__main__':

   '''Runs the processes described above'''

   if results.inputfile:
      infilename = results.inputfile
   elif results.plotraypath:
      rayplotpath = results.plotraypath
   elif results.inputpath:
      inputpath = results.inputpath
   else:
      print 'No arguments supplied: see Get_Data_For_Tomo.py -h for details'
      sys.exit(1)
      
   phasechoices = ["P","S"]
   if results.phase not in phasechoices and results.inputpath and not results.tcheck and not results.tcorrect:
       print 'ERROR: You need to enter the phase of interest. Choose from P or S. See --help for details'
       sys.exit(1)

   if results.inputfile and results.inputpath:
      print 'Do not try to specify a data download and tomography prepare in the same step: First download the data and then check the directory structure'
      sys.exit(1)

   ######################
   #Call obspyDMT to get the data
   if results.inputfile:
      inputlist = readparamfile(infilename)
      call_obspyDMC(inputlist)

   #####################
   #plot raypaths 
   if results.plotraypath:
      plot_raypaths(rayplotpath)

   #####################
   #Check for event time errors
   if results.tcheck and results.inputpath:
      print 'Checking for suspect times'
      Suspecttimes(inputpath)
   elif results.tcorrect and results.inputpath:
      print 'Correcting suspect times'
      Correctsuspecttimes(inputpath)
   elif results.inputpath:
      print 'Preparing for tomography'
      prepare_files_for_tomo(inputpath)
   else:
    print 'Done!'


