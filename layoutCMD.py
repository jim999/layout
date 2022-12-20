import argparse
import ast
import traceback

import layoutConfig
import layoutUtils   as utils
'''
#---------------------------------------------------------------------------------------
# Set up the parser
#
# format is layoutCMD -m manager name [add_sensor | print_table | stop]
#---------------------------------------------------------------------------------------
'''
cmd_parser = argparse.ArgumentParser(description='pass commands to a layout component')

subparser  = cmd_parser.add_subparsers(dest='command')

parent       = argparse.ArgumentParser(description='pass commands to the layout booking manager')    

stop = subparser.add_parser('stop'    ,parents=[parent],add_help=False ,help="Stop a layout component runing. For example the controller")

stop.add_argument('-m' ,'--manager'  , type=str.lower ,required=True  ,help='The name of the booking manager',choices=['bookingmanager','controller'])

print_table = subparser.add_parser('print_table'    ,parents=[parent],add_help=False                            ,help="Print the booking manager table")
print_table.add_argument('-m' ,'--manager',  type=str.lower ,required=False,default='bookingmanager'            ,help='The name of the booking manager, default is %(default)s')
                                                                                                               
print_route = subparser.add_parser('print_route'    ,parents=[parent],add_help=False                            ,help="Print the a route if it is active")
print_route.add_argument('-m' ,'--manager',  type=str.lower ,required=False,default='controller'                ,help='The name of the controller, default is %(default)s')
print_route.add_argument('-t' ,'--train'     ,required=True                                                     ,help='The name the train that is active')
                                                                                                               
list_active = subparser.add_parser('list_active'    ,parents=[parent],add_help=False                            ,help="return a list of active dispatch requests ")
list_active.add_argument('-m' ,'--manager',  type=str.lower ,required=False,default='controller'                ,help='The name of the controller, default is %(default)s')
                                                                                                               
print_system_resources = subparser.add_parser('print_system_resources'    ,parents=[parent],add_help=False      ,help="print the system resources")
print_system_resources.add_argument('-m' ,'--manager',  type=str.lower ,required=False,default='controller'     ,help='The name of the controller, default is %(default)s')
                                                                                                               
print_train_resources = subparser.add_parser('print_train_resources'    ,parents=[parent],add_help=False        ,help="print a trains resources")
print_train_resources.add_argument('-m' ,'--manager',  type=str.lower ,required=False,default='controller'      ,help='The name of the controller, default is %(default)s')
print_train_resources.add_argument('-t' ,'--train'     ,required=True                                           ,help='The name the train that is active')
                                                                                                                  
add_sensors = subparser.add_parser('add_sensors',parents=[parent],add_help=False                                ,help="Add a sensor or sensors to the booking manager table")
add_sensors.add_argument('-m' ,'--manager'  ,type=str.lower ,required=False,default='bookingmanager'            ,help='The name of the booking manager, default is %(default)s')
add_sensors.add_argument('-s' ,'--sensors'  ,type=str.lower ,required=False,default='bookingmanager'            ,help='The sensor names to be added to the sensor table')
add_sensors.add_argument('-o' ,'--owner'    ,type=str.lower ,required=False,default='None'                      ,help='The owner of the sensors, defaults to %(default)s')
add_sensors.add_argument('-v' ,'--value'    ,type=str.lower ,required=False,default='UNKNOWN'                   ,help='The value of the sensors (ACTIVE|INACTIVE|UNKNOWN, default is %(default)s',choices=["active","inactive","unknown"])
                                                                                                                 
set_sensors = subparser.add_parser('set_sensors',parents=[parent],add_help=False                                ,help="Change the state of a sensor or sensors to ACTIVE or INACTIVE")
set_sensors.add_argument('-m' ,'--manager'  ,      required=False,default='bookingmanager'                      ,help='The name of the booking manager, default is %(default)s')
set_sensors.add_argument('-s' ,'--sensors'  ,      required=True                                                ,help='The sensor names to be added to the sensor table')
set_sensors.add_argument('-v' ,'--value'    ,      required=True                                                ,help='The value the sensors are to be set to choices are (%(choices)s), default is %(default)s',choices=["active","inactive","unknown"])
                                                                                                                 
