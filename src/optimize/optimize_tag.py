import os
import sys
import json
import numpy as np

from utils import common_tools as ct
from utils.data_handler import DataHandler as dh
from utils.env import *

import pdb 


def params_handler(params, info, pre_res, **kwargs):
    # load training data
    if ( "walk_file" not in params ) or ( not os.path.exists(params["walk_file"]) ):
        params["walk_file"] = pre_res["tag_walker"]["walk_file"]
    # set the embedding size
    params["embedding_model"]["embed_size"] = info["embed_size"]
    params["embedding_model"]["batch_size"] = params["batch_size"]
    params["embedding_model"]["logger"] = info["logger"]

    return {}


@ct.module_decorator
def optimize(params, info, pre_res, **kwargs):
    res = params_handler(params, info, pre_res)
    
    pdb.set_trace()

    G = dh.load_as_graph(params["walk_file"])
    params["embedding_model"]["num_nodes"] = len(G.nodes())

    # model init
    print ("[+] The embedding model is model.%s" % (params["embedding_model"]["func"]))
    info["logger"].info("[+] The embedding model is model.%s\n" % (params["embedding_model"]["func"]))
    model_handler = __import__("model." + params["embedding_model"]["func"], fromlist = ["model"])
    model = model_handler.NodeEmbedding(params["embedding_model"])
    model.build_graph()

    # get_batch generator
    print ("[+] The batch strategy is batch_strategy.%s" % (params["batch_strategy"]))
    info["logger"].info("[+] The batch strategy is batch_strategy.%s\n" % (params["batch_strategy"]))
    bs_handler = __import__("batch_strategy." + params["batch_strategy"], fromlist=["batch_strategy"])
    bs = bs_handler.BatchStrategy(G, params)

    # train model
    mus, logsigs = model.train(bs.get_batch)
    sigs = np.exp(logsigs)

    # map the the mus and sigs with their name according to G 
    res["mus"], res["sigs"] = map_id_to_label(G, mus, sigs) 
    res["embedding_path"] = os.path.join(RES_PATH, info["result_folder"]) 

    # save in the file
    dh.save_dict(res["mus"], res["embedding_path"]+".mus")
    dh.save_dict(res["sigs"], res["embedding_path"]+".sigs")

    return res


def map_id_to_label(G, mus, sigs):
    nrow = len(mus)
    assert len(G.nodes()) == nrow, "Fatal Error: the # of G.nodes() != # of mus' row"
    mp_mus = dict()
    mp_sigs = dict()

    for i in range(nrow):
        assert i in G, "Fatal Error: the node id not in G"
        mp_mus[G.node[i]["name"]] = mus[i]
        mp_sigs[G.node[i]["name"]] = sigs[i]

    return mp_mus, mp_sigs

