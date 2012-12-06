from collections import OrderedDict
from datetime import *
from pytoggl.config import APIConfig
import requests, json
import csv

"""
API TO-DO
1. Config file specifies users, API keys
2. Get time data for each user
3. Generate metrics for each user
4. Generate aggregate metrics
"""

""" CSV File Indicies """
CSV_USER        = 0
CSV_EMAIL       = 1
CSV_CLIENT      = 2
CSV_PROJECT     = 3
CSV_DESCRIPTION = 5
CSV_STARTDATE   = 7
CSV_STARTTIME   = 8
CSV_ENDDATE     = 9
CSV_ENDTIME     = 10
CSV_DURATION    = 11
CSV_TAGS        = 12

def rreplace(s, old, new, occurrence):
    li = s.rsplit(old, occurrence)
    return new.join(li)

class TimeEntry:
    def __init__(self):
        self.user = ""          # API and CSV
        self.description = ""   # API and CSV
        self.startDate = ""     # API and CSV
        self.endDate = ""       # API and CSV
        self.startTime = ""     # API and CSV
        self.endTime = ""       # API and CSV
        self.duration = ""      # API and CSV
        self.tags = []          # API and CSV
        self.start = ""         # API ONLY
        self.stop = ""          # API ONLY

    def firstTag(self):
        if len(self.tags) == 0:
            return 'Uncategorized'
        return self.tags[0]

    def hasTag(self, tagName):
        return (tagName in self.tags)

    @classmethod
    def ParseLine(cls,line):
        """
        ParseLine:
            Parses a time entry from a CSV file
            Returns a TimeEntry
        """
        try:
            t = TimeEntry()
            t.user = line[CSV_USER].strip()

            t.description = line[CSV_DESCRIPTION].strip()

            t.startTime = line[CSV_STARTTIME].strip()[0:8] # Cut GMT-offset
            t.startTime = datetime.strptime(t.startTime, '%H:%M:%S')

            t.startDate = line[CSV_STARTDATE].strip()
            t.startDate = datetime.strptime(t.startDate, '%Y-%m-%d')
            
            t.endTime = line[CSV_ENDTIME].strip()[0:8] # Cut GMT-offset
            t.endTime = datetime.strptime(t.endTime, '%H:%M:%S')

            t.endDate = line[CSV_ENDDATE].strip()
            t.endDate = datetime.strptime(t.endDate, '%Y-%m-%d')

            t.duration = line[CSV_DURATION].strip()
            t.duration = datetime.strptime(t.duration,'%H:%M:%S')
            t.duration = timedelta( \
                minutes=t.duration.minute, \
                seconds=t.duration.second, \
                hours=t.duration.hour)
            t.tags = line[CSV_TAGS].split(',')
            return t
        except:
            return None
        
    @classmethod
    def ParseJSONEntry(cls, user, struct):
        try:
            t = TimeEntry()
            t.user = user
            # TODO t.startTime
            # TODO t.startDate
            # TODO t.endTime
            # TODO t.endDate
            # TODO t.duration
            t.description = struct['description']
            t.start = struct['start']
            t.stop = struct['stop']
            t.tags = struct['tag_names']
            return t
        except:
            return None

