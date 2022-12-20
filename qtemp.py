import os, time

while 1:
  os.system("vcgencmd measure_temp")
  time.sleep(2)
