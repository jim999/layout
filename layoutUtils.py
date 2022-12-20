import ast
import socket
import threading
import time
import traceback
    
import sys
import os

import layoutConfig 


if (sys.platform.startswith('java')):
    import layoutDispatcher
    from jmri_bindings import *
#=====================================================================================================================
# A number of common class obects
#=====================================================================================================================
class utils():
      def __init__(self,controller=None):
          self.printMsg=printMsg(caller='utils.utils')
          self.controller=controller
          
      #------------------------------------------------------------------------------------------------------------
      # send data to the database manager
      #---------------------------------------------------------------------------------------------------------
      def sendToDBManager(self,caller="UNKNOWN",cmd=None,params='None',table='None',manager_type="dispatchDatabaseManager"):
          resp=tcpClient(caller=caller,manager_type=manager_type).sendData("{{'cmd':'{}','table':'{}','params':{} }}".format(cmd,table,params))
          resp_dict=ast.literal_eval(resp)
          
          if not resp_dict['cmd_successful']:
             self.printMsg._print('f(sendTodBManager)',"ERROR",'system','{} for command {}'.format(resp_dict["error_message"],resp_dict["cmd"]))
          return resp_dict
      #----------------------------------------------------------------------------------
      # Functionto dump an object
      #----------------------------------------------------------------------------------
      def dump_object(self,obj,caller="UNKNOWN"):
          for attr in dir(obj):
              print("caller({}) {} {}".format(caller,obj,attr))
          
          self.printMsg       = printMsg(caller='controller')
      '''
      #==========================================================================================================================================
      # get a train or toute module
      #  
      #  self.getModule('my_package.my_module.my_class')
      #
      #  def getModule(self.components)
      #      components = name.split('.')
      #      mod = __import__(components[0])
      # 
      #      for comp in components[1:]:
      #          print(mod,comp)
      #          mod = getattr(mod, comp)
      # 
      #      return mod
      #
      #==========================================================================================================================================
      '''
      def getModule(self,name,module_files):
          module=None
          for f in module_files:
              try:
                 module =__import__(f)
                 if module: reload(module)
                 module = getattr(module,name)
                 
              except AttributeError:
                module=None
                continue
          try:
             return module()
          except:
             return None 


'''
#--------------------------------------------------------------------------------------------------------
# Simple TCP server to receive requests and put them on the appropriate queue
#
# This tcp server waits on incoming transactions when it receives one it places 
# the client socket object and the request on a queue. This is then processed by
# the appropriate manager. 
#
# The queue passed is the queue where a valid request is to be put. 
#
# Note:  This is a python3 module and runs outside of jmri and jython.
#-----------------------------------------------------------------------------------
'''
class tcpServer(threading.Thread):
      def __init__(self,caller=None,queue=None,manager_type="None"):
         try:
           self.printMsg            =printMsg(caller="tcpServer")
           self.caller              = caller
           self.manager_type        = manager_type
           self.tcp_buf_size        = 8192
           self.function_name       = "f(tcpServer)"
           self.queue               = queue
         
           if self.manager_type=="bookingmanager":
              self.port=layoutConfig.booking_manager_port
              self.booking_manager_queue=queue
              self.function_name="f(tcpServer_bm)"
              
           elif self.manager_type=="dispatchmanager":
                self.port=layoutConfig.dispatch_database_manager_port
                self.dispatch_console_console_queue=queue
                self.function_name="f(tcpServer_DDM)"
                
           elif self.manager_type=="controller":
                self.port=layoutConfig.controller_queue_port
                self.controller_request_queue=queue
                self.function_name="f(tcpServer_CLTR)"
           else:
              self.printMsg._print(self.function_name,"ERROR","system","invalid tpServer type {}".format(self.manager_type))
         except:
             
             self.printMsg._print(self.function_name,"ERROR","system",traceback.format_exc())   
        
      #--------------------------------------------------------------------------
      # Start the tcp server listener
      #--------------------------------------------------------------------------
      def start(self):
          try:
              if self.manager_type in ["dispatchmanager","bookingmanager","controller"]:
                 self.server_socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                 self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                 self.server_socket.bind(('',self.port ))
                 self.server_socket.listen(500)
                 
                 t=threading.Thread(target=self._run,name="{} tcpServer thread".format(self.manager_type))
                 t.start()
                 return(True)
              else:
                 self.printMsg._print(self.function_name,"ERROR","system","invalid tpServer type {}".format(self.manager_type)) 
                 return(False)
          except:
              self.printMsg._print(self.function_name,"ERROR","system",traceback.format_exc())
              return False
      
      def _run(self):
          try:
             #--------------------------------------------------------------------------
             # loop waiting for connections
             #--------------------------------------------------------------------------
             
             while True:
                    #
                    # Wait on a request comming in
                    #
                    client_socket, client_address = self.server_socket.accept()
                    #
                    # receive the data put it on the appropriate managers queue and go wait for more requests
                    #
                    try:
                       client_socket.settimeout(1)
                       client_request=client_socket.recv(self.tcp_buf_size).decode()
                       self.printMsg._print(self.function_name,"TCP_INFO","system","{}, received from {}".format(client_request,client_address))
                       self.queue.put((client_socket, client_address, client_request))
                    except socket.timeout:
                        #self.printMsg._print(self.function_name,'ERROR','system',"{} Forcing client socket closed".format(self.caller))
                        break
                        #client_socket.close()
          except Exception as err:
                self.printMsg._print(self.function_name,"ERROR","system","{}".format(err))
                print(traceback.format_exc())
                return 
                
      def stop(self):
          self.server_socket.close()
