from layoutSchemaColors import *
'''
#====================================================================================
# layout color schema definitions.
#====================================================================================
'''
#===================================================================================
# Global defaults
#===================================================================================
font_size_default     = 14
font_name_default     = "Dialog"
font_color_default    = "black"
font_bold_default     = False
font_italic_default   = False
hidden_default_state  = False
#-----------------------------------------------------------------------------------------------------------------------------------
#
# NAME                          : the name of this schema
# hidden                        : if a poaitional lable does not have a hidden value defined then use this or use global defaults
# font_name                     : if a positional label does not habe a font name defined then use this or use global defaults
# font_bold                     : if the bold status of a positionable label is not defined then use this or use global defaults
# font_italic                   : if the itlaic status of a positionable label is not defined then use this or use global defaults
# font_size                     : the font size of a positionable label is not defined then use this or use global defaults.
# booked_track_color            : the color a block booked by the dispatcher will be
# occupied_track_color          : the color an occupied block will be
# background_color              : the color of the background
# turnout_circle_thrown_color   : the color of a thrown turnouts circle
# tunout_circle_color           : the color of a closed trunout circle
# default_track_color           : the color of unoccupied tracks
# block_contents_icon_color     : the color of hte block icon contents
# positionable_labels           : look for the label that starts with the key text
#                                 and set it to color,font,bold,italic,size
#
#-------------------------------------------------------------------------------------------------------------------------------------
FULLY_DEFINED_SAMPLE       = { "NAME"                         : "FULLY_DEFINED_SAMPLE",
                               "hidden"                       : True,
                               "font_name"                    : "Dialog",
                               "font_bold"                    : True,
                               "font_italic"                  : False,
                               "font_size"                    : 14,
                               "booked_track_color"           : jWhite,
                               "occupied_track_color"         : jRed,
                               "background_color"             : jLightGray,
                               "turnout_circle_thrown_color"  : jYellow,
                               "turnout_circle_color"         : jGreen,
                               "turnout_circle_size"          : 3,
                               "default_track_color"          : jBlack,
                               "block_contents_icon"          : {               'color' :jPink,      'font':'Dialog', 'bold':True,'italic' :False,'size':24},
                               "positionable_labels"          : { 'Test'      :{'color' :jMaroon,    'font':'Dialog', 'bold':True,'italic' :True, 'size':24,'hidden' : False},
                                                                  'BL'        :{'color' :jBlue,      'font':'Dialog', 'bold':True,'italic' :False,'size':12,'hidden' : True},
                                                                  'PS'        :{'color' :jDarkGreen, 'font':'Dialog', 'bold':True,'italic' :False,'size':16,'hidden' : True},
                                                                  'TO'        :{'color': jYellow,    'font':'Dialog', 'bold':True,'italic' :False,'size':14,'hidden' : True},
                                                                 },
                             }
BLACK_BG                   = {  "NAME"                        : "BLACK_BG",
                                "hidden"                      : True,
                                "font_name"                   : "Times Roman",
                                "font_bold"                   : True,
                                "font_italic"                 : False,
                                "booked_track_color"          : jBrightYellow,
                                "background_color"            : jBlack,
                                "occupied_track_color"        : jRed,
                                "turnout_thrown_circle_color" : jRed,
                                "turnout_closed_circle_color" : jGreen,
                                "turnout_circle_size"         : 3,
                                "default_track_color"         : jCream,
                                "block_contents_icon"         : {               'color' :jPink,       'font':'Dialog', 'bold':True,'italic' :False,'size':14,"hidden": False},
                                "positionable_labels"         : { 'Test'      :{'color' :jWhite,      'font':'Dialog', 'bold':True,'italic' :True, 'size':24,"hidden": False},
                                                                  'BL'        :{'color' :jYellow,     'font':'Dialog', 'bold':True,'italic' :False,'size':12,"hidden": False},
                                                                  'PS'        :{'color' :jBrightGreen,'font':'Dialog', 'bold':True,'italic' :False,'size':12,},
                                                                  'TO'        :{'color': jYellow,     'font':'Dialog', 'bold':True,'italic' :False,'size':12,},
                                                                  "SH"        :{'color': jLightGray,  'font':'Dialog', 'bold':True,'italic' :False,'size':12,},
                                                                 },
                             }
NAVY_BG                    = {  "NAME"                        : "NAVY_BG",
                                "hidden"                      : False,
                                "font_name"                   : "Times Roman",
                                "font_bold"                   : True,
                                "font_italic"                 : False,
                                "booked_track_color"          : jCream,
                                "background_color"            : jNavy,
                                "turnout_thrown_circle_color" : jRed,
                                "turnout_closed_circle_color" : jGreen,
                                "turnout_circle_size"         : 3,
                                "default_track_color"         : jBlack,
                                "block_contents_icon"         : {               'color' :jPink,       'font':'Dialog', 'bold':True,'italic' :False,'size':14,"hidden": False},
                                "positionable_labels"         : { 'test'      :{'color' :jWhite,      'font':'Dialog', 'bold':True,'italic' :True, 'size':14,"hidden": False},
                                                                  'BL'        :{'color' :jYellow,     'font':'Dialog', 'bold':True,'italic' :False,'size':12,"hidden": False},
                                                                  'PS'        :{'color' :jBrightGreen,'font':'Dialog', 'bold':True,'italic' :False,'size':12,"hidden": True},
                                                                  'TO'        :{'color': jYellow,     'font':'Dialog', 'bold':True,'italic' :False,'size':12,"hidden": True},
                                                                  "SH"        :{'color': jBlack,      'font':'Dialog', 'bold':True,'italic' :False,'size':12,"hidden": True},
                                                                 },
                             }
