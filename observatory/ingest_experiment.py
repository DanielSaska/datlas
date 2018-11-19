from bson import objectid
from .tools.human_id import generate_name
from .tools.git_sha import get_sha
from .tools.slaves import load_pickle
from .tools.slaves import gmap_slave
from .tools.slaves import expmap_slave
import multiprocessing
import os
import errno
import os.path
import pickle

def ingest_experiment(cfg,exp_cfg,mdb_client,pool):
    db = mdb_client.datlas
    if exp_cfg["type"] == "experiment":
        in_db = db.experiments
        a_db = db.experiment_analysis
    elif exp_cfg["type"] == "tag":
        in_db = db.tags
        a_db = db.tag_analysis
    else:
        return

    #Check whether experiment has been processed for this commit already
    sha = get_sha()

    #Initialize constructs
    experiment = {
            "name": exp_cfg["name"],
            "commit": sha,
            "recordings": [],
            "analysis": []
            }
    experiment_analysis = []

    #Check whether the count of recordings agrees with current amount of recordings
    for rcd in exp_cfg["recordings"]:
        epid = objectid.ObjectId(rcd[0])
        rcd[0] = epid
        experiment["recordings"].append(epid)

    log = {"name": exp_cfg["name"],"commit": sha}
    r = in_db.find_one(log, {"name": 1, "commit": 1, "recordings": 1})
    if r is not None and exp_cfg["changed"] is not True:
        if len(experiment["recordings"]) == len(r["recordings"]):
            eql = True
            for rcd in experiment["recordings"]:
                if rcd not in r["recordings"]:
                    eql = False
                    break
            if eql:
                print("Skipping {} {} because it already exists in the database at the current commit.".format(exp_cfg["type"],exp_cfg["name"]))
                return

    print("Processing {} {}".format(exp_cfg["type"],exp_cfg["name"]))

    #If we have analysis to do and the experiment satisfieds constraints, call map() on them
    addons = set()
    loadables = set()
    for a in exp_cfg["analysis_addons"]:
        for rcdi in range(len(exp_cfg["recordings"])):
            rcd = exp_cfg["recordings"][rcdi]
            if (exp_cfg["type"] == "experiment" and a.on(data=rcd[1],experiment=exp_cfg["name"])) or \
               (exp_cfg["type"] == "tag" and a.on(data=rcd[1],tag=exp_cfg["name"])):
                    addons.add(a)
                    loadables.add(rcdi)

    loadable_ids = list(loadables) #Not all recordings may be used, only load used recordings
    loadables = []
    for i in loadable_ids:
       loadables.append(exp_cfg["recordings"][i])
    addons = list(addons)

    if len(addons) > 0:
        mapresults_fut = [pool.apply_async(expmap_slave, args=(cfg,rcd,addons,exp_cfg)) for rcd in loadables]
        mapresults = [fut.get() for fut in mapresults_fut]

        for i, adn in enumerate(addons):
            adnmapresults = [mr[i] for mr in mapresults if mr[i] is not None]
            res = adn.reduce(adnmapresults)
            if type(res) is not list:
                res = [res]
            for r in res:
                experiment_analysis.append({
                    "_id": objectid.ObjectId(),
                    "exp_name": exp_cfg["name"],
                    "commit": sha,
                    "data": r
                    })
                experiment["analysis"].append(experiment_analysis[-1]["_id"])

    a_db.delete_many({"exp_name": exp_cfg["name"]})
    if len(experiment_analysis) > 0:
        a_db.insert_many(experiment_analysis)
    in_db.replace_one({"name": exp_cfg["name"]},experiment, upsert=True)
