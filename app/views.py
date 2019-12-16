# ------------------------------------------------------------------------------
__author__ = 'Darren Hatcher'

sCSS = '<style>\
    table {\
      border-collapse: collapse;\
      width: 100%;\
    }\
    th {\
      text-align: left;\
      padding: 2px;\
      background-color: #f2f2f2;\
    }\
    td {\
      text-align: left;\
      padding: 2px;\
    }\
    tr:nth-child(even) {background-color: #f2f2f2;}\
    </style>'
sCSSCentre = '<style>\
    #header_table {\
      border-collapse: collapse;\
      width: 100%;\
    }\
    #header_th {\
      text-align: center;\
      padding: 2px;\
      background-color: #f2f2f2;\
    }\
    #header_td {\
      text-align: center;\
      padding: 2px;\
    }\
    tr:nth-child(even) {background-color: #f2f2f2;}\
    </style>'    
# ------------------------------------------------------------------------------

import time
import datetime
import json

from app import app, qpylib, render_template, request
import ConfigParser 

from flask import render_template
from qpylib import qpylib
# ------------------------------------------------------------------------------

gLogSourceType = 'Experience%'
gLogSourcePeriod = ' 1 DAYS'
gLogSourceDivisor = 3600000 # in msec, 3600000=1hour,

gPoll_metrics_query = 'SELECT \
categoryname(category) as "Event", \
MIN((starttime - devicetime)/'+str(gLogSourceDivisor)+') as "MIN_Latency", \
MAX((starttime - devicetime)/'+str(gLogSourceDivisor)+') as "MAX_Latency", \
AVG((starttime - devicetime)/'+str(gLogSourceDivisor)+') as "AVE_Latency", \
STDEV((starttime - devicetime)/'+str(gLogSourceDivisor)+') as "Std_Dev_Latency", \
sum(eventcount) as "Event_Count" \
from events \
where eventcount >= 0 AND logsourcename(logsourceid) ILIKE \''+gLogSourceType+'\' \
GROUP BY "Event" \
ORDER BY "Std_Dev_Latency" DESC \
LAST '+gLogSourcePeriod
    
DEFAULT_SEC_TOKEN = '1063f153-2140-41dc-87c7-1302462c86ea'

# API endpoint for Ariel Database searches
ARIEL_SEARCHES_ENDPOINT = '/api/ariel/searches'
# Timeout to wait until giving up on polling an Ariel search
TIMEOUT_MILLISECONDS = 15000
# JSON headers for all requests
JSON_HEADERS = {}
JSON_HEADERS['content-type'] ='application/json'
JSON_HEADERS['SEC'] = str(DEFAULT_SEC_TOKEN)   
qpylib.log('Set JSON_HEADERS DEFAULT_SEC_TOKEN to: '+JSON_HEADERS['SEC'],'info')
qpylib.log(json.dumps(JSON_HEADERS),'info')

# Response when a request with no response body is successful
SUCCESS_RESPONSE = {'success': 'true'}
# Response when a request with no response body fails
FAILURE_RESPONSE = {'success': 'false'}
# Response when a polling request times out
TIMEOUT_RESPONSE = {'error': 'Query timed out'}
# ------------------------------------------------------------------------------

# build iout the html to send back to the dashboard
def buildResults():
    # get latency metrics list
    
    start = time.time()
    sjResults = pollFoLatencyMetrics()
    end = time.time()

    #firstly, did we get any ? if not
    if sjResults == TIMEOUT_RESPONSE:
        # There are no latency results so return some HTML to say so
        sResults = '<table id=\'tResults\'>'
        sResults += '<tr><th>Latency Response</th><tr>'
        sResults += '<tr><td>Latency metrics not available from the AQL search - timed out. Please check log files.</td></tr>'
        sResults += '<table>'
    
        return sCSS + sResults

    if sjResults == FAILURE_RESPONSE:
        sResults = '<table id=\'tResults\'>'
        sResults += '<tr><th style=\'text-align: center;\'>Latency Response</th><tr>'
        sResults += '<tr><td style=\'text-align: center;\'>Query response failed. Please check <b>app.log</b> log file.</td></tr>'
        sResults += '<table>'
        return sCSS + sResults

    # must be ok ... parse into any results ...

    #work out the units header ...
    if (gLogSourceDivisor/1000) == 3600:
        sUnits=' (hours)'
    else:
        sUnits=''
    
    sResults = '<table id=\'tResults\'>'
    sResults += '<tr><th style=\'font-weight: bold;\'>Event Type</th><th style=\'font-weight: bold;text-align: center;\'>Minimum'+sUnits
    sResults += '</th><th style=\'font-weight: bold;text-align: center;\'>Maximum'+sUnits+'</th><th style=\'font-weight: bold;text-align: center;\'>Average'+sUnits
    sResults += '</th><th style=\'font-weight: bold;text-align: center;\'>Std Deviation'+sUnits+'</th><th style=\'font-weight: bold;text-align: center;\'>Count</th><tr>'

    iCounter = 0
    iTotalElements = 0
    for item in sjResults["events"]: 
        sResultsLine = '<tr>'
        iCounter = iCounter + 1
        
        value0 = item["Event"]
        sResultsLine += '<td>'+value0+'</td>'
        
        value1 = item["MIN_Latency"]
        sResultsLine += '<td style=\'text-align: center;\'>{0:.1f}'.format(value1)+'</td>'
        value2 = item["MAX_Latency"]
        sResultsLine += '<td style=\'text-align: center;\'>{0:.1f}'.format(value2)+'</td>'
        value3 = item["AVE_Latency"]
        sResultsLine += '<td style=\'text-align: center;\'>{0:.1f}'.format(value3)+'</td>'
        value4 = item["Std_Dev_Latency"]
        sResultsLine += '<td style=\'text-align: center;\'>{0:.1f}'.format(value4)+'</td>'
        value5 = item["Event_Count"]
        iTotalElements = iTotalElements + value5
        sResultsLine += '<td style=\'text-align: center;\'>' + '{0:.0f}'.format(value5) + '</td>'
        sResultsLine += '</tr>'
        sResults += sResultsLine
        qpylib.log("Found - "+sResultsLine, 'info')
            
    qpylib.log("Total results: "+str(iCounter), 'info')
    if iCounter == 0:
        #no results so put an empty line in
        sResults += '<tr><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><tr>'
        
    sResults += '</table>'
    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    
    sHeaderNotes = 'Total of <b>'+str(iCounter)
    sHeaderNotes += '</b> results found for log source filter: <b>'+gLogSourceType
    sHeaderNotes += '</b> for the filter period: <b>'+gLogSourcePeriod+'</b>'

    sFooterNotes = 'Last refreshed: <b>'+st+ '</b> - '
    time_taken = end - start
    qpylib.log("Time taken to refresh:"+str(time_taken))
    sTimeTaken = "Time taken to refresh: <b>{0:.2f}</b>".format(time_taken) 

    return sCSS +sResults + sCSSCentre + sHeaderNotes + '<br>' + sFooterNotes + ' ' + sTimeTaken + ' secs ' + ' - Total event count: <b>{0:.0f}</b>'.format(iTotalElements)
    