book_sensors = subparser.add_parser('book_sensors',parents=[parent],add_help=False                              ,help="Book a number of sensors to a given engine")
book_sensors.add_argument('-m' ,'--manager' ,      required=False,default='bookingmanager'                      ,help='The name of the booking manager, default is %(default)s')
book_sensors.add_argument('-s' ,'--sensors' ,      required=True                                                ,help='The sensor names to be added to the sensor table')
book_sensors.add_argument('-o' ,'--owner'   ,      required=False                                               ,help='The owner of the sensors')
book_sensors.add_argument('-f' ,'--force'   ,      required=False,action='store_true'                           ,help='Force the first sensor to be booked no mater what value it is or who owns it in the bookingmanager table')
                                                                                                                 
release_sensors  = subparser.add_parser('release_sensors',parents=[parent],add_help=False                       ,help="Release a number of sensors for a given engine")
release_sensors.add_argument('-m' ,'--manager' ,   required=False,default='bookingmanager'                      ,help='The name of the booking manager, default is %(default)s') 
release_sensors.add_argument('-s' ,'--sensors' ,   required=True                                                ,help='The sensor names to be released ')
release_sensors.add_argument('-o' ,'--owner'   ,   required=True                                                ,help='The engine the sensors belong to, the sensor owner')
release_sensors.add_argument('-f' ,'--force'   ,   required=False,action='store_true'                           ,help='force the blocks to be release')

set_flags = subparser.add_parser('set_flags',parents=[parent],add_help=False                                    ,help="define setting for an engine")
set_flags.add_argument('-m' ,'--manager'  ,        required=False,type=str.lower      ,default='controller'     ,help='The name of the controller, default is %(default)s') 
set_flags.add_argument('-t' ,'--train'    ,        required=True                                                ,help='the name of engine') 
set_flags.add_argument('-f' ,'--fade'     ,        required=False,type=str.upper,choices=['TRUE','FALSE']       ,help='the fade flag')
set_flags.add_argument('-ho','--hold'     ,        required=False,type=str.upper,choices=['TRUE','FALSE']       ,help='the hold flag')
set_flags.add_argument('-w' ,'--wait'     ,        required=False,type=str.upper,choices=['TRUE','FALSE']       ,help='the wait flag')
set_flags.add_argument('-k' ,'--keys'     ,        required=False,type=str.upper,choices=['TRUE','FALSE']       ,help='the keys flag')
set_flags.add_argument('-so','--sound'    ,        required=False,type=str.upper,choices=['TRUE','FALSE']       ,help='the sound flag')

status = subparser.add_parser('status',parents=[parent],add_help=False                                          ,help="Release a number of sensors for a given engine")
status.add_argument('-m' ,'--manager'     ,        required=False,default='controller'                          ,help='The name of the manager, default is %(default)s') 
status.add_argument('-t' ,'--train',   required=True                                                            ,help='The name the train whose status is to be returned ')

dispatch = subparser.add_parser('dispatch',parents=[parent],add_help=False                                      ,help="dispacth an engine on a given route")
dispatch.add_argument('-m' ,'--manager'   ,         required=False,type=str.lower  ,default='controller',        help='The name of the controller, default is %(default)s') 
dispatch.add_argument('-t' ,'--train'     ,         required=True                                               ,help='The name the train who is to be dispatched')
dispatch.add_argument('-r' ,'--route'     ,         required=True                                               ,help='The name the route the train is to be dispatched on')
dispatch.add_argument('-f' ,'--fade'      ,         required=False,type=str.upper,choices=['TRUE','FALSE']      ,help='Fade the engine sound')
dispatch.add_argument('-w' ,'--wait'      ,         required=False,type=str.upper,choices=['TRUE','FALSE']      ,help='Enable wait sensor checking')
dispatch.add_argument('-k' ,'--keys'      ,         required=False,type=str.upper,choices=['TRUE','FALSE']      ,help='Enable key sensorchecking')
dispatch.add_argument('-s' ,'--startup'   ,         required=False,type=str.upper,choices=['TRUE','FALSE']      ,help='Enable start up processing - go through the engine startup routine as defined in the train profile')
dispatch.add_argument('-so','--sound'     ,         required=False,type=str.upper,choices=['TRUE','FALSE']      ,help='turn sound on or off, off if not specified on if specified')
dispatch.add_argument('-ho','--hold'      ,         required=False,type=str.upper,choices=['TRUE','FALSE']      ,help='hold the train')
dispatch.add_argument('-l' ,'--loops'     ,         required=False,default=99999                                ,help='The number of loops of the layout to be done, default is %(default)')
dispatch.add_argument('-rt','--retrys'    ,         required=False,default=1                                    ,help='The number of times to retry booking a subroute before terminating,  default is %(default)')
dispatch.add_argument('-la','--look_ahead',         required=False                                    ,help='The number blocks that make a subroute, default is %(default)s')
dispatch.add_argument('-mo','--mode',               required=False,default='BACKANDFORTH',type=str.upper,choices=["BACKANDFORTH",'CONTINUOS'],help='The mode for the dispatcher (CONTINUOS | BACKANDFORTH), default is %(default)s')
dispatch.add_argument('-rd','--route_direction' ,   required=False,default='FORWARD',     type=str.upper,choices=["FORWARD",'REVERSE']       ,help='The direction we will move along the route, default is %(default)s')
dispatch.add_argument('-td','--throttle_direction',required=False,default='FORWARD',      type=str.upper,choices=["FORWARD",'REVERSE']       ,help='The direction the train throttle should be set, default is %(default)s')

