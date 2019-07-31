#!/bin/python3
from .ingest.recording import ingest_recording
from .ingest.experiment import ingest_experiment
from .ingest.group import ingest_group
from pymongo import MongoClient
import json
import os
from multiprocessing import Process
import multiprocessing
import time
import platform

def creation_date(fl):
    try:
        return os.path.getmtime(fl)
    except Exception:
        return None


def search_files(directory='.', extension=''):
    results = []
    extension = extension.lower()
    for dirpath, dirnames, files in os.walk(directory):
        for name in files:
            if extension and name.lower().endswith(extension):
                results.append([dirpath, name])
    return results

def slave_rec(payload, cfg, analysis_addons, groups):
    client = MongoClient(cfg["uri_mongodb"])
    results = []
    for d in payload:
        results.append(ingest_recording(d[0],d[1],client, cfg, analysis_addons, groups))
    return results


class State:
    def __init__(self,cfg):
        print("Starting pool with {} workers.".format(cfg.n_threads))
        self.pool = multiprocessing.Pool(processes=cfg.n_threads)
        self.client = MongoClient(cfg.uri_mongodb)
        self.cache_files = set()
        self.cache_file_dates = {}
        self.cache_recordings = {}


def run(cfg,stateful=False,state=None,verbose=True):
    if stateful: 
        if state is None:
            s = State(cfg)
        else:
            s = state
    else:
        s = State(cfg)
    cfg_p = {
            "pickle_dir": cfg.dir_pickles,
            "uri_mongodb": cfg.uri_mongodb
            }

    #For every data type, check for new files
    print("--- Found recordings:")
    for k in cfg.data_types.keys():
        recordings = search_files(directory="{}/{}".format(cfg.dir_data,cfg.data_types[k]["dir"]), extension='meta.json')
        for r in recordings:
            rc = "{}/{}".format(r[0],r[1])
            cd = creation_date(rc)
            if rc not in s.cache_files or s.cache_file_dates[rc] == cd:
                print(rc)
                s.cache_files.add(rc)
                s.cache_file_dates[rc] = cd
                data = cfg.data_types[k]["class"](r[0],r[1],fill=False)
                if str(data.id) not in s.cache_recordings.keys():
                    s.cache_recordings[str(data.id)] = {"__date__": datetime.datetime.fromtimestamp(cd)}
                s.cache_recordings[str(data.id)][k] = data
                if s.cache_recordings["__date__"] < datetime.datetime.fromtimestamp(cd):
                    s.cache_recordings["__date__"] = datetime.datetime.fromtimestamp(cd)
    print("--- End of list")

        

    #We split up workloads
    payloads = []
    for i in range(int(cfg.n_threads)):
        payloads.append([])
    rkeys = list(s.cache_recordings.keys())
    for ki in range(len(rkeys)):
        k = rkeys[ki]
        payloads[ki%int(cfg.n_threads)].append([k, s.cache_recordings[k]])
    processes = []

    print("--- Jobs scheduled")
    #Process all recordings and get results of the processing     
    results_futures = [s.pool.apply_async(slave_rec, args=(pl,cfg_p,cfg.addons,cfg.groups)) for pl in payloads]
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
        t["analysis_addons"] = cfg.addons
        ingest_experiment(cfg_p,t,s.client,s.pool)
    for ek in experiments.keys():
        e =  experiments[ek]
        e["name"] = ek
        e["type"] = "experiment"
        e["analysis_addons"] = cfg.addons
        ingest_experiment(cfg_p,e,s.client,s.pool)
    for gk in pgroups.keys():
        g = pgroups[gk]
        ingest_group(cfg_p,g["class"],g["recordings"],g["changed"],s.client,s.pool)
    return s




