import os

for engine in ('shunt3026','shunt8691','engine4035'):
    os.system(f'python layoutCMD.py terminate -t {engine} -f')

