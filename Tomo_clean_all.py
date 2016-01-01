#!/usr/bin/env python

#######################
#Robert MS July 2015
#######################

#Removes various stages of processing from data directories. BE CAREFUL when using! 

#-all : Deletes everything associated with antelope/cross correlation (but keep SAC files)
#-xcoor : Delete cross-correlation related files: This is probably not necessary as these get overwritten anyway when a new crosscorrelation is done
#-origins : IMPORTANT: Run this after you've done picking, and it will clean up any mess that has been written to the antelope database origins files
#-assoc : Deletes all .assoc files: Probably don't want to do this
#-recreate : Remake the antelope database after its been deleted with -all


import glob
import os
import argparse 
import sys

parser = argparse.ArgumentParser()

parser.add_argument('-all',action='store_true',default=False,dest='all',help='Delete everything apart from the SAC files')

parser.add_argument('-xcorr',action='store_true',default=False,dest='xcorr',help='Delete just the xcorrelation-related files')

parser.add_argument('-origins',action='store_true',default=False,dest='origins',help='Enter the directory and remove all but the first event in Z.origins')

parser.add_argument('-path',action='store',dest='path',help='Full path to the event directries. Must be given')

parser.add_argument('-assoc',action='store_true',default=False,dest='assoc',help='Delete assoc files')

parser.add_argument('-recreate',action='store_true',default=False,dest='recreate',help='Just remake all the antelope databases')

parser.add_argument('-phase',action='store',default='P',dest='phase',help='The seismic phase we are interested in. Choose P or S')

results = parser.parse_args()
phase = results.phase

if (phase != "S"):
   if phase != "P":
      print 'Entered phase must be S or P'
      sys.exit(1)

try:
   os.chdir(results.path)
except:
   print 'No path given'
   sys.exit(1)

def removeall():
   '''Remove all but the SAC files'''

   events = glob.glob('20*')
   cwd = os.getcwd()
   
   for event in events:
      os.chdir(event)
      os.chdir('BH_VEL')
      os.system('mkdir ../tmp')
      os.system('mv *BH* ../tmp')
      os.system('rm *')
      os.system('mv ../tmp/* .')
      os.system('rm -r ../tmp')
      os.chdir(cwd)

def remakedatabases(phase):
   '''Call after having run remove all to remake the database'''

   print 'Remaking database' 

   events = glob.glob('20*')
   cwd=os.getcwd()
   
   for event in events:
      print event
      os.chdir(event)
      os.chdir('BH_VEL')
      if phase == 'P':
         os.system('sac2db *.BHZ Z')
      elif phase == 'S':
         os.system('sac2db *.BHT T')
      else:
         print 'Phase not found'
      os.chdir(cwd)

def removexcorr(phase):
   '''Call to remove cross correlation-related files'''

   events = glob.glob('20*')
   cwd = os.getcwd()
   
   for event in events:
      os.chdir(event)
      os.chdir('BH_VEL')
      if (phase == "P"):
         os.system('rm Z.P*')
      if (phase == "S"):
         os.system('rm T.S*')
      os.system('rm xcorr_input.txt')
      os.chdir(cwd)
      
def removeassoc():
   '''Call to remove antelope .assoc files'''

   events = glob.glob('20*')
   cwd = os.getcwd()
   
   for event in events:
      os.chdir(event)
      os.chdir('BH_VEL')
      os.system('rm *.assoc')
      os.chdir(cwd)
      
def removeorigins(phase):
   '''Call to remove all but the last entry in the .origins files'''
   
   events = glob.glob('20*')
   cwd = os.getcwd()

   if (phase == 'P'): 
   
      for event in events:
         os.chdir(event)
         os.chdir('BH_VEL')
         try:
            infile=open('Z.origin','r')
            lines = infile.readlines()
            infile.close()
            outfile=open('Z.origin','w')
            outfile.write(lines[-1]) #only write the last line - should be the one where all the arrivals have been assciated
            outfile.close()
         except:
            print 'No origins file found in %s' %event
         os.chdir(cwd) 

   if (phase == 'S'):

      for event in events:
         os.chdir(event)
         os.chdir('BH_VEL')
         try:
            infile=open('T.origin','r')
            lines = infile.readlines()
            infile.close()
            outfile=open('T.origin','w')
            outfile.write(lines[-1]) #only write the last line - should be the one where all the arrivals have been assciated
            outfile.close()
         except:
            print 'No origins file found in %s' %event
         os.chdir(cwd) 
         
if results.all:
   removeall()
elif results.xcorr:
   removexcorr(phase)
elif results.origins:
   removeorigins(phase)
elif results.assoc:
   removeassoc()
elif results.recreate:
   remakedatabases(phase)
else:
   print 'No argument entered. See help file for useage' 
   