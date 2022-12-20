import os
import time
loops=2

os.system(f'python layoutCMD.py dispatch -t shunt8691 -r testRoute1 --retrys 9000 --look_ahead 2 \
                                        --route_direction reverse  --loops {loops} \
                                        --throttle_direction forward')
time.sleep(0.5)
os.system(f'python layoutCMD.py dispatch -t shunt3026 -r testRoute3 --retrys 9000 --look_ahead 2 \
                                        --route_direction reverse  --loops {loops} \
                                        --throttle_direction forward  ')
time.sleep(0.6)
os.system(f'python layoutCMD.py dispatch -t engine4035 -r testRoute2 --retrys 9000 --look_ahead 2 \
                                        --route_direction forward  --loops {loops} \
                                        --throttle_direction forward  ')
                                        





