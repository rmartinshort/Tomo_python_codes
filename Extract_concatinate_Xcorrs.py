#!/usr/bin/env python


#This script can be copied into the data base directory and run on the event file names in order to extract all the Xcorr data
###################
#Extracts X correlation data from all available event directories and makes one master correlation file per frequency band
###################

import glob
import os

count = 0
eventdirs = glob.glob('20*')
cwd = os.getcwd()

try:
  os.system('rm *ALL.dat')
except:
  'No existing all X_corr files found'

for event in eventdirs:
  os.chdir(event)
  os.chdir('BH_VEL')
  
  all_Xbands = glob.glob('*.clean') #find all the cross correlation bands
  for item in all_Xbands:
     itemname = item[:13]
     outfilename = itemname+'ALL.dat'
     if count == 0: 
         os.system('cat %s > %s' %(item,cwd+'/'+outfilename))
     else:
         os.system('cat %s >> %s' %(item,cwd+'/'+outfilename))

  count += 1 
  os.chdir(cwd)
    

