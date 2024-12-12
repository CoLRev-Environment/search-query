# test the parser because list is to much for me


from search_query.constants import LinterMode
from search_query.parser import parse

if __name__ == "__main__":
    query_string = "(((tr=\"digital\") OR \"work\" OR (ti= singlesidedNEAR2deaf*)) AND (au=\"mnm\" OR \"Peter\") AND (au=\"xy\" OR au=\"yx\") AND au=\"testauth\") AND \"Thesis\" Languages: English"
    
    #query_string = 'TS=(((\"single sided\" NEAR/2 deaf*) OR (\"single sided\" NEAR/2 \"hearing loss*\") OR (\"single sided\" NEAR/2 \"loss of hearing\") OR (unilateral* NEAR/2 deaf*) OR (unilateral* NEAR/2 \"hearing loss\") OR (unilateral* NEAR/2 \"loss of hearing\") OR (asymmetric* NEAR/2 deaf*) OR (asymmetric* NEAR/2 \"hearing loss*\") OR (asymmetric* NEAR/2 \"loss of hearing\") OR \"deaf ear\" OR \"deaf side\") AND (locali* OR spatial* OR space OR direction* OR (sound NEAR/2 source*) OR (sound NEAR/2 test*) OR (sound NEAR/2 detect*) OR (noise NEAR/2 test*)))'
    
    #query_string = '"One Health" and ("Veterinary" and "Animal" and "peter") AND ("Medicine" OR "Human" or "peter") and ("Environment" OR "Ecosystem")'

    # query_string = 'TS=(self* NEAR/7 (massag* OR ti=myofascial OR "manual therapy" OR au= reflexology)) NOT TS=("foam roller" OR "foam rolling" OR "roller massage" OR "rolling massage" OR "manual lymph drainage")'

    # query_string = 'ALL=("abundance") AND All=(Asset-Based Approach OR (Asset-Based Community Development or Community assets) OR Community asset mapping OR Cultural assets OR Research assets OR Strengths-Based Approach OR Resource-Based Approach OR Positive Deviance Approach OR Capability Approach OR Capacity-Building Approach OR Resilience-Based Approach OR Empowerment Approach OR Solution-Focused Approach OR Positive Psychology Approach OR Community Asset Mapping)'

    # query_string = '(TS=("irgendwas1" OR "irgendwas2" or ("irgendewas 3" near/4 "irgendeas4") or nochmal or (sowas or etwas)))'

    # query_string = '( TS=("WHO EMT" or "World Health Organization EMT" or "emergency medical team*" or "emergency response team*" or (disaster NEAR/3 team*) or "rapid response team*" or "mobile medical unit*" or "field hospital*" or "medical rescue team*" or "medical relief team*" or "medical assistance team*" or (trauma NEAR/3 team*) or "foreign medical team*" or (mobile crisis NEAR/3 team*) or "Red Cross" or "Red Crescent" or "Medecins Sans Frontieres" or "Doctors without Borders" or "International Medical Corps" or "RedR UK" or "RedR UK" or Americares or "Global Medic Force" or GlobalMedic or "International Rescue Committee" or "International Rescue and Relief" or "International Rescue and Relief" or "Team Rubicon" or "Direct Relief" or "Save the Children" or "White Helmets" or "humanitarian organization*" or "humanitarian organisation*" or "humanitarian network*" or "nongovernmental organi$ation*" or "non-governmental organi$ation*" or NGO or NGOs or (civil NEAR/1 military) or (civilian NEAR/1 military) or "relief worker*") or TI=(doctor* or physician* or clinician* or surgeon* or nurse* or ((health* or medical) NEAR/2 (personnel or professional* or practitioner* or provider* or staff or worker*)) or medics) ) AND TS=("armed conflict*" or "aid station*" or "conflict zone*" or "conflict setting*" or "combat zone*" or war or wars or warzone* or warfight* or warfare or insurgenc* or "complex humanitarian environment*" or "complex humanitarian environment*" or "hostile environment*" or "conflict medicine" or "humanitarian conflict*" or "humanitarian cris*" or ((semi-permissive or semipermissive or non-permissive or nonpermissive) NEAR/1 environment*) ) AND TI=( prepar* or protect* or readiness or ready* or train or trained or training* or pre-deploy* or predeploy* or deploy* or redeploy* or safe* or "situational awareness" or security or brief* or prebrief* or pre-brief* or debrief* or "hazard vulnerability" or "after action review*" or "after action report*" or AAR or (risk* NEAR/3 manag*) ) not (Languages: English) py=2013'
    
    # query_string = 'TS=((nasal* OR intranasal* OR intra-nasal* OR transnasal* OR trans-nasal* OR nasopharyng*) NEAR/2 (highflow OR high-flow OR "high frequency" OR cannula$ OR canula$ OR prong$ OR speculum OR oxygen* OR ventilat* OR airway*))'

    # Fehler hier, weil safe mit 2 search fields in or kommt, aber Sapn$e* zweimal in near kommt
    # und NEAR/NONE als parent
    #query_string = '(safe* NEAR/5 Sapn$e*) AND (time NEAR/5 zeit*)'

    # query_string = 'exp1 NEAR/2 exp2 NEAR/9 exp3'

    syntax = 'wos'
    DB = {}
    search_fields="Title and Abstract"
    linter_mode = LinterMode.NONSTRICT
    
    print(query_string)

    if linter_mode:
        print('Current linter mode: ' + linter_mode)
    else:
        print('No mode for the linter was selected.\nStrict linter mode assumed.')

    ret = parse(query_string, search_fields=search_fields, syntax=syntax, mode=linter_mode)

    # Print for validation
    print(ret.to_string("structured"))
    query_pre_notation = ret.to_string("pre_notation")
    print(query_pre_notation)