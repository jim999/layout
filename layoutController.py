#
#
#
import jmri
import jmri.jmrix.SystemConnectionMemoManager
import ast
import os
import sys
import Queue     as queue
import threading as threading

import traceback

import layoutConfig
import layoutReload
import layoutListeners

reload(layoutReload)

import layoutUtils as utils 

reload(utils)

from jmri_bindings import *

if (sys.platform.startswith('java')):
    import jmri_bindings
    import layoutDispatcher
    import layoutJMRIUtils as jmriUtils
    reload(layoutDispatcher)
    
'''
#===============================================================================================================================================
# jmri layout controller 
#================================================================================================================================================
'''
class layoutController(jmri.jmrit.automat.AbstractAutomaton):

      def __init__(self):
          pass

      #==========================================================================================================================================
      # JMRI initialiation rounte
      #
      # 1. check if we are already runnong if yes then exit - cannot have more
      #    than one instance controlling the layout
      #
      # . start a tcp server to receive request and put them on the controller_request_queue
      #
      # . wait on a request comming on to the request queue
      #
      # . pass the request immediately to a dispatcher thread who will check that it is a valid train and route. If not valid issue an error
      #    message and exit.
      # 
      # . start the controller thread running. This thread waits for input 
      #===========================================================================================================================================
      def init(self):
          if layoutConfig.reload_modules : layoutReload.reloadModules().reloadModules()
          self.block_manager            = blocks 
          self.sensor_manager           = sensors
          self.turnout_manager          = turnouts
          self.signal_manager           = signals
          self.masts_manager            = masts
          
          self.active_request_lock      = threading.Lock()
          
          self.train_locks              = {}
          
          self.active_requests          = {}
          
          self.tcpBMClient              = utils.tcpClient(caller='layoutController',manager_type='bookingmanager')
          
          self.jmriUTILS                = jmriUtils.jmriutils(controller=self,sensor_manager=self.sensor_manager,block_manager=self.block_manager,\
                                                              turnout_manager=self.turnout_manager,signal_manager=self.signal_manager,masts_manager=self.masts_manager)
                                                              
          self.utils                    = utils.utils(controller=self)
          
          self.initialised              = False
           
          self.controller_request_queue = queue.Queue()
          self.panel_manager_queue      = queue.Queue()
          
          self.controller_socket        = None
          
          self.printMsg                 = utils.printMsg(caller='layoutController')
          


      def handle(self):
          #-------------------------------------------------------------------------------------------------------------------------------------
          # if we are already running then return
          #-------------------------------------------------------------------------------------------------------------------------------------
          if self.isRunning():
             self.printMsg._print('f(handle)',"ERROR","system","layoutController already running exiting")
             return 
          #--------------------------------------------------------------------------------------------------------------------------------------
          # Restart the booking manager
          #--------------------------------------------------------------------------------------------------------------------------------------
          if not self.jmriUTILS.startBmgr():
             return 
          #--------------------------------------------------------------------------------------------------------------------------------------
          # Add all block sensors to the booking manager table and set up a listener for each block sensor
          #--------------------------------------------------------------------------------------------------------------------------------------
          self.setAllBlockSensors(mode='add')
          #--------------------------------------------------------------------------------------------------------------------------------------
          # Define all system wide sensors
          #--------------------------------------------------------------------------------------------------------------------------------------
          self.jmriUTILS.addSensorsAndListeners('system')
          #-------------------------------------------------------------------------------------------------------------------------------------
          # Turn all signals red
          #-------------------------------------------------------------------------------------------------------------------------------------
          self.setAllSignalsRed()
          #-------------------------------------------------------------------------------------------------------------------------------------
          # start a tcpServer. Any tcp requests will be place on the controller_request_queue by the tcp server. 
          #-------------------------------------------------------------------------------------------------------------------------------------
          self.tcpServer=utils.tcpServer(caller='controller',queue=self.controller_request_queue,manager_type="controller")
          if not (self.tcpServer.start()):
             self.printMsg._print('f(handle)',"ERROR","system","failed to start a tcpServer - terminating")
             return
          #-------------------------------------------------------------------------------------------------------------------------------------
          # wait on an item being placed on our queue but thetcpServer.
          # 
          # valid requests are:
          #
          #  {'command':'run'        , 'train' : train_name,'route':'route_name','loops':nnnn,'mode':'BACKANDFORTH|CONTINUOS','route_direction':'FORAWRD|REVERSE'}
          #  {'command':'status'     , 'train' : train_name}
          #  {'command':'terminate'  , 'train' : train_name}
          #  {'command':'print_route', 'train' : train_name}
          #  {'command':'hold'       , 'train' : train_name or 'all' , 'on' : True|False}
          #  {'command':'start'      , 'train' : train_name or 'all' , 'on' : True|False}
          #  {'command':'wait'       , 'train' : train_name or 'all' , 'on' : True|False}
          #  {'command':'key'        , 'train' : train_name or 'all' , 'on' : True|False}
          #  {'command':'sound'      , 'train' : train_name or 'all' , 'on' : True|False}
          #
          #  self.active_requests {train_name:{'train_instance' : None    , 'route_instance':None, 'train' : train_name,'
          #                                     dispatched':None,'dispatch_instance':None
          #                                    'route'     :route_name       , 
          #                                    'speed_lock' : threading.Lock(), 
          #                                    'status'  : status , status_code: 0, 'status_reason':[reason,xxx,yyy,...], 
          #                                    'retrys' : nnnnn, retry_count:0
          #                                    'speed'     :0.0              , 
          #                                    'loops'   : nnnn   , 'active_loop':nnnn, 'loops_remaining' : nnnn ,
          #                                    'active_subroute' : subroute        , 
          #                                    'num_subroutes' : None 
          #                                    'active_subroute_num':None.
          #                                    'route_direction' : route_direction , 'mode' : mode, 
          #                                    'flags: {'fade' : False  , 'startup' : False  , 'keys' : False , 'sound' : False , 
          #                                              'wait' : False, 'dispatcher_hold' : False, 'hold': False
          #                                            }  
          #                                   }
          #                       }
          #
          #  status         : validating | dispatched | finished | terminated |  holding | building
          #
          #  status_reason  : validating  : request
          #
          #                   validated   : dispatch reuest has a valid route and train    
          #
          #                   building    : building route
          #
          #                   built       : route has been built successfuly 
          #
          #                 : dispatched  : 'waiting' : for_start_time       | for_time          | wait_action_required     
          #                                             release_of_subroute | subroute_booking | start_block_to_go_active
          #
          #                               : 'running' : blank or wait_for_route_complete_sensor
          #
          #                 : holding     : 
          #
          #                 : terminated  : 'system'
          #              
          #
          #  loops          : the number of loops to be done
          #
          #  active_loop    : the current loop number
          #
          #  retrys         : the number of retrys when booking a block sensor
          #
          #  return a request number to the caller.
          #
          #-------------------------------------------------------------------------------------------------------------------------------------
          self.intialised=True
          self.printMsg._print('f(handle)',"INITIALISING","system","layoutController initialised waiting on requests") 
          while True:
              request='{}'
              client_raddr=''
              client_socket=''  
              try:  
                 client_socket,client_raddr,request=self.controller_request_queue.get()
                 
                 try:             
                      if layoutConfig.reload_modules : 
                         layoutReload.reloadModules().reloadModules() 

                      request=ast.literal_eval(request)
                 except:
                      self.printMsg._print('(handle)','WARNING','system','failed to convert {} to a dictionary, data received from {}'.format(request,client_raddr)) 
                 #--------------------------------------------------------------------------------------------------------------------------------
                 # Got a request on our queue. If it is the stop command then go through our stop process. Else start a thread to process the
                 # commmand and go back and wait on another command being placed on our queue.
                 #--------------------------------------------------------------------------------------------------------------------------------
                 self.printMsg._print('(handle)','CTLR_REQUEST','system','received {} from {}'.format(request,client_raddr))
                
                 try:
                    if request['cmd'].upper()=='STOP':
                       self.stop_runing()
                       return
                 except:
                     print(traceback.format_exc())
                 t=threading.Thread(target=self.processCommand,kwargs={'request':request,'client_socket':client_socket,'client_raddr':client_raddr})
                 t.start()
              except:
                 self.printMsg._print('handle',"ERROR",'system','{} from {}'.format(request,client_raddr)) 
                 print(traceback.format_exc())
                 #
                 # Their will be no client_socket or client_raddr if we killed our selves using the jmri Thread Monitor
                 # 
                 if client_socket=='' and client_raddr=='':
                    self.stop_runing()
                    return
      '''
      #===========================================================================================================================================
      #
      # process the command:
      #
      # dispatch              : Check that a train and route are valied and then pass controll over to a disaotcher to build the route and 
      #                         dispatch a train
      #
      # status                : send the atatus of a train back to the caller
      #
      # terminate             : stop a train running. Force option will remove a train from the active requests queue
      #
      #===========================================================================================================================================
      '''
      def processCommand(self,request=None,client_socket=None,client_raddr=None): 
          function_name='f(processCommand)'
          try:
             response="{}"
             if str(request['train']).upper()=='ALL':
                for train_name in self.active_requests:
                    request['train']=str(train_name)
                    print(train_name,">>>>>>>>>>>>>>>>>>>>>",request)
                    response=self.doRequest(request=request,client_socket=client_socket,client_raddr=client_raddr)
            
             else: 
                response=self.doRequest(request=request,client_socket=client_socket,client_raddr=client_raddr)
             
             self.sendResponse(client_socket,response)
          except:
             print(traceback.format_exc()) 
             
      def doRequest(self,request=None,client_socket=None,client_raddr=None):  
          function_name='f(doRequest)'        
          try:
             if request['train'] not in self.train_locks:
                self.train_locks[request['train']]=threading.Lock()
             
             if layoutConfig.trace_command_locks: self.printMsg._print(function_name,'LOCK',request['train'],'lock requested for {}'.format(request['cmd']))   
             
             with self.train_locks[request['train']] :  
             
                  if layoutConfig.trace_command_locks: self.printMsg._print(function_name,'LOCK',request['train'],'lock obtained for {}'.format(request['cmd']))         
             
                  request['cmd']=request['cmd'].upper()
                  
                  if request['cmd'].upper()   =='STATUS' : cmd_successful,error_code,error_message,resp=self.getStatus(request)
                  
                  elif request['cmd'] =='DISPATCH':
                       if request['train'] in self.active_requests:
                          cmd_successful=False
                          error_code=4203
                          error_message='Train {} already on dispatch queue. Try terminate -f {} first'.format(request['train'],request['train'])
                          resp={}
                       else:
                          self.initialiseActiveRequest(train=request['train'],route=request['route'])
                          
                          cmd_successful,error_code,error_message,resp=self.jmriUTILS.checkTrainRoute(request)
                          #
                          # If train and route vaidated ok, hand things over to the dispatcher and tell the user
                          #
                          if cmd_successful:
                             self.jmriUTILS.addSensorsAndListeners(request['train'])
                             self.setFlags(request)
                             dispatcher=layoutDispatcher.layoutDispatcher(self,request['train'])
                             dispatcher.setName("__dispatcher__{}".format(request['train']))
                             
                             self.setActiveRequest(request['train'],caller=function_name,dispatcher_instance=dispatcher,dispatched=True,status_code=6001)
                             
                             dispatcher.start() 
                             
                             self.waitMsec(100)
                             
                  elif request['cmd'] =='PRINT_SYSTEM_RESOURCES': 
                       cmd_successful=True
                       error_code=0
                       error_message=''
                       resp={}
                       t=threading.Thread(target=self.printResources,kwargs={'train_name':'system'})
                       t.start()
                       
                  elif request['cmd'] =='SET_FLAGS':
                       self.setFlags(request)
                                 
                       cmd_successful=True
                       error_code=0
                       error_message=''
                       resp={}
         
                  elif request['cmd'] =='LIST_ACTIVE':
                       active=[]
                       cmd_successful=True
                       error_code=0
                       error_message=''
                       for x in self.active_requests:
                           active.append(x,)  
                       resp={'active_list':active}
         
                  elif request['train'] not in self.active_requests:
                     cmd_successful=False
                     error_code=4205
                     error_message='Train {} not on dispatch queue'.format(request['train'])
                     resp={}
                       
                  elif request['cmd'] =='PRINT_TRAIN_RESOURCES': 
                       cmd_successful=True
                       error_code=0
                       error_message=''
                       resp={}
                       t=threading.Thread(target=self.printResources,kwargs={'train_name':request['train']})
                       t.start()
                  elif request['cmd'] =='PRINT_ROUTE': 
                       cmd_successful=True
                       error_code=0
                       error_message=''
                       resp={}
                       if request['train'] in self.active_requests: #and self.active_requests[request['train']]['print_route']:
                          t=threading.Thread(target=self.active_requests[request['train']]['dispatcher_instance'].printRoute)
                          t.start() 
                       else:
                          cmd_successful=False
                          error_code=4205
                          error_message='Train {} not on dispatch queue'.format(request['train'])
                          resp={}
                  elif request['cmd'] =='TERMINATE':
                        self.printMsg._print(function_name,'TERMINATE',request['train'],'Request to terminate train {} '.format(request['train']),state='terminating')
                        
                        self.setActiveRequest(request['train'],caller=function_name,status_code=6004,status_reason='user terminated',status='terminated')
                        try:
                           self.sensor_manager.provideSensor("MS:IS:terminate:{}".format(request['train'])).setKnownState(ACTIVE)
                        except:
                            pass
                        if str(request['force']).upper()=='TRUE':
                           #
                           # Terminate sensor has been turned on so wait on dynamic train sensors cleaning up
                           #
                           while self.checkForResources(request['train']): #self.active_requests[request['train']]['dispatcher_running']==True:
                                self.waitMsec(5)

                           self.waitMsec(100)
                           try: del self.active_requests[request['train']]['dispatcher_instance']
                           except: pass                      
                           try: del self.active_requests[request['train']]
                           except: pass
                        
                        cmd_successful=True
                        error_code=0
                        error_message=''
                        resp={}
                  else:
                     cmd_successful=False
                     error_code=4999
                     resp={}
                     error_message="unknown command {}".format(request['cmd'])
                     resp={}
                  #----------------------------------------------------------------------------------------------------------------------------------
                  # print the response to the console and send the reponse back to the client
                  #----------------------------------------------------------------------------------------------------------------------------------
                  response="{{'cmd_successful':{},'error_code':{},'error_message':'{}','request':'{}','train':{},'resp':{}}}".format(cmd_successful,\
                                                                                         error_code,error_message,request['cmd'],request['train'],request)
                  
                  if error_code>0:
                    self.printMsg._print('(processCommand)','CTLR_RESPONSE_ERR','system','{} to {}'.format(response,client_raddr))
                  else:
                     self.printMsg._print('f(processCommand)',"CTLR_RESPONSE","system",response)
                  
                  #self.sendResponse(client_socket,response)
             
             if layoutConfig.trace_command_locks: self.printMsg._print(function_name,'LOCK',request['train'],'lock released for {}'.format(request['cmd']))     
          
          except Exception as err:
                 if layoutConfig.trace_active_requests_locks : print("active requests lock status is : {}".format(self.active_request_lock.locked()))
                 self.printMsg._print("f(proessCommand)","ERROR","system",traceback.format_exc())
                 error_code=5000
                 error_message="unknown error {}".format(err)
                 cmd_successful=False
                 response="{{'cmd_successful':{},'error_message':'{}','error_code':{} ,'request':{}, 'resp':''}}".format(cmd_successful,traceback.format_exc(),error_code,request)
                 #client_socket.send(response.encode())      
                 #client_socket.close()
          return(response)
      '''
      #==========================================================================================================================================
      # set a sensors state
      #===========================================================================================================================================
      '''
      def setFlags(self,request):
      
          for flag in request:
              
              if flag in ('keys','fade','wait','hold','sound','startup'):
                 
                 if request[flag].upper()=="TRUE" : request[flag]='True'
                 
                 if request[flag].upper()=="FALSE" : request[flag]='False'
                 
                 if request[flag]=='True' or request[flag]=='False': pass
                 else: continue
        
                 exec("self.setActiveRequest('{}',caller='set_flags',{}={})".format(request['train'],flag,request[flag]))
               
                 if request[flag]==True or request[flag]=='True': 
                    state=ACTIVE
                    alt_state=INACTIVE
                 else: 
                    state=INACTIVE
                    alt_state=ACTIVE
                 sensor_name='MS:IS:{}:{}'.format(flag,request['train'])
                 self.sensor_manager.getSensor(sensor_name).setKnownState(state)
      '''
      #==========================================================================================================================================
      # set a sensors state
      #===========================================================================================================================================
      '''
      def setSensor(self,sensor_name=None,train_name=None,state=ACTIVE):
          sn='MS:IS:{}:{}'.format(sensor_name,train_name)
          self.sensor_manager.getSensor(sn).setKnownState(state)
      '''
      #==========================================================================================================================================
      # send a response on the client socket and close it
      #===========================================================================================================================================
      '''
      def sendResponse(self,client_socket,response):   
          client_socket.send(response.encode())      
          client_socket.close()
          return
      '''
      #===========================================================================================================================================
      #
      # stop running:
      #
      #===========================================================================================================================================
      '''
      def stop_runing(self):
          self.printMsg._print('f(stop)',"WARNING","system","layoutController request to STOP received") 
          self.tcpServer.server_socket.close()
          #
          # terminate all trains
          #
          for sensor_name in self.sensor_manager.getNamedBeanSet().toArray():
             if str(sensor_name).startswith('MS:IS:terminate'):
                self.sensor_manager.getSensor(str(sensor_name)).setKnownState(ACTIVE)
          
          self.removeSystemResources()
      '''    
      #===========================================================================================================================================
      #
      # remove system resources running:
      #
      #===========================================================================================================================================
      '''
      def removeSystemResources(self,train_name='system'):
          #
          # remove all system resources
          #
          listener=layoutListeners.layoutListeners()
          for sensor_name in layoutConfig.command_sensors:
              sn="MS:IS:"+sensor_name+":"+train_name
              sensor=self.sensor_manager.getSensor(sn)
              listener.setListener(caller='removeSystemResoureces',sensor=sensor,train_name='system',mode='remove',listener_reference='INTERNAL_SYSTEM_SENSOR',controller=self)
          self.setAllBlockSensors(mode='remove',toggle_power=False)
          return
      '''
      #=========================================================================================================================================
      # Initialise an entry in the self.active_requests dictionary for a train
      #==========================================================================================================================================
      '''
      def initialiseActiveRequest(self,train,route=None):
          
          self.active_requests[train]                               = {}
          self.active_requests[train]['speed_lock']                 = threading.Lock()
          self.active_requests[train]['train']                      = train
          self.active_requests[train]['train_instance']             = None
          self.active_requests[train]['route']                      = route
          self.active_requests[train]['route_instance']             = None
          self.active_requests[train]['dispatcher_instance']        = None
          self.active_requests[train]['dispatched']                 = False
          self.active_requests[train]['status']                     = 'validating'
          self.active_requests[train]['status_code']                = 6000
          self.active_requests[train]['status_reason']              = 'train {}  and {}'.format(train,route)
          self.active_requests[train]['retrys']                     = None
          self.active_requests[train]['loops']                      = None
          self.active_requests[train]['active_loop']                = 0
          self.active_requests[train]['loops_remainig']             = 0
          self.active_requests[train]['retry_count']                = 0
          self.active_requests[train]['retrys_remaining']           = 0
          self.active_requests[train]['speed']                      = None
          self.active_requests[train]['max_speed']                  = None
          self.active_requests[train]['look_ahead']                 = None
          self.active_requests[train]['subroutes']                  = None
          self.active_requests[train]['active_subroute']            = None
          self.active_requests[train]['active_subroute_num']        = None
          self.active_requests[train]['num_subroutes']              = None
          self.active_requests[train]['mode']                       = 'BACKANDFORTH'
          self.active_requests[train]['route_direction']            = 'UNKNOWN'
          self.active_requests[train]['throttle_direction']         = 'UNKNOWN'
          self.active_requests[train]['route_complete_sensor_name'] = None
          self.active_requests[train]['last_block_sensor_name']     = None
          self.active_requests[train]['flags']                      = {}
          self.active_requests[train]['flags']['fade']              = False
          self.active_requests[train]['flags']['keys']              = False
          self.active_requests[train]['flags']['wait']              = False
          self.active_requests[train]['flags']['hold']              = False
          self.active_requests[train]['flags']['sound']             = False
          self.active_requests[train]['flags']['startup']           = False
          self.active_requests[train]['flags']['sound']             = False
          self.active_requests[train]['flags']['dispatcher_hold']   = False

          return self.active_requests[train]
      '''
      #=========================================================================================================================================
      # Set an entry in the active_reuqests dictionary
      #=========================================================================================================================================
      '''
      def setActiveRequest(self,train,caller="UNKNOWN",status=None,status_reason=None,retrys=None,loops=None, active_loop=None, active_subroute=None, \
                                fade=None,wait=None, keys=None,sound=None,startup=None,\
                                train_instance=None,route_instance=None,dispatched=None,route_direction=None,mode=None,retry_count=None,\
                                dispatcher_instance=None,status_code=None,speed=None,hold=None,dispatcher_hold=None,look_ahead=None,num_subroutes=None,\
                                active_subroute_num=None,subroutes=None,max_speed=None,\
                                route_complete_sensor_name=None,last_block_sensor_name=None,flip_route=None,throttle_direction=None\
                          ):
             function_name='f(setActiveRequest)'                 
             
             if train not in self.active_requests: return
             
             if route_direction and route_direction.upper() != "FORWARD": route_direction = "REVERSE"
             
             if layoutConfig.trace_active_requests_locks  :self.printMsg._print(function_name,"LOCK",'system',"{} request for lock on active_requests. thread {}".format(caller,threading.currentThread().getName()))
            
             with self.active_request_lock:
                  if train_instance       : self.active_requests[train]['train_instance']       = train_instance
                  if route_instance       : self.active_requests[train]['route_instance']       = route_instance
                  if status               : self.active_requests[train]['status']               = status
                  if status_code          : self.active_requests[train]['status_code']          = status_code
                  if status_reason        : self.active_requests[train]['status_reason']        = status_reason
                  if retrys               : self.active_requests[train]['retrys']               = int(retrys)
                  if loops                : self.active_requests[train]['loops']                = int(loops)
                  if speed                : self.active_requests[train]['speed']                = speed
                  if max_speed            : self.active_requests[train]['max_speed']            = max_speed
                  if active_loop          : self.active_requests[train]['active_loop']          = int(active_loop)
                  if active_subroute      : self.active_requests[train]['active_subroute']      = active_subroute
                  
                  if dispatcher_instance != None : self.active_requests[train]['dispatcher_instance']  = dispatcher_instance
                  if dispatched          != None : self.active_requests[train]['dispatched']           = dispatched
                  if route_direction     != None : self.active_requests[train]['route_direction']      = route_direction.upper()
                  if throttle_direction  != None : self.active_requests[train]['throttle_direction']   = throttle_direction.upper()
                  if look_ahead          != None : self.active_requests[train]['look_ahead']           = look_ahead
                  if mode                != None : self.active_requests[train]['mode']                 = mode.upper()
                  if retry_count         != None : self.active_requests[train]['retry_count']          = retry_count
                  if status_code         != None : self.active_requests[train]['status_code']          = status_code
                  if num_subroutes       != None : self.active_requests[train]['num_subroutes']        = num_subroutes
                  if subroutes           != None : self.active_requests[train]['subroutes']            = subroutes
                  if active_subroute_num != None : self.active_requests[train]['active_subroute_num']  = active_subroute_num
                  
                  if route_complete_sensor_name !=None : self.active_requests[train]['route_complete_sensor_name']  = route_complete_sensor_name
                  if last_block_sensor_name     !=None : self.active_requests[train]['last_block_sensor_name']   = last_block_sensor_name
              
                  if fade            != None  : self.active_requests[train]['flags']['fade']            = fade
                  if keys            != None  : self.active_requests[train]['flags']['keys']            = keys
                  if wait            != None  : self.active_requests[train]['flags']['wait']            = wait
                  if hold            != None  : self.active_requests[train]['flags']['hold']            = hold
                  if startup         != None  : self.active_requests[train]['flags']['startup']         = startup
                  if sound           != None  : self.active_requests[train]['flags']['startup']         = sound
                  if dispatcher_hold != None  : self.active_requests[train]['flags']['dispatcher_hold'] = dispatcher_hold
                  #if flip_route      != None  : 
                  #   if  str(flip_route).upper()=='TRUE' :
                  #       self.active_requests[train]['flags']['flip_route']  = True
                  #   else: 
                  #      self.active_requests[train]['flags']['flip_route']  = False
                  
                  if self.active_requests[train]['loops'] != None and (self.active_requests[train]['loops'] >= self.active_requests[train]['active_loop']):
                        self.active_requests[train]['loops_remainig'] = self.active_requests[train]['loops'] - self.active_requests[train]['active_loop']
                                     
                  if retrys !=None:
                     self.active_requests[train]['retrys_remaining'] = self.active_requests[train]['retrys'] - self.active_requests[train]['retry_count']                 
            
             if layoutConfig.trace_active_requests_locks  :self.printMsg._print(function_name,"LOCK",'system',"{} removing lock on active_requests, thread {}".format(caller,threading.currentThread().getName()))
             
             return self.active_requests[train]

      '''
      #=========================================================================================================================================
      # Print a train request to the terminal
      #==========================================================================================================================================
      '''
      def printActiveRequest(self,train):
          if train=='ALL':
             print('active requests ==> {}'.format(self.active_requests))
          else:
             print('\nactive request for train {}'.format(train))
             print('-'*85)
             for k,v in self.active_requests[train].items():
                 print('{} {}'.format(k.ljust(25),v))
      '''
      #==========================================================================================================================================
      # get the status of a train
      #
      #  the request is a dictionary in the form  : {'manager': 'controller', 'cmd': 'status', 'train': 'shunt3026'}
      #
      #==========================================================================================================================================
      '''
      def getStatus(self,request):
          cmd_successful=False
          
          if request['train'] in self.active_requests:
             cmd_successful=True
             error_code=0
             error_message=''
             active_request_copy=self.active_requests[request['train']].copy()
        
             if 'train_instance' in active_request_copy : del active_request_copy['train_instance']
             if 'route_instance' in active_request_copy : del active_request_copy['route_instance']
             if 'print_route' in active_request_copy : del active_request_copy['print_route']
             if 'dispatcher_instance' in active_request_copy : del active_request_copy['dispatcher_instance']
             if 'speed_lock' in active_request_copy : del active_request_copy['speed_lock']
        
             resp=active_request_copy
          else:
             cmd_successful=False
             error_code=4200                                                               # Train is not in the dispatch list 
             error_message='{} is not active'.format(request['train'])
             resp={}
          return cmd_successful,error_code,error_message,resp
      '''
      #==========================================================================================================================================
      # Set all signals red
      #==========================================================================================================================================
      '''
      def setAllSignalsRed(self):
          for signal_mast in self.masts_manager.getNamedBeanSet():
              signal_mast.setAspect('Stop')
      '''
      #==========================================================================================================================================
      # 
      #==========================================================================================================================================
      '''
      def getInitialised(self):
          return self.initialised
      def getRequestQueue(self):
          return self.controller_request_queue                     # a ponter to the queue
      '''
      #==========================================================================================================================================
      #
      #==========================================================================================================================================
      '''
      def putRequest(self,request):
          self.controller_request_queue.put(request)               # a dictionary item
          self.active_reequest_numbers.append(request_number)      # save this as an active request
          self.request_number+=1                                   # increment the request number
          return self.request_number-1                             # give the user his request number
      '''
      #==========================================================================================================================================
      # check if we are already running
      #==========================================================================================================================================
      '''
      def isRunning(self):
          while True:
              number_of_instances=jmri.jmrit.automat.AutomatSummary.instance().length()
              instance_list=[]
              for i in range(number_of_instances):
                  jmri_thread_name=jmri.jmrit.automat.AutomatSummary.instance().get(i).getName()
                  my_name=type(self).__name__
                  if my_name in jmri_thread_name :
                     instance_list.append(jmri_thread_name)
              if  len(instance_list)<2: break
              else:
                return True
          return False
          
      '''
      #==========================================================================================================================================
      # Return our intialisation state
      #==========================================================================================================================================
      '''
      def isInitialised(self):
          return self.initialised
      '''
      #====================================================================================================================
      # Add all blocks to the booking manager and create a listener for each block.
      #=====================================================================================================================
      '''
      def setAllBlockSensors(self,mode='add',toggle_power=True):
          try:
             function_name='f(addAllBlockSensors)'
             my_sensors=self.sensor_manager.getNamedBeanSet().toArray()
             failed  = 0
             success = 1
             listener=layoutListeners.layoutListeners()
             for sensor in my_sensors:
                 sensor_name=sensor.getSystemName()
                 if sensor_name[2:6]==":BS:":
                    sensor=self.sensor_manager.getSensor(sensor_name)
                    sensor_state=sensor.describeState(sensor.getKnownState())
                    listener.setListener(caller='setAllBlockSensors',sensor=sensor,mode=mode,listener_reference="BLOCK_OCCUPIED_SENSOR",controller=self)
                    if mode == 'add':
                       req="{{'cmd':'add_sensors','sensors':'{}','owner':'None','value':'{}'}}".format(sensor_name,sensor_state)
                       resp=self.tcpBMClient.sendData(data=req)
                       resp=ast.literal_eval(resp)
                
                       if not resp['cmd_successful']:
                          self.printMsg._print(function_name,owner,"ERROR","error code {} error message {}".format(resp['error_code'],resp['error_message']),state="Error")
             
             if toggle_power: self.jmriUTILS.togglePower()
          except :
              self.printMsg._print(function_name,"ERROR",'system',traceback.format_exc())
          return
      '''
      #====================================================================================================================
      # print system resources
      #=====================================================================================================================
      '''
      def checkForResources(self,train_name):
          function_name='f(checkForResources)'
          #   
          # check if there are still some property chnage listeners running 
          #
          for sensor in self.sensor_manager.getNamedBeanSet().toArray():
              for oldListener in sensor.getPropertyChangeListenersByReference(train_name):
                  #sensor_reference=sensor.getListenerRef(oldListener)
                  #print(sensor_reference)
                  return True
                  
          return False
          
      def printResources(self,train_name='system'):
         try: 
             function_name='f(printResources)'
             #    
             # get all property change listeners 
             #
             for sensor_name in self.sensor_manager.getNamedBeanSet().toArray():
                 sensor_name=str(sensor_name)
                 sensor=self.sensor_manager.getSensor(sensor_name)
                 for oldListener in sensor.getPropertyChangeListenersByReference(train_name):
                     sensor_reference=sensor.getListenerRef(oldListener)
                     self.printMsg._print(function_name,"CTLR_RESOURCE",train_name,"found {} for {} ".format(sensor_reference,sensor_name))
                     self.waitMsec(2)
         except :
             print(traceback.format_exc())
      '''
      #====================================================================================================================
      # get a throttle and return it to the caller
      #=====================================================================================================================
      '''
      def getMyThrottle(self,throttleNumber, throttleNumLong) :
          return self.getThrottle(throttleNumber,throttleNumLong,1)