RED_BG                     = {  "NAME"                        : "RED_BG",
                                "hidden"                      : False,
                                "booked_track_color"          : jCream,
                                "background_color"            : jRed,
                                "occupied_track_color"        : jOrange,
                                "turnout_thrown_circle_color" : jOrange,
                                "turnout_closed_circle_color" : jGreen,
                                "turnout_circle_size"         : 3,
                                "default_track_color"         : jBlack,
                                "block_contents_icon"         : {               'color' :jBlue,       'font':'Dialog', 'bold':True,'italic' :True,'size':24,"hidden": False},
                             }
WHITE_BG                   = {  "NAME"                        : "WHITE_BG",
                                "hidden"                      : False,
                                "font_name"                   : "Times Roman",
                                "font_bold"                   : True,
                                "font_italic"                 : False,
                                "booked_track_color"          : jCream,
                                "background_color"            : jWhite,
                                "occupied_track_color"        : jRed,
                                "turnout_thrown_circle_color" : jRed,
                                "turnout_closed_circle_color" : jGreen,
                                "turnout_circle_size"         : 3,
                                "default_track_color"         : jBlack,
                             }
MAROON_BG                  = {  "NAME"                        : "MARRON_BG",
                                "hidden"                      : False,
                                "font_name"                   : "Times Roman",
                                "font_bold"                   : True,
                                "font_italic"                 : False,
                                "font_size"                   : 10,
                                "booked_track_color"          : jCream,
                                "occupied_track_color"        : jRed,
                                "background_color"            : jMaroon,
                                "turnout_thrown_circle_color" : jRed,
                                "turnout_closed_circle_color" : jGreen,
                                "turnout_circle_size"         : 3,
                                "default_track_color"         : jBlack,
                                "block_contents_icon"         : {               'color' :jPink,      'font':'Dialog', 'bold':True,'italic' :False,'size':20,"hidden": False},
                                "positionable_labels"         : { 'Test'      :{'color' :jWhite,     'font':'Dialog', 'bold':True,'italic' :True, 'size':24,'hidden':False},
                                                                  'BL'        :{'color' :jBlue,      'font':'Dialog', 'bold':True,'italic' :False,'size':12,'hidden':False},
                                                                }
                                
                             }
GRAY_BG                    = { "NAME"                         : "GRAY_BG",
                               "hidden"                       : False,
                               "font_name"                    : "Dialog",
                               "font_bold"                    : True,
                               "font_italic"                  : False,
                               "font_size"                    : 14,
                               "booked_track_color"           : jWhite,
                               "occupied_track_color"         : jRed,
                               "background_color"             : jLightGray,
                               "turnout_circle_thrown_color"  : jYellow,
                               "turnout_circle_color"         : jGreen,
                               "turnout_circle_size"          : 3,
                               "default_track_color"          : jBlack,
                               "block_contents_icon"          : {               'color' :jMaroon,    'font':'Dialog', 'bold':True,'italic' :False,'size':24},
                               "positionable_labels"          : { 'Test'      :{'color' :jMaroon,    'font':'Dialog', 'bold':True,'italic' :True, 'size':24,'hidden':False},
                                                                  'BL'        :{'color' :jBlue,      'font':'Dialog', 'bold':True,'italic' :False,'size':10,'hidden':False},
                                                                  'PS'        :{'color' :jDarkGreen, 'font':'Dialog', 'bold':True,'italic' :False,'size':16,'hidden':False},
                                                                  'TO'        :{'color': jYellow,    'font':'Dialog', 'bold':True,'italic' :False,'size':14,'hidden' : True},
                                                                 },
                             }
PINK_BG                    = {  "NAME"                        : "PINK_BG",
                                "hidden"                      : False,
                                "font_name"                   : "Times Roman",
                                "font_bold"                   : True,
                                "font_italic"                 : False,
                                "booked_track_color"          : jCream,
                                "background_color"            : jPink,
                                "turnout_thrown_circle_color" : jRed,
                                "turnout_closed_circle_color" : jGreen,
                                "turnout_circle_size"         : 3,
                                "default_track_color"         : jBlack,
                                "block_contents_icon"         : {              'color' :jMaroon,    'font':'Dialog', 'bold':True,'italic' :False,'size':24},
                                "positionable_labels"         : {'Test'      :{'color':jTeal,       'font':'Dialog', 'bold':True,'italic':False,'size':16},
                                                                 'BL'        :{'color':jOlive,      'hidden':True,'size':20},
                                                                 'PS'        :{'color':jCyan},
                                                                 'TO'        :{'color':jMagenta  },
                                                                },
                             }

color_schema_menu_items    = {"Black"          : BLACK_BG,
                              "Gray"           : GRAY_BG,
                              "Maroon"         : MAROON_BG,
                              "Navy"           : NAVY_BG,
                              "Pink"           : PINK_BG,
                              "Red"            : RED_BG,
                              "White"          : WHITE_BG,
                             }

