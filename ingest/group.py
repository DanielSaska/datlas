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

def ingest_group(cfg,g,recordings, changed,mdb_client,pool):
    db = mdb_client.get_default_database()
    g_db  = db.groups
    a_db  = db.group_analysis

    l_sha = get_sha()

    group = {
            "name": g.name(),
            "description": g.description(),
            "commit": l_sha,
            "recordings": [],
            "analysis": []
            }
    group_analysis = []


    #Check whether the count of recordings agrees with current amount of recordings
    for rcd in recordings:
        rid = objectid.ObjectId(rcd[0])
        rcd[0] = rid
        group["recordings"].append(rid)

    db_rec = g_db.find_one({"name": g.name()}, {"name": 1, "commit": 1, "recordings": 1, "analysis": 1})
    if db_rec is not None:
        db_adns = list(a_db.find({"_id": {"$in": db_rec["analysis"]}}, {"data": 0}))
    else: 
        db_adns = []

    data_changed = False
    if db_rec is not None and changed is not True:
        if len(group["recordings"]) == len(db_rec["recordings"]):
            for rcd in group["recordings"]:
                if rcd not in db_rec["recordings"]:
                    data_changed = True
                    break
    #If we have analysis to do and the experiment satisfieds constraints, call map() on them
    l_adns_changed = set()
    l_adns_unchanged = set()
    l_adns_unchanged_id = []
    loadables = set()
    for a in g.addons():
        for rcdi in range(len(recordings)):
            adn_run = False
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

    for a in g.addons():
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
        print("Skipping group {} because it already exists in the database at the current commit.".format(g.name()))
        return
    print("Processing group {}".format(g.name()))
    group["analysis"] = list(l_adns_unchanged_id)

    mapresults_fut = [pool.apply_async(gmap_slave, args=(cfg,rcd,g.addons())) for rcd in recordings]
    mapresults = [fut.get() for fut in mapresults_fut]

    for i, adn in enumerate(g.addons()):
        adn_type = "{}.{}".format(adn.__module__,adn.__qualname__) 
        try:
            adn_version = adn.version()
        except AttributeError:
            adn_version = l_sha


        adnmapresults = [mr[i] for mr in mapresults]
        res = adn.reduce(adnmapresults)
        if type(res) is not list:
            res = [res]
        for r in res:
            group_analysis.append({
                "_id": objectid.ObjectId(),
                "g_name": group["name"],
                "commit": l_sha,
                "type": adn_type,
                "version": adn_version,
                "data": r
                })
            group["analysis"].append(group_analysis[-1]["_id"])


    a_db.delete_many({"g_name": group["name"], "_id": {"$nin": l_adns_unchanged_id}})
    if len(group_analysis) > 0:
        a_db.insert_many(group_analysis)
    g_db.replace_one({"name": g.name()},group, upsert=True)
