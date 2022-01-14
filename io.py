#! /usr/bin/env python
import requests,json
from datetime import datetime,timezone,timedelta
from requests.models import HTTPError

url = "https://api.octopus.energy/v1/graphql/"
apikey="" #Y Your Octopus API Key
accountNumber="" # Your Octopus Account Number
deltaOnStartInMinutes=0

dateTimeToUse = datetime.now()
if dateTimeToUse.hour < 17:
    dateTimeToUse = dateTimeToUse-timedelta(days=1)
ioStart = dateTimeToUse.astimezone().replace(hour=23, minute=30, second=0, microsecond=0)
ioEnd = dateTimeToUse.astimezone().replace(microsecond=0).replace(hour=5, minute=30, second=0, microsecond=0)+timedelta(days = 1)

def refreshToken(apiKey,accountNumber):
    try:
        query = """
        mutation krakenTokenAuthentication($api: String!) {
        obtainKrakenToken(input: {APIKey: $api}) {
            token
        }
        }
        """
        variables = {'api': apikey}
        r = requests.post(url, json={'query': query , 'variables': variables})
    except HTTPError as http_err:
        print(f'HTTP Error {http_err}')
    except Exception as err:
        print(f'Another error occurred: {err}')

    jsonResponse = json.loads(r.text)
    return jsonResponse['data']['obtainKrakenToken']['token']

def getObject():
    try:
        query = """
            query getData($input: String!) {
                plannedDispatches(accountNumber: $input) {
                    startDt
                    endDt
                }
            }
        """
        variables = {'input': accountNumber}
        headers={"Authorization": authToken}
        r = requests.post(url, json={'query': query , 'variables': variables, 'operationName': 'getData'},headers=headers)
        return json.loads(r.text)['data']
    except HTTPError as http_err:
        print(f'HTTP Error {http_err}')
    except Exception as err:
        print(f'Another error occurred: {err}')

def getTimes():
    object = getObject()
    return object['plannedDispatches']

def returnPartnerSlotStart(startTime):
    for x in times:
        slotStart = datetime.strptime(x['startDt'],'%Y-%m-%d %H:%M:%S%z')
        slotEnd = datetime.strptime(x['endDt'],'%Y-%m-%d %H:%M:%S%z')
        if(startTime == slotEnd):
            return slotEnd

def returnPartnerSlotEnd(endTime):
    for x in times:
        slotStart = datetime.strptime(x['startDt'],'%Y-%m-%d %H:%M:%S%z')
        slotEnd = datetime.strptime(x['endDt'],'%Y-%m-%d %H:%M:%S%z')
        if(endTime == slotStart):
            return slotEnd

#Get Token
authToken = refreshToken(apikey,accountNumber)
times = getTimes()
timeNow = datetime.now().astimezone()
nextRunStart = ioStart
nextRunEnd = ioEnd
for x in times:
    slotStart = datetime.strptime(x['startDt'],'%Y-%m-%d %H:%M:%S%z')
    slotEnd = datetime.strptime(x['endDt'],'%Y-%m-%d %H:%M:%S%z')
    if slotStart > timeNow:
        #Slot is in the future so start scheduling - check if slot is in the IO period:
        if slotStart < ioStart or slotStart > ioEnd:
            #It is outside our period - is it less than the current nextRunStart
            if slotStart < nextRunStart or nextRunStart < timeNow:
                nextRunStart = slotStart
    if slotEnd > timeNow:
        if slotEnd < ioStart or slotEnd > ioEnd:
            if (slotEnd < nextRunEnd or nextRunEnd < timeNow) or (slotStart == ioEnd and slotEnd < nextRunEnd) or (slotStart == ioEnd and nextRunEnd == ioEnd):
                partnerSlot = returnPartnerSlotEnd(slotEnd)
                if not partnerSlot:
                    nextRunEnd = slotEnd
                else:
                    if partnerSlot != ioStart:
                        nextRunEnd = partnerSlot

nextRunStart -= timedelta(minutes=deltaOnStartInMinutes)

outputJson = {'nextRunStart':nextRunStart , 'nextRunEnd':nextRunEnd, 'timesObj': times, 'updatedAt': dateTimeToUse}
outputJsonString = json.dumps(outputJson, indent=4, default=str)
print(outputJsonString)