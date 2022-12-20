import ast
import threading
import traceback
import os
import queue
import sqlite3 as sqlite
import layoutUtils as utils
import layoutReload

import layoutConfig

from importlib import reload
'''
#----------------------------------------------------------------------------------
# Booking manager class
#
# create a databse to hold the sensors and their current value
# start the tcp server and wait for requests 
# the tcp server will add the request to teh booking manager queue
#
# get a request from the queue and process it
#
# the booking mnaager is desinged to be called by the layout appliaction therefore 
# error checking is limited
#
#----------------------------------------------------------------------------------
'''
class bookingManager():
      def __init__(self):
        self.sensor_table   = "sensor_table"
        self.table_justify  = 30
        self.bm_queue       = queue.Queue()
        self.printMsg       = utils.printMsg(caller='bookingManager')
        self.function_name  = "f(bookingManager)"
        self.db_initialised = False
        self.stop           = False
        
        self.curLock        = threading.Lock()
 
        self.printMsg._print(self.function_name,"BKMGR_INIT","system","Booking manager starting")
      
      def start(self):
          
          self.createDatabase()
          tcpServer=utils.tcpServer(caller='bookingManager',queue=self.bm_queue,manager_type='bookingmanager')
          if not tcpServer.start():
             self.Stop()
          
          try:
             while True:
                   client_socket,client_raddr,client_request=self.bm_queue.get()
                   if layoutConfig.reload_modules: layoutReload.reloadModules().reloadModules()
                   
                   try:
                      request=ast.literal_eval(client_request)
                   except:
                      print("failed to create dictionary from string >>>>{}<<<< with ast closeing raddr={}".format(client_request,client_raddr)) 
                      client_socket.close()
                      continue
                   
                   t=threading.Thread(target=self.processCommand,kwargs={'request':request,'client_socket':client_socket,'client_raddr':client_raddr,'cursor':self.cur})
                   t.start()
          
          except Exception:
             self.printMsg._print("f(start)","ERROR","system",traceback.format_exc())
      #===========================================================================================================================
      # Process the command sent ot the booking manager
      #===========================================================================================================================
      def processCommand(self,request=None,client_socket=None,client_raddr=None,cursor=None):
          try:
              error_message="UNKNOWN COMMAND"
              error_code=4999
              cmd_successful=False
              
              self.printMsg._print('f(processCommand)','BKMGR_REQUEST','system',f'received request {request} from {client_raddr}')
              #--------------------------------------------------------------------------------------
              # Call the appropriate function to handle the request
              #--------------------------------------------------------------------------------------
              request_save=request.copy()
              request['cmd'] = request['cmd'].lower()
              
              if request['cmd']=="set_sensors":
                 cmd_successful,error_code,error_message=self.setValueOrOwner(request)
                 
              elif request['cmd']=="book_sensors":
                 cmd_successful,error_code,error_message=self.bookSensors(request)
          
              elif request['cmd']=="release_sensors":
                 cmd_successful,error_code,error_message=self.releaseSensors(request)
              
              elif request['cmd']=="add_sensors":
                 cmd_successful,error_code,error_message=self.addSensorToTable(request)
              
              elif request['cmd']=="are_you_ready":
                   cmd_successful=True
                   error_code=0
                   error_message=''
              elif request['cmd']=="print_table":
                 error_message=''
                 error_code=0
                 cmd_successful=True
                 self.printTable(cursor=cursor)
              
              elif request['cmd']=="stop":
                   self.Stop()
              #---------------------------------------------------------------------------------------
              # respond to the client and close the socket
              #---------------------------------------------------------------------------------------
              response=f"{{'cmd_successful':{cmd_successful},'error_message':'{error_message}','error_code':{error_code} ,'request':{request_save}}}"
              
              if error_code==4006 or error_code==4003:
                 self.printMsg._print('f(processCommand)','BKMGR_RESPONSE_FB','system',f'{response} to {client_raddr}') 
                 
              elif error_code>0:
                 self.printMsg._print('f(processCommand)','BKMGR_RESPONSE_ERR','system',f'{response} to {client_raddr}')
              else:    
                 self.printMsg._print('f(processCommand)','BKMGR_RESPONSE','system',f'{response}  to {client_raddr}')
              
              client_socket.send(response.encode()) 
              #print("Closing client socket raddr={}".format(client_raddr))     
              client_socket.close()  
         
          except Exception as err:
              self.printMsg._print("f(proessCommand)","ERROR","system",traceback.format_exc()) 
              return(cmd_successful,error_code,error_message)
      #======================================================================================================
      # Stop myself from running
      #======================================================================================================
      def Stop(self):
          self.printMsg._print('f(processCommand)',"WARNING","system","stop request received")
          os.system('kill {}'.format( os.getpid()))
          sys.exit(1)
      #===========================================================================================================================
      #  Build the database to hold the sensors and their value
      #===========================================================================================================================
      def createDatabase(self):
         self.printMsg._print(self.function_name,"BKMGR_INFO","system","creating instroage layout sensor database")
         
         self.database=":memory:"                                            # In mmory database
         
         self.db=sqlite.connect(self.database,check_same_thread=False)       # Get a databse object
         self.db.row_factory = sqlite.Row

         self.cur = self.db.cursor()                                          # Get a cursor to the database
         self.cur.execute('SELECT SQLITE_VERSION()')                          # Get the version
         self.data = self.cur.fetchone()                                      # Get the line

         self.printMsg._print(self.function_name,"BKMGR_INFO","system",f"SQLite version: {self.data[0]}")
         #----------------------------------------------------------------------------------------------
         # Create a table to hold our sensor information
         #---------------------------------------------------------------------------------------------
         self.sql=(f"CREATE TABLE IF NOT EXISTS {self.sensor_table} (SENSOR PRIMARY KEY,OWNER text,VALUE text)")
         self.cur.execute(self.sql)

         self.printMsg._print(self.function_name,"BKMGR_INIT","system","Booking Manager database started")
         self.db_initialised=True
         return
      #===========================================================================================================================
      # change the value of a sensor ACTIVE|INACTIVE.
      #===========================================================================================================================
      def setValueOrOwner(self,request,owner=None):
          function_name = "f(setValueOrOwner)"
          try:
              if isinstance(request["sensors"],tuple) or isinstance(request["sensors"],list):
                 sensors= request["sensors"] 
              else:
                 sensors= request["sensors"].split(',')
                 
              for b in sensors: 
                  if b=='' : continue

                  if owner:
                     sql=f"UPDATE {self.sensor_table} SET OWNER='{owner}' WHERE SENSOR='{b}'" 
                  else:
                     sql=f"UPDATE {self.sensor_table} SET VALUE='{request['value'].upper()}' WHERE SENSOR='{b}'"
                  with self.curLock:
                       self.cur.execute(sql)

          except sqlite.Error as err:
                 error_message=err
                 error_code=4002
                 cmd_successful=False
                 self.printMsg._print("f(setStateOwner)","ERROR","system",traceback.format_exc())
                 return(cmd_successful,error_code,error_message)
          except Exception as err:
                 error_message=err
                 error_code=4999
                 cmd_successful=False
                 self.printMsg._print("f(setStateOwner)","ERROR","system",traceback.format_exc())
                 return(cmd_successful,error_code,error_message)
          error_message=''
          error_code=0
          cmd_successful=True
          return (cmd_successful,error_code,error_message)
      #===========================================================================================================================
      # Add a sensor to be managed to the database
      #===========================================================================================================================
      def addSensorToTable(self,request):
          
          function_name = "f(addSensorToTable)"
          
          request["sensors"]=f'{request["sensors"]},'.split(',')
          
          for b in request["sensors"]:
              if b=="" : continue
              b=b.strip()
              request["value"]=request["value"].strip()
              request["owner"]=request["owner"].strip()    
              try:
                 sql=(f'INSERT OR REPLACE INTO  {self.sensor_table}  (SENSOR,VALUE,OWNER) VALUES("{b}","{request["value"].upper()}","{request["owner"]}")')  
                 with self.curLock: 
                      self.cur.execute(sql)
              except sqlite.Error as err:
                  error_message=err
                  error_code=4001
                  cmd_successful=False
                  return(cmd_successful,error_code,error_message)
              except Exception as err:
                  error_message=err
                  error_code=4999
                  cmd_successful=False
                  return(cmd_successful,error_code,error_message)
          
          error_message=''
          error_code=0
          cmd_successful=True
          
          return(cmd_successful,error_code,error_message)
      #===========================================================================================================================
      # Book a sensor or list of sensors if the sensor is not inactive then it cannot be booked
      #
      # If the owner is the same as the owner in the table then book it
      # if the owner is blank, and it is not active  then book it
      # if the owner is not blank, not none and not me then dont reserve.
      #
      # Note the first sensor in the request must be the first sensor in the sub route 
      #      or route
      #
      # Note the row retrieved is in the order it was created - sensor, owner,value
      #
      # Note it is assumed that all sensors exist in the table
      #
      # note force will book the first sensor in the block as long as it is owned by owner
      #
      #===========================================================================================================================
      def bookSensors(self,request):
          function_name = "f(bookSensor)"

          if isinstance(request["sensors"],tuple) or isinstance(request["sensors"],list):
              sensors=request["sensors"]
          else:
             sensors=f'{request["sensors"]},'.split(',')

          cmd_successful=True
          error_message=''
          error_code=0
          for sensor_number,b in enumerate(sensors):
              if b=='': continue
              
              sql=f'select * from {self.sensor_table} where SENSOR="{b}"'
              with self.curLock:
                   self.cur.execute(sql)

              row=self.cur.fetchone()
 
              if row :
                 if (request['force']=='True' and sensor_number==0) or \
                         (row['OWNER']==request['owner'])    or \
                         (row['OWNER'] == 'None' and row['VALUE']=='INACTIVE'):
                    pass
                 else:
                    if row['OWNER'] != 'None':
                       error_message=f'sensor {b} value {row["VALUE"]}, is owned by {row["OWNER"]}'
                       error_code=4006
                    else:
                       error_message=f'sensor {b} value is {row["VALUE"]}, is not owned by {request["owner"]} and is not forced so sensor cannot be booked'
                       error_code=4003
                    cmd_successful=False
                    break
          if cmd_successful:
             cmd_successful,error_code,error_message=self.setValueOrOwner(request,owner=request['owner'])
          return(cmd_successful,error_code,error_message) 
      #===============================================================================================================================
      # Relese sensors for a train.
      #
      #  Note if a block is active it is not released and if a list oc sensors to be released has any sensor active none are released
      #
      #===============================================================================================================================
      def releaseSensors(self,request):
          function_name = "f(releaseSensor)"
          
          cmd_successful=True
          error_code=0
          error_message=''
          
          if isinstance(request["sensors"],tuple) or isinstance(request["sensors"],list):
              sensors=request["sensors"]
          else:
              sensors=f'{request["sensors"]},'.split(',')

          if 'force' in request:
              force=request['force']
              if str(force).upper()=='TRUE' or str(force).upper()=='1':
                 force=True 
              else:
                 force=False

          self.sql=f'SELECT * FROM {self.sensor_table} where (OWNER="{request["owner"]}")'
          
          with self.curLock:
               self.cur.execute(self.sql)
          
               rows=self.cur.fetchall()
          
          if len(rows)>0:
             table_sensors={}
             for row in rows:
                 table_sensors[row['sensor']]={'value':row['VALUE'],'owner':row['OWNER']}
             for sensor in sensors:
                 if len(table_sensors)==0:
                    cmd_successful=False
                    error_code=4006
                    error_message=f'sensor or sensors not booked' 
                    release=False
                    break
                 elif sensor.upper()=='ALL':
                     sensors=table_sensors
                     release=True
                     break
                 elif sensor not in table_sensors:
                    cmd_successful=False
                    error_code=4007
                    error_message=f'sensor {sensor} with owner {request["owner"]} was not found in the sensor table'
                    release=False
                    break
                 elif force:
                     release=True
                     break
                 elif table_sensors[sensor]['value']=='ACTIVE':
                    error_message="sensor {} is active and cannot be release".format(sensor)
                    cmd_successful=False
                    error_code=4004
                    release=False
                    break
                 else:
                   release=True
          
             if release:     
                for sensor in sensors:  
                    self.sql=f'UPDATE {self.sensor_table} SET OWNER="None" where (SENSOR="{sensor}")'
                    with self.curLock:
                         self.cur.execute(self.sql)
                
                cmd_successful=True
                error_code=0
                error_message=''
          else:
              cmd_successful=True
              error_code=0
              error_message=''        
          return(cmd_successful,error_code,error_message)

      #===========================================================================================================================
      #
      # Print out a table : Note this will be printed on the central jmri server console
      #
      #===========================================================================================================================
      def printTable(self,cursor=None):
          function_name = "f(printTable)"
          #--------------------------------------------------------------------------------------------------
          # Get the header and print it on the screen
          #--------------------------------------------------------------------------------------------------
          header=""

          with self.curLock:
               cursor.execute("select * from "+self.sensor_table+" order by OWNER , VALUE ")
          for col_name in cursor.description :
              header=header+col_name[0].ljust(self.table_justify)+"|"
          self.printMsg._print(function_name,"TABLE",'system',"+"+"-"*self.table_justify*3+"--"+"+")
          self.printMsg._print(function_name,"TABLE",'system',"|"+header)
          self.printMsg._print(function_name,"TABLE",'system',"+"+"-"*self.table_justify*3+"--"+"+")
          #--------------------------------------------------------------------------------------------------
          # Retrieve each row in the table and print it on the screen
          #-------------------------------------------------------------------------------------------------
          rows = cursor.fetchall()
          for i in range(len(rows)):
              data=""
              for j in rows[i-1]:
                  data=data+j.ljust(self.table_justify)+"|"
              self.printMsg._print(function_name,"TABLE",'system',"|"+data)
              import time
              time.sleep(0.001)
              self.printMsg._print(function_name,"TABLE",'system',"+"+"-"*self.table_justify*3+"--"+"+")
          return
#=============================================================================================================
# If running from the command line then do this
#============================================================================================================
if __name__ == "__main__":
   try:
      bm=bookingManager().start()
   except Exception as err:
      utils.printMsg(caller='laytoutBKManager')._print("main","ERROR","system",traceback.format_exc()) 
