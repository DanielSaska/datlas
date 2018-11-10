#!/bin/python3
from observatory.ingest import ingest_recording, ingest_experiment, ingest_group
from pymongo import MongoClient
import zmq
import json
import argparse
import os
from multiprocessing import Process
import multiprocessing
import time

def search_files(directory='.', extension=''):
    results = []
    extension = extension.lower()
    for dirpath, dirnames, files in os.walk(directory):
        for name in files:
            if extension and name.lower().endswith(extension):
                results.append([dirpath, name])
    return results

def slave_rec(payload, cfg):
    client = MongoClient(cfg['mongodb'])
    results = []
    for d in payload:
        results.append(ingest_recording(d[0],d[1], client, cfg))
    return results

ap = argparse.ArgumentParser()
ap.add_argument("-c", "--config",
	help="path to the config.json file")
args = vars(ap.parse_args())

cfg = json.load(open(args["config"]))
print("Starting pool with {} workers.".format(cfg["threads"]))
pool = multiprocessing.Pool(processes=cfg["threads"])
client = MongoClient(cfg['mongodb'])


zmq_context = zmq.Context()
zmq_socket = zmq_context.socket(zmq.REQ)
zmq_socket.connect(cfg["zmq"])
print(cfg["zmq"])

cache_files = set();
cache_recordings = {}


while True:
    zmq_socket.send_json({"req": "get_data_types"})
    resp = zmq_socket.recv_json()
    if "err" in resp:
        pass #TODO: handle error
    data_types = resp["data"]
    #For every data type, check for new files
    print("--- Found recordings:")
    for k in data_types.keys():
        recordings = search_files(directory="{}/{}".format(cfg['data_dir'],data_types[k]["dir"]), extension='meta.json')
        for r in recordings:
            rc = "{}/{}".format(r[0],r[1])
            print(rc)
            if rc not in cache_files:
                cache_files.add(rc)
                zmq_socket.send_json({"req": "get_id", "data": {"type": k, "dir": r[0], "fname": r[1]}})
                resp = zmq_socket.recv_json()
                if "err" in resp:
                    pass #TODO: handle error
                rid = resp["data"]
                if rid not in cache_recordings.keys():
                    cache_recordings[rid] = {}
                cache_recordings[rid][k] = {"dir": r[0], "fname": r[1]};
    print("--- End of list")

        

    #We split up workloads
    payloads = []
    for i in range(int(cfg["threads"])):
        payloads.append([])
    rkeys = list(cache_recordings.keys())
    for ki in range(len(rkeys)):
        k = rkeys[ki]
        payloads[ki%int(cfg["threads"])].append([k, cache_recordings[k]])
    processes = []

    print("--- Jobs scheduled")
    #Process all recordings and get results of the processing     
    results_futures = [pool.apply_async(slave_rec, args=(pl,cfg)) for pl in payloads]
    print("--- Waiting for jobs to finish")
    results = [fut.get() for fut in results_futures]
    print("--- Jobs have finished")

    #Find all experiments and tags

    tags = {}
    experiments = {}
    pgroups = {}
    for rs in results:
        for r in rs:
            if r["experiment"] not in experiments:
                experiments[r["experiment"]] = {"changed": False, "recordings": []}
            if r["changed"] == True:
                experiments[r["experiment"]]["changed"] = True
            experiments[r["experiment"]]["recordings"].append([r["id"],r["data_types"]])
            for t in r["tags"]:
                if t not in tags:
                    tags[t] = {"changed": False, "recordings": []}
                if r["changed"] == True:
                    tags[t]["changed"] = True
                tags[t]["recordings"].append([r["id"],r["data_types"]])
            for g in r["groups"]:
                if g.name() not in pgroups:
                    pgroups[g.name()] = {"class": g, "changed": False, "recordings": []}
                if r["changed"] == True:
                    pgroups[g.name()]["changed"] = True
                pgroups[g.name()]["recordings"].append([r["id"],r["data_types"]])


    print("Experiments submited for analysis:")
    print("{}".format(list(experiments.keys())))
    print("Tags submited for analysis:")
    print("{}".format(list(tags.keys())))
    print("Groups submited for analysis:")
    print("{}".format(list(pgroups.keys())))
    for tk in tags.keys():
        t =  tags[tk]
        t["name"] = tk
        t["type"] = "tag"
        t["analysis_addons"] = addons
        ingest_experiment(cfg,t,client,pool)
    for ek in experiments.keys():
        e =  experiments[ek]
        e["name"] = ek
        e["type"] = "experiment"
        e["analysis_addons"] = addons
        ingest_experiment(cfg,e,client,pool)
    for gk in pgroups.keys():
        g = pgroups[gk]
        ingest_group(cfg,g["class"],g["recordings"],g["changed"],client,pool)


    time.sleep(60)




