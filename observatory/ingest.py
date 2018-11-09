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


def ingest_recording(strid,data_dict,mdb_client,cfg,analysis_addons=[],groups=[]):
    #Get experiment type, data available and tags
    tags = set()
    etype = ""
    for k in data_dict.keys():
        if data_dict[k].tags is not None:
            for t in data_dict[k].tags:
                tags.add(t)
            if data_dict[k].type is not None:
                etype = data_dict[k].type
    tags = list(tags)
    
    #Find applicable analysis groups
    apply_groups = []
    for g in groups:
        if g.on(data=list(data_dict.keys()),experiment=etype,tags=tags):
            apply_groups.append(g)

    ret = {
            "id": strid,
            "tags": tags,
            "experiment": etype,
            "groups": apply_groups,
            "data_types": list(data_dict.keys()),
            "changed": False
            }

    epid = objectid.ObjectId(strid)

    db = mdb_client.ezo
    rec_db = db.recordings
    plg_db = db.plugins
    ana_db = db.analysis

    #Check whether we have any changes
    sha = get_sha()
    dbrec = rec_db.find_one({"_id": epid, "commit": sha})
    if dbrec and ana_db.find_one({"_id": epid, "commit": sha}): #Already executed
        dt = dbrec["data_types"]
        changed = False
        for k in data_dict.keys():
            if k not in dt:
                changed = True
                break
        if not changed:
            print("Skipping recording {} because it already exists in the database at the current commit.".format(strid))
            return ret
    ret["changed"] = True

    #Fill data and pickle
    for k in data_dict.keys():
        data_dict[k].fill()
        try:
            os.makedirs("{}/{}".format(cfg["pickle_dir"],k))
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
        pf = open("{}/{}/{}.p".format(cfg["pickle_dir"],k,strid),'wb')
        pickle.dump(data_dict[k],pf)
        pf.close()
    
    recording_details = {
            "_id": epid,
            "commit": sha,
            "data_types": [],
            "datetime": None,
            "duration": None,
            "sample": {
                "dpf": None,
                "expression": None,
                "description": None
                },
            "description": None,
            "experiment": None,
            "plugins": [],
            "tags": [],
            "err": []
            }

    plugins = []
    analysis_details = {
            "_id": epid,
            "commit": sha,
            "addons": [],
            "err": []
            }
 

    ##################################################
    #Recording Details
    for k in data_dict.keys():
        recording_details = data_dict[k].populate_rec_details(recording_details)

    ##################################################
    #Plugins
    for k in data_dict.keys():
        plugins.append(data_dict[k].generate_plugin())
        plugins[-1]["exp_id"] = epid
        plugins[-1]["data_type"] = k
        recording_details["data_types"].append(k)


    ##################################################
    #Analysis details

    #Get all addons from analysis groups
    all_addons = []
    for g in apply_groups:
        all_addons += g.addons()
    all_addons += analysis_addons
    all_addons = list(set(all_addons))
    for adn in all_addons:
        adn_run = False
        if adn.on(data=data_dict.keys(),experiment=etype): adn_run = True
        for tag in tags:
            if adn.on(data=data_dict.keys(),tag=tag): 
                adn_run = True
                break
        if adn_run:
            mapresults = [adn.map(data_dict)]
            res = adn.reduce(mapresults)
            if type(res) is list:
                analysis_details["addons"] += res
            else:
                analysis_details["addons"].append(res)

    ##################################################
    #Recording meta
    hid = generate_name()
    existing_record = rec_db.find_one({"_id": epid}) #Does not have human id
    if existing_record and "human_id" in existing_record:
        hid = existing_record['human_id']
    else:
        while rec_db.find_one({"human_id": hid}): #Generate new one if exists
            hid = generate_name()
    recording_details["human_id"] = hid
        
    for p in plugins:
        plg_db.replace_one({"exp_id": p["exp_id"], "data_type": p["data_type"]},p,upsert=True)
    ana_db.replace_one({"_id": epid},analysis_details,upsert=True)
    rec_db.replace_one({"_id": epid},recording_details,upsert=True)
    return ret

