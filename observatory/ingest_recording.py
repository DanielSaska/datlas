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

    db = mdb_client.datlas
    r_db = db.recordings
    ra_db = db.recording_analysis
    dt_db = db.recording_data
    dtv_db = db.recording_data_visualizations

    #Check whether we have any changes
    sha = get_sha()
    dbrec = r_db.find_one({"_id": epid, "commit": sha})
    if dbrec: #Already executed
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
    
    recording = {
            "_id": epid,
            "commit": sha,
            "data_types": [],
            "summary": {},
            "analysis": [],
            "tags": tags,
            "experiment": etype,
            "err": []
            }
    recording_analysis = []

    data_types = []
    data_type_visualizations = []

    ##################################################
    #Recording Details
    for k in data_dict.keys():
        recording["summary"] = data_dict[k].populate_summary(recording["summary"])

    ##################################################
    #Data Types
    for k in data_dict.keys():
        dt, anls = data_dict[k].generate_db_entry()
        data_types.append(dt)
        data_types[-1]["rec_id"] = epid
        data_types[-1]["data_type"] = k
        data_types[-1]["visualizations"] = []
        recording["data_types"].append(k)
        for a in anls:
            data_type_visualizations.append({
                "rec_id": epid,
                "data_type": k,
                "commit": sha,
                "_id": objectid.ObjectId(),
                "data": a
                })
            data_types[-1]["visualizations"].append(data_type_visualizations[-1]["_id"])

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
            if type(res) is not list:
                res = [res]
            for a in res:
                recording_analysis.append({
                    "_id": objectid.ObjectId(),
                    "rec_id": epid,
                    "commit": sha,
                    "data": a
                    })
                recording["analysis"].append(recording_analysis[-1]["_id"])



    ##################################################
    #Recording meta
    hid = generate_name()
    existing_record = r_db.find_one({"_id": epid}) #Does not have human id
    if existing_record and "human_id" in existing_record:
        hid = existing_record['human_id']
    else:
        while r_db.find_one({"human_id": hid}): #Generate new one if exists
            hid = generate_name()
    recording["human_id"] = hid
        
    dtv_db.delete_many({"rec_id": epid})
    ra_db.delete_many({"rec_id": epid})
    if len(data_type_visualizations) > 0:
        dtv_db.insert_many(data_type_visualizations)
    for dt in data_types:
        dt_db.replace_one({"rec_id": dt["rec_id"], "data_type": dt["data_type"]},dt,upsert=True)

    if len(recording_analysis) > 0:
        ra_db.insert_many(recording_analysis)
    r_db.replace_one({"_id": epid},recording,upsert=True)
    return ret
