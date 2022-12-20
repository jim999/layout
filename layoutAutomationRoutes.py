#import layout_definitions

import random
import sys
if sys.platform.startswith('java'):
   import jmri
#FORWARD=layout_definitions.FORWARD
#REVERSE=layout_definitions.REVERSE
#===================================================================================
# Classes to define routes in the system
#
# Note : The route manage only deals with sensors define in the sensor table 
#
#
#==================================================================================
#class automationRoutesBaseClass(jmri.jmrit.automat.AbstractAutomaton) :
class automationRoutesBaseClass():
   #----------------------------------------------------------------------------------------
   # Dummy entries -  DO NOT CHANGE
   #----------------------------------------------------------------------------------------
   def __init__(self):

       self.routeDescription         = "dummy" 
       self.lookAhead                = 99999                                                   # Number of blocks to look ahead
       self.route_loops              = 1
       self.routeName                = "dummy"

       self.fwdCompleteSensor        = None                                                    # Forward route complete sensor
       self.revCompleteSensor        = None                                                    # Reverse route complete sensor
       self.fwdWaitTimeDefault       = 1                                                       # Time in seconds to wait before doing the next loop
       self.revWaitTimeDefault       = 2                                                       # Time in seconds to wait before doing the next loop
       self.appSpeedDefault          = 0
       self.revAppSpeedDefault       = 0.00
       self.fwdAppSpeedDefault       = 0.00
       self.maxSpeed                 = 1.0                                                     # The maximum speed for this route
       self.fwdStartSpeedDefault     = 0.10                                                    # Speed to start at if in the forward direction
       self.revStartSpeedDefault     = 0.10                                                    # Speed to start at if in the reverse direction
       self.revWaitTimeByTrain       = {}                                                      # Time to wait before doing a reverse cycle
       self.fwdWaitTimeByTrain       = {}                                                      # Time to wait before doing a forward cycle

       self.fwdStartSpeedByTrain     = {}                                                      # Default start speed for a particular train
       self.revStartSpeedByTrain     = {}
       self.revSpeedSensorsByTrain   = {}                                                      # If these block sensors get booked then wait on these sensors going active to set the speed
       self.fwdSpeedSensorsByTrain   = {}                                                      # If these block sensors get booked then wait on these sensors going active to set the speed
       self.fwdAppStopSensorsByTrain = {}                                                      # If we cannot book the next block then these are the stop sensors
       self.revAppStopSensorsByTrain = {}
       self.fwdKeySensorsByTrain     = {}                                                      # if these block sensors get booked then wait on these sensors going active and run the
       self.revKeySensorsByTrain     = {}
       self.fwdWaitSensorsByTrain    = {}                                                      # if these block get booked then wait on these sensors going active, go to idle
       self.revWaitSensorsByTrain    = {}

       self.routePathBlocks          = ()                                                      # Flow of train through the blocks
       self.routePathSensors         = ()                                                      # Sensors for each block (Same order as routePathBlocks)
       self.turnouts                 = {}                                                      # Turnout positions when block is booked
       self.signals                  = {}                                                      # Signals to be set
       self.fwdSignals               = {} 
       self.revSignals               = {} 
       
