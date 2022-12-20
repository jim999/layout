#--------------------------------------------------------------------------
#
# Class returnSettings are the base functions inhereted from all train
# profiles. 
#
# This class should not be called or created directly and should only be 
# used in conjunction with a object profile
#
#--------------------------------------------------------------------------
import random

#import layout_definitions

class trainDefaultProfileSettings():

    def __init__(self):

       self.throttle               = None
       self.sensorManager          = None
       throttleNumLong             = True

       self.startupSequence        = {}
       self.stopSequence           = {}
#-----------------------------------------------------------------------------------
# Function key mapings for shunt3162
#
#----------------------------------------------------------------------------------
class shunt3026(trainDefaultProfileSettings):
    def __init__(self):

       trainDefaultProfileSettings.__init__(self)

       self.description                = "Shunt3026 train"
       self.lights                     = "F0"
       self.sound                      = "F1"
       self.long_horn                  = "F2"
       self.short_horn                 = "F3"
       self.break_release              = "F4"
       self.buffer_clash_coupling      = "F5"                                            # On buffer clash, off coupling
       self.cab_door                   = "F8"
       self.dispatch_whistle_ack       = "F9"                                            # On dispatch whustle, off driver ack
       self.flange                     = "F10"
       self.compressor                 = "F11"
       self.air_cylinder               = "F12"
       self.rail_clack                 = "F13"
       self.fade                       = "F14"
       self.cab_lights                 = "F15"
       self.direction_lights           = "F16"                                           # F0,F6,F7 must be off

       self.key_text                   = {"F0" :"lights",
                                          "F1" :"sound",
                                          "F2" :"long horn","F3":"short horn",
                                          "F4" :"break release",
                                          "F5" :"buffer clash/couple",
                                          "F8" :"Cab door open/close",
                                          "F9" :"dispatch whistle/acknowledge",
                                          "F10":"flange",
                                          "F11":"compressor",
                                          "F12":"air cylinder",
                                          "F13":"rail clack",
                                          "F14":"fade",
                                          "F15":"cab lights",
                                          "F16":"direction lights" }
       #
       # key to press with time to wait before pressing the key and the length of time the key should be on before
       # turning it on. 
       #
       #     Note  : if a key has toggle set the off time will not affect it. 
       #     Note  : if the off time is <0 then it is never turrned off
       #
       self.startupSequence            = ({self.cab_door:(0,2)},{self.cab_lights:(1,0)},
                                          {self.fade:(0,0)},{self.sound:(3,0)},
                                          {self.sound:(0,0)},
                                          {self.lights:(0,1)},{"F6":(0,1)},{"F7":(0,1)},
                                          {self.direction_lights:(1,0)},
                                          {self.dispatch_whistle_ack:(3,1)},
                                          {self.flange:(1,0)},
                                          {self.break_release:(1,1)}
                                         )
       self.stopSequence               = ({self.sound:(1,0.1)},
                                          {self.direction_lights:(0,1)},
                                          {self.cab_lights:(15,1)},
                                          {self.cab_door:(2,3)},
                                          {self.flange:(1,1)},
                                          {self.fade:(1,0.1)}
                                         )

       self.key_seq_1                  = ({self.short_horn:(0,0.5)},{self.long_horn:(0.0,1)})
       self.key_seq_2                  = self.key_seq_1
       self.key_seq_3                  = ({},)

       self.throttleNumLong            = True
       self.throttleNumber             = 3026
#-----------------------------------------------------------------------------
# Shunt8691

