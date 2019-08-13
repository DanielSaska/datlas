from bson import objectid


def db_del_recordings(recording_ids,mdb_client):
    db = mdb_client.get_default_database()
    r_db = db.recordings
    ra_db = db.recording_analysis
    dt_db = db.recording_data
    dtv_db = db.recording_data_visualizations

    epids = []
    for rid in recording_ids:
        epids.append(objectid.ObjectId((rid))

    r_db.remove({'_id':{'$in':epids}})
    ra_db.remove({"rec_id": {'$in':epids}})
    dt_db.remove({"rec_id": {'$in':epids}})
    dtv_db.remove({"rec_id": {'$in':epids}})


