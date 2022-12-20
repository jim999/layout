#
#
#
version                       = "V1.0.0"
booking_manager_port          = 50000
controller_queue_port         = 50001

client_timeout                = 5                                          # minimum value of 1.5

booking_manager_program       = "python /home/pi/.jmri/jython/layoutBKManager.py"

ignore1                       = ["SEND","layoutCMD",'TCP_INFO',]

ignore2                       = ['S_CHANGE_BLOCK','S_CHANGE_approach','S_CHANGE_INTERNAL','S_CHANGE_fade','S_CHANGE_speed','S_CHANGE_wait2','S_CHANGE_sound',\
                                 'S_CHANGE_hold','S_CHANGE_keys','S_CHANGE_terminate','S_CHANGE_route_complete','S_CHANGE_last_block','S_CHANGE_running']

ignore3                       = ['BKMGR_REQUEST','ADD_LISTENER','REMOVE_LISTENER','BUILD','VALIDATE','CTLR_REQUEST2']

ignore4                       = ["BKMGR_RESPONSE","BKMGR_RESPONSE_ERR"]

ignore5                       = ["BKMGR_RESPONSE_FB",]

ignore                        = ignore1 + ignore2 + ignore3 + ignore4 +ignore5

trace_command_locks           = False
trace_active_requests_locks   = False
trace_active_requests_status  = False
reload_modules                = True


train_modules                 = ('layoutTrainProfiles',)
route_modules                 = ('layoutAutomationRoutes',)
#=================================================================================================================================================
# command_sensors     : one of each of these is created by the controller and used to controll system wide commands. For example turn fade on for
#                       all engines
#
#                       one of each of these is created by a dispatcher when a train is dispatched and are used to controll a moving engine. Listeners
#                       are created for these dynamicallty
#    
# set_inactive        : these sensors are set inactive before a run
#
# listener_references : Listeners are setup for these   
#
# subroute_listeners  : these are listeners that are set as and when reuqired throughout a run                                 
#
#===================================================================================================================================================
command_sensors               = ('finished','terminate','running','fade','hold','dispatcher_hold','startup','wait','wait_running','keys','sound',)
set_inactive                  = ('finished','terminate','running','dispatcher_hold','wait_running')

subroute_listeners            = ('speed','wait','keys','approach')

listener_references           = ("INTERNAL_SYSTEM_SENSOR",'BLOCK_OCCUPIED_SENSOR')

#INACTIVE                      = 4
#ACTIVE                        = 2
#====================================================================================================
# Message level colors used by printMsg when printing to terminal
#====================================================================================================
BLUE                          ='\033[34m'
BRIGHT_BLUE                   ='\033[94m'
GREEN                         ='\033[32m'
BRIGHT_GREEN                  ='\033[92m'
YELLOW                        ='\033[33m'
BRIGHT_YELLOW                 ='\033[93m'
MAGENTA                       ='\033[35m'
BRIGHT_MAGENTA                ='\033[95m'
RED                           ='\033[31m'
BRIGHT_RED                    ='\033[91m'
CYAN                          ='\033[36m'
BRIGHT_CYAN                   ='\033[96m'
BRIGHT_WHITE                  ='\033[97m'
ENDC                          ='\033[00m'
NORMAL                        ='\033[00m'
WHITE                         ='\033[00m'
BOLD                          ='\033[01m'
UNDERLINE                     ='\033[04m'
ORANGE                        ="\033[38;2;255;165;0m"
BRIGHT_ORANGE                 ="\033[48;5;208;165;0m"
ORANGE_BG                     ="\033[48;2;255;165;0m"

color                         = {
                                  "BKMGR"              : BRIGHT_BLUE,
                                  "BKMGR_INFO"         : GREEN,
                                  "BKMGR_RESPONSE"     : BRIGHT_GREEN,
                                  "BKMGR_RESPONSE_ERR" : BRIGHT_RED,
                                  "BKMGR_REQUEST"      : GREEN,
                                  "BKMGR_INIT"         : YELLOW,
                                  "BKMGR_STARTED"      : BRIGHT_YELLOW,
                                  "BKMGR_TABLE"        : WHITE,
                                  "BUILD"              : GREEN,
                                  "CTLR_REQUEST"       : GREEN,
                                  "CTLR_RESPONSE"      : BRIGHT_GREEN,
                                  "CTLR_RESPONSE_ERR"  : BRIGHT_RED,
                                  "CTLR_RESOURCE"      : WHITE,
                                  "DRIVER"             : ORANGE,
                                  "DRIVER_SP"          : BRIGHT_CYAN,
                                  "DRIVER_C"           : BRIGHT_CYAN,
                                  "DRIVER_APP"         : ORANGE,
                                  "ADD_LISTENER"       : GREEN,
                                  "REMOVE_LISTENER"    : GREEN,
                                  "S_CHANGE_INTERNAL"  : GREEN,
                                  "S_CHANGE_terminate" : YELLOW,
                                  "S_CHANGE_BLOCK"     : GREEN,
                                  "TERMINATE"          : BRIGHT_RED,
                                  "TERMINATED"         : BRIGHT_RED,
                                  "BOOKED_SUBROUTE"    : BRIGHT_CYAN,
                                  "VALIDATE"           : GREEN,
                                  "VALIDATED"          : GREEN,
                                  "DISPATCHER"         : BRIGHT_YELLOW,
                                  "NORMAL"             : NORMAL,
                                  "INITIALISING"       : BRIGHT_CYAN,
                                  "WARNING"            : BRIGHT_YELLOW,
                                  "ERROR"              : BRIGHT_RED,
                                  "STOPCOLOR"          : ENDC
                                }
