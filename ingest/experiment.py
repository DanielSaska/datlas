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
    db = mdb_client.get_default_database()
    if exp_cfg["type"] == "experiment":
        in_db = db.experiments
        a_db = db.experiment_analysis
    elif exp_cfg["type"] == "tag":
        in_db = db.tags
        a_db = db.tag_analysis
    else:
        return

    #Check whether experiment has been processed for this commit already
    l_sha = get_sha()

    #Initialize constructs
    experiment = {
            "name": exp_cfg["name"],
            "commit": l_sha,
            "recordings": [],
            "analysis": []
            }
    experiment_analysis = []

    #Check whether the count of recordings agrees with current amount of recordings
    for rcd in exp_cfg["recordings"]:
        epid = objectid.ObjectId(rcd[0])
        rcd[0] = epid
        experiment["recordings"].append(epid)

    db_rec = in_db.find_one({"name": exp_cfg["name"]}, {"name": 1, "commit": 1, "recordings": 1, "analysis": 1})
    if db_rec is not None:
        db_adns = list(a_db.find({"_id": {"$in": db_rec["analysis"]}}, {"data": 0}))
    else: 
        db_adns = []
 

    data_changed = False
    if db_rec and exp_cfg["changed"] is not True:
        if len(experiment["recordings"]) == len(db_rec["recordings"]):
            for rcd in experiment["recordings"]:
                if rcd not in db_rec["recordings"]:
                    data_changed = True
                    break

    #If we have analysis to do and the experiment satisfieds constraints, call map() on them
    l_adns_changed = set()
    l_adns_unchanged = set()
    l_adns_unchanged_id = []
    loadables = set()
    for a in exp_cfg["analysis_addons"]:
        for rcdi in range(len(exp_cfg["recordings"])):
            adn_run = False
            rcd = exp_cfg["recordings"][rcdi]
            if (exp_cfg["type"] == "experiment" and a.on(data=rcd[1],experiment=exp_cfg["name"])) or \
               (exp_cfg["type"] == "tag" and a.on(data=rcd[1],tag=exp_cfg["name"])):
                adn_run = True
            if adn_run:
                adn_type = "{}.{}".format(a.__module__,a.__qualname__) 
                try:
                    adn_version = a.version()
                except AttributeError:
                    adn_version = l_sha

                changed = True
                for db_a in db_adns:
                    if "type" not in db_a:
                        continue
                    if db_a["type"] != adn_type:
                        continue
                    if "version" not in db_a:
                        break
                    if db_a["version"] == adn_version:
                        changed = False
                    break
                if changed or data_changed:
                    l_adns_changed.add(a)
                    loadables.add(rcdi)
    for a in exp_cfg["analysis_addons"]:
        if a not in l_adns_changed:
            l_adns_unchanged.add(a)
            l_adns_unchanged_id.append(a)

            adn_type = "{}.{}".format(a.__module__,a.__qualname__) 
            try:
                adn_version = a.version()
            except AttributeError:
                adn_version = l_sha
            for db_a in db_adns:
                if db_a["type"] != adn_type:
                    continue
                if db_a["version"] == adn_version:
                    l_adns_unchanged_id.append(db_a["_id"])
                break

    if len(l_adns_changed) == 0:
        print("Skipping {} {} because it already exists in the database at the current commit.".format(exp_cfg["type"],exp_cfg["name"]))
        return
    print("Processing {} {}".format(exp_cfg["type"],exp_cfg["name"]))
    experiment["analysis"] = list(l_adns_unchanged_id)

    loadable_ids = list(loadables) #Not all recordings may be used, only load used recordings
    loadables = []
    for i in loadable_ids:
       loadables.append(exp_cfg["recordings"][i])
    l_adns_changed = list(l_adns_changed)

    if len(l_adns_changed) > 0:
        mapresults_fut = [pool.apply_async(expmap_slave, args=(cfg,rcd,l_adns_changed,exp_cfg)) for rcd in loadables]
        mapresults = [fut.get() for fut in mapresults_fut]

        for i, adn in enumerate(l_adns_changed):
            adn_type = "{}.{}".format(adn.__module__,adn.__qualname__) 
            try:
                adn_version = adn.version()
            except AttributeError:
                adn_version = l_sha

            adnmapresults = [mr[i] for mr in mapresults if mr[i] is not None]
            res = adn.reduce(adnmapresults)
            if type(res) is not list:
                res = [res]
            for r in res:
                experiment_analysis.append({
                    "_id": objectid.ObjectId(),
                    "exp_name": exp_cfg["name"],
                    "type": adn_type,
                    "version": adn_version,
                    "commit": l_sha,
                    "data": r
                    })
                experiment["analysis"].append(experiment_analysis[-1]["_id"])

    a_db.delete_many({"exp_name": exp_cfg["name"], "_id": {"$nin": l_adns_unchanged_id}})
    if len(experiment_analysis) > 0:
        a_db.insert_many(experiment_analysis)
    in_db.replace_one({"name": exp_cfg["name"]},experiment, upsert=True)
