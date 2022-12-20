#==========================================================================================================
# Requires     : layout_lefcm and layoutSchemaColors
#
# Author       : Jim Anderson
#
# Desription   : Code to dynamically change the colors, fonts etc. used on a JMRI Layout Editor Panel.
#
#=========================================================================================================
import traceback
import threading
import time

import jmri
import jmri.util.FileUtil as FileUtil
import java
import java.lang.ThreadDeath

from javax.swing import JMenu
from javax.swing import JMenuItem
from javax.swing import JCheckBoxMenuItem
from javax.swing import JFileChooser
from javax.swing import JOptionPane
from javax.swing.filechooser import FileFilter

from java.io import FileWriter
from java.io import File

from java.util import Scanner

import sys


if 'layout_lefcm' not in sys.modules:
    SNAPSHOT=True
else:
    SNAPSHOT=False
    
import layout_lefcm
reload(layout_lefcm)

import layoutSchemaConfig

import layoutSchemaLefcmMin



reload(layoutSchemaLefcmMin)

reload(layoutSchemaConfig)

version = "1.0.0"

'''
#==========================================================================================================
#
# A class to manipulate the layoutEditor setting on any layoutEditor Frames that are open
#
#============================================================================================================
'''
class layoutEditorFrameColorManager(jmri.jmrit.automat.AbstractAutomaton):
    #global layout_editor_event_monitor
    #--------------------------------------------------------------------------------------------------------
    # jmri init function 
    #--------------------------------------------------------------------------------------------------------
    def init(self):
        self.frames=self.getLayoutEditorFrames()
        return
    #--------------------------------------------------------------------------------------------------------
    # jmri handle function
    #--------------------------------------------------------------------------------------------------------
    def handle(self):
        try:
           self.main_code()
        except java.lang.ThreadDeath:
           pass
        except:
            print(traceback.format_exc())
    def main_code(self):
        #-----------------------------------------------------------------------------------------------------
        # check if we are already running. If so then stop any old version and leave the new instance running
        #-----------------------------------------------------------------------------------------------------
        num_instances=0
        number_of_instances=jmri.jmrit.automat.AutomatSummary.instance().length()
        for i in range(number_of_instances):
            jmri_thread_name=jmri.jmrit.automat.AutomatSummary.instance().get(i).getName()
            my_name=type(self).__name__
            if my_name in jmri_thread_name :
                num_instances=num_instances+1
        while num_instances >1:
           n=jmri.jmrit.automat.AutomatSummary.instance().length()
           for i in range(n):
               jmri_thread_name=jmri.jmrit.automat.AutomatSummary.instance().get(i).getName()
               if my_name in jmri_thread_name :
                   jmri.jmrit.automat.AutomatSummary.instance().get(i).stop()
                   break
           num_instances=num_instances-1
        #----------------------------------------------------------------------------------------------------
        # Save the current colors and set up an edit mode action routine
        #----------------------------------------------------------------------------------------------------
        self.saveEditModesAndAddAction()
        #----------------------------------------------------------------------------------------------------
        # Sit here forever doing nothing. the action routines will handle everything
        #---------------------------------------------------------------------------------------------------
        try:
           event_object=threading.Event()
           event_object.wait()
        except:
            pass
    #--------------------------------------------------------------------------------------------------------
    # get all layout editor frames
    #--------------------------------------------------------------------------------------------------------
    def getLayoutEditorFrames(self):
        frames={}
        for frame in jmri.util.JmriJFrame.getFrameList():
            if isinstance(frame, jmri.jmrit.display.layoutEditor.LayoutEditor):
               frames[frame.getTitle()]=frame
        return frames
    #---------------------------------------------------------------------------------------------------------
    # get the edit mode for all panels and save them, then add an action routine 
    #----------------------------------------------------------------------------------------------------------
    def saveEditModesAndAddAction(self):
        for title,frame in self.frames.items():
           menu_bar=frame.getJMenuBar()
           for x in range(menu_bar.getMenuCount()):
               menu_item=menu_bar.getMenu(x)
               if menu_item.text=="Options":
                  for y in range(menu_item.getItemCount()):
                      if  menu_item.getItem(y)!=None and menu_item.getItem(y).text=="Edit Mode":
                         if menu_item.getItem(y).isSelected() :
                             edit_mode=True
                         else:
                             edit_mode=False
                         menu_item.getItem(y).actionPerformed=editModeAction(title,edit_mode,SNAPSHOT).actionToPerform
