import sys

if (sys.platform.startswith('java')):
    import java.awt.Color
#=============================================================================================
# Colors used by JPANELs
#=============================================================================================
    jWhite            = java.awt.Color.white
    jRed              = java.awt.Color.red
    jMaroon           = java.awt.Color(128,0,0)
    jBrightRed        = java.awt.Color.red.brighter()
    jOrange           = java.awt.Color.orange
    jYellow           = java.awt.Color.yellow
    jBrightYellow     = java.awt.Color.yellow.brighter()
    jDarkGreen        = java.awt.Color(0,128,0)
    jOlive            = java.awt.Color(128,128,0)
    jGreen            = java.awt.Color.green
    jBrightGreen      = java.awt.Color.green.brighter()
    jBlue             = java.awt.Color.blue
    jLightBlue        = java.awt.Color(51,153,255)
    jCyan             = java.awt.Color.cyan
    jMagenta          = java.awt.Color.magenta
    jLightGray        = java.awt.Color.lightGray
    jGray             = java.awt.Color.gray
    jPink             = java.awt.Color.pink
    jBlack            = java.awt.Color.black
    jTeal             = java.awt.Color(0,128,128)
    jNavy             = java.awt.Color(0,0,128)
    jCream            = java.awt.Color(255,255,224)
    jDarkCream        = java.awt.Color(255,255,180)
    jPurple           = java.awt.Color(128,0,128)
    jNone             = None
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
BOLD                          ='\033[01m'
UNDERLINE                     ='\033[04m'
ORANGE                        ="\033[38;2;255;165;0m"
ORANGE_BG                     ="\033[48;2;255;165;0m"
