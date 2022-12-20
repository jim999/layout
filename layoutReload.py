
import sys

import layoutConfig 
import layoutUtils as utils


if (sys.platform.startswith('java')):
   import layoutListeners
   import layoutDispatcher
   import layoutJMRIUtils as jmriUtils
   
try:
    from importlib import reload
except: 
    pass
class reloadModules():
      #==========================================================================================================================================
      # If we are to reload any modules then do this function
      #==========================================================================================================================================
      def reloadModules(self):
          reload(layoutConfig)
          reload(utils)
          if (sys.platform.startswith('java')):
              reload(layoutListeners)
              reload(jmriUtils)
              reload(layoutDispatcher)
