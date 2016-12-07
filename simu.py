'''
Created on 19 Aug 2016

@author: romeokienzler
'''
from scipy.integrate import odeint
# import matplotlib.pyplot as plt
import numpy as np
from flask import Flask, Response, redirect, url_for, request, render_template
import os

from cStringIO import StringIO
from rexec import RHooks


import json
import random
import time
import uuid
import ibmiotf.application
import ibmiotf.device
import threading



app = Flask(__name__)

# On Bluemix, get the port number from the environment variable VCAP_APP_PORT
# When running this app on the local machine, default the port to 8080
port = int(os.getenv('VCAP_APP_PORT', 8080))

state="healthy"
sigma = 10.0
rho = 28.0
beta = 8.0 / 3.0
commandId = 0
serviceOptions = []
options = {}
platChoice = 0
error = 'null'


#thread loop to publish data on Watson IOTF
def loop(deviceCli, listArr):

    global options
    global commandId

    while True:
        time.sleep(2)
        for row in listArr:
            if commandId == 1:
                data = { 'data' : str(row) }
                def myOnPublishCallback():
                    print("Confirmed event %s received by IoTF\n" % str(row))

                success = deviceCli.publishEvent("lorenz", "json", data, qos=0, on_publish=myOnPublishCallback)
                if not success:
                    print("Not connected to IoTF")
                time.sleep(1)
                
            elif commandId == 0:
                deviceCli.disconnect()
                return
    return


def Lorenz(state, t):
  # unpack the state vector
  x = state[0]
  y = state[1]
  z = state[2]


  # compute state derivatives
  xd = sigma * (y - x)
  yd = (rho - z) * x - y
  zd = x * y - beta * z

  # return the state derivatives
  return [xd, yd, zd]

#initilise devices on IOTF watson platform
def initiliseDevice():
    
    global options
    global serviceOptions
    global platChoice
    global error

    print "in initDevice"
    def myAppEventCallback(event):
        print("Received live data from %s (%s) sent at %s: data=%s " % (event.deviceId, event.deviceType, event.timestamp.strftime("%H:%M:%S"), data['data'] ))

    print platChoice
    print  serviceOptions[int (platChoice) - 1 ]
    options = (serviceOptions[int (platChoice) - 1 ]).copy()
    print options

    #initilize devicetypeid and deviceid
    rand = random.randrange(1,1000,1)

    InitDeviceTypeId = "TestDeviceType" + str(rand)
    InitDeviceId = "TestDevice" + str(rand)
    InitAuthToken = "password"
    InitAuthMethod = "token"

    # Initialize the application client.
    try:
        
        #appOptions = ibmiotf.application.ParseConfigFromBluemixVCAP()
        appCli = ibmiotf.application.Client(options)
    except Exception as e:
        print(str(e))
        error = str(e)

    print (appCli)

    deviceList = appCli.api.getDevices()
    print deviceList
    deviceTypeNum = deviceList.get('meta')
    print deviceTypeNum
    rows = deviceTypeNum['total_rows']
    print rows

    try:
        apiCli = ibmiotf.api.ApiClient(options)
    except Exception as e:
        print(str(e))
        error = str(e)
        
    print (apiCli)

    if ( rows == None or rows == 0 ):
        deviceNum = createDevice(options, InitDeviceTypeId, InitDeviceId, InitAuthToken)
        print deviceNum
    else:
        results = deviceList['results']
        print results

        status = results[0]
        print status

        deviceTypeId = status['typeId']
        print deviceTypeId

        deviceId = status['deviceId']
        print deviceId
        
        print("\nDeleting an existing device")
        deleted = apiCli.deleteDevice(deviceTypeId, deviceId)
        print("Device deleted = ", deleted)
        time.sleep(5)
        print InitDeviceId
        #create device
        deviceNum = createDevice(options, InitDeviceTypeId, InitDeviceId, InitAuthToken)

    options['type'] = InitDeviceTypeId
    options['id'] = InitDeviceId
    options['auth-method'] = InitAuthMethod
    options['auth-token'] = InitAuthToken

    # Connect and configuration the application
    # - subscribe to live data from the device we created, specifically to "greeting" events
    # - use the myAppEventCallback method to process events
    try:
        appCli.connect()
        appCli.subscribeToDeviceEvents(deviceTypeId, deviceId, "lorenz")
        appCli.deviceEventCallback = myAppEventCallback
    except Exception as e:
        print(str(e))
        error = str(e)

#root function pointing to index.html
@app.route('/')
def root():
    global state
    global serviceOptions
    global platChoice
    global commandId
    global error

    return render_template('index.html', state=state, serviceOptions = serviceOptions, iotplaformChoice = platChoice, dataState = commandId, error = error)