#import layout_automation_routes_base_class
#-----------------------------------------------------------------------------------
#
# Class  :  define a route. Inherits methods from automationRoutesBaseClass
#
#           move on test track from block 1 through block 2 to block 3
#
#-----------------------------------------------------------------------------------
class testRoute1(automationRoutesBaseClass) :
   def __init__(self,routeDescription=None,routeName=""):
       self.init()
   def init(self):
       #----------------------------------------------------------------------------------------
       # Required section
       #---------------------------------------------------------------------------------------
       automationRoutesBaseClass.__init__(self)
       #
       # All definitions refer to the direction an engine travels along a route the route_direction setting
       #
       self.lookAhead                = 1
       self.routeDescription         = "move from block 1 through block 2 to block 3"
       self.routeName                = "test Route 1"


       self.fwdCompleteSensor        = "MS:PS:PS01_13"                                        # Forward route complete sensor
       self.revCompleteSensor        = "MS:PS:PS01_14"                                        # Reverse route complete sensor
       self.revWaitTimeDefault       = 2.0                                                    # Time in seconds to wait before doing the next loop
       self.fwdWaitTimeDefault       = 2.0                                                    # Time in seconds to wait before doing the next loop
       self.appSpeedDefault          = 0.05                                                   # Speed to go to if block ahead is active
       self.revStartSpeedDefault     = 0.1
       self.fwdStartSpeedDefault     = 0.1
       self.maxSpeed                 = 0.3

       self.routePathBlocks          = ("BL1"  , "BL2"  , "BL3")                              # Flow of train through the blocks (Forward direction)
       self.routePathSensors         = ("MS:BS:BS01_35",'MS:BS:BS01_34',"MS:BS:BS01_39")      # Sensors for each block (Same order as routePathBlocks)

       self.turnouts                 = {"MS:BS:BS01_34" :{"MT:TO:TO01_4" :"CLOSED",
                                                          "MT:TO:TO01_21":"OPEN"},
                                       }                                                      # Turnout positions when these blocks are booked

       self.fwdSignals               = {'MS:BS:BS01_34':(('MA01_4' ,),('MA01_22',)),
                                        'MS:BS:BS01_39':(('MA01_5' ,),('MA01_21',))}          # if in these blocks get booked then set the signal green and red
                                                                                              # {block_sensor:(greensignals),(redsignals),}
       self.revSignals               = {'MS:BS:BS01_34':(('MA01_21',),('MA01_5' ,)),
                                        'MS:BS:BS01_35':(('MA01_22',),('MA01_4' ,))}          # if in these blocks get booked  then set the signal green,red

       self.fwdWaitTimeByTrain       = {"shunt3026":0,"shunt8691":2}                          # Time to wait between loops by train in seconds when in forward direction
       self.revWaitTimeByTrain       = {"shunt3026":0,"shunt8691":2}                          # Time to wait between loops by train in seconds when in reverse direction

       self.fwdStartSpeedByTrain     = {"shunt3026":0.35,"shunt8691":0.35}                    # Default start speed for a particular train
       self.revStartSpeedByTrain     = {"shunt3026":0.25,"shunt8691":0.26}

       self.fwdSpeedSensorsByTrain   = {"shunt3026":{"MS:BS:BS01_35"  :{"MS:PS:PS01_14" :0.10},
                                                    },
                                        "shunt8691":{"MS:BS:BS01_34"  :{"MS:BS:BS01_34" :0.10},
                                                     "MS:BS:BS01_39"  :{"MS:BS:BS01_39" :0.23}
                                                    }
                                       }                                                      # If these block sensors for these trains get booked then wait on these sensors going active
                                                                                              # to set the speed
       #self.fwdSpeedSensorsByTrain   = {}
       self.revSpeedSensorsByTrain   = {"shunt3026":{"MS:BS:BS01_35"  :{"MS:BS:BS01_35" :0.10},
                                                     "MS:BS:BS01_34"  :{"MS:BS:BS01_34" :0.06},
                                                    },
                                        "shunt8691":{"MS:BS:BS01_35"  :{"MS:BS:BS01_35"  :0.2 },
                                                     "MS:BS:BS01_34"  :{"MS:BS:BS01_34"  :0.05},
                                                    }
                                       }                                                      # If these block sensors get booked then wait on these sensors going active
                                                                                              # to set the speed

       #self.revSpeedSensorsByTrain   = self.fwdSpeedSensorsByTrain                            # If these block sensors get booked then wait on these sensors going active
                                                                                              # to set the speed

       self.fwdAppStopSensorsByTrain = {"shunt8691":{"MS:BS:BS01_35" :{"MS:PS:PS01_5" : 0.03},
                                                     "MS:BS:BS01_39" :{"MS:PS:PS01_5" : self.appSpeedDefault}
                                                    }
                                       }                                                      # If we cannot book the next block then these are the stop sensors for the last block in the
                                                                                              # current booked subroute. If no stop sensors defined then stop and wait for next block to clear.

       self.revAppStopSensorsByTrain = {"shunt8691":{"MS:BS:BS01_35":{"MS:PS:PS01_5":self.appSpeedDefault}
                                                    }
                                       }

       self.revWaitSensorsByTrain    = {"shunt8691":{"MS:BS:BS01_35"  :{"MS:BS:BS01_35":5}
                                                    }
                                       }                                                      # if these blocks/block sensors get booked then wait on these sensors going active, go to idle
                                                                                              # and wait for the specified seconds

       self.fwdWaitSensorsByTrain   = {}                                                      # it these sensors are activated then go to idel and wait fo n seconds

       self.fwdKeySensorsByTrain     = {"shunt3026":{"MS:BS:BS01_35" :{"MS:PS:PS01_14" :("key_seq_1",),
                                                                       "MS:PS:PS01_5"  :("key_seq_2",)},
                                                     "MS:BS:BS01_39" :{"MS:PS:PS01_13" :("key_seq_1",)}
                                                    },
                                        "shunt8691":{"MS:BS:BS01_35" :{"MS:PS:PS01_14" :("key_seq_3",),
                                                                       "MS:PS:PS01_5"  :("key_seq_2",)},
                                                     "MS:BS:BS01_39" :{"MS:PS:PS01_13" :("key_seq_1",)}
                                                    }
                                       }                                                      # if these blocks (sensors) get booked then wait on these sensors going active 
                                                                                              # and run the train key sequence.
       self.revKeySensorsByTrain     = {"shunt8691":{"MS:BS:BS01_35" :{"MS:PS:PS01_14"  :("key_seq_3",),
                                                                       "MS:PS:PS01_13"  :("key_seq_2",)}
                                                    }
                                       }                                                      # if these blocks (sensors) get booked then wait on these sensors going active
                                                                                              # and run the train key sequence.

