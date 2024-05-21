#!/usr/bin/env python3
"""Query parser."""
from __future__ import annotations

import json
from abc import ABC
from abc import abstractmethod
from pathlib import Path
from typing import List
from typing import Optional
from typing import Union

from search_query.query import Query
from search_query.or_query import OrQuery
from search_query.and_query import AndQuery
from search_query.not_query import NotQuery


import re

class Node:
    def __init__(self, value: str = "NOT_INITIALIZED", operator: bool = False, children=None, fields=""):
        self.operator = operator
        self.value = value
        if children is None:
            self.children = []
        else:
            self.children = children
        
        # TODO : currently translating to pubmed. Should be generalized
        fields = fields.replace("AB=", "Abstract")
        self.fields = fields

class QueryParser:

    def simplify_tree(self, node):
        # Simplify based on associativity
        if not node.children or not node.operator:
            return  # Base case: if the node is a leaf or has no operator, return

        children_to_move = []
        children_to_append = []

        for i, child in enumerate(node.children):
            self.simplify_tree(child)  # Recursively simplify the child first
            if child.operator and node.operator and child.value == node.value:
                children_to_move.append(i)
                children_to_append.extend(child.children)

        node.children = [child for i, child in enumerate(node.children) if i not in children_to_move]
        node.children = children_to_append + node.children
        # Note: search queries often have parentheses at the beginning.
        # otherwise, node.children.extend(children_to_append) would be better

    def convert_node_to_query(self, node):

        if node.operator:
            if node.value == "AND":
                return AndQuery([self.convert_node_to_query(child) for child in node.children], search_field=node.fields)
            elif node.value == "OR":
                return OrQuery([self.convert_node_to_query(child) for child in node.children], search_field=node.fields)
            elif node.value == "NOT":
                return NotQuery([self.convert_node_to_query(child) for child in node.children], search_field=node.fields)
            elif node.value == "NOT_INITIALIZED" and len(node.children) == 1:
                return self.convert_node_to_query(node.children[0])
            else:
                raise ValueError(f"Invalid operator: {node.value}")
        else:
            return node.value


class WOSParser(QueryParser):

    def tokenize(self, expression):
        expression = expression.replace('”', '"').replace('“', '"')
        pattern = r'[A-Z]+=|\"[^\"]*\"|\bAND\b|\bOR\b|\bNOT\b|\(|\)|\b[\w-]+\b\*?'
        tokens = re.findall(pattern, expression)
        return [token.strip() for token in tokens if token.strip()]

    def is_term(self, token):
        return token not in ['AND', 'OR', "NOT", ')', '('] and not token.endswith("=")

    def parse_node(self, tokens, fields = ""):
        
        # Assume that expressions start with "(" (we can always add surrounding parentheses)

        node = Node(fields=fields, operator=True)

        current_operator = ""
        expecting_operator = False
        while tokens:
            next_item = tokens.pop(0)
            # print(next_item)
            if next_item.endswith("="):
                fields = next_item
                next_item = tokens.pop(0)
            # To make it more robust
            # if expecting_operator and item not in ["AND", "OR"]:
            #     if item == "or":
            #         item = "OR"
            #     elif item == "and":
            #         item = "AND"
            if next_item == ')':
                # Make sure we dont' read "()"
                assert len(node.children) > 0
                break

            if self.is_term(next_item):
                value = next_item.lstrip('"').rstrip('"')
                term_node = Node(value=value, operator=False, fields=fields)
                node.children.append(term_node)
                expecting_operator = True
                continue

            if next_item == "AND":
                assert expecting_operator
                if current_operator not in ["AND", ""]:
                    raise ValueError("Invalid Syntax")
                node.operator = True
                node.value = "AND"
                expecting_operator = False
                continue

            if next_item == "OR":
                assert expecting_operator, tokens
                if current_operator not in ["OR", ""]:
                    raise ValueError("Invalid Syntax")
                node.operator = True
                node.value = "OR"
                expecting_operator = False
                continue
                
            if next_item == "NOT":
                assert expecting_operator, tokens
                if current_operator not in ["NOT", ""]:
                    raise ValueError("Invalid Syntax")
                node.operator = True
                node.value = "NOT"
                expecting_operator = False
                continue

            if next_item == '(':
                node.children.append(self.parse_node(tokens, fields))
                # if tokens:
                #     assert tokens.pop(0) == ')', tokens
                expecting_operator = True

        # Single-element parenthesis
        if node.value == "NOT_INITIALIZED" and len(node.children) == 1:
            node = node.children[0]

        # Could add the tokens from which the node was created to the node (for debugging)
        return node


    def parse(self, query):
        query = f"({query})"
        print(query)
        tokens = self.tokenize(query)
        # print(tokens)
        # print(tokens)
        ret = self.parse_node(tokens)
        # print([r.value for r in ret.children[0].children])
        self.simplify_tree(ret)
        query = self.convert_node_to_query(ret)
        return query
        


