"""Known synthetic calibration targets, not an application oracle."""
import json
import sys
import threading

mode = sys.argv[1]
if mode == 'timeout': threading.Event().wait()
elif mode == 'exception': raise RuntimeError('deliberately injected exception')
elif mode == 'resource':
    chunks = []
    try:
        while True: chunks.append(bytearray(16 * 1024 * 1024))
    except MemoryError:
        print(json.dumps({'kind':'RESOURCE'}))
elif mode == 'correct': print(json.dumps({'kind':'OK','value':42}))
elif mode == 'incorrect': print(json.dumps({'kind':'OK','value':43}))
elif mode == 'invalid': print(json.dumps({'kind':'REJECT','value':'invalid'}))
elif mode == 'fresh_state':
    state = []
    print(json.dumps({'kind':'OK','value':len(state)}))
elif mode == 'corrupt': print('{corrupted fixture')
else: raise ValueError('unknown calibration mode')
