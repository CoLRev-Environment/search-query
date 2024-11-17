# test the parser because list is to much for me
import datetime
import json
import os
from pathlib import Path

import inquirer

import search_query.exception as search_query_exception
from search_query.parser import parse

if __name__ == "__main__":
    query_string = "(((\"digital\") OR \"work\" OR (singlesidedNEAR2deaf*)) AND (au=\"mnm\" OR \"Peter\") AND (au=\"xy\" OR au=\"yx\") AND au=\"testauth\") AND \"Thesis\""
    
    query_string = "TS=(((\"single sided\" NEAR/2 deaf*) OR (\"single sided\" NEAR/2 \"hearing loss*\") OR (\"single sided\" NEAR/2 \"loss of hearing\") OR (unilateral* NEAR/2 deaf*) OR (unilateral* NEAR/2 \"hearing loss\") OR (unilateral* NEAR/2 \"loss of hearing\") OR (asymmetric* NEAR/2 deaf*) OR (asymmetric* NEAR/2 \"hearing loss*\") OR (asymmetric* NEAR/2 \"loss of hearing\") OR \"deaf ear\" OR \"deaf side\") AND (locali* OR spatial* OR space OR direction*OR (sound NEAR/2 source*) OR (sound NEAR/2 test*) OR (sound NEAR/2 detect*) OR (noise NEAR/2 test*)))"
    
    query_string = '"One Health" AND ("Veterinary" OR "Animal") AND ("Medicine" OR "Human") AND ("Environment" OR "Ecosystem")'

    query_string = 'TS=(self* NEAR/7 (massag* OR myofascial OR "manual therapy" OR reflexology)) NOT TS=("foam roller" OR "foam rolling" OR "roller massage" OR "rolling massage" OR "manual lymph drainage")'

    query_string = 'ALL=("abundance") AND All=(Asset-Based Approach OR Asset-Based Community Development OR Community assets OR Community asset mapping OR Cultural assets OR Research assets OR Strengths-Based Approach OR Resource-Based Approach OR Positive Deviance Approach OR Capability Approach OR Capacity-Building Approach OR Resilience-Based Approach OR Empowerment Approach OR Solution-Focused Approach OR Positive Psychology Approach OR Community Asset Mapping)'

    syntax = 'wos'
    DB = {}
    search_fields="ALL"
    
    print(query_string)
    ret = parse(query_string, search_fields=search_fields, syntax=syntax)

    # Print for validation
    print(ret.to_string("structured"))
    query_pre_notation = ret.to_string("pre_notation")
    print(query_pre_notation)