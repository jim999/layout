
class testrun(jmri.jmrit.automat.AbstractAutomaton):
      def init(self):
          pass
      def handle(self):
          sensors.getSensor('MS:BS:BS01_34').setKnownState(ACTIVE)
          self.waitMsec(2000)
          sensors.getSensor('MS:BS:BS01_35').setKnownState(ACTIVE)
testrun().start()