#------------------------------------------------------------------------------------------------------
# simple tcp client
#
# data to send should be a string in the form "{'cmd':'book this', "some_other_variable":"some_ther_value"}"
# the response should be a the same data but with an additional element called cmd_successful
#
#---------------------------------------------------------------------------------------------------------
class tcpClient():
    def __init__(self,caller=None,queue=None,manager_type=None):
        try:
           self.printMsg      = printMsg(caller="tcpClient")
           self.caller        = caller
           self.function_name="f(__init__)"
           self.manager_type=manager_type
           
           self.tcp_buf_size   = 8192
           self.socket_timeout = layoutConfig.client_timeout                              # If server slows down this may need to be increased
           
           self.init           = False
           
           if self.manager_type=="bookingmanager":
              self.port          = layoutConfig.booking_manager_port 
              self.init          = True
              
           elif self.manager_type=="dispatchmanager":
              self.port          = layoutConfig.dispatch_database_manager_port
              self.init          = True
           elif self.manager_type=="controller":
              self.port          = layoutConfig.controller_queue_port
              self.init          = True
           else:
              self.printMsg._print(self.function_name,"ERROR","system","invalid tpServer type {}".format(self.manager_type))
        except:
            self.printMsg._print(self.function_name,"ERROR","system",traceback.format_exc()) 
            
    def sendData(self,wait=True,data=None,quiet=False):
       self.function_name="f(sendData)"
       if not self.init: return None
       data_dict=''
       try:
          self.printMsg._print(self.function_name,"SEND","system",data)
          self.local_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
          
          try:
             self.local_socket.connect(("",self.port))
             self.local_socket.settimeout(self.socket_timeout)
          except socket.error as err: 
              if not quiet:
                 self.printMsg._print('f(sendData)','WARNING','system',"error {}, while trying to connect to a manager called {}, check the manager is running".format(err,self.manager_type))
              return False
          cmd=data
          #------------------------------------------------------------------------------
          # process the response. Sends the data to the server and wait for its response
          #------------------------------------------------------------------------------
          try:
            self.local_socket.send(data.encode())
            if wait:
               data='' 
               count=0
               while True:
                     self.local_socket.settimeout(self.socket_timeout)
                     data = str(self.local_socket.recv(self.tcp_buf_size))
                     if isinstance(data,bytes):
                         data=data.decode()
                     if (not data) or data==str(b'') or data==u'' or data=='':
                         break
                     count+=1
                     if count>10: break
                         
                     data_dict=data_dict+data
                     
          except socket.error as socket_err:
              print("caller {} {} >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<".format(self.caller,cmd),traceback.format_exc())
              self.printMsg._print(self.function_name,"ERROR","system","{} connecting to {} {} for command {}".format(self.caller,self.manager_type,socket_err,cmd))
              if isinstance(data_dict,dict):
                 data_dict["cmd_successful"]=False
                 data_dict["error_message"]='"'+str(socket_err)+"'"
              else:
                  data_dict=None
          except Exception as err:
              self.printMsg._print(self.function_name,"ERROR","system","{} receiving from {} {}".format(self.caller,self.manager_type,err))
              if isinstance(data_dict,dict):
                 data_dict["cmd_successful"]=0
                 data_dict["error_message"]="'"+str(err)+"'"
              raise(err)

       except Exception as err:
          self.printMsg._print(self.function_name,"ERROR","system",traceback.format_exc())
          if isinstance(data_dict,dict):
             data_dict["error_message"]="'"+str(err)+"'"
             data_dict["cmd_successful"]=False
       #print(">>>>>>>>>>>>>>>>>>>> CLOSING SOCKET <<<<<<<<<<<<<<<<<<<<")
       self.local_socket.close()
       return str(data_dict)