#create devices on watson IOTF platform
def createDevice(options, InitDeviceTypeId, InitDeviceId, InitAuthToken):
    
    global error
    
    try:
        apiCli = ibmiotf.api.ApiClient(options)
    except Exception as e:
        print(str(e))
        
    print (apiCli)

    deviceInfo1 = {"serialNumber": "100087", "manufacturer": "ACME Co.", "model": "7865", "deviceClass": "A", "description": "My shiny device", "fwVersion": "1.0.0", "hwVersion": "1.0", "descriptiveLocation": "Office 5, D Block"}
    metadata1 = {"customField1": "customValue1", "customField2": "customValue2"}
    time.sleep(2)


    deviceTypeId = InitDeviceTypeId
    print("Registering a device type")
    try:
        deviceType = apiCli.addDeviceType( typeId = deviceTypeId, description = "My first device type", deviceInfo = deviceInfo1, metadata = metadata1)

        time.sleep(2)
    except Exception as e:
        print(str(e))

    deviceId = InitDeviceId
    authToken = InitAuthToken
    metadata2 = {"customField1": "customValue3", "customField2": "customValue4"}
    deviceInfo = {"serialNumber": "001", "manufacturer": "Blueberry", "model": "e2", "deviceClass": "A", "descriptiveLocation" : "Bangalore", "fwVersion" : "1.0.1", "hwVersion" : "12.01"}
    location = {"longitude" : "12.78", "latitude" : "45.90", "elevation" : "2000", "accuracy" : "0", "measuredDateTime" : "2015-10-28T08:45:11.662Z"}

    print("\nRegistering a new device")
    try:
        retVal = apiCli.registerDevice(deviceTypeId, deviceId, authToken, deviceInfo, location, metadata2)
    except Exception as e:
        print(str(e))
        error = str(e)
    
    time.sleep(2)

    return retVal

#get watson iotf platform list from VCAP services
def getIotfPlatformList():

    print "in sendIotfList"
    global serviceOptions
    global origServiceOptions
    
    vcap_port = os.getenv('VCAP_APP_PORT')
    vcap_config = os.getenv('VCAP_SERVICES')
    vcap_app_config = os.getenv ('VCAP_APPLICATION')

    print vcap_port
    print vcap_config
    print vcap_app_config

    cred_data = json.loads(vcap_config)
    print(cred_data)
    print len(cred_data)


    index = 0
    iotf_services = {}
    for key, value in cred_data.items():
        if key.startswith('iotf'):
            iotf_services = cred_data[key]

    total_services = len(iotf_services)        
    print "IOTF Services bound with application = ", total_services

    index = 0
    serviceCred = {}

    while index < total_services:

        cred = iotf_services[index] 
        serviceCred['name'] = iotf_services[index]['name']
        serviceCred['org'] = iotf_services[index]["credentials"]['org']
        serviceCred['id'] = iotf_services[index]["credentials"]['apiKey']
        serviceCred['auth-key'] = iotf_services[index]["credentials"]['apiKey']
        serviceCred['auth-token'] = iotf_services[index]["credentials"]['apiToken']
        serviceOptions.append(serviceCred.copy())
        index += 1

    print serviceOptions

#select platform as per user choice
@app.route('/selectPlatform/', methods=['GET'])
def selectPlat():
    global platChoice
    platChoice = request.args.get('selectplat')
    print "Platform choice ", platChoice
    initiliseDevice()
    return redirect("/", code=302)

#stop publishing data on watson iotf platform on STOP command from user
@app.route('/nodata/')
def stopData():
    global commandId
    commandId = 0
    print "no data"
    return str(commandId)

#start publishing data on watson iotf platform on STOP command from user
@app.route('/data/')
def lorenz():
    state0 = [2.0, 3.0, 4.0]
    t = np.arange(0.0, 30.0, 0.01)


    state = odeint(Lorenz, state0, t)
    x = np.array(t)
    x.shape = (3000, 1)

    returnValue = np.concatenate((x, state), axis=1)
    listArr = returnValue.tolist()

    #code for publishing data on IOTF Watson platform
    global commandId

    global options
    global error

    commandId = 1
    try:
        deviceCli = ibmiotf.device.Client(options)
    except Exception as e:
        print("Caught exception connecting device: %s" % str(e))
        error = str(e)


    # Connect and send a datapoint "hello" with value "world" into the cloud as an event of type "greeting" 10 times
    try:
        deviceCli.connect()
    except Exception as e:
        print("Caught exception connecting device: %s" % str(e))
        error = str(e)
 
    threading2 = threading.Thread(target=loop, args=(deviceCli, listArr ) )
    threading2.start()
    return str(commandId)

#set parameters for HEALTHY state
@app.route('/healthy')
def healthy(): 
    global state
    global sigma
    global rho
    global beta 
    state="healthy"
    sigma = 10.0
    rho = 28.0
    beta = 8.0 / 3.0
    return redirect("/", code=302)
  
#set parameters for BROKEN state
@app.route('/broken')
def broken():
    global state
    global sigma
    global rho
    global beta 
    state="broken"
    sigma = 30.0
    rho = 128.0
    beta = 28.0 / 3.0
    return redirect("/", code=302)

@app.route('/test')
def test():
    global sigma
    global rho
    global beta 
    return str(sigma)

#error handling routines
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html', error=error), 500

@app.errorhandler(403)
def page_forbidden(e):
    return render_template('403.html'), 500

#main function
if __name__ == '__main__':
    getIotfPlatformList()
    app.run(host='0.0.0.0', port=port)