'''
#-----------------------------------------------------------------------------------------------
# Class to perform an action when the edit mode state chnages
#-----------------------------------------------------------------------------------------------
'''        
class editModeAction(FileFilter):
      def __init__(self,title,edit_mode,SNAPSHOT):
          self.jython_scripts_path     = FileUtil.getScriptsPath()
          self.current_dir             = None
          self.instorgae_schema_loaded = False
          self.menu_schema             = None
          self.menu_bar                = None
          self.active_schema           = None                                  # Name of the schema being used from the schema menu
          self.active_schema_values    = {}
          self.original_schema_values  = layoutSchemaLefcmMin.active_schema_values
          self.suspend_schema_action   = False
          self.title                   = title
          self.edit_mode               = edit_mode
          self.schema_types            = (".schema",)
     
          self.frame=jmri.util.JmriJFrame.getFrame(self.title)
          
          layoutSchemaConfig.ORIGINAL=self.original_schema_values
          layoutSchemaConfig.color_schema_menu_items["Original"]=self.original_schema_values
          self.frame.repaint()
          #-------------------------------------------------------------------------------------------------
          # If this is the first time we have run then take a snapshot of the panel colors
          # incase we are reinvoked.
          #-------------------------------------------------------------------------------------------------
          if SNAPSHOT:
             self.active_schema="Original"
             exec("self.original_schema_values="+self.getActiveSchemaValues())

             layoutSchemaConfig.color_schema_menu_items ["Original"]=self.original_schema_values

             file_writer = FileWriter(self.jython_scripts_path+"__ORIGINAL__.schema")
             for x in self.getActiveSchemaValues():
                 file_writer.write(x)
             file_writer.close()
          else:
            old_active_schema=self.active_schema
            
            self.active_schema="Original"
            file_reader=Scanner(File(self.jython_scripts_path+"__ORIGINAL__.schema")) 
           
            data=""
           
            while file_reader.hasNextLine():
                 data = data+file_reader.nextLine()
           
            file_reader.close()
           
            self.original_schema_values=eval(data)
            
            layoutSchemaConfig.ORIGINAL=self.active_schema
            self.active_schema=old_active_schema
           
          self.createSchemaMenu()
      #-----------------------------------------------------------------------------------------------
      # Do this section when a layoutEditor panel moves between modes (edit mode selected or edit mode
      # deselected.
      #------------------------------------------------------------------------------------------------
      def actionToPerform(self,e):
          try:
             self.newValue=e.source.isSelected()
             self.edit_mode=self.newValue
             
             if self.newValue:
                self.newValueText="True"
             else:
                 self.newValueText="False"
             return                 
             #self.createSchemaMenu()                                      # Create the schema menu
             #self.getActiveSchemaValues()                                 # get the settings currently defined
          except java.lang.Exception as err:
              print(traceback.format_exc()) 
          except:
              print(traceback.format_exc())
      #------------------------------------------------------------------------------------------------------------
      # Do this if a schema is selected from the menu_bar schema then set the panels colors. this is called via an 
      # actionPerformed callback
      #------------------------------------------------------------------------------------------------------------
      def setPanelColors(self,e):
          try:
              if not self.suspend_schema_action:
                 self.active_schema=e.getActionCommand()
                 layout_lefcm.active_schema=self.active_schema
                 
                 self.setColors()                                           # Set the colors for the active schema
                 self.getActiveSchemaValues()                               
                 self.frame.setAllTracksToDefaultColors()                   # Get jmri to Update the display
                 self.saveLayoutLEFCM()                                     # Save the active schema stuff for another time
          except java.lang.Exception as err:
              print(traceback.format_exc())
          except:
              print(traceback.format_exc())
          return
      #------------------------------------------------------------------------------------------------------
      # Do this when we want to reload the frame color manager config
      #------------------------------------------------------------------------------------------------------
      def reloadFCMConfig(self):
          reload(layoutSchemaConfig)
          layoutSchemaConfig.color_schema_menu_items["Original"]=self.original_schema_values
      #-------------------------------------------------------------------------------------------------------
      # Moving from edit_mode selected to edit_mode not selected so add a menu item ("Schema") to the menu bar 
      # and restore the colors that were saved before we went to edit mode. 
      #--------------------------------------------------------------------------------------------------------
      def createSchemaMenu(self):

          if self.suspend_schema_action:
             return
          self.menu_schema=JMenu("Schema")
          self.menu_bar=self.frame.getJMenuBar()
          #--------------------------------------------------------------------------------------
          # remove any old schema entries from the menu_bar
          #--------------------------------------------------------------------------------------
          for _ in range(self.menu_bar.getMenuCount()):
             if str(self.menu_bar.getComponent(_).text)=="Schema":
                self.menu_bar.remove(_)

          self.menu_bar.add(self.menu_schema)
          self.menu_bar.validate()
          #------------------------------------------------------------------------------------
          # Add any valid menu items to the new menue_bar (schema) and add an actionPerformed 
          # function for each menu item 
          #------------------------------------------------------------------------------------
          x=[]
          for _ in layoutSchemaConfig.color_schema_menu_items:
            x.append(str(_))
          x.sort()
          for name in x:
              self.menu_schema.add(JMenuItem(name,actionPerformed=self.setPanelColors))

          if self.isInstorgeSchemaLoaded():
             self.instorage_menu_item=JMenuItem("Instorage",actionPerformed=self.setPanelColors)
             self.menu_schema.add(self.instorage_menu_item)
          
          self.menu_schema.addSeparator()
          
          self.suspendCheckBox=JCheckBoxMenuItem("Suspend",actionPerformed=self.suspendSchema)

          self.menu_schema.add(self.suspendCheckBox)
          self.menu_schema.addSeparator()
          
          self.menu_schema.add(JMenuItem("Export",actionPerformed=self.saveSchema))
          self.menu_schema.addSeparator()
          
          #-----------------------------------------------------------------------------------------------
          # if we are not in edit mode thne add the show all option 
          #-----------------------------------------------------------------------------------------------
          self.menu_schema.add(JMenuItem("Import",actionPerformed=self.loadSchema))
          self.menu_schema.addSeparator()
          self.menu_schema.add(JMenuItem("Reload schemas",actionPerformed=self.reloadSchemaMenuActionToPerform))
          self.menu_schema.addSeparator()
          self.menu_schema.add(JMenuItem("About schema",actionPerformed=self.aboutActionToPerform))

          self.setColors()
          
          #-----------------------------------------------------------------------------------
          # validate
          #-----------------------------------------------------------------------------------
          self.menu_bar.validate()
          return
      #--------------------------------------------------------------------------------------------------
      #
      #----------------------------------------------------------------------------------------------
      def reloadSchemaMenuActionToPerform(self,e):
          self.reloadFCMConfig()
          self.createSchemaMenu()
          self.createSchemaMenu()
          return
      #-----------------------------------------------------------------------------------------
      # Do this action when about is selcted fomr the schema menu
      #-----------------------------------------------------------------------------------------
      def aboutActionToPerform(self,e):
          infoMessage="LayoutEditor Frame Color Manager\n "+\
                      "       Version {}".format(version)
          JOptionPane.showMessageDialog(self.frame, infoMessage, "InfoBox: "+self.frame.getTitle(), JOptionPane.INFORMATION_MESSAGE);
          return
      #-----------------------------------------------------------------------------------------
      # Set the color scheme
      #
      # Calls setBlockContents and setPositioableLabels
      #------------------------------------------------------------------------------------------
      def setColors(self):
          self.reloadFCMConfig()
          if self.active_schema==None:
             return
          if self.active_schema.upper()=="INSTORAGE":
              schema=self.instorage_schema_values
          elif self.active_schema.upper()=="ORIGINAL":
              schema=self.original_schema_values
          else:
             schema=layoutSchemaConfig.color_schema_menu_items[str(self.active_schema)]
             
          if "booked_track_color" not in schema:
             schema["booked_track_color"]="java.awt.Color(255,255,255)"
             
          if "background_color" in schema:
             
             self.frame.setBackgroundColor(schema["background_color"])
          if "default_track_color" in schema:
              self.frame.setDefaultTrackColor(schema["default_track_color"])
          if "occupied_track_color" in schema:
             self.frame.setDefaultOccupiedTrackColor(schema["occupied_track_color"])
          if "turnout_circle_thrown_color" in schema:
              self.frame.setTurnoutCircleThrownColor(schema["turnout_circle_thrown_color"])
          if "turnout_circle_color" in schema:
             self.frame.setTurnoutCircleColor(schema["turnout_circle_color"])
          if "turnout_circle_size" in schema:
              self.frame.setTurnoutCircleSize(schema["turnout_circle_size"])
          if "positionable_labels" in schema:
              self.positionable_labels=schema["positionable_labels"]
              self.setPositionableLabels()
          else:
             self.positionable_labels=None
             
          if "block_contents_icon" in schema:
              self.setBlockContents(schema)
      #------------------------------------------------------------------------------------------------
      # Do this to set to colors for the blockContentsIcons
      #
      # Should only be invoked by setColors
      #
      #------------------------------------------------------------------------------------------------
      def setBlockContents(self,schema):
          #------------------------------------------------------------------------------------------------
          # set the global values
          #------------------------------------------------------------------------------------------------
          for x in self.frame.getBlockContentsLabelList():
              x.setHidden(layoutSchemaConfig.hidden_default_state)
              x.setFont(java.awt.Font(layoutSchemaConfig.font_name_default,\
                                      layoutSchemaConfig.font_bold_default|layoutSchemaConfig.font_italic_default,\
                                      layoutSchemaConfig.font_size_default))
              font=x.getFont()
              
              if x.getText()!=None:
                 width=x.getFontMetrics(font).stringWidth(x.getText())
                 width=width+10
                 font_dimension=java.awt.Dimension(width,font.getSize())
                 x.setSize(font_dimension)
          
          if "block_contents_icon" in schema:
            for blockContentsIcon in self.frame.getBlockContentsLabelList():
             
              s1=s2=False
              
              if "color" in schema["block_contents_icon"]:
                 blockContentsIcon.setForeground(schema["block_contents_icon"]["color"])
              else:
                 blockContentsIcon.setForeground(java.awt.Color(0,0,0))
                 
              if "bold" in schema["block_contents_icon"]:
                  if schema["block_contents_icon"]["bold"]:
                     s1=java.awt.Font.BOLD
                  else:
                     s1=java.awt.Font.PLAIN
              
              if "italic" in schema["block_contents_icon"]:
                  if schema["block_contents_icon"]["italic"]:
                     s2=java.awt.Font.ITALIC
              
              if "name" in schema["block_contents_icon"]:
                  name=schema["block_contents_icon"]["name"]
              else:
                  name=blockContentsIcon.getFont().name
              
              if "size" in schema["block_contents_icon"]:
                 s3=schema["block_contents_icon"]["size"]
              else:
                 s3=blockContentsIcon.getFont().size
              
              blockContentsIcon.setFont(java.awt.Font(name,s1|s2,s3))
              font=blockContentsIcon.getFont()

              text=str(blockContentsIcon.getText())

              font=java.awt.Font("Dialog", s1|s2, s3)
              
              blockContentsIcon.setFont(font)
 
              width=blockContentsIcon.getFontMetrics(font).stringWidth(text)+5

              blockContentsIcon.setSize(width,s3)
          return
      #---------------------------------------------------------------------------------------------
      # Should only be invoked by setColors
      #----------------------------------------------------------------------------------------------
      def setPositionableLabels(self):
          hidden_state_default = layoutSchemaConfig.hidden_default_state
          font_size_default    = layoutSchemaConfig.font_size_default
          font_name_default    = layoutSchemaConfig.font_name_default
          font_bold_default    = layoutSchemaConfig.font_bold_default
          font_italic_default  = layoutSchemaConfig.font_italic_default
          font_color_default   = layoutSchemaConfig.font_color_default
          #-------------------------------------------------------------------------------------------------
          # For this schema set the hidden state if sepecified
          #-----------------------------------------------------------------------------------------------
          if self.active_schema.upper()=="INSTORAGE":
             config=eval("layoutSchemaConfig.INSTORAGE")
          else:
              config=layoutSchemaConfig.color_schema_menu_items[self.active_schema]
              
          if 'hidden' in config:
              hidden_state_default = config['hidden']
              
          if 'font_name' in config:
              font_name_default = config['font_name']
              
          if 'font_size' in config:
              font_size_default = config['font_size']
              
          if 'font_bold' in config:
              font_bold_default = config['font_bold']
              
          if 'font_italic' in config:
              font_italic_default = config['font_italic']
          
          for frame_positionable_label in self.frame.getLabelImageList():
              if frame_positionable_label.getText()!=None:
                 frame_positionable_label.setHidden(hidden_state_default)
                   
                 frame_positionable_label.setFont(java.awt.Font(font_name_default, font_bold_default|font_italic_default, font_size_default))
                 
                 font=frame_positionable_label.getFont()
                 
                 width=frame_positionable_label.getFontMetrics(font).stringWidth(frame_positionable_label.getText())
                 
                 width=width+10
                 
                 font_dimension=java.awt.Dimension(width,font.getSize())
                 
                 frame_positionable_label.setSize(font_dimension)
                 
                 for starts_with_text in self.positionable_labels:
                     
                     size=font_size_default
                     font=font_name_default
                     s1=font_bold_default
                     s2=font_italic_default
                     
                     if frame_positionable_label.getText().startswith(starts_with_text):
                        if "hidden" in self.positionable_labels[starts_with_text]:
                            frame_positionable_label.setHidden(self.positionable_labels[starts_with_text]["hidden"])
                    
                        if 'color' in self.positionable_labels[starts_with_text]:
                            frame_positionable_label.setForeground(self.positionable_labels[starts_with_text]['color'])
                        font=frame_positionable_label.getFont()
                        
                        if "size" in self.positionable_labels[starts_with_text]:
                            size=self.positionable_labels[starts_with_text]['size']
                        if 'bold' in self.positionable_labels[starts_with_text]:
                            if self.positionable_labels[starts_with_text]["bold"]:
                                s1=java.awt.Font.BOLD
                            else: s1=java.awt.Font.PLAIN
                        else: s1=font.getStyle()
                        
                        if 'italic' in self.positionable_labels[starts_with_text]:
                            if self.positionable_labels[starts_with_text]["italic"]:
                                s2=java.awt.Font.ITALIC
                            else: s2=java.awt.Font.PLAIN
                        else: s2=font.getStyle()
                        
                        style=s1|s2
                    
                        if 'font' in self.positionable_labels[starts_with_text]:
                            font_name=self.positionable_labels[starts_with_text]['font']
                        else: font_name=font.getName()
                        
                        frame_positionable_label.setFont(java.awt.Font(font_name, style, size))
                        font=frame_positionable_label.getFont()
                        width=frame_positionable_label.getFontMetrics(font).stringWidth(frame_positionable_label.getText())
                        
                        width=width+10
                        font_dimension=java.awt.Dimension(width,size)
                        
                        frame_positionable_label.setSize(font_dimension)
      #---------------------------------------------------------------------------------------------------------------------
      # Get the layout values we are interested in
      #---------------------------------------------------------------------------------------------------------------------
      def getActiveSchemaValues(self):
          spaces=10
          if self.active_schema==None:
             return
          if self.active_schema.upper()=="INSTORAGE":
             config=eval("layoutSchemaConfig.INSTORAGE")
          elif self.active_schema.upper()=="ORIGINAL":
             config=eval("layoutSchemaConfig.ORIGINAL")
          else:
             config=layoutSchemaConfig.color_schema_menu_items[self.active_schema]
          #---------------------------------------------------------------------------------------------------------------
          # Do background, turnout track colors and turnout circle size
          #--------------------------------------------------------------------------------------------------------------
          if self.active_schema=="INSTORAGE":
             name = "INSTORAGE"
             booked_track_color=self.frame.defaultAlternativeTrackColorColor
          elif self.active_schema=="Original":
             name="ORIGINAL"
             booked_track_color=self.frame.defaultAlternativeTrackColorColor
          elif "NAME" in config:
              name=config["NAME"]
          else:
              name=self.active_schema
          
          name="'{}'".format(name)

          if (self.active_schema!="INSTORAGE" ):
             if "booked_track_color" not in config:
                 if self.frame.getBackgroundColor()==java.awt.Color.white:
                    booked_track_color=java.awt.Color.black
                 else:
                    booked_track_color=java.awt.Color.white
             else:
                booked_track_color=config["booked_track_color"]

          if layoutSchemaConfig.hidden_default_state:
              hs="True"
          else:
              hs="False"
          if layoutSchemaConfig.font_bold_default:
              fb="True"
          else:
              fb="False"
          if layoutSchemaConfig.font_italic_default:
              fi="True"
          else:
              fi="False"
         
          s="{\n"+\
            "'NAME'                                   :  {},\n".format(name)+\
            "'hidden'                                 :  {},\n".format(hs)+\
            "'font_name'                              : '{}',\n".format(layoutSchemaConfig.font_name_default)+\
            "'font_bold'                              :  {},\n".format(fb)+\
            "'font_italic'                            :  {},\n".format(fi)+\
            "'font_size'                              :  {},\n".format(layoutSchemaConfig.font_size_default)+\
            "'background_color'                       :  {},\n".format(self.frame.getBackgroundColor())+\
            "'booked_track_color'                     :  {},\n".format(booked_track_color)+\
            "'turnout_cricle_color'                   :  {},\n".format(self.frame.turnoutCircleColor)+\
            "'turnout_circle_thrown_color'            :  {},\n".format(self.frame.turnoutCircleThrownColor)+\
            "'turnout_circle_size'                    :  {},\n".format(self.frame.getTurnoutCircleSize())+\
            "'default_track_color'                    :  {},\n".format(self.frame.getDefaultTrackColorColor())+\
            "'default_track_color_color'              :  {},\n".format(self.frame.getDefaultTrackColorColor())+\
            "'default_occupied_track_color'           :  {},\n".format(self.frame.getDefaultOccupiedTrackColorColor())+\
            "'default_occupied_track_color_color'     :  {},\n".format(self.frame.getDefaultOccupiedTrackColorColor())+\
            "'default_alternative_track_color'        :  {},\n".format(self.frame.defaultAlternativeTrackColorColor)+\
            "'default_alternativeTrack_color_color'   :  {},\n".format(self.frame.defaultAlternativeTrackColorColor)

          while "[" in s:
              s=s.replace("[","(").replace("]",")").replace("r=","").replace("g=","").replace("b=","").strip("(").strip(")")

          #-----------------------------------------------------------------------------------------------------------------
          # Do the block contents labels. We only get the forst one we find
          #-----------------------------------------------------------------------------------------------------------------
          cl=""
          for cl in self.frame.getBlockContentsLabelList():
              cl='{'+"'color' : {}, 'font' : '{}', 'size' : {}, 'bold' : {}, 'italic' : {}, 'hidden' : {}".format(\
                                            str(cl.getForeground()).ljust(31),\
                                            str(cl.getFont().name).ljust(15),\
                                            str(cl.getFont().size).ljust(3),\
                                            str(cl.getFont().isBold()),\
                                            str(cl.getFont().isItalic()),\
                                            str(cl.isHidden()),\
                                            )+'},'
              break
          if cl=="":
             cl="{'__@@dummy@@__':'__@@dummy@@__'},"
          cl="'block_contents_icon'                    :  "+cl
          
          cl=cl.replace("[","(").replace("]",")").replace("r=","").replace("g=","").replace("b=","")                                  

          #------------------------------------------------------------------------------------------------------
          # do the positional labels.
          #------------------------------------------------------------------------------------------------------
          ps=""
          
          for positionable_label in self.frame.getLabelImageList():
              
              if positionable_label.getText()!=None and positionable_label.getText()!="":
                 ss='{'+"'color' : {}, 'font' : '{}', 'size' : {}, 'bold' : {}, 'italic' : {}, 'hidden' : {}".format(\
                                            str(positionable_label.getForeground()).ljust(34),\
                                            str(positionable_label.getFont().name).ljust(15),\
                                            str(positionable_label.getFont().size).ljust(3),\
                                            str(positionable_label.getFont().isBold()).ljust(5),\
                                            str(positionable_label.getFont().isItalic()).ljust(5),\
                                            str(positionable_label.isHidden()),\
                                            )+"},"
                 ps="'"+(positionable_label.getText().strip()+"'").ljust(30)+": "+ss+"\n"+" "*45+ps
          
          if ps=="":
             ps="'__@@dummy@@__':'__@@dummy@@__'},"
          else:
             ps=ps+"\n"+" ".ljust(40)+"},"

          ps="\n'positionable_labels'                    :  {"+ps
          
          ps=ps.replace("[","(").replace("]",")").replace("r=","").replace("g=","").replace("b=","")
          
          active_schema_values=s+cl+ps+"\n"+"}"

          self.active_schema_values=active_schema_values

          return active_schema_values
      #-------------------------------------------------------------------------------------------
      # If the suspend check box was selsected then flag that we should remove the ability to 
      # change schemas
      #--------------------------------------------------------------------------------------------
      def suspendSchema(self,e):
          if e.source.isSelected():
             self.suspend_schema_action=True
          else:
             self.suspend_schema_action=False
             
             
      def isInstorgeSchemaLoaded(self):
          return self.instorgae_schema_loaded
          
      def setInstorageSchemaLoaded(self,value):
          self.instorgae_schema_loaded=value
      #-------------------------------------------------------------------------------------------
      # Do this if we want to save the schema to disk for later use
      #--------------------------------------------------------------------------------------------
      def saveSchema(self,e):
          fileChooser=JFileChooser()

          file_filter=FileFilter(self.schema_types)
          fileChooser.setFileHidingEnabled(False);
          
          if self.current_dir==None:
             fileChooser.setCurrentDirectory(File(self.jython_scripts_path));
          else:
              fileChooser.setCurrentDirectory(File(self.current_dir))

          fileChooser.setDialogType(JFileChooser.SAVE_DIALOG)
          fileChooser.setFileFilter(file_filter)
          #---------------------------------------------------------------------------
          # display the save dialog box and wait on the user to hit the save or cancel
          # button.
          #----------------------------------------------------------------------------

          result=fileChooser.showSaveDialog(self.frame)
          
          if result==JFileChooser.APPROVE_OPTION:
             file_to_save=fileChooser.getSelectedFile()
             self.current_dir=file_to_save.getAbsolutePath()
             
             if not file_to_save.name.lower().endswith(".schema"):
                file_to_save=File("{}{}".format(file_to_save,".schema"))
             #--------------------------------------------------------------------------
             # Check if file already exists, if not save it to disk else ask if we are 
             # to overwrite it. 
             #---------------------------------------------------------------------------
             if file_to_save.createNewFile():
                write_to_disk=True
             else:
                #--------------------------------------------------------------------------
                # Check if the user wants to overwrite the file.
                #--------------------------------------------------------------------------
                write_to_disk=False
                option = JOptionPane.showConfirmDialog (self.frame, "File Already exists, \n      continue?","Warning",JOptionPane.YES_OPTION)
                if option==JOptionPane.YES_OPTION:
                    write_to_disk=True
             #------------------------------------------------------------------------------
             # write the schema to disk
             #------------------------------------------------------------------------------
             if write_to_disk:
                file_writer = FileWriter(file_to_save);
                file_writer.write(self.getActiveSchemaValues())
                file_writer.close()
      #-----------------------------------------------------------------------------------------
      # Do this if we want to load a previouslay saved schema
      #-----------------------------------------------------------------------------------------
      def loadSchema(self,e):
          fileChooser=JFileChooser()
          fileChooser.setFileHidingEnabled(False);
          fileChooser.setDialogType(JFileChooser.OPEN_DIALOG)
          if self.current_dir==None:
             fileChooser.setCurrentDirectory(File(self.jython_scripts_path));
          else:
              fileChooser.setCurrentDirectory(File(self.current_dir))
          file_filter=FileFilter(self.schema_types)
          fileChooser.setFileFilter(file_filter)
          
          result=fileChooser.showOpenDialog(self.frame)
          
          if result==JFileChooser.APPROVE_OPTION:
             file_to_open=fileChooser.getSelectedFile()
             file_to_open=file_to_open.getAbsolutePath()
           
             file_reader=Scanner(File(file_to_open)) 
           
             data=""
           
             while file_reader.hasNextLine():
                  data = data+file_reader.nextLine()
           
             file_reader.close()
           
             self.instorage_schema_values=eval(data)
             
             self.active_schema="INSTORAGE"
             self.setInstorageSchemaLoaded(True)
             
             layoutSchemaConfig.INSTORAGE=self.active_schema
             
             self.createSchemaMenu()        
             #self.setColors()
             self.saveLayoutLEFCM()
      #-------------------------------------------------------------------------------------------------
      # used to preserve the active schema across invocations
      #----------------------------------------------------------------------------------------------------
      def saveLayoutLEFCM(self):
          layout_lefcm.active_schema=self.active_schema
          f=open("{}/layout_lefcm.py".format(self.jython_scripts_path),"w")
          f.write("import java\n")
          f.write("active_schema='{}'\n".format(self.active_schema))
          f.write("active_schema_values=\\\n"+self.getActiveSchemaValues())
          f.close()
#------------------------------------------------------------------------------------------------------------
# Class to handle abstract FileFilter class (Need to provide accept and getDescription methods)
#-------------------------------------------------------------------------------------------------------------          
class FileFilter(FileFilter):
    def __init__(self,schema_types):
        self.schema_types=schema_types
        pass

    def accept(self,f):
        if f.isDirectory():
           return True
        fname=f.name.lower()
        for schema_type in self.schema_types:
            if fname.endswith(schema_type):
               return True
        else:
           return False

    def getDescription(self):
        d=""
        for t in self.schema_types:
            d=d+t+","
        self.__description=d.strip(",")
        return self.__description
#-----------------------------------------------------------------------------------------------------
# Code to invoke layoutEditorFrameColorManager class instance to manage changing colors on the layout
#-------------------------------------------------------------------------------------------------------
try:
    layoutEditorFrameColorManager().start()
except java.lang.Exception as err:
    print(traceback.format_exc())
except:
    print(traceback.format_exc())