'''
#--------------------------------------------------------------------------------------------------------
#
# Class to print to the screen
#
# if msg_level is error or fatal then print any traceback information
#
# output will either go to the JPanel consoles or the stdout screen
#
# Caller       -  is the function that call me
# color        -  produce color messages or not
#
#-----------------------------------------------------------------------------------------------------------
'''
class printMsg(threading.Thread):
   def __init__(self,caller="UNKNOWN",color=True,controller=None):
        self.color=color
        self.caller=caller
        self.controller=controller

        if color:
           self.color_start=layoutConfig.color["NORMAL"]
           self.color_stop =layoutConfig.color["NORMAL"]
        else:
           self.color_start=""
           self.color_stop=""
   #--------------------------------------------------------------------------------------------------
   #
   # function         : the name of the calling function
   #
   # msg_level        : The message level. Used to color messages and write traceback info if
   #                    appropriate
   #
   # train_name       : the name of the train the message applies to. If this is console then the
   #                    jPanel console is written to.
   #
   # text             : the message text
   #
   # state            : the text to be dispalyed in the state column of the dispatch console
   #
   #--------------------------------------------------------------------------------------------------
   def _print(self,function,msg_level,train_name,text,state=None) :
       try:
          t=threading.Thread(target=self.start,kwargs={'function':function,'msg_level':msg_level,'controller':self.controller,\
                                                       'train_name':train_name,'text':text,'state':state})
          t.start()
       except:
           print(traceback.format_exc()) 
   def start(self,function=None,msg_level=None,train_name=None,text=None,state=None,controller=None):
       try:
          self.function=function
          self.controller=controller
          self.text=text
          self.color_start=""
          self.color_stop=""
          if msg_level in layoutConfig.ignore:
             if state!=None:
                self.setState() 
             return
          self.train_name  = train_name
          #if self.train_name.upper()=="IGNORE"  or self.train_name.upper()=="DUMMY":
          #   self.train_name=""
   
          self.msg_level=msg_level.strip()
          self.state=state
   
          if (self.color):
              self.color_start=layoutConfig.color["NORMAL"]
              self.color_stop=layoutConfig.color["STOPCOLOR"]
              if self.msg_level in layoutConfig.color:
                 self.color_start=layoutConfig.color[self.msg_level]
          
          self.color_stop=layoutConfig.color["STOPCOLOR"]
          self.msg_text="{}{}{}{}{}{}{}".format(self.color_start,\
                                                self.caller.ljust(20," "),\
                                                self.function.ljust(23," "),\
                                                self.msg_level.strip().ljust(23," "),\
                                                str(self.train_name).strip().ljust(15," "),\
                                                str(self.text).strip(),\
                                                self.color_stop)
          #
          # If the state is not None then ask the panel manager to update the status
          #
          if self.state!=None:
             self.setState()
          print(self.msg_text)
          time.sleep(0.1)
          sys.stdout.flush()
          time.sleep(0.1)
          if self.controller!=None and layoutConfig.trace_active_requests_status and not self.train_name=='system':
             request=self.controller.active_requests[self.train_name]
             print("active request status is {} with status reason {} and status code {}".format(request['status'],request['status_reason'],request['status_code']))
             time.sleep(0.1)
             sys.stdout.flush()
             time.sleep(0.1)
     
       except:
          print(traceback.format_exc()) 
          sys.stdout.flush()
   def setState(self):
      # print(">>>>>>>>>>>>>>>>>>>>>>>>> Setting panel status to {}".format(self.state))
      return

