def parse(query_str, query_type: str = "wos") -> Query:
    """Parse a query string."""
    if query_type == "wos":
        return WOSParser().parse(query_str)
    else:
        raise ValueError(f"Invalid query type: {query_type}")


if __name__ == "__main__":

    # for tests:
    cases = [("AB=(Health)", ["AB=", "(", "Health", ")"]),
             ("AB=Health", ["AB=", "Health"]),
             ("Health", ["Health"]),
             ("(Health*)", ["(", "Health*", ")"]),
             ("(Health NOT Care*)", ["(", "Health", "NOT", "Care*", ")"])]
    for case in cases:
        assert WOSParser().tokenize(case[0]) == case[1], WOSParser().tokenize(case[0])


    # STRATEGIE: Web-of-science und pubmed

    WOS_QUERIES = [
        {"source": "https://www.cabidigitallibrary.org/doi/10.1079/searchRxiv.2023.00382",
         "query_string": """(((TS=(bamboo* OR Bambusa OR Dendrocalamus OR Gigantochloa OR Guadua OR Melocanna OR Ochlandra OR Phyllostachys OR Thyrsostachys OR Schizostachyum OR Arundinia OR Lingnania OR Oxytenthera OR Chusquea)) AND TS=(socioeconomic OR socio-economic OR rural OR empower* OR communit* OR econom* OR “value chain*” OR “cultural heritage” OR “traditional knowledge” OR industr* OR livelihood* OR financ* OR poverty OR income* OR inclus*)) AND TS=(Change* OR relation* OR develop* OR afect* OR project* OR program* OR interven* OR initiative* OR implement*)) AND TS=(Climat* OR outcome* OR result* OR impact* OR social* OR “food security” OR gender* OR environment* OR contribut* OR ecolog* OR evaluat* OR beneft* OR efect* OR “global warming” OR “land restoration” OR soil* OR water* OR air OR capacit* OR particip*)"""
         },
        {"source": "https://www.cabidigitallibrary.org/doi/10.1079/searchRxiv.2024.00507",
         "query_string": """TS=(orphan AND drug) AND (pric* OR value OR cost)"""},
         # TO validate:
        {"source": "https://www.cabidigitallibrary.org/doi/10.1079/searchRxiv.2024.00477",
         "query_string": """("Health emergency communication" OR "Emergency health communication" OR "Crisis communication" OR "Public health messaging" OR "Emergency information dissemination" OR "Health promotion during emergencies" OR "Disease prevention communication" OR "Health behaviour change communication" OR "Emergency preparedness communication" OR "Disaster preparedness communication" OR "Emergency response communication") AND ("Community resilience" OR "Community mobilization" OR "Community mobilisation" OR "Community efforts for resilience" OR "Community collaboration for resilience" OR "Self-support within communities" OR "Social infrastructure resilience" OR "Building community resilience" OR "Strengthening community resilience" OR "Promoting community resilience" OR "Enhancing community resilience" OR "Fostering community resilience")"""},
         {"source": "https://www.cabidigitallibrary.org/doi/10.1079/searchRxiv.2024.00503",
          "query_string": """((((Black*) AND (people* OR person* OR individual* OR popula* OR communit* OR folk* OR human* OR race OR racial* OR women OR woman OR female* OR men OR man)) OR Negro* OR ((African* OR Afro*) AND (American* OR Ancest*)) OR "African Continental Ancestry Group*") AND (DASH* OR "MIND diet*" OR ((Diet*) AND (hypertensi* OR "blood pressure" OR HBP)) OR (("weight loss*" OR "weight reduction" OR "low calor*" OR hypocalor* OR "low energy*" OR "low sodium*" OR "low salt*" OR saltless* OR "salt free*" OR "low fat*" OR "fat free*" OR "low lipid*" OR "low cholesterol*" OR "low sugar" OR "sugar free*" OR therap* OR modificat* OR intervention* OR treatment* OR reduc* OR restrict*) AND (diet* OR nutrition*)) OR ((fat OR fats OR salt* OR sodium* OR natrium OR diet* OR calor* OR oil OR oils OR sugar*) AND (restric*))))"""},
        # TODO : CHECK NOT!?!!
        {"source": "https://www.cabidigitallibrary.org/doi/10.1079/searchRxiv.2024.00475",
         "query_string": """TS=("eating disorder*" OR "disordered eating") AND TS=(autonom* OR Choice OR Agency OR "Self-efficacy" OR "Self efficacy") AND TS=(Consent OR Voluntary OR "Self- endorse*" OR "Self-initiate*" OR "Self-admi*" OR "Patient-controlled" OR Collaborat* OR Participat* OR "Client feedback" OR "Client perspective" OR "Lived experience") AND LA=(English) NOT TS=(animal*) NOT TS=(child*)"""},
         {"source": "https://www.cabidigitallibrary.org/doi/10.1079/searchRxiv.2024.00458",
          "query_string": """((((TI=ICU OR AB=ICU) OR (TI=ICUS OR AB=ICUS) OR (TI="critical care*" OR AB="critical care*") OR (TI="intensive care*" OR AB="intensive care*") OR (TI="critical ill*" OR AB="critical ill*") OR (TI="critically ill*" OR AB="critically ill*")) AND ((TI=readmission* OR AB=readmission*) OR (TI=discharge* OR AB=discharge*) OR (TI=outpatient* OR AB=outpatient*) OR (TI="out patient*" OR AB="out patient*") OR (TI=Aftercare OR AB=Aftercare) OR (TI="after care" OR AB="after care") OR (TI=followup OR AB=followup) OR (TI="follow up" OR AB="follow up") OR (TI="after treatment*" OR AB="after treatment*") OR (TI="post treatment*" OR AB="post treatment*") OR (TI=postacute OR AB=postacute) OR (TI="post acute" OR AB="post acute"))) AND ((TI=rehab* OR AB=rehab*) OR (TI=habilit* OR AB=habilit*) OR (TI=therap* OR AB=therap*) OR (TI=ADL OR AB=ADL) OR (TI=ADLs OR AB=ADLs) OR (TI="activities of daily living" OR AB="activities of daily living") OR (TI="functional status" OR AB="functional status") OR (TI="self care" OR AB="self care"))) AND (((TI=utiliz* OR AB=utiliz*) OR (TI=use OR AB=use) OR (TI=uses OR AB=uses) OR (TI=usage* OR AB=usage*) OR (TI=accept* OR AB=accept*) OR (TI=participat* OR AB=participat*) OR (TI=involv* OR AB=involv*) OR (TI=engag* OR AB=engag*) OR (TI=access* OR AB=access*)))"""},
        {"source": "https://www.cabidigitallibrary.org/doi/10.1079/searchRxiv.2023.00421",
         "query_string": """(("problem based*" OR "problem centered*" OR "problem oriented*" OR "experiential learning*"OR PBL OR "case based learn*" OR "inquiry based learn*" OR "self directed learn*" OR "student centered learn*" OR "team based*" OR TBL OR "team learning*"OR "team approach*" OR Teamwork*) AND (clerkship* OR "professional education" OR "vocational education" OR "clinical apprenticeship*" OR "med ed*" OR GME OR "medical fellowship*" OR Residenc* OR resident* OR "house staff*" OR "medical intern*" OR "dental intern*" OR UME OR round* OR RN OR BSN OR MSN OR APRN OR DNP OR "educational nursing research*" OR "pharmacy intern*" OR "interprofessional education*" OR "interdisciplinary education*" OR ((clinical* OR didactic* OR health* OR medical* OR medicine* OR nurs* OR pharmac* OR "public health" OR dental* OR dentist* OR "physician assistant*" OR "physical therap*") AND (curricul* OR education* OR student* OR undergrad* OR gradua*))) AND (Communication* OR Miscommunication* OR Misinformation* OR "information seeking*" OR Language* OR Dialect* OR Literac* OR Illiterac* OR Narrati* OR Negotiat* OR "conflict resolution*" OR Mediat* OR Arbitrat* OR Diplomac* OR "verbal behavior*" OR Speech* OR "public speaking" OR Persuasion OR Brainwashing OR "group process*" OR "group think" OR "group meet*" OR Consensus OR "group dynamic*" OR Groupthink OR "organizational dynamic*" OR "organization dynamic*" OR "social loaf*" OR "organizational behavior*" OR "organization behavior*" OR "group pressure*" OR "social dynamic*" OR "group interaction*" OR "collective efficac*" OR "team efficac*" OR "group potenc*" OR "group structure*" OR "peer group*" OR "peer assessment*" OR "peer evaluation*" OR "peer learning*" OR "peer pressure" OR "peer influence*" OR "peer review*" OR Role* OR "sensitivity training group*" OR "group sensitivity training*" OR "T group*" OR Tgroup* OR "group encounter*"))"""}

    ]

    # TODO : list format:
    # https://www.cabidigitallibrary.org/doi/10.1079/searchRxiv.2024.00492

    for wos_query in WOS_QUERIES:
        print('--------------------')
        query = parse(wos_query["query_string"])
        print()
        print(query.to_string(syntax='pubmed'))
        print()
        print(query.to_string())
        # return parse(tokens)
    
    # parse(WOS_QUERIES[1]["query_string"])
    # print(query)