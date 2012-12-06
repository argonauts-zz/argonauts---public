from datetime import *
from collections import OrderedDict
import csv
import sys
import os

# Index constants for CSV records
DSC = 5
TAG = 12
DUR = 11

def isValid (entry, validTasks):
    """
    This function checks a time entry for a valid task name 
    matching a valid tag. Returns true if valid, false if not.
    entry: A list row from a CSV file representing a time entry
    tasks: A list of valid task,tag pairs 
    """
    desc = entry[DSC].strip().lower()
    tag = entry[TAG].strip().lower()
    for task in validTasks:
       if desc == task[0] and tag == task[1]:
           return True
    return False

def validate (timeLog, taskList):
    """
    This function validates a time log file against a set of
    valid tags and tasks, generating two output files:
    bad_timelog - a CSV file containing all bad time entries
    report_timelog - a CSV file containing any processed metrics
    timeLog: The CSV time log file to validate
    taskList: The text file contaning valid task, tag pairs
    """
    # Create valid task list from taskList file
    valid = [line.strip() for line in open(taskList)]
    valid = [[v.strip().lower() for v in t.split(',')] for t in valid]

    # Create container to hold aggregate time data by WP entry
    WPs = OrderedDict([(k[0], datetime.strptime("00:00:00","%H:%M:%S"))\
                           for k in valid])
    
    # Create container to hold bad time data
    ERs = []

    # Parse time data
    with open (timeLog, 'rb') as f:
        reader = csv.reader(f, delimiter=',')
        for r in reader:
            if isValid(r, valid):
                dur = datetime.strptime(r[DUR],"%H:%M:%S")
                WPs[r[DSC].strip().lower()] += timedelta( \
                    minutes=dur.minute, \
                    seconds=dur.second, \
                    hours=dur.hour)
            else:
                ERs.append(r)
    
    # Write bad time data out to a csv file
    (head, tail) = os.path.split(timeLog)
    with open(head + "/bad_" + tail, 'wb') as f:
        writer = csv.writer(f)
        writer.writerows(ERs)
    
    # Write a time report out to a csv file
    with open(head + "/report_" + tail, 'wb') as f:
        report = [[k.upper(),v.strftime("%H:%M:%S")] for k,v in WPs.iteritems()]
        writer = csv.writer(f)
        writer.writerows(report)

if __name__ == '__main__':
    validate(sys.argv[1], sys.argv[2])