#-----------------------------------------------------------------------------------
#
# Class  :  define a route. Inherits methods from automationRoutesBaseClass
#
#           move on test track from block 1 through block 2 to block 3
#
#-----------------------------------------------------------------------------------
class testRoute2(automationRoutesBaseClass) :
   def __init__(self,routeDescription=None,routeName=""):
       self.init()
   def init(self):
       #----------------------------------------------------------------------------------------
       # Required section
       #---------------------------------------------------------------------------------------
       automationRoutesBaseClass.__init__(self)

       #
       # All definitions refer to the direction an engine travels along a route the route_direction setting
       #
       self.lookAhead                = 1
       self.routeDescription         = "move from block 5 through block 2 to block 1"
       self.routeName                = "test Route 2"
       self.maxSpeed                 = 0.5
       self.revWaitTimeDefault       = 0                                                      # Time in seconds to wait before doing the next loop
       self.fwdWaitTimeDefault       = 1                                                      # Time in seconds to wait before doing the next loop
       self.appSpeedDefault          = 0.05                                                   # Speed to go to if block ahead is active
       self.revStartSpeedDefault     = 0.10
       self.fwdStartSpeedDefault     = 0.1
       self.fwdStartSpeedByTrain     = {"shunt3026":0.20}                                     # Default start speed for a particular train or use the default
       self.revStartSpeedByTrain     = {"shunt3026":0.15}
       self.fwdCompleteSensor        = "MS:PS:PS01_14"                                        # Forward route complete sensor
       self.revCompleteSensor        = "MS:PS:PS01_12"                                        # Reverse route complete sensor
       self.routePathBlocks          = ("BL5"  , "BL2"  , "BL1")                              # Flow of train through the blocks
       self.routePathSensors         = ("MS:BS:BS01_33",'MS:BS:BS01_34',"MS:BS:BS01_35")      # Sensors for each block (Same order as routePathBlocks)
       self.turnouts                 = {"MS:BS:BS01_34" :{"MT:TO:TO01_4" :"OPEN",
                                                          "MT:TO:TO01_21":"OPEN"}}            # Turnout positions when these blocks are booked
                                                          
       self.fwdStartSpeedByTrain     = {"shunt3026":0.35,"shunt8691":0.35}                    # start speed for a particular train
       self.revStartSpeedByTrain     = {"shunt3026":0.25,"shunt8691":0.36} 
                                                          
       self.fwdSignals               = {'MS:BS:BS01_34':(('MA01_17',),('MA01_18',)),
                                        'MS:BS:BS01_35':(('MA01_22',),('MA01_4' ,))}          # if in these blocks are booked then set the signal (red,green)
       self.revSignals               = {'MS:BS:BS01_34':(('MA01_4' ,),('MA01_22',)),          # {block_sensor:(greensignals),(redsignals),}
                                        'MS:BS:BS01_33':(('MA01_18',),('MA01_17',))}          # if these blocks are book then set the signal (red,green)
                                                                                              # {block_sensor:(greensignals),(redsignals),}    

       self.revWaitTimeByTrain       = {"shunt3026":0,"shunt8691":2}                          # Time to wait between loops by train in seconds when in forward direction
       self.fwdWaitTimeByTrain       = {"shunt3026":0,"shunt8691":2}                          # Time to wait between loops by train in seconds when inreverse direction

       self.fwdSpeedSensorsByTrain   = {"shunt3026":{"MS:BS:BS01_35"  :{"MS:PS:PS01_14" :0.20},
                                                    },
                                        "shunt8691":{"MS:BS:BS01_35"  :{"MS:BS:BS01_35" :0.20},
                                                     "MS:BS:BS01_34"  :{"MS:BS:BS01_34" :0.08},
                                                    }
                                       }                                                      # If these block sensors for these trains get booked then wait on these sensors going active
                                                                                              # to set the speed
       self.revSpeedSensorsByTrain   = {"shunt3026":{"MS:BS:BS01_35"  :{"MS:PS:PS01_14" :0.20},
                                                    },
                                        "shunt8691":{"MS:BS:BS01_34"  :{"MS:BS:BS01_34" :0.05},
                                                     "MS:BS:BS01_33"  :{"MS:BS:BS01_33" :0.20}
                                                    }
                                       } 

       self.fwdKeySensorsByTrain     = {"shunt3026":{"MS:BS:BS01_35" :{"MS:PS:PS01_14" :("key_seq_1","K2"),
                                                                       "MS:PS:PS01_5"  :("key_seq_2",)},
                                                     "MS:BS:BS01_33" :{"MS:PS:PS01_13" :("key_seq_1",)}
                                                    },
                                        "engine4035":{"MS:BS:BS01_35":{"MS:BS:BS01_35" : ("key_seq_1",)}
                                                     }
                                       }                                                      # if these blocks (sensors) get booked then wait on these sensors going active
                                                                                              # and run the train key sequence.
