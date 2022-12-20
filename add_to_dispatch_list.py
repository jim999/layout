#
#
#
#
try:
   import tkinter as tk
except ImportError:
   import Tkinter as tk
import inspect
import sys

import layout_definitions

module=__import__(layout_definitions.trains_file)
module=__import__(layout_definitions.routes_file)
#================================================================================================================
#
# Display the input panel that will add an entry in the dispatcher launch table
#
#================================================================================================================
class add_to_dispatch_table():

    def  __init__(self):
         self.modes       = ["BACKANDFORTH","CONTINUOS"]
         self.retrys      = 90000
         self.loops       = 2
         self.look_ahead  = 2
         self.directions  = ["FORWARD","REVERSE"]
         self.padding     = "   "
         self.train_names = []
         self.route_names = []
         self.train_name_row = 1
         self.route_name_row = 2
         self.loops_row      = 3
         self.look_ahead_row = 4
         self.retry_row      = 5
         self.mode_row       = 6
         self.direction_row  = 7

         self.root_window =  tk.Tk()

         self.root_window.title("dispatch launch console")
         self.root_window.geometry("300x220")
    #-------------------------------------------------------------------------------------------------------------
    # Get a list of all trains defined in layout_train_profiles.py. These are the only trains allowed
    #-------------------------------------------------------------------------------------------------------------
    def setTrainNames(self):
        train_members=inspect.getmembers(sys.modules[layout_definitions.trains_file], inspect.isclass)

        self.train_names=[]
        
        for train_name in train_members:
            if train_name[0]!="trainDefaultProfileSettings":
               self.train_names.append(train_name[0])
        return self.train_names
    def getTrainNames(self):
        self.setTrainNames()
        return self.train_names()
    #-------------------------------------------------------------------------------------------------------------
    # Get a list of all routes defined in layout_routes_profiles.py. These are the only routes allowed
    #-------------------------------------------------------------------------------------------------------------

    def setRouteNames(self):
        route_members=inspect.getmembers(sys.modules[layout_definitions.routes_file], inspect.isclass)

        self.route_names=[]
        
        for route_name in route_members:
            if route_name[0]!="automationRoutesBaseClass":
               self.route_names.append(route_name[0])
        return self.route_names
        
    def getRouteNames(self):
        self.setRouteNames()
        return self.route_names()
    #--------------------------------------------------------------------------------------------------------------
    # Build and display the panel
    #--------------------------------------------------------------------------------------------------------------
    def display(self):
        
        self.setTrainNames()                                   # set self.train_names
        self.setRouteNames()                                   # set self.route_names
        
        tk.Label(master=self.root_window,text=" ").grid(row=0,column=0)
        tk.Label(master=self.root_window,text="{}Train Name".format(self.padding)).grid(row=self.train_name_row,column=0,sticky="W")
        tk.Label(master=self.root_window,text="{}Route Name".format(self.padding)).grid(row=self.route_name_row,column=0,sticky="W")
        tk.Label(master=self.root_window,text="{}Loops".format(self.padding)).grid(row=self.loops_row,column=0,sticky="W")
        tk.Label(master=self.root_window,text="{}Look Ahead".format(self.padding)).grid(row=self.look_ahead_row,column=0,sticky="W")
        tk.Label(master=self.root_window,text="{}Retrys".format(self.padding)).grid(row=self.retry_row,column=0,sticky="W")
        tk.Label(master=self.root_window,text="{}Mode".format(self.padding)).grid(row=self.mode_row,column=0,sticky="W")
        tk.Label(master=self.root_window,text="{}Direction".format(self.padding)).grid(row=self.direction_row,column=0,sticky="W")



        train_name_list_value=tk.StringVar(self.root_window)
        train_name_list_value.set(self.train_names[0])
        train_name_menu= tk.OptionMenu(self.root_window, train_name_list_value,*self.train_names)
        train_name_menu.grid(row=self.train_name_row,column=1,sticky="W")
        
        route_name_list_value=tk.StringVar(self.root_window)
        route_name_list_value.set(self.route_names[0])
        route_name_menu= tk.OptionMenu(self.root_window, route_name_list_value,*self.route_names)
        route_name_menu.grid(row=self.route_name_row,column=1,sticky="W")
        
        entry_loops      = tk.Entry(master=self.root_window)
        entry_look_ahead = tk.Entry(master=self.root_window)
        entry_retrys     = tk.Entry(master=self.root_window)

        entry_loops.grid(row=3, column=1,sticky="W")
        entry_look_ahead.grid(row=4, column=1,sticky="W")
        entry_retrys.grid(row=5,column=1,sticky="W")

        entry_retrys.insert(0,"90000")
        entry_loops.insert(0,"2")
        entry_look_ahead.insert(0,"2")


        mode_list_value = tk.StringVar(self.root_window)                                          # Variable to keep track of the option selected in mode menue
        mode_list_value.set(self.modes[0])
        mode_menu = tk.OptionMenu(self.root_window, mode_list_value,*self.modes)                  # Create the mode menu widget and passing the options_list and mode_value to it
        mode_menu.grid(row=self.mode_row,column=1,sticky="W")

        direction_list_value = tk.StringVar(self.root_window)
        direction_list_value.set(self.directions[0])
        direction_menu  = tk.OptionMenu(self.root_window, direction_list_value,*self.directions)
        direction_menu.grid(row=self.direction_row,column=1,stick="W")

        add_button = tk.Button(self.root_window, text="Add",command=self.add)
        add_button.grid(row=99,column=0,sticky="W")

        quit_button = tk.Button(self.root_window, text="Quit",command=self.close)
        quit_button.grid(row=99,column=1,sticky="E")

        self.root_window.mainloop()

    #----------------------------------------------------------------------------------------
    # close the panel
    #----------------------------------------------------------------------------------------
    def close(self):
        #self.closeDB()
        self.root_window.destroy()
    
    #-----------------------------------------------------------------------------------------
    # Add an entry to the sql database
    #------------------------------------------------------------------------------------------
    def add(self):
        pass
        # self.addRecord()
    def openDB(self)
        

add_window=add_to_dispatch_table()
add_window.display()

