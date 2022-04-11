import datetime
import subprocess
import time
import json

def watch_pods():
    pods = {}
    watch = True
    while watch:
        try:
            p = subprocess.Popen(['kubectl', 'get', 'pods', '-o=wide'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = p.communicate()
            tstamp = time.time()
            lines = stdout.decode('utf-8').splitlines()[1:]
            for line in lines:
                name, _, status, _, _, _, node, _, _ = line.split()
                if name not in pods:
                    pods[name] = {'node': node, 'status': {}}
                    print(name, node)
                if status not in pods[name]['status']:
                    pods[name]['status'][status] = tstamp
                    print(name, status, tstamp)
            time.sleep(1)
        except KeyboardInterrupt:
            watch = False
            print('stop watching')
    print('dumping results')
    with open('pods.json', 'w') as events_file:
        events_file.write(json.dumps(pods, indent=2))
        

if __name__ == '__main__':
    watch_pods()
