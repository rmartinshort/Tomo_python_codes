#!/usr/bin/env python

#Robert MS, July 2015
#Appended October 2015 for S wave tomography

#This code is quite bad: Needs to be improved for readability
#Note: in order for the cross correlation code to work, the sampling rate of the data files must be 20 Hz


#Runs cross correlations on antelope associated databases, then culls the data according to the following criteria:
#minimum CC coefficient of 0.9 
#maximum std of 0.02
#It does this for all frequency bands present

#####################
#WARNING
#When running this on large volumes of data, you may need to edit the xcorr_input.txt file within each data directory. An example of such a file is as follows
#Z                      - database name
#P                      - phase
#BHZ                    - channel
#y                      - accept default freq bands (four of them: 0.02-0.1; 0.4-0.8, 0.1-0.8,0.8-2.0) 
#y                      - accept default periods and pulse widths 
#2                      - uncertainty in user time pick (s)
#20                     - separation between target and nearest interfering phase (dependent on epicentral distance)
#8                      - maximum tolerance for delays 
#40                     - half width of window to read in
#TOLK                  - stations to ignore [if any: list one per line]
######################

#The parameters seem to work well for Alaska P tomography 
#Z
#P
#BHZ
#n
#0.02 0.5 0.8 0.8
#0.1 0.9 1.2 2.0
#n
#10 4 1.5 1
#0.2
#20
#10
#5
#stop
#TOLK

callxP = '/data/dna/rmartin/ALASKA/prep_for_tomo/call_xcorrP.sh' #script that calls the cross correlation (for P wave tomography)
callxS = '/data/dna/rmartin/ALASKA/prep_for_tomo/call_xcorrS.sh' #script that calls the cross correlation (for S wave tomography)

##This file contains an example setup
example_params='/data/dna/rmartin/ALASKA/prep_for_tomo/xcorr_input_S.txt'

import glob
import sys
import argparse
import os

parser = argparse.ArgumentParser()

parser.add_argument('-path',action='store',dest='datapath',help='Path to the data directories in event/BH_VEL/stations format')

parser.add_argument('-allx',action='store_true',default=False,dest='allx',help='Append if you want to apply X correlation event when no xcorr_input file is not present [you probably shouldnt do this]')

parser.add_argument('-phase',action='store',default='P',dest='phase',help='Append the phase you want to run the cross-correlation process on. Choose P or S')

results = parser.parse_args()

phase = results.phase


def cull_xcorrelations(phase):
   '''Opens the text file output by the cross correlation and removes any entries that do not fit the criteria'''

   os.system('rm *.clean')

   if (phase == 'P'):
    xcorrfiles = glob.glob('Z*.sr.lp*')

   elif (phase == 'S'):
    xcorrfiles = glob.glob('T*.sr.lp*')

   else:
    print 'Input phase not recognized'
    sys.exit(1)

   for infile in xcorrfiles:
      corrfile = open(infile,'r')
      lines = corrfile.readlines()
      corrfile.close()
      
      outfilename = infile+'.clean'
      outfile = open(outfilename,'w')
      for line in lines:
         vals = line.split('   ')
         if len(vals[-2]) < 10:
            corrval = float(vals[-1])
            std = float(vals[-2])
            if ((abs(std) < 0.02) and (corrval > 0.9)):
               outfile.write(line)     

if results.datapath:
   filepath = results.datapath
else:
   print 'No arguments entered: See the help for details on how to use this script'
   sys.exit(1)
   
cwd = os.getcwd()

try:
  os.chdir(filepath)
except:
  print 'Specified file path %s doesnt seem to exist' %filepath
  
events = glob.glob('20*')
eventdir = os.getcwd()
for event in events:
  os.chdir(event)
  os.chdir('BH_VEL')
  os.system('pwd')
  
  if results.allx:
     print 'Proceeding to copy the example file. The xcorrelation will probably work, but may not be ideal'
     os.system('cp %s .' %example_params)
  
  #Check of a cross correlation param file exists
  elif os.path.isfile('xcorr_input.txt'):
     print 'Found the following xcorr_input.txt'
     os.system('cat xcorr_input.txt')
     os.system('%s xcorr_input.txt' %callx)
  else:
     print 'WARNING: NO XCORR FILE FOUND'
     sys.exit(1)	

  ################################################
  #Do the correlation - should probably check that the right database exists too
  ################################################

  if (phase == 'P'):
    os.system('%s' %callxP)
  elif (phase == 'S'):
    os.system('%s' %callxS)
  else:
    print 'Phase not recognized'
    sys.exit(1)
        
  #Cull bad data      
  cull_xcorrelations(phase)
  os.chdir(eventdir)
  
  
  
  
  
  
  
  
  
  
