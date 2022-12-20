#=============================================================================================
# 
# Test script for retrieving multiple throttles
#
#=============================================================================================
import jmri
import sys
import time

CYAN   = '\33[96m'
RED    = '\33[31m'
YELLOW = '\33[33m'
ENDC   = '\33[00m'

class TCtl(jmri.jmrit.automat.AbstractAutomaton):
   def init(self):
       self.attempts=5
       self.throttle={}
       self.throttles_to_get=(4035,3026,103,8691,2021)

   def handle(self):
       for throttle_number in self.throttles_to_get:
           count=1

           self.throttle[throttle_number]=self.getThrottle(throttle_number,True)

           while (self.throttle[throttle_number]==None and count < self.attempts):
               count+=1
               print("{}>>>>>>>>>>>>>> Attmpt {} to get throttle {} ".format(YELLOW, count, throttle_number, ENDC))
               self.throttle[throttle_number]=self.getThrottle(throttle_number,True,1)
               sys.stdout.flush()
               time.sleep(1)

           if self.throttle[throttle_number]==None:
              print("{}>>>>>>>>>>>>>> failed to get throttle {} after {} attempts {}".format(RED, throttle_number, count, ENDC))
              sys.stdout.flush()
           else:
              print("{} >>>>>>>>>>>>>> throttle {} took {} attempts {}".format(CYAN, throttle_number, count, ENDC))
              sys.stdout.flush()
       print("Throttles are {}".format(self.throttle))

TCtl().start()
