from bson import objectid
from .tools.human_id import generate_name
from .tools.git_sha import get_sha
from .tools.slaves import load_pickle
from .tools.slaves import gmap_slave
from .tools.slaves import expmap_slave
import multiprocessing
import os
import time
import errno
import os.path
import pickle


def recording_changed(db_rec, l_rec):
    test_commit = False
    changed = False

    #Validate that recording is in database
    if not db_rec: return True #No recording? changed.

    #Validate that we have all data types
    for k in l_rec["data_types"]:
        if k not in db_rec["data_types"]:
            return True #We are missing a date type. Changed.

    #Validate versions if applicable
    if 'data_versions' not in db_rec:
        test_commit = True #We do not have data versions, we have to test commit
    else:
        for k, v in l_rec["data_versions"].items():
            if db_rec['data_versions'][k] != v:
                return True #Version differs. Changed.
            if v is None:
                test_commit = True #Does not provide version, we test commit
                break
    #Validate commit (if necessary)
    if test_commit and db_rec["commit"] != l_rec["commit"]:
        return True # Commit differs, Changed.

    #Validate file modification dates
    if 'data_mod_times' not in db_rec:
        return True #Mod times not available, Changed
    else:
        for k, v in l_rec["data_mod_times"].items():
            if db_rec['data_mod_times'][k] != v:
                return True #Mod date differs. Changed.
            if v is None:
                return True #No mod date, Changed.
    return False

def data_changed(db_rec, l_rec, data_key):
    if not db_rec: return True #No recording? changed.
    if data_key not in db_rec["data_types"]:
        return True #No data in database, Changed

    if 'data_versions' not in db_rec:
        if not (db_rec["commit"] == l_rec["commit"]):
            return True #Commit differs, Changed
    else:
        if data_key not in db_rec['data_versions']:
            return True #Not versioned, Changed
        elif db_rec['data_versions'][data_key] != l_rec['data_versions'][data_key]:
            return True #Version differs
        elif db_rec['data_versions'][data_key] is None:
            if not (db_rec["commit"] == l_rec["commit"]):
                return True #Commit differs, Changed

    if 'data_mod_times' not in db_rec:
        return True #No mod times
    if data_key not in l_rec["data_mod_times"]:
        return True #No mod time
    elif db_rec['data_mod_times'][data_key] != db_rec['data_mod_times'][data_key]:
        return True #Differing version
    return False
    

def recording_details(data_dict):
    etype = ""
    tags = set()
    for k in data_dict.keys():
        if data_dict[k].tags is not None:
            for t in data_dict[k].tags:
                tags.add(t)
            if data_dict[k].type is not None:
                etype = data_dict[k].type
    tags = list(tags)
    return etype, tags

def local_data_versions(data_dict):
    versions = {}
    for k, v in data_dict.items():
        try:
            versions[k] = v.version()
        except AttributeError:
            versions[k] = None
    return versions

def local_data_mod_times(data_dict):
    mod_times = {}
    for k, v in data_dict.items():
        try:
            mod_times[k] = v.__date__.replace(microsecond=0)
        except AttributeError:
            mod_times[k] = None

    return mod_times
 