#
#----------------------------------------------------------------------------
class shunt8691(trainDefaultProfileSettings,shunt3026):
      def  __init__(self):

       trainDefaultProfileSettings.__init__(self)

       self.description                 = "Shunt8691 train"
       self.lights                     = "F0"
       self.sound                      = "F1"
       self.long_horn                  = "F2"
       self.short_horn                 = "F3"
       self.break_release              = "F4"
       self.buffer_clash_coupling      = "F5"                                            # On buffer clash, off coupling
       self.direction_lights           = "F6"
       self.cab_door                   = "F8"
       self.dispatch_whistle_ack       = "F9"                                            # On dispatch whustle, off driver ack
       self.flange                     = "F10"
       self.compressor                 = "F11"
       self.air_cylinder               = "F12"
       self.rail_clack                 = "F13"
       self.fade                       = "F14"
       self.cab_lights                 = "F15"

       self.key_text                   = {"F0" : "lights",
                                          "F1" : "sound",
                                          "F2" : "long horn","F3":"short horn",
                                          "F4" : "break reelease",
                                          "F5" : "buffer clash/couple",
                                          "F6" : "direction lights",
                                          "F8" : "Cab door open/close",
                                          "F9" : "dispatch whistle/acknowledge",
                                          "F10": "flange",
                                          "F11": "compressor",
                                          "F12": "air cylinder",
                                          "F13": "rail clack",
                                          "F14": "fade",
                                          "F15": "cab lights",
                                          "F16": "direction lights" }

       self.startupSequence            = ({self.cab_door:(0,2)},{self.cab_lights:(1,0)},
                                          {self.sound:(3,0)},
                                          {self.direction_lights:(1,0)},
                                          {self.dispatch_whistle_ack:(3,2)},
                                          {self.flange:(1,0)},
                                          {self.break_release:(1,1)}
                                         )
       self.stopSequence               = ({self.flange:(0,2)},
                                          {self.sound:(1,1)},
                                          {self.direction_lights:(1,1)},
                                          {self.cab_lights:(10,1)},
                                          {self.cab_door:(2,3)}
                                         )

       self.key_seq_1                  = ({self.short_horn:(0,1)},{self.long_horn:(0.0,1)})
       self.key_seq_2                  =  self.key_seq_1 # ({},)
       self.key_seq_3                  = ({self.dispatch_whistle_ack:(0,1)},{self.dispatch_whistle_ack:(0,1)})

       self.throttleNumLong            = True
       self.throttleNumber             = 8691


#-----------------------------------------------------------------------------
# Flaying scottsman definitions
#-----------------------------------------------------------------------------
class scottsman(trainDefaultProfileSettings):
      def  __init__(self):
           trainDefaultProfileSettings.__init__(self)

#           shunt8691.__init__(self)

           self.description             = "Flying Scottsman"
           self.throttleNumber         = 103
           self.throttleNumLong        = True


           self.startupSequence        = {}
           self.stopSequence           = {}
#-----------------------------------------------------------------------------
# Shunt8691
#
#----------------------------------------------------------------------------
class engine4035(trainDefaultProfileSettings,shunt3026):
      def  __init__(self):

       trainDefaultProfileSettings.__init__(self)

       self.description                 = "Engine 4035 train"
       self.lights                     = "F0"
       self.sound                      = "F1"
       self.high_tone_horn             = "F2"
       self.low_tone_horn              = "F3"
       self.break_release              = "F4"
       self.buffer_clash_coupling      = "F5"                                            # On buffer clash, off coupling
       self.direction_lights           = "F6"
       self.cab_door                   = "F8"
       self.dispatch_whistle_ack       = "F9"                                            # On dispatch whustle, off driver ack
       self.flange                     = "F10"
       self.compressor                 = "F11"
       self.air_cylinder               = "F12"
       self.driver_hold                = "F13"
       self.cab_lights_driver_end      = "F14"
       self.cab_lights_non_driver_end  = "F15"
       self.fade                       = "F16"

       self.key_text                   = {"F0" : "lights",
                                          "F1" : "sound",
                                          "F2" : "high tone horn",
                                          "F3" : "low tone horn",
                                          "F4" : "break release",
                                          "F5" : "buffer clash/couple",
                                          "F6" : "direction lights",
                                          "F8" : "Cab door open/close",
                                          "F9" : "dispatch whistle/acknowledge",
                                          "F10": "flange",
                                          "F11": "compressor",
                                          "F12": "air cylinder",
                                          "F13": "driver hold",
                                          "F14": "cab lights driver end",
                                          "F15": "cab lights non driver end",
                                          "F16": "fade" }


       self.startupSequence            = ({self.cab_door:(0,2)},{self.cab_lights_driver_end:(1,0)},
                                          {self.sound:(3,0)},
                                          {self.lights:(0,0.1)},
                                          {self.dispatch_whistle_ack:(3,1)},
                                          {self.flange:(0,0)},
                                          {self.break_release:(1,1)}
                                         )
       self.stopSequence               = ({self.flange:(0,2)},
                                          {self.sound:(0,2)},
                                          {self.cab_lights_driver_end:(10,1)},
                                          {self.cab_door:(2,3)}
                                         )

       self.key_seq_1                  = ({self.high_tone_horn:(0,0.5)},{self.low_tone_horn:(1.0,0.5)})

       self.throttleNumLong            = True
       self.throttleNumber             = 4035
