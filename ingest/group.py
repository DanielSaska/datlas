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
    db = mdb_client.datlas
    g_db  = db.groups
    a_db  = db.group_analysis

    sha = get_sha()

    group = {
            "name": g.name(),
            "description": g.description(),
            "commit": sha,
            "recordings": [],
            "analysis": []
            }
    group_analysis = []


    #Check whether the count of recordings agrees with current amount of recordings
    for rcd in recordings:
        rid = objectid.ObjectId(rcd[0])
        rcd[0] = rid
        group["recordings"].append(rid)

    log = {"name": g.name(),"commit": sha}

    r = g_db.find_one(log, {"name": 1, "commit": 1, "recordings": 1})

    if r is not None and changed is not True:
        if len(group["recordings"]) == len(r["recordings"]):
            eql = True
            for rcd in group["recordings"]:
                if rcd not in r["recordings"]:
                    eql = False
                    break
            if eql:
                print("Skipping group {} because it already exists in the database at the current commit.".format(g.name()))
                return

    print("Processing group {}".format(g.name()))

    mapresults_fut = [pool.apply_async(gmap_slave, args=(cfg,rcd,g.addons())) for rcd in recordings]
    mapresults = [fut.get() for fut in mapresults_fut]

    for i, adn in enumerate(g.addons()):
        adnmapresults = [mr[i] for mr in mapresults]
        res = adn.reduce(adnmapresults)
        if type(res) is not list:
            res = [res]
        for r in res:
            group_analysis.append({
                "_id": objectid.ObjectId(),
                "g_name": group["name"],
                "commit": sha,
                "data": r
                })
            group["analysis"].append(group_analysis[-1]["_id"])


    a_db.delete_many({"g_name": group["name"]})
    if len(group_analysis) > 0:
        a_db.insert_many(group_analysis)
    g_db.replace_one({"name": g.name()},group, upsert=True)