class testRoute3(automationRoutesBaseClass) :
   def __init__(self,routeDescription=None,routeName=""):
       self.init()
   def init(self):
       #----------------------------------------------------------------------------------------
       # Required section
       #---------------------------------------------------------------------------------------
       automationRoutesBaseClass.__init__(self)
       #
       # All definitions refer to the direction an engine travels along a route the route_direction setting
       #
       self.lookAhead                = 1
       self.routeDescription         = "move along block 6"
       self.routeName                = "test Route 3"
       self.revWaitTimeDefault       = 0                                                      # Time in seconds to wait before doing the next loop
       self.fwdWaitTimeDefault       = 1                                                      # Time in seconds to wait before doing the next loop
       self.appSpeedDefault          = 0.05                                                   # Speed to go to if block ahead is active
       self.revStartSpeedDefault     = 0.20
       self.fwdStartSpeedDefault     = 0.1
       self.fwdStartSpeedByTrain     = {"shunt3026":0.20}                                     # Default start speed for a particular train
       self.revStartSpeedByTrain     = {"shunt3026":0.20}
       self.fwdCompleteSensor        = "MS:PS:PS01_4"                                         # Forward route complete sensor
       self.revCompleteSensor        = "MS:PS:PS01_17"                                        # Reverse route complete sensor
       self.routePathBlocks          = ("BL6",)                                               # Flow of train through the blocks
       self.routePathSensors         = ("MS:BS:BS01_32",)                                     # Sensors for each block (Same order as routePathBlocks)



