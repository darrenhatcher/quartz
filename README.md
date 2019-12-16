# Basic QRadar Dashboard Item Showing Event Latency
This repository is python (2.x) and Python flask application to implement a basic SIEM dashboard item for IBM QRadar 7.3.1 (and portable for 7.3.2).

## What Is it For?
This dashboard application is useful to watch SIEM log sources and determine if the time for the event is not real-time. It is is most useful for watching log sources from Azure and AWS to detemrine if traffic is delayed (for whatever reason). 

## How do I use?
To use the code, you can either use the IBM App Editor and pull in the code directly, or zip the repository up and import as a zip file locally.

## Once Downloaded ...
Once downloaded and imported, there are things you need to do to use:
* Edit the <code>views.py</code> file and add your SEC token. This is a hexadecimal string you need to create under "Authorised Services" to permit the application to make AQL queries. This looks like <code>DEFAULT_SEC_TOKEN = '1063f153-2140-41dc-87c7-1302462c86ea'</code>
* Edit the <code>views.py</code> file and adjust the variable <code>gLogSourceType = 'Experience%'</code> to your log source filter needed. The default filter is for traffic from the IBM QRadar Experience Centre application.
* If it all installed normally, you should be able to add the dashboard to any of the default workspaces. Look for <b>Custom Dashboards->Latency Dashboard<b>

##If you have problems ...
You will need to look at the log files for the application inside the docker instance it is running as. Log files are created by the application as it goes along, so if the dashboard does not work, to debug the application, log on to the SIEM using <code>ssh</code> and run the command:

<code>docker ps</code> 

Review the output and look for the four digit number in the docker instance. Then use the docker instance of the dashboard (the first column which is a hexadecimal number) and then run:

<code>docker container exec -it \<docker instance\> bash</code>

From there (if successful you should be at the shell prompt), go to the <code>/store/log</code> folder and look at <code>app.log</code> and <code>startup.log</code>.

Notes:
* The code is developed using the version of Python used at the time (2.x in this case), noting that official support for Python 2.x ends 31/12/2019. This is a limitation and nothing the author can do about it.
* You need a working IBM QRadar SIEM to import the code. It should import and operate in the IBM QRadar "community edition" as well as full versions of QRadar.
* If something is broken, add an issue to the github issues tracker and I'll have a look.