class TimeLog:
    def __init__(self):
        self.entries = []

    def append(self, entry):
        self.entries.append(entry)

    def getSize(self):
        return len(self.entries)

    def getDataSeriesByInterval(self,startdate,enddate,interval=7):
        result = OrderedDict()
        series = []
        users = []
        date = datetime.strptime(startdate,'%m-%d-%y') 
        
        # Find all users in database
        for entry in self.entries:
            if entry.user not in series:
                users.append(entry.user)
                series.append(entry.user)
                series.append(entry.user + "_util")
                series.append(entry.user + "_debt")
        series.append('Total')
        series.append('Running Average')
        # Create result dictionary by week
        while date <= datetime.strptime(enddate,'%m-%d-%y'):
            begin = date
            date += timedelta(days=interval)
            end = date - timedelta(days=1)
            seriesInstance = {k:timedelta(seconds=0) for k in series}
            for entry in self.entries:
                if entry.startDate >= begin and entry.startDate <= end:
                    seriesInstance[entry.user] += entry.duration
                    seriesInstance['Total'] += entry.duration
            self.convertToHours(seriesInstance)
            key = datetime.strftime(end,'%m/%d/%y')
            result[key] = seriesInstance
        # Calculate running average and utilization
        runningSum = 0.0
        counter = 0
        for k in result.keys():
            counter = counter + 1
            runningSum += result[k]['Total']
            result[k]['Running Average'] = (runningSum/counter)
            for u in users:
                if result[k]['Total'] != 0.0:
                    result[k][u + "_util"] = \
                        result[k][u]/result[k]['Total']
        return result

    def getTimesByTask(self, filters=None):
        result = {}
        for entry in self.entries:
            key = None
            if type(filters) is list:
                for f in filters:
                    if entry.description.lower().count(f.lower()) > 0:
                        key = entry.description.lower()
                        break
            else:
                key = entry.description.lower()
            if key != None and key in result:
                result[key] += entry.duration
            elif key != None:
                result[key] = entry.duration
        self.convertToHours(result)
        return result

    def getTimesByTag(self):
        result = {}
        for entry in self.entries:
            key = entry.firstTag()
            if key in result:
                result[key] += entry.duration
            else:
                result[key] = entry.duration
        self.convertToHours(result)
        return result

    def getTimesByUser(self):
        result = {}
        for entry in self.entries:
            key = entry.user
            if key in result:
                result[key] += entry.duration
            else:
                result[key] = entry.duration
        self.convertToHours(result)
        return result

    def convertToHours(self, struct):
        iterator = None
        if type(struct) is dict:
            iterator = struct.keys()
        elif type(struct) is list:
            iterator = range(0,len(struct))
        for key in iterator:
            struct[key] = struct[key].seconds/3600.0 \
                + struct[key].days * 24

    @classmethod
    def ParseCSVFile(cls, fileLocation):
        result = TimeLog()
        with open (fileLocation, 'rb') as f:
            reader = csv.reader(f, delimiter=',')
            for line in reader:
                obj = TimeEntry.ParseLine(line)
                if obj != None:
                    result.append(obj)
        return result
    
    @classmethod
    def ParseResponse(cls, struct, result):
        if result == None:
            result = []
        for i in struct:
            result.append(TimeEntry.ParseEntry(i))

def print_dict(dictionary, indent=4):
    print json.dumps(dictionary, indent=indent)

def api(key, params=None):
    apiCall = ""
    if params:
        apiCall = APIConfig().API_PREFIX + key + ".json?" + params
    else:
        apiCall = APIConfig().API_PREFIX + key + ".json"
    return apiCall

def session(headers=None):
    if headers:
        return requests.session(auth=APIConfig().MY_AUTH, headers=headers)
    else:
        return requests.session(auth=APIConfig().MY_AUTH)

def jsonquery(key):
    with session() as r:
        response = r.get(api(key))
        content = response.content
        if response.ok:
            data = json.loads(content)["data"]
            if type(data) is list:
                data.reverse()
            return data
        else:
            exit("Error: Verify credentials in ~/.toggl")

def jsonqueryInterval(key, startdate, enddate):
    midnight = "00:00:00"
    almostMidnight = "23:59:59"
    params = "start_date="+startdate+"T"+midnight+"&end_date="\
        +enddate+"T"+almostMidnight
    with session() as r:
        response = r.get(api(key, params))
        content = response.content
        if response.ok:
            data = json.loads(content)["data"]
            if type(data) is list:
                data.reverse()
            return data
        else:
            exit("Error: Verify credentials in ~/.toggl")















