# jmri_bindings.py
#
# Default objects for interaction with JMRI from a python script.
# This file may be needed only if jython.exec=true in python.properties
#
# These should be kept consistent with those in jmri.script.JmriScriptEngineManager
# and help/en/html/tools/scripting/Start.shtml
# 

# Default imports
import java
import jmri
import jmri.Sensor.ACTIVE          as ACTIVE
import jmri.Sensor.INACTIVE        as INACTIVE
import jmri.Sensor.UNKNOWN         as UNKNOWN

# JMRI default managers
sensors      = jmri.InstanceManager.getDefault(jmri.SensorManager)
turnouts     = jmri.InstanceManager.getDefault(jmri.TurnoutManager)
lights       = jmri.InstanceManager.getDefault(jmri.LightManager)
signals      = jmri.InstanceManager.getDefault(jmri.SignalHeadManager)
masts        = jmri.InstanceManager.getDefault(jmri.SignalMastManager)
routes       = jmri.InstanceManager.getDefault(jmri.RouteManager)
blocks       = jmri.InstanceManager.getDefault(jmri.BlockManager)
reporters    = jmri.InstanceManager.getDefault(jmri.ReporterManager)
memories     = jmri.InstanceManager.getDefault(jmri.MemoryManager)
powermanager = jmri.InstanceManager.getDefault(jmri.PowerManager)
addressedProgrammers = jmri.InstanceManager.getDefault(jmri.AddressedProgrammerManager)
globalProgrammers = jmri.InstanceManager.getDefault(jmri.GlobalProgrammerManager)
dcc          = jmri.InstanceManager.getDefault(jmri.CommandStation)
audio        = jmri.InstanceManager.getDefault(jmri.AudioManager)
shutdown     = jmri.InstanceManager.getDefault(jmri.ShutDownManager)
layoutblocks = jmri.InstanceManager.getDefault(jmri.jmrit.display.layoutEditor.LayoutBlockManager)
warrants     = jmri.InstanceManager.getDefault(jmri.jmrit.logix.WarrantManager)

# common JMRI constants
import jmri.Turnout.CLOSED         as CLOSED
import jmri.Turnout.THROWN         as THROWN
import jmri.Turnout.CABLOCKOUT         as CABLOCKOUT
import jmri.Turnout.PUSHBUTTONLOCKOUT  as PUSHBUTTONLOCKOUT
import jmri.Turnout.UNLOCKED       as UNLOCKED
import jmri.Turnout.LOCKED         as LOCKED

import jmri.Sensor.ACTIVE          as ACTIVE
import jmri.Sensor.INACTIVE        as INACTIVE

import jmri.Light.ON               as ON
import jmri.Light.OFF              as OFF

import jmri.NamedBean.UNKNOWN      as UNKNOWN
import jmri.NamedBean.INCONSISTENT as INCONSISTENT

import jmri.SignalHead.DARK        as DARK
import jmri.SignalHead.RED         as RED
import jmri.SignalHead.YELLOW      as YELLOW
import jmri.SignalHead.GREEN       as GREEN
import jmri.SignalHead.LUNAR       as LUNAR
import jmri.SignalHead.FLASHRED    as FLASHRED
import jmri.SignalHead.FLASHYELLOW as FLASHYELLOW
import jmri.SignalHead.FLASHGREEN  as FLASHGREEN
import jmri.SignalHead.FLASHLUNAR  as FLASHLUNAR
# application globals