class testRoute1_C(testRoute1):
   def __init__(self):
       self.init()
   def init(self):

       testRoute1.init(self)

       self.routeDescription         = "move in a loop from block 1 through block 2 through block 3  and to block 1"
       self.routeName                = self.routeName+" Continuous"
       self.fwdCompleteSensor        = "MS:PS:PS01_14"

class testRoute2_C(testRoute2):
   def __init__(self):
       self.init()
   def init(self):

       testRoute2.init(self)

       self.routeDescription         = "move in a loop from block 5 through block 2 through block 1  and to block 5"
       self.routeName                = self.routeName+" Continuous"
       self.fwdCompleteSensor        = "MS:PS:PS01_12"
#-----------------------------------------------------------------------------------
#
# Class  :  define a route. Inherits methods from automationRoutesBaseClass
#
#           move on test track from block 1 through block 2 to block 3
#
#-----------------------------------------------------------------------------------
class testRoute4(automationRoutesBaseClass) :
   def __init__(self,routeDescription=None,routeName=""):
       self.init()
   def init(self):
       #----------------------------------------------------------------------------------------
       # Required section
       #---------------------------------------------------------------------------------------
       automationRoutesBaseClass.__init__(self)

       self.lookAhead                = 1
       self.routeDescription         = "move in a continuous circle"
       self.routeName                = "test Route 4"


       self.fwdCompleteSensor        = "MS:PS:PS100_4"                                        # Forward route complete sensor
       self.revCompleteSensor        = "MS:PS:PS100_4"                                        # Reverse route complete sensor
       self.revWaitTimeDefault       = 2.0                                                    # Time in seconds to wait before doing the next loop
       self.fwdWaitTimeDefault       = 2.0                                                    # Time in seconds to wait before doing the next loop
       self.appSpeedDefault          = 0.05                                                   # Speed to go to if block ahead is active
       self.revStartSpeedDefault     = 0.20
       self.fwdStartSpeedDefault     = 0.1
       self.maxSpeed                 = 0.3

       self.routePathBlocks          = ("BL106"        ,"BL100"        ,"BL101"        ,"BL102"        ,"BL103"         ,"BL104"         ,"BL105"         ,"BL106")                # Flow of train through the blocks (Forward direction)
       self.routePathSensors         = ("MS:BS:BS101_2",'MS:BS:BS100_2',"MS:BS:BS100_4","MS:BS:BS100_5","MS:BS:BS100_12","MS:BS:BS100_13","MS:BS:BS100_14","MS:BS:BS101_2")        # Sensors for each block (Same order as routePathBlocks)

       self.turnouts                 = {"MS:BS:BS101_2" :{"MT:TO:TO100_27" :"CLOSED"},
                                        "MS:BS:BS100_14":{"MT:TO:TO100_21" :"CLOSED"},
                                       }                                                      # Turnout positions when these blocks are booked

       self.fwdWaitTimeByTrain       = {"shunt3026":0,"shunt8691":0}                          # Time to wait between loops by train in seconds when in forward direction
       self.revWaitTimeByTrain       = {"shunt3026":0,"shunt8691":0}                          # Time to wait between loops by train in seconds when in reverse direction

       self.fwdStartSpeedByTrain     = {"shunt3026":0.35,"shunt8691":0.35}                    # Default start speed for a particular train
       self.revStartSpeedByTrain     = {"shunt3026":0.25,"shunt8691":0.26}

