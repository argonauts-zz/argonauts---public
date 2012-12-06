'''
Created on Jun 9, 2012

@author: mjlenzo
'''
from collections import OrderedDict
import getpass
from github import Github
from github import Repository
from github import Organization
from github import Issue
from datetime import *
from pytz import timezone

from matplotlib.dates import MONDAY
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
from pylab import \
    figure, WeekdayLocator, DayLocator, DateFormatter, date2num, rcParams

rcParams['xtick.major.pad']='15'

TICK_MONDAY = WeekdayLocator(MONDAY)
TICK_ALLDAYS = DayLocator()
FMT_MAJOR = DateFormatter('%b-%d')
FMT_MINOR = DateFormatter('%d')

defects = ['Req. Defect', 'Arch. Defect', 'Design Defect', 'Code Defect']
eastern = timezone('US/Eastern')
utc = timezone('UTC')
enoc = None
argo = None
git = None
issues = []

def init(userName, password):
    git = Github(userName, password)
    for org in git.get_user().get_orgs():
        if org.name == "EnerNOC, Inc.":
            enoc = org
            argo = enoc.get_repo('argo')
    for issue in argo.get_issues(state="Open"):
        issues.append(issue)
    for issue in argo.get_issues(state="Closed"):
        issues.append(issue)
    

def getIssues(startDate, endDate, tag=None):
    startDate = startDate + "/00:00:00"
    endDate = endDate + "/23:59:59"
    active_issues = OrderedDict()
    start_loc = eastern.localize(datetime.strptime(startDate,'%m-%d-%y/%H:%M:%S')) 
    end_loc = eastern.localize(datetime.strptime(endDate,'%m-%d-%y/%H:%M:%S')) 
    
    end_utc = end_loc.astimezone(utc)
    start_utc = start_loc.astimezone(utc)
    
    while start_utc <= end_utc:
        interval_start_utc = start_utc
        interval_end_utc = interval_start_utc + timedelta(hours=23,minutes=59, seconds=59)
        #print "from " + str(interval_start_utc.astimezone(eastern)) + " to " + str(interval_end_utc.astimezone(eastern))
        issue_list = []
        for issue in issues:
            created_at_utc = utc.localize(issue.created_at)
            closed_at_utc = None if issue.closed_at is None\
                else utc.localize(issue.closed_at)
            labelList = [label.name for label in issue.labels\
                         if label.name == tag]
            if tag == None:
                labelList.append("all")
            if len(labelList) > 0 and created_at_utc <= interval_end_utc:
                if closed_at_utc is None or closed_at_utc <= interval_end_utc:
                    issue_list.append(issue)
                    #print issue.title + " created:" + str(created_at_utc.astimezone(eastern)) + " " + issue.state     
        start_utc += timedelta(days=1)
        key = datetime.strftime(interval_start_utc.astimezone(eastern),'%m-%d-%y')
        active_issues[key] = issue_list  
    return active_issues

def format_date_plot(plotList, includeMinor=True):
    for ax in plotList:
        ax.yaxis.grid(True, 'major')
        ax.xaxis.grid(True, 'minor')
        ax.xaxis.set_major_locator(TICK_MONDAY)
        ax.xaxis.set_major_formatter(FMT_MAJOR)
        ax.xaxis.set_minor_locator(TICK_ALLDAYS)
        if includeMinor:
            ax.xaxis.set_minor_formatter(FMT_MINOR)

        ax.tick_params(which='both', width=2)
        ax.tick_params(which='major', length=4)
        ax.legend(loc='best')

def graphIssues(issueRegister, title):
    series_dates = [date2num(datetime.strptime(k,'%m-%d-%y'))\
             for k in issueRegister.keys()]
    series_NumOpen = []
    series_NumClosed = []
    series_NumRemain = []
    for k in issueRegister.keys():
        numOpen = 0
        numClosed = 0
        for issue in issueRegister[k]:
            numOpen = numOpen + 1  
            if issue.state == 'closed':
                numClosed = numClosed + 1
        series_NumOpen.append(numOpen)
        series_NumClosed.append(numClosed)
        series_NumRemain.append(numOpen - numClosed)
        
    # Create figure
    fig = figure(num=None, \
                 figsize=(12, 8), \
                 dpi=80, \
                 facecolor='w',\
                 edgecolor='k')
    ax1 = fig.add_subplot(1,1,1)
    ax1.set_title(title)
    ax1.plot_date(series_dates, series_NumOpen, \
                  label = 'Issues Opened', \
                  color='red', ls='-', marker='o')
    ax1.plot_date(series_dates, series_NumClosed, \
                  label = 'Issues Closed', \
                  color ='black', ls='-', marker='x')
    ax1.bar(series_dates, series_NumRemain, 0.4 ,label='Remaining', color='grey')
    
    # Format plot areas
    format_date_plot([ax1])
    fig.autofmt_xdate()
    return fig
 
def graphContainment(issueRegister, title):
    """
    Phase Containment Effectiveness:
    - Requirements Analysis
    - Architecture Design
    - ADEW/Prototyping/Experimentation
    - Detailed Design
    - Detailed Design Review
    - Implementation
    - Unit/Integration Testing
    - Architectural Verification
    """
    series_reqPhase = []
    series_archPhase = []
    series_ADEWPhase = []
    series_expPhase = []
    series_designPhase = []
    series_reviewPhase = []
    series_implPhase = []
    series_testPhase = []
    series_verificationPhase = []
    
    for k in issueRegister.keys():
        reqPhase = 0
        archPhase = 0
        ADEWPhase = 0
        expPhase = 0
        designPhase = 0
        reviewPhase = 0
        implPhase = 0
        testPhase = 0
        verificationPhase = 0
        for issue in issueRegister[k]:
            labelList = [label.name for label in issue.labels]
            if 'Req. Defect' in labelList:
                reqPhase = reqPhase + 1
            elif 'Arch. Defect' in labelList:
                archPhase = archPhase + 1
                
    
def save_to_pdf(figureList, filename):
    pp = PdfPages(filename)
    for figure in figureList:
        figure.savefig(pp, format='pdf')
    pp.close()

if __name__ == '__main__':
    userName = getpass.getpass("Username:")
    password = getpass.getpass("Password:")
    init(userName, password)
    all = getIssues('05-22-12','06-18-12')
    arch = getIssues('05-22-12','06-18-12', "Arch. Defect")
    design = getIssues('05-22-12','06-18-12', "Design Defect")
    code = getIssues('05-22-12','06-18-12', "Code Defect")
    fig1 = graphIssues(arch, 'Arch. Defects')
    fig2 = graphIssues(design, 'Design Defects')
    fig3 = graphIssues(code, 'Code Defects')
    #fig4 = graphContainment(all, 'Phase Containment')
    save_to_pdf([fig1,fig2,fig3], "out.pdf")
    
    