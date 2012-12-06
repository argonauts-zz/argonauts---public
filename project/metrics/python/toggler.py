#!/usr/local/bin/python

from matplotlib.dates import SUNDAY
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
from pylab import \
    figure, WeekdayLocator, DayLocator, DateFormatter, date2num, rcParams
from pytoggl.api import *

rcParams['xtick.major.pad']='15'

TICK_SUNDAYS = WeekdayLocator(SUNDAY)
TICK_ALLDAYS = DayLocator()
FMT_MAJOR = DateFormatter('%b-%d')
FMT_MINOR = DateFormatter('%d')

def graphUtilization(series, seriesIndex, includeMinor=True):
    # Get x-axis intervals
    dates = [date2num(datetime.strptime(k,'%m/%d/%y')) \
                 for k in series.keys() if series[k]['Total'] > 0.0]
    user = APIConfig().getSeries()[seriesIndex]
    # Create figure
    fig = figure(num=None, \
                     figsize=(12, 8), \
                     dpi=80, \
                     facecolor='w',\
                     edgecolor='k')
    fig.suptitle(user, fontsize=20)

    ax = fig.add_subplot(1,1,1)
    intervalData  = \
        [series[k][user + "_util"]\
             for k in series.keys() if series[k]['Total'] > 0.0]
    ax.bar(dates, intervalData, 0.8 ,label='Utilization', color='k')
    ax.axhline(y=1.0/APIConfig().NUM_USERS, \
               label='Target', \
               color='k', ls='--', lw=2, marker=None)
    
    ax.set_title('Utilization (avg = {0:.2f})'.format(\
            sum(intervalData)/len(intervalData)))
    format_date_plot([ax], includeMinor)
    fig.autofmt_xdate()
    return fig

def graphSeries(series, seriesIndex, totalHours, includeMinor=True):

    # Get x-axis intervals
    dates_all = [date2num(datetime.strptime(k,'%m/%d/%y'))\
                 for k in series.keys()]
    dates_cut = [date2num(datetime.strptime(k,'%m/%d/%y')) \
                 for k in series.keys() if series[k]['Total'] > 0.0]
    user = APIConfig().getSeries()[seriesIndex]
    xmax = dates_all[-1]
    xmin = dates_all[0]

    # Create figure
    fig = figure(num=None, \
                     figsize=(12, 8), \
                     dpi=80, \
                     facecolor='w',\
                     edgecolor='k')
    fig.suptitle(user, fontsize=20)

    # SUBPLOT 1
    # Graph user's time data for each interval
    intervalData_all = [series[k][user]\
                        for k in series.keys()]
    intervalData_cut = [series[k][user]\
                        for k in series.keys()\
                        if series[k]['Total'] > 0.0]

    target = totalHours/len(intervalData_all)
    ax1 = fig.add_subplot(2,1,1)
    ax1_hrs = ax1.bar(dates_cut, intervalData_cut, 0.4 ,label='Worked', color='b')
    #ax1_hrs = ax1.plot_date(dates_cut, intervalData_cut, \
    #                            label = 'Worked', \
    #                            color='b', ls='-', marker='o')
    ax1_bar = ax1.axhline(y=target,\
        label="Target ({0:.2f} hrs)".format(target),\
        color='k', ls='--', lw=2, marker=None)
    ax1.set_title("Hours Worked ({0:.2f} hrs)"\
                      .format(sum(intervalData_all)))
    ax1.set_ylabel('Person hours')
    ax1.set_xlim(xmin, xmax)
    
    # SUBPLOT 2
    # Graph user's burndown
    burn = totalHours
    burnData = []
    for d in intervalData_cut:
        burn = (burn - d)
        burnData.append(burn)
    ax2 = fig.add_subplot(2,1,2)
    ax2.plot_date([dates_all[0],dates_all[-1]], \
                       [totalHours - totalHours/len(series), 0], \
                      label='Target',\
                      color="k", ls='--', lw=2, marker=None)
    ax2.plot_date(dates_cut, burnData, \
                      label='Burndown', \
                      color='b', ls='-', marker=None)
    ax2_fit = np.polyfit(dates_cut, burnData, 1)
    ax2_trend = np.poly1d(ax2_fit)
    ax2_remain = ax2_trend(dates_all[-1])
    ax2_zero = datetime.fromordinal(ax2_trend.r).strftime('%b-%d')
    ax2.plot_date(dates_all,ax2_trend(dates_all), \
                      label='Trend: ' + ax2_zero, \
                      color="r", ls='--', lw=2, marker=None)
    ax2.set_ylim(0)

    ax2.set_title('Resource Trajectory ({0:.2f} hrs)'.format(ax2_remain))
    ax2.set_ylabel('Person hours')

    # Format plot areas
    format_date_plot([ax1,ax2], includeMinor)
    fig.autofmt_xdate()
    return fig

def save_to_pdf(figureList, filename):
    pp = PdfPages(filename)
    for figure in figureList:
        figure.savefig(pp, format='pdf')
    pp.close()

def format_date_plot(plotList, includeMinor=True):
    for ax in plotList:
        ax.yaxis.grid(True, 'major')
        ax.xaxis.grid(True, 'minor')
        ax.xaxis.set_major_locator(TICK_SUNDAYS)
        ax.xaxis.set_major_formatter(FMT_MAJOR)
        ax.xaxis.set_minor_locator(TICK_ALLDAYS)
        if includeMinor:
            ax.xaxis.set_minor_formatter(FMT_MINOR)

        ax.tick_params(which='both', width=2)
        ax.tick_params(which='major', length=4)
        ax.legend(loc='best')

def create_report(log,\
                  startDate,\
                  endDate,\
                  out,\
                  reportType='daily',
                  includeMinor=True):

    if log.getSize() == 0:
        print "No Data for {0} to {1}".format(startDate, endDate)
        return

    interval = 1 # one day
    if reportType == 'weekly':
        interval = 7 # seven days
    data = log.getDataSeriesByInterval(startDate, endDate, interval)
    
    userEffort = APIConfig().EFFORT_PER_WEEK/(8.0-interval) * len(data.keys())
    totalEffort = APIConfig().NUM_USERS * userEffort

    fig_list = []
    # Total
    fig_list.append( graphSeries(data, 0, totalEffort, includeMinor))
    # Users
    for i in range(1, len(APIConfig().getSeries())):
        f = graphSeries(data, i, userEffort, includeMinor)
        fig_list.append(f)
        #f = graphUtilization(data, i, includeMinor)
        #fig_list.append(f)
    save_to_pdf(fig_list, out)

if __name__ == '__main__':
    report_iterations = False
    report_spring = False
    log = TimeLog.ParseCSVFile('../csv/toggl.csv')
    if report_iterations:
        create_report(log, '05-06-12', '05-12-12', 'springeosp.pdf')
        create_report(log, '04-15-12', '05-05-12', 'iteration10.pdf')
        create_report(log, '04-01-12', '04-14-12', 'iteration9.pdf')
        create_report(log, '03-18-12', '03-31-12', 'iteration8.pdf')
        create_report(log, '03-04-12', '03-17-12', 'iteration7.pdf')
        create_report(log, '02-12-12', '03-03-12', 'iteration6.pdf')
        create_report(log, '01-15-12', '02-11-12', 'iteration5.pdf')
    if report_spring:
        create_report(log, '01-15-12', '05-12-12',\
                          'spring12.pdf', 'weekly', False)
    #create_report(log, '05-20-12', '05-26-12','week1.pdf')
    #create_report(log, '05-27-12', '06-02-12','week2.pdf')
    #create_report(log, '06-03-12', '06-09-12','week3.pdf')
    create_report(log, '06-10-12', '06-16-12','week4.pdf')
    #create_report(log, '05-22-12', '05-28-12','iteration12.pdf')
    #create_report(log, '05-29-12', '06-04-12','iteration13.pdf')
    
    
    
