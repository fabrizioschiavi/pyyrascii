#!/usr/bin/env python
# -*- coding: UTF-8; -*-

"""
PyYrAscii
-------

PyYrAscii is a simple python grapher for using Yr.no’s weather data API.

You are welcome to participate in this project!
"""

__version__ = '0.4'
__url__ = 'https://github.com/ways/pyyrascii'
__license__ = 'GPL License'
__docformat__ = 'markdown'

import SocketServer, subprocess, re, sys, string
import pyyrlib # https://github.com/ways/pyyrlib
import pyofc # https://github.com/ways/pyofflinefilecache

def wind_symbols():
  return {
    "N":" N", "NNE":"NE", "NE":"NE", "ENE":"NE", \
    "E":" E", "ESE":"SE", "SE":"SE", "SSE":"SE", \
    "S":" S", "SSW":"SW", "SW":"SW", "WSW":"SW", \
    "W":" W", "WNW":"NW", "NW":"NW", "NNW":"NW"}


def get_pyyrascii (location):
  weatherdata, source = pyyrlib.returnWeatherData(location, True)

  if not weatherdata:
    return False

  verbose = False
  ret = "" #all output goes here
  graph=dict()
  tempheight = 11
  timeline = 13
  windline = 14
  windstrline = 15
  rainline = 16
  graph[rainline] = "   " #rain
  graph[windline] = "   " #wind
  graph[windstrline] = "   " #wind strenght
  graph[timeline] = "   " #time
  temphigh = -99
  templow = 99
  tempstep = -1
  hourcount = 22
  screenwidth = 80
  #rain in graph:
  rainheigth = 6
  rainstep = -1
  rainhigh = 0
  wind = wind_symbols()

  #collect temps, rain from xml
  for item in weatherdata['tabular'][:hourcount]:
    if int(item['temperature']) > temphigh:
      temphigh = int(item['temperature'])
      #print "h" + item['temperature']

    if int(item['temperature']) < templow:
      templow = int(item['temperature'])
      #print "l" + item['temperature']

    if float(item['precipitation']) > rainhigh:
      rainhigh = float(item['precipitation'])

  if verbose:
    print "high",temphigh,"low",templow,"rainhigh",rainhigh

  #scale y-axis. default = -1
  if tempheight < (temphigh - templow):
    tempstep = -2
    if verbose:
      print "Upped timestep"

  #scale rain-axis
  #TODO

  if temphigh == templow:
    templow = temphigh-1

  temps=[]
  #create temp range
  for t in range(int(temphigh), int(templow)-1, tempstep):
    temps.append(t)

  if verbose:
    print "temps",temps

  #extend temp range
  #temps = [ (temps[0] +1) ] + temps
  for t in range(0, tempheight):
    if len(temps)+1 < tempheight:
      if t%2 == 0: #extend down
        temps.append( temps[len(temps)-1] - abs(tempstep) )
      else: #extend up
        temps = [ temps[0] + abs(tempstep) ] + temps
  #temps.append( temps[len(temps)-1] -1 ) #TODO:remove me?

  if verbose:
    print "temps",temps

  #write temps to graph
  for i in range(1, tempheight+abs(tempstep)):
    #print i
    try:
      graph[i] = str(temps[i-1]).rjust(3, ' ')
    except KeyError as (errno, strerror):
      print "err ",i,errno,strerror
      pass
    except IndexError as err: #list empty
      #print "err ",err
      pass

  #print "graph",graph

  #write rainaxis to graph
  rain = []
  for r in range(1, rainheigth, abs(rainstep)):
    rain.insert(r, '%2.0f mm ' % r)

  print "rain axis",str(rain)

  #draw graph elements:
  time=[]
  #for each x (time)
  for item in weatherdata['tabular'][:hourcount]:
    #create rain on x axis
    graph[rainline] += " " + '%2.0f' % float(item['precipitation'])
    #create wind on x axis
    graph[windline] += " " + \
      (wind[ item['windDirection']['code'] ] \
      if 0 != item['windSpeed']['mps'] else " O")
    #create wind strength on x axis
    graph[windstrline] += " " + '%2.0f' % float(item['windSpeed']['mps'])
    #create time on x axis
    graph[timeline] += " " + str(item['from'])[11:13] #2012-01-17T21:00
    #create time range
    time.append(str(item['from'])[11:13])

    #for each y (temp) look for matching temp, draw graph
    for i in range(1, hourcount):
      if tempheight < i:
        break

      #draw temp
      try:
        #parse out numbers to be compared
        temptomatch = [ int(item['temperature']) ]
        tempingraph = int(graph[i][:3].strip())

        if tempstep < -1: #TODO: this should scale higher than one step
          temptomatch.append(temptomatch[0] - 1)

        #print "temptomatch",temptomatch
        #print "graph",tempingraph

        if tempingraph in temptomatch:
          #print temptomatch, graph[i][:3].strip()
          if int(item['symbolnumber']) in [3,4,15]: #parly
            graph[i] += "==="
          elif int(item['symbolnumber']) in [5,6,7,8,9,10,11,12,13,14]: #clouded
            graph[i] += "###"
          else: #clear
            graph[i] += "---"
        else:
          graph[i] += "   "
      except KeyError as err:
        #print err
        pass

      #draw rain
      try:
        #print "rain" + str(tempheight-i)
        #print rain[tempheight-i][:2]
        #if float(rain[tempheight-i][:2]) == float(item['precipitation']):
        #  print "rain" + item['precipitation']
        #'%2.0f' % float(item['precipitation'])
        pass
      except IndexError as e:
        pass

  #  print item
  #  break

  #Legends
  graph[0] = " 'C" + string.rjust('Rain (mm) ', screenwidth-3)
  graph[rainline] +=    " Rain (mm)"
  graph[windline] +=    " Wind dir."
  graph[windstrline] += " Wind(mps)"
  graph[timeline] +=    " Hour"

  #header
  headline = "-= Meteogram for " +\
    str(source)\
    .replace('http://www.yr.no/sted/', '')\
    .replace('http://www.yr.no/place/', '')\
    .replace('/forecast.xml','')\
    .replace('/forecast_hour_by_hour.xml','')
  if location.isdigit():
    headline += " for the next " + str(hourcount) + " hours"
  headline += " =-"
  ret += string.center(headline, screenwidth) + "\n"

  #print graph
  for g in graph.values():
    ret += g + "\n"

  ret += '\nLegend:   --- : Sunny   === : Clouded   ### : Rain/snow \n' +\
    'Weather forecast from yr.no, delivered by the Norwegian Meteorological ' +\
    'Institute and the NRK.\n'

  return ret


if __name__ == "__main__":
  # Test if location is provided
  if sys.argv[1] == []:
    location = "0458"
  else:
    location = ''.join(sys.argv[1:])

  print get_pyyrascii(location)
  sys.exit(0)