def ingest_experiment(cfg,exp_cfg,mdb_client,pool):
    db = mdb_client.ezo
    if exp_cfg["type"] == "experiment":
        in_db = db.experiment_details
    elif exp_cfg["type"] == "tag":
        in_db = db.tag_details
    else:
        return

    #Check whether experiment has been processed for this commit already
    sha = get_sha()

    #Initialize constructs
    exp_details = {
            "name": exp_cfg["name"],
            "commit": sha,
            "recordings": [],
            "analysis": {
                "addons": [
                    ]
                }
            }

    #Check whether the count of recordings agrees with current amount of recordings
    for rcd in exp_cfg["recordings"]:
        epid = objectid.ObjectId(rcd[0])
        rcd[0] = epid
        exp_details["recordings"].append(epid)

    log = {"name": exp_cfg["name"],"commit": sha}

    r = in_db.find_one(log, {"name": 1, "commit": 1, "recordings": 1})

    if r is not None and exp_cfg["changed"] is not True:
        if len(exp_details["recordings"]) == len(r["recordings"]):
            eql = True
            for rcd in exp_details["recordings"]:
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
        '''
        data_futures = [pool.apply_async(load_pickle, args=(cfg,rcd[0],rcd[1])) for rcd in loadables]
        data = [fut.get() for fut in data_futures]
        for adn in addons:
            processibles = []
            for d in data:
                if (exp_cfg["type"] == "experiment" and adn.on(data=d.keys(),experiment=exp_cfg["name"])) or \
                   (exp_cfg["type"] == "tag" and adn.on(data=d.keys(),tag=exp_cfg["name"])):
                        processibles.append(d)

            mapresults_fut = [pool.apply_async(adn.map, args=(d,)) for d in processibles]
            mapresults = [fut.get() for fut in mapresults_fut]
            res = adn.reduce(mapresults)
            if type(res) is list:
                exp_details["analysis"]["addons"] += res
            else:
                exp_details["analysis"]["addons"].append(res)
        '''
        #NEW
        mapresults_fut = [pool.apply_async(expmap_slave, args=(cfg,rcd,addons,exp_cfg)) for rcd in loadables]
        mapresults = [fut.get() for fut in mapresults_fut]

        for i, adn in enumerate(addons):
            adnmapresults = [mr[i] for mr in mapresults if mr[i] is not None]
            res = adn.reduce(adnmapresults)
            if type(res) is list:
                exp_details["analysis"]["addons"] += res
            else:
                exp_details["analysis"]["addons"].append(res)
        #NEW END

    in_db.replace_one({"name": exp_cfg["name"]},exp_details, upsert=True)

def ingest_group(cfg,group,recordings, changed,mdb_client,pool):
    db = mdb_client.ezo
    g_db  = db.group_details 
    sha = get_sha()

    g_details = {
            "name": group.name(),
            "description": group.description(),
            "commit": sha,
            "recordings": [],
            "analysis": {
                "addons": [
                    ]
                }
            }

    #Check whether the count of recordings agrees with current amount of recordings
    for rcd in recordings:
        rid = objectid.ObjectId(rcd[0])
        rcd[0] = rid
        g_details["recordings"].append(rid)

    log = {"name": group.name(),"commit": sha}

    r = g_db.find_one(log, {"name": 1, "commit": 1, "recordings": 1})

    if r is not None and changed is not True:
        if len(g_details["recordings"]) == len(r["recordings"]):
            eql = True
            for rcd in g_details["recordings"]:
                if rcd not in r["recordings"]:
                    eql = False
                    break
            if eql:
                print("Skipping group {} because it already exists in the database at the current commit.".format(group.name()))
                return

    print("Processing group {}".format(group.name()))

    mapresults_fut = [pool.apply_async(gmap_slave, args=(cfg,rcd,group.addons())) for rcd in recordings]
    mapresults = [fut.get() for fut in mapresults_fut]

    for i, adn in enumerate(group.addons()):
        adnmapresults = [mr[i] for mr in mapresults]
        res = adn.reduce(adnmapresults)
        if type(res) is list:
            g_details["analysis"]["addons"] += res
        else:
            g_details["analysis"]["addons"].append(res)

    g_db.replace_one({"name": group.name()},g_details, upsert=True)