terminate = subparser.add_parser('terminate',parents=[parent],add_help=False                                    ,help='Terminate a train, use ')
terminate.add_argument('-m' ,'--manager'   ,required=False,type=str.lower      ,default='controller'            ,help='The name of the controller, default is %(default)s') 
terminate.add_argument('-t' ,'--train'     ,required=True                                                       ,help='The name the train who is to be dispatched')
terminate.add_argument('-f' ,'--force'     ,required=False,action='store_true'                                  ,help='force an engine of the active_reuqests queue. Note this may or may not stop a train')
'''
# retrieve subparsers from parser
subparsers_actions = [
    action for action in cmd_parser._actions 
    if isinstance(action, argparse._SubParsersAction)]
# there will probably only be one subparser_action,
# but better safe than sorry
for subparsers_action in subparsers_actions:
    # get all subparsers and print help
    for choice, subparser in subparsers_action.choices.items():
        print(f"{choice}")
        print(subparser.format_help())
'''
args  = cmd_parser.parse_args()
'''
#---------------------------------------------------------------------------------------
#
# Process the command
#
#----------------------------------------------------------------------------------------
'''
def sendToManager(data=None,stop=False,print_detail=False):
   try: 
      tcpClient=utils.tcpClient(caller="layoutCMD",manager_type=args.manager)
      if stop:
         tcpClient.sendData(wait=False,data=f"{{{data}}}")          
      else:
         resp=tcpClient.sendData(data=f"{{{data}}}")

      command_dict={}

      if not stop and resp:
         command_dict=ast.literal_eval(resp)
         if print_detail:
            for k,v in command_dict.items():
                print(k,'===>',v)
                
                if k=='resp':
                   for x,y in v.items():
                       print(x,'===>',y)
   except Exception:
       if stop:
          return None
       else:
         utils.printMsg(caller='layoutCMD')._print("layoutCMD",'ERROR','system',f"{traceback.format_exc()}")
   return command_dict

stop=False
valid_commands=('set_flags','print_train_resources','print_system_resources','list_active','print_route','terminate','add_sensors','book_sensors','print_table','release_sensors','set_sensors','stop','status','dispatch')

if args.command in valid_commands:
   string_dict=''
   if 'sensors' in args and isinstance(args.sensors,str):
      args.sensors=args.sensors.strip('[').strip(']').split(',')
   
   for k,v in args.__dict__.items():
       if k=='command' : 
          k='cmd'
       if isinstance(v,list):
          string_dict=string_dict+f"'{k}':{v},"
       else:
          string_dict=string_dict+f"'{k}':'{v}',"
              
       if isinstance(v,bool): pass
       
       elif (not isinstance(v,list) and not isinstance(v,int) and not isinstance(v,float)): 
          if v!=None and v.upper()=="STOP":
             stop=True
       
          
   resp=sendToManager(data=string_dict,stop=stop,print_detail=False)
else:
    utils.printMsg(caller='layoutCMD')._print("layoutCMD",'ERROR','system',f"unknown command {args.command}")
if __name__!="__main__":
   exit(resp)