def ingest_recording(strid,data_dict,mdb_client,cfg,analysis_addons=[],groups=[]):
    #Get experiment type, data available and tags
    l_date_mod = data_dict["__date__"].replace(microsecond=0)
    del data_dict["__date__"]
    
    l_etype, l_tags = recording_details(data_dict)
    l_data_versions = local_data_versions(data_dict)
    l_data_mod_times = local_data_mod_times(data_dict)
    l_sha = get_sha()
    
    #Find applicable analysis groups
    apply_groups = []
    for g in groups:
        if g.on(data=list(data_dict.keys()),experiment=l_etype,tags=l_tags):
            apply_groups.append(g)

    ret = {
            "id": strid,
            "commit": l_sha,
            "tags": l_tags,
            "experiment": l_etype,
            "groups": apply_groups,
            "src_modified": l_date_mod,
            "data_types": list(data_dict.keys()),
            "data_versions": l_data_versions,
            "data_mod_times": l_data_mod_times,
            "changed": False
            }
   
    epid = objectid.ObjectId(strid)

    db = mdb_client.get_default_database()
    r_db = db.recordings
    ra_db = db.recording_analysis
    dt_db = db.recording_data
    dtv_db = db.recording_data_visualizations

    #Check whether we have any changes
           
    db_rec = r_db.find_one({"_id": epid, "src_modified": { "$gte": l_date_mod }})
    if db_rec is not None:
        db_adns = list(ra_db.find({"_id": {"$in": db_rec["analysis"]}}))
    else: 
        db_adns = []
     
    #Find addons we need to run
    l_adns = [] 
    l_adns_changed = []
    l_adns_unchanged = []
    l_adns_unchanged_id = []
    for g in apply_groups:
        l_adns += g.addons()
    l_adns += analysis_addons
    l_adns = list(set(l_adns))
    for adn in l_adns:
        adn_run = False
        if adn.on(data=data_dict.keys(),experiment=l_etype): adn_run = True
        else:
            for tag in l_tags:
                if adn.on(data=data_dict.keys(),tag=tag): 
                    adn_run = True
                    break
        if adn_run:
            adn_type = "{}.{}".format(adn.__module__,adn.__qualname__) 
            try:
                adn_version = adn.version()
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
                    l_adns_unchanged_id.append(db_a["_id"])
                break
            if changed:
                l_adns_changed.append(adn)
            else:
                l_adns_unchanged.append(adn)
 
    if not recording_changed(db_rec, ret) and len(l_adns_changed) == 0:
        print("Skipping {}".format(strid))
        return ret
    ret["changed"] = True

    #Did individual data files cahnge?
    d_changed = {}
    for k in data_dict.keys():
        d_changed[k] = data_changed(db_rec, ret, k)

    #Fill data and pickle
    for k in data_dict.keys():
        fname = "{}/{}/{}.p".format(cfg["pickle_dir"],k,strid)
        change = d_changed[k] or not os.path.isfile(fname)
        if not change: #Try loading data
            try:
                pf = open(fname,'rb')
                data_dict[k] = pickle.dump(pf)
                pf.close()
            except:
                change = True #Something went wrong, lets fill instead

        if change:
            data_dict[k].fill()
            try:
                os.makedirs("{}/{}".format(cfg["pickle_dir"],k))
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
            pf = open(fname,'wb')
            pickle.dump(data_dict[k],pf)
            pf.close()
    
    recording = {
            "_id": epid,
            "commit": l_sha,
            "src_modified": l_date_mod,
            "data_types": [],
            "data_versions": l_data_versions,
            "data_mod_times": l_data_mod_times,
            "summary": {},
            "analysis": l_adns_unchanged_id,
            "tags": l_tags,
            "experiment": l_etype,
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
    l_d_unchanged = []
    for k in data_dict.keys():
        recording["data_types"].append(k)
        if d_changed[k]:
            dt, anls = data_dict[k].generate_db_entry()
            data_types.append(dt)
            data_types[-1]["rec_id"] = epid
            data_types[-1]["data_type"] = k
            data_types[-1]["visualizations"] = []
            data_types[-1]["meta"] = []

            for a in anls:
                data_type_visualizations.append({
                    "rec_id": epid,
                    "data_type": k,
                    "commit": l_sha,
                    "_id": objectid.ObjectId(),
                    "data": a
                    })
                data_types[-1]["visualizations"].append(data_type_visualizations[-1]["_id"])
            try:
                data_types[-1]["meta"].append({"name": "Processing Date", "value": time.asctime(time.localtime())+" (local time)"})
                dt_fn = data_dict[k].get_filename()
                data_types[-1]["meta"].append({"name": "File Location", "value": str(dt_fn)})
                dt_fd = os.stat(dt_fn)
                data_types[-1]["meta"].append({"name": "File Size", "value": "{} bytes".format(dt_fd.st_size)})
                data_types[-1]["meta"].append({"name": "File Creation Date", "value": time.asctime(time.localtime(dt_fd.st_ctime))+" (local time)"})
                data_types[-1]["meta"].append({"name": "File Modification Date", "value": time.asctime(time.localtime(dt_fd.st_mtime))+" (local time)"})
            except:
                pass
        else:
            l_d_unchanged.append(k)


    ##################################################
    #Analysis details

    #Get all addons from analysis groups
    for adn in l_adns_changed:
        adn_type = "{}.{}".format(adn.__module__,adn.__qualname__) 
        try:
            adn_version = adn.version()
        except AttributeError:
            adn_version = l_sha
            
        mapresults = [adn.map(data_dict)]
        res = adn.reduce(mapresults)
        if type(res) is not list:
            res = [res]
        for a in res:
            recording_analysis.append({
                "_id": objectid.ObjectId(),
                "rec_id": epid,
                "type": adn_type,
                "version": adn_version,
                "commit": l_sha,
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
        
    dtv_db.delete_many({"rec_id": epid, "data_type": { "$nin": l_d_unchanged }})
    ra_db.delete_many({"rec_id": epid, "_id": {"$nin": l_adns_unchanged_id}})
    if len(data_type_visualizations) > 0:
        dtv_db.insert_many(data_type_visualizations)
    for dt in data_types:
        dt_db.replace_one({"rec_id": dt["rec_id"], "data_type": dt["data_type"]},dt,upsert=True)

    if len(recording_analysis) > 0:
        ra_db.insert_many(recording_analysis)
    r_db.replace_one({"_id": epid},recording,upsert=True)
    return ret
