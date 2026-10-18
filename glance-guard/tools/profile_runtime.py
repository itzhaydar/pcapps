"""Measure an already-running app, without inspecting frames or user activity."""
import argparse
import json
import time
import psutil

parser=argparse.ArgumentParser()
parser.add_argument("pid",type=int)
parser.add_argument("--seconds",type=int,default=60)
args=parser.parse_args()
process=psutil.Process(args.pid)
process.cpu_percent()
samples=[]
for _ in range(args.seconds):
    time.sleep(1)
    samples.append((process.cpu_percent(), process.memory_info().rss/1024**2))
print(json.dumps({"samples":len(samples),"cpu_percent_one_core_mean":sum(x[0] for x in samples)/len(samples),
    "rss_mib_peak":max(x[1] for x in samples)},indent=2))
