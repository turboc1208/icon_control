#####################################################
#
#  Icon_Control.py
#
#  Set image on icon to show state.
#
#  Version  Date       Person      Description
#   0.2     24JUL2017  CC          First push from new server        
#
#  Install:
#
#  Download the pictures you want.  Green, Yellow and Red icon images 
#  are available in this repository.  
#  Place them in the .homeassistant/www directory.  Create the www directory if its not there.
#  Put the Icon_control.py app in your appdaemon code storage directory.
#  Add the app to your appdaemon.cfg file as follows
#
#  [icon_control]
#  module=icon_control
#  class=icon_control
#
#  Setup the self.entities JSON string below as follows All non-numeric values must be in double quotes
#  entities={"sensor.upstairs_sensor_battery":{"attribute":"state",
#                                               "levels":{"1":{"value":25,"img":"/local/icon1.jpg"},
#                                                     "2":{"value":50,"img":"/local/icon2.jpg"},
#                                                     "3":{"value":75,"img":"/local/icon3.jpg"},
#                                                     "4":{"value":100,"img":"/local/icon4.jpg"}},
#                                               "notify":"EmailChip"},
#           "light.office_light_level":{"attribute":"state",
#                                               "levels":{"0":{"value":0,"img":"/local/light_off.jpg},
#                                                     "2":{"value":64,"img":"/local/light_dim.jpg"},
#                                                     "3":{"value":128,"img":"/local/light_med.jpg"},
#                                                     "4":{"value":255,"img":"/local/light_bright.jpg"}},
#                                             "notify":"EmailChip"}}
#       
#######################################################
import appdaemon.plugins.hass.hassapi as hass
import datetime
import time
import json
               
class icon_control(hass.Hass):

  def initialize(self):
    # self.LOGLEVEL="DEBUG"
    self.log("icon_control App")
    self.entities={"empty":"list"}
    if "entities" in self.args:
      e_data=""
      e_data=self.args["entities"]
      self.entities=json.loads(e_data)
    else:
      self.log("error entities must be specified in appdaemon.cfg")
    self.log("entities={}".format(self.entities))
    if "interval" in self.args:
      interval=self.args["interval"]
    else:
      interval=5
    for s in self.entities:
      self.listen_state(self.state_handler,s,attribute=self.entities[s]["attribute"])
    self.check_icon_state()
    self.run_every(self.timer_handler,self.datetime(),interval*60)
    self.log("icon_control initialization complete")

  def timer_handler(self,kwargs):
    self.log("timer Check")
    self.check_icon_state()
     
  def state_handler(self,entity,attribute,old,new,kwargs):
    currentpic=self.get_state(entity,attribute="entity_picture")
    if currentpic==None:
      self.check_icon_state(e=entity)
   
  def check_icon_state(self,**kwargs):
    blist=[]
    if "e" in kwargs:
      blist.append(kwargs["e"])
    else:   
      for b in self.entities:
        blist.append(b)
    for b in blist:
      s=self.entities[b]["attribute"]
      result=self.get_state(b,attribute=s)
      self.log("Entity {} is at {}%".format(b,result))
      if (result==None) or (result=="") or (result=="unknown") :
        self.log("Entity {} returned None skipping".format(b))
        continue
      self.log("entities[{}]['levels']={}".format(b,self.entities[b]))
      for level in sorted(self.entities[b]["levels"]):
        self.log("level={} result={}, level[value]={}".format(level,result,self.entities[b]["levels"][level]["value"]))
        if int(float(result))<=self.entities[b]["levels"][level]["value"]:
          self.set_state(b,attributes={"entity_picture":self.entities[b]["levels"][level]["img"]})
          break
      self.log("level={}".format(level))
      if level==len(self.entities[b]["levels"]):    
        msg="{} icon is at {}%.  Please replace/recharge the entities".format(b,result)
        if not "last_notification" in self.entities[b]:
          self.entities[b]["last_notification"]=self.date()-datetime.timedelta(days=1)
        if self.entities[b]["last_notification"]<self.date():
          self.entities[b]["last_notification"]=self.date()
          if "notify" in self.entities[b]:
            try:
              self.log("Sending entity alert for {} to {}".format(b,self.entities[b]["notify"]))
              self.notify(msg,name=self.entities[b]["notify"],title="low entity warning")
            except:
              self.log("{} notify failed {}".format(b,self.entities[b]["notify"]))
              pass