# ------------------------------------------------------------------------------
#build a Flask app route, this route will build a Json construct, of which there is a 'html' attribute to contain a html string
@app.route('/getLatencyDashboardItem', methods=['GET'])
def getLatencyDashboardItem():
    try:
        qpylib.log("getLatencyDashboardItem>>>")
        sResults = buildResults()
        return json.dumps({'id':'LatencyDashboardItem','title':'Latency Dashboard','HTML':sResults })
        #return json.dumps({'id':'LastOffenseDashBoardItem','title':'Last Offense Dashboard','HTML':render_template('dashboard.html') })
    except Exception as e:
        qpylib.log( "Error "  + str(e) )
        raise
# ------------------------------------------------------------------------------
#@app.route('/pollFoLatencyMetr ics')
def pollFoLatencyMetrics():
    FN_NAME = 'pollFoLatencyMetrics'
    
    qpylib.log('Entered '+FN_NAME,'info')

    # get the results ...
    # firstly get a search ID
    
    qpylib.log(FN_NAME+': Using search:'+gPoll_metrics_query,'info')
    # Parameter of ?query_expression=QUERY
    params = {'query_expression': gPoll_metrics_query}
    # HTTP POST to /api/ariel/searches?query_expression=QUERY
    response = qpylib.REST(
        'POST',
        ARIEL_SEARCHES_ENDPOINT,
        headers=JSON_HEADERS,
        params=params
    ).json()
    time.sleep(0.5) # just in case

    #Check the respoonse code is not 401
    if 'http_response' in response:
        if response['code'] == 401:
            qpylib.log(FN_NAME+': Problem in the response. 401 returned','info')
            return FAILURE_RESPONSE
            # then something wrong
    #else:
    #    qpylib.log(FN_NAME+': Problem with HTTP response. No http response found/returned.','info')
    #    qpylib.log(FN_NAME+': Actual Response: '+json.dumps(response),'info')
    #    return FAILURE_RESPONSE

    # Returns the response
    qpylib.log(FN_NAME+': Search Query ID  Response: '+json.dumps(response),'info')
    
    # We want the field in the JSON ...  "search_id": "10094c6f-6190-419f-9f69-b4743a55ea52",
    qpylib.log(FN_NAME+': Found search ID:'+response['search_id'],'info')
    
    # then poll for the results
    search_id = response['search_id']
    
    # Start time that the polling began at
    init_time = time.time()
    while init_time + TIMEOUT_MILLISECONDS > time.time():
        # While within the timeout
        # Poll with an HTTP GET request to the Ariel searches endpoint specifying
        # a search to retrieve the information of
        # /api/ariel/searches/SEARCH_ID
        response = qpylib.REST(
            'GET',
            '{0}/{1}'.format(ARIEL_SEARCHES_ENDPOINT, search_id),
            headers=JSON_HEADERS
        ).json()
        if 'http_response' in response:
            # If there's an 'http_response' attribute in the response
            # the request has failed, output the response and error
            return json.dumps(response)
        if response['status'] == 'COMPLETED':
            # If the status of the query is COMPLETED, the results can now be retrieved
            # Make an HTTP GET request to the Ariel searches endpoint specifying
            # a search to retrieve the results of
            # /api/ariel/searches/SEARCH_ID/results
            final_response = qpylib.REST(
                'GET',
                '{0}/{1}/results'.format(ARIEL_SEARCHES_ENDPOINT, search_id),
                headers=JSON_HEADERS
            ).json()
            qpylib.log(FN_NAME+': Output for search for search ID:'+response['search_id']+' is :'+json.dumps(final_response),'info')
            # Return the results
            return final_response
            
        # Wait for 1 second before polling again to avoid spamming the API
        time.sleep(1)
    # If the polling has timed out, return an error
    qpylib.log(FN_NAME+': Output for search for search ID:'+response['search_id']+' is :'+TIMEOUT_RESPONSE,'info')
    return TIMEOUT_RESPONSE
#-------------------------------------------------------------------------------