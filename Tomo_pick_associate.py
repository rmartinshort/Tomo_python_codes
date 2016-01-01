#!/usr/bin/env python

#Robert MS, June 2015
##################################
#Auto use of dbpick: Enters event directories and runs dbpick, so that arrivals can be chosen
##################################
#Remember to call antsrc before running this! 


print "Did you remember to call >ansrc? Quit the program and do so now if you didn't, otherwise it won't work"

import os 
import glob
import argparse
import datetime
import sys

parser = argparse.ArgumentParser()

parser.add_argument('-path',action='store',dest='fullpath',help='Full path to the directory containing the events [ie /home/data/mydatadir, where 20*... are stored]')

parser.add_argument('-fromlog',action='store_true',default=False,dest='logfile',help='Append to carry on picking from where you left off last time the log file was accessed')

parser.add_argument('-phase',action='store',default="P",dest='phase',help='Append the phase that you want to pick (will choose BHT for S and BHZ for P')

results = parser.parse_args()

#def associate_picks(zfiles):
#   '''Takes a list of Z files created by antelope and clones them, then runs dbassoc_arrival on them, to associate the picks with the database'''
   
#   for zfile in zfiles:
#      nameparts = zfile.split('.')
#      newname = nameparts[0]+'_out.'+nameparts[1]
#      os.system('cp %s %s' %(zfile,newname))
 
#   os.system('dbassoc_arrival Z Z_out') #associate the arrivals

if results.fullpath:
	path = results.fullpath
else:
	print 'No path to events entered. See help'
	sys.exit(1)

###################################################
#MAIN
###################################################
   
os.chdir(path)
cwd = os.getcwd()
eventdirs = glob.glob('20*')
phase = results.phase

#--------------------
#Creates a file containing all the picks so far: allows you to come back where you left off
#--------------------
pickedevents = []

if results.logfile:
	if os.path.isfile('picking_log.dat'):
		print 'Log of picked events found'
		logfile = open('picking_log.dat','r')
		lines = logfile.readlines()
		logfile.close()

		for element in lines[1:]:
			event = element.split(' ')
			pickedevents.append(event[0].strip())

	else:
		print 'No picked events log. Creating one'
		logfile = open('picking_log.dat','w')
		now = datetime.datetime.now()
		logfile.write('%s phase picking log. Created at %s\n' %(phase,str(now)))
		logfile.close()

print '----------------------------------------------------------------------'
print '\nThe following events already show picks:\n'
print pickedevents  
print '----------------------------------------------------------------------'
       
for datadir in sorted(eventdirs):

	if datadir not in pickedevents:

		os.chdir(datadir)
		os.chdir('BH_VEL')

		sacfiledir = os.getcwd()

		if ( phase == "P"):

			if os.path.isfile('Z.assoc'):


				###############
				#Note: This is always true if the data has been processed by the 'Get_Prep' script, because the obspy-entered arrivals generate an assoc file.
				###############

				print 'Picking P in file %s' %datadir
				usr_in = str(raw_input('Do you still want to see the data? [Enter Y or N] '))

				if usr_in.strip() == 'Y':

					print '-----------------------------------------------------------\n\nPicking in %s\n\n-----------------------------------------------------------'%sacfiledir
					os.system('dbpick Z')
					print 'Done picking in %s' %datadir 

					pickedevents.append(datadir)

					if results.logfile:
						print 'Pick logged'
						logfile = open(cwd+'/picking_log.dat','a')
						logfile.write('%s\n' %str(datadir))
						logfile.close()

		elif (phase == "S"):

			if os.path.isfile('T.assoc'):


				###############
				#Note: This is always true if the data has been processed by the 'Get_Prep' script, because the obspy-entered arrivals generate an assoc file.
				###############

				print 'Picking S in file %s' %datadir
				usr_in = str(raw_input('Do you want to see the data? [Enter Y or N] '))

				if usr_in.strip() == 'Y':

					print '-----------------------------------------------------------\n\nPicking in %s\n\n-----------------------------------------------------------'%sacfiledir
					os.system('dbpick T')
					print 'Done picking in %s' %datadir 
					pickedevents.append(datadir)

					if results.logfile:
						print 'Pick logged'
						logfile = open(cwd+'/picking_log.dat','a')
						logfile.write('%s\n' %str(datadir))
						logfile.close()

		else:

			print 'Entered phase was not understood. Run script with -phase P|S'
			sys.exit(1)

		os.chdir(cwd)



print 'Done: You may need to clean the origin files before proceeding. Do this with Tomo_clean_all.py'

