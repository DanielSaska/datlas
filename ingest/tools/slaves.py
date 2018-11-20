import pickle 

def fill_data(data):
    return data.fill()

def load_pickle(cfg,rid,data_types):
    ret = {}
    for dt in data_types:
        pf = open("{}/{}/{}.p".format(cfg["pickle_dir"],dt,str(rid)),'rb')
        ret[dt] = pickle.load(pf)
    return ret

def gmap_slave(cfg,rcd,adns):
    data = load_pickle(cfg,rcd[0],rcd[1])
    ret = []
    for adn in adns:
        ret.append(adn.map(data))
    return ret

def expmap_slave(cfg,rcd,adns,exp_cfg):
    data = load_pickle(cfg,rcd[0],rcd[1])
    ret = []
    for adn in adns:
        if (exp_cfg["type"] == "experiment" and adn.on(data=data.keys(),experiment=exp_cfg["name"])) or \
           (exp_cfg["type"] == "tag" and adn.on(data=data.keys(),tag=exp_cfg["name"])):
            ret.append(adn.map(data))
        else:
            ret.append(None)
    return ret



