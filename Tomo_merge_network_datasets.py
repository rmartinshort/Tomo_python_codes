#!/usr/bin/env python

#This script is set up for a specific case and needs to be generalised! 

#######################
#Robert MS July 2015
#######################
#Merge datasets from multiple networks - only move events that appear in both networks. If the data has been downloaded with obspyDMT
#then this code will only work if the event selection windows where the same across all networks.

#BE CAREFUL WITH THIS SCRIPT - IT MOVES THINGS AROUND!

import os
import sys
import glob


def mergealaska():

	cwd = os.getcwd()

	os.chdir('/data/dna/rmartin/ALASKA/DATA/obspyDMT_TA/Alaska_merged/2015-06-11_2015-08-29')
	allTAevents = glob.glob('20*')
	os.chdir(cwd)

	os.chdir('/data/dna/rmartin/ALASKA/DATA/obspyDMT_TA/Alaska_AK/2015-06-11_2015-08-29')
	allAKevents = glob.glob('20*')

	for event in allAKevents:
	   if event in allTAevents:
		  os.system('mv %s/BH_VEL/* /data/dna/rmartin/ALASKA/DATA/obspyDMT_TA/Alaska_merged/2015-06-11_2015-08-29/%s/BH_VEL/' %(event,event)) 
		  print 'Merged %s' %event
	   else:
		  print 'Event %s unmatched' %event
	  
	os.chdir(cwd)

#clear up merged directory - all the data that this deletes should still be present in the TA and AK dirs

def cleanmerged():
   
   os.chdir('/data/dna/rmartin/ALASKA/DATA/obspyDMT_TA/Alaska_merged/2015-06-11_2015-08-29')
   
   cwd = os.getcwd()
   
   events = glob.glob('20*')
   for event in events:
      os.chdir(event)
      
      os.system('rm -r info')
      os.system('rm -r Resp')
      
      os.chdir(cwd)
      
      
if __name__ == '__main__':
   mergealaska()
   cleanmerged()
      
      
      
      
      
      
      
      
      
      
