

"""
Given a CoMon query, prints the returned nodes. For use with 
Assumes that 
Matt Borgard - 2/12/07
"""

import urllib2
import string
import sys

#if((len(sys.argv) < 2) or (sys.argv[1] == "--help") or (sys.argv[1] == "-help") or (sys.argv[1] == "help")):
#	print "Error: Invalid number of arguments. Usage - comonscript \"QUERY\"  Be sure to include quotes around your query, or use the escape sequence for the '&' character."
#	sys.exit(1)


def comon(query):
	
	#   Formats the URL   #
	ii = 0
	commaNeeded = 0


	if(query.find("'") == -1):
		#Finds select= and adds a ' after the =
		while (commaNeeded != 1 and ii < len(query)-6): 
			if (query[ii:ii+7] == 'select='): 
				query = query[0:ii+7]+"'"+query[ii+7:] 
				commaNeeded = 1
			ii += 1

		#If there is an option after select= 
		while(commaNeeded and ii < len(query)-1):
			if (query[ii] == '&' and query[ii+1] != '&' and query[ii-1] != '&'): #If we need to add a comma, look for a single &
				query = query[0:ii+1]+"'"+query[ii+1:0]
				commaNeeded = 0
			ii += 1

		#Adds ' to the end if there are no other options after select=
		while(commaNeeded):
			query = query+"'"
			commaNeeded = 0

		# Replaces spaces with '%20' #
		ii = 0
		while(ii < len(query)):
			if query[ii] == " ":
				url = url[0:ii]+"%20"+url[ii+1:]
			ii += 1


	
	ii = 0
	output = ""
	url1 = 'http://summer.cs.princeton.edu/status/tabulator.cgi?table=table_nodeviewshort&format=nameonly&'
	url2 = query
	url = url1 + url2
	f = urllib2.urlopen(url)
	s = f.read()
	f.close()
	
	while ((s[0:11] == "query error") and (s[ii:ii+3] != "<p>")):
		output += s[ii]
		ii += 1
	if(ii != 0):
		print output
		sys.exit(1)

	return s

