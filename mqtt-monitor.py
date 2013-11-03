#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim tabstop=4 expandtab shiftwidth=4 softtabstop=4

#
# mmqtt-monitor
#    P
#


__author__ = "Dennis Sell"
__copyright__ = "Copyright (C) Dennis Sell"


APPNAME = "mqtt-monitor"
VERSION = "0.11"
WATCHTOPIC = "/raw/" + APPNAME + "/command"

import os
import sys
import time
import logging
import threading
from daemon import Daemon
from mqttcore import MQTTClientCore
from mqttcore import main


class MyMQTTClientCore(MQTTClientCore):
    def __init__(self, appname, clienttype):
        MQTTClientCore.__init__(self, appname, clienttype)
        self.clientversion = VERSION
        self.watchtopic = WATCHTOPIC
        self.monitorlist = self.cfg.MONITOR_LIST
        self.interval = self.cfg.INTERVAL
        self.pause = self.cfg.PAUSE
        self.clientversion = VERSION
        self.response = {}

        self.t = threading.Thread(target=self.do_thread_loop)

    def on_connect(self, mself, obj, rc):
        MQTTClientCore.on_connect(self, mself, obj, rc)
        self.mqttc.subscribe( "/clients" + "/+/ping", 2)
        self.t.start()

    def on_message(self, mself, obj, msg):
        MQTTClientCore.on_message(self, mself, obj, msg)
        if (msg.topic == self.clientbase + "ping"):
            pass  #ugly here TODO
        else:
            topic = msg.topic.split("/")
            if (( topic[1] == "clients" ) and ( topic[3] == "ping") and ( msg.payload == "response" )):        
                self.response[topic[2]] = True
                print "reponse from ", topic[2]

    def do_thread_loop(self):
        while ( self.running ):
            if ( self.mqtt_connected ):    
                for client in self.monitorlist:
                    self.response[client] = False
                    print "Pinging ", client
                    self.mqttc.publish( "/clients/" + client + "/ping", "request", qos=0, retain=0 )
                time.sleep(self.pause)
                #self.mqttc.publish("/raw/mqtt-monitor/status", "", qos=2, retain=True)
                for client in self.monitorlist:
                    if self.response[client] == False:
                        print "No reponse from ", client
                        self.mqttc.publish( "/raw/mqtt-monitor/status", "Client " + client + " is no longer responding.", qos=2, retain=False )
                if ( self.interval ):
                    print "Waiting ", self.interval, " minutes for next update."
                    time.sleep(self.interval*60)
            pass


class MyDaemon(Daemon):
    def run(self):
        mqttcore = MyMQTTClientCore(APPNAME, clienttype="single")
        mqttcore.main_loop()


if __name__ == "__main__":
    daemon = MyDaemon('/tmp/' + APPNAME + '.pid')
    main(daemon)
