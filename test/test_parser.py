#!/usr/bin/env python
"""Tests for search query translation"""
import pytest

from search_query.parser import parse
from search_query.parser import WOSListParser
from search_query.parser import WOSParser

# flake8: noqa: E501


@pytest.mark.parametrize(
    "query_string, tokens",
    [
        (
            "AB=(Health)",
            [("AB=", (0, 3)), ("(", (3, 4)), ("Health", (4, 10)), (")", (10, 11))],
        ),
        ("AB=Health", [("AB=", (0, 3)), ("Health", (3, 9))]),
        ("Health", [("Health", (0, 6))]),
        ("(Health*)", [("(", (0, 1)), ("Health*", (1, 8)), (")", (8, 9))]),
        (
            "(Health NOT Care*)",
            [
                ("(", (0, 1)),
                ("Health", (1, 7)),
                ("NOT", (8, 11)),
                ("Care*", (12, 17)),
                (")", (17, 18)),
            ],
        ),
        (
            """TI=(((morphine NEAR/2 equ*) or MME)) OR AB=(((morphine NEAR/2 equ*) or MME))""",
            [
                ("TI=", (0, 3)),
                ("(", (3, 4)),
                ("(", (4, 5)),
                ("(", (5, 6)),
                ("morphine", (6, 14)),
                ("NEAR/2", (15, 21)),
                ("equ*", (22, 26)),
                (")", (26, 27)),
                ("or", (28, 30)),
                ("MME", (31, 34)),
                (")", (34, 35)),
                (")", (35, 36)),
                ("OR", (37, 39)),
                ("AB=", (40, 43)),
                ("(", (43, 44)),
                ("(", (44, 45)),
                ("(", (45, 46)),
                ("morphine", (46, 54)),
                ("NEAR/2", (55, 61)),
                ("equ*", (62, 66)),
                (")", (66, 67)),
                ("or", (68, 70)),
                ("MME", (71, 74)),
                (")", (74, 75)),
                (")", (75, 76)),
            ],
        ),
        (
            """TS=((narcotic-free or narcoticfree or narcotic-sparing or narcoticsparing or non-opioid or nonopioid or non-opiate or nonopiate or opioid-free or opioidfree or OFA or opiate-based or opiatebased or opioid-based or opioidbased or OBA or opioid-less or opioidless or opiate-less or opiateless or opioid-reduced or opiate-reduced or opiate-free or opiatefree or opioid-sparing or opioidsparing or opiate-sparing or opiatesparing or opioid management or opiate management))""",
            [
                ("TS=", (0, 3)),
                ("(", (3, 4)),
                ("(", (4, 5)),
                ("narcotic-free", (5, 18)),
                ("or", (19, 21)),
                ("narcoticfree", (22, 34)),
                ("or", (35, 37)),
                ("narcotic-sparing", (38, 54)),
                ("or", (55, 57)),
                ("narcoticsparing", (58, 73)),
                ("or", (74, 76)),
                ("non-opioid", (77, 87)),
                ("or", (88, 90)),
                ("nonopioid", (91, 100)),
                ("or", (101, 103)),
                ("non-opiate", (104, 114)),
                ("or", (115, 117)),
                ("nonopiate", (118, 127)),
                ("or", (128, 130)),
                ("opioid-free", (131, 142)),
                ("or", (143, 145)),
                ("opioidfree", (146, 156)),
                ("or", (157, 159)),
                ("OFA", (160, 163)),
                ("or", (164, 166)),
                ("opiate-based", (167, 179)),
                ("or", (180, 182)),
                ("opiatebased", (183, 194)),
                ("or", (195, 197)),
                ("opioid-based", (198, 210)),
                ("or", (211, 213)),
                ("opioidbased", (214, 225)),
                ("or", (226, 228)),
                ("OBA", (229, 232)),
                ("or", (233, 235)),
                ("opioid-less", (236, 247)),
                ("or", (248, 250)),
                ("opioidless", (251, 261)),
                ("or", (262, 264)),
                ("opiate-less", (265, 276)),
                ("or", (277, 279)),
                ("opiateless", (280, 290)),
                ("or", (291, 293)),
                ("opioid-reduced", (294, 308)),
                ("or", (309, 311)),
                ("opiate-reduced", (312, 326)),
                ("or", (327, 329)),
                ("opiate-free", (330, 341)),
                ("or", (342, 344)),
                ("opiatefree", (345, 355)),
                ("or", (356, 358)),
                ("opioid-sparing", (359, 373)),
                ("or", (374, 376)),
                ("opioidsparing", (377, 390)),
                ("or", (391, 393)),
                ("opiate-sparing", (394, 408)),
                ("or", (409, 411)),
                ("opiatesparing", (412, 425)),
                ("or", (426, 428)),
                ("opioid management", (429, 446)),
                ("or", (447, 449)),
                ("opiate management", (450, 467)),
                (")", (467, 468)),
                (")", (468, 469)),
            ],
        ),
        (
            """TS=((((multimodal$ or multi-modal$ or unimodal$ or uni-modal$ or conventional) NEAR/1 (an$esthe* or analge* or approach or strategy or strategies or protocol$ or regimen$)) or MITA or ((combination or combined) NEAR/1 (infusion* or injection*))))""",
            [
                ("TS=", (0, 3)),
                ("(", (3, 4)),
                ("(", (4, 5)),
                ("(", (5, 6)),
                ("(", (6, 7)),
                ("multimodal$", (7, 18)),
                ("or", (19, 21)),
                ("multi-modal$", (22, 34)),
                ("or", (35, 37)),
                ("unimodal$", (38, 47)),
                ("or", (48, 50)),
                ("uni-modal$", (51, 61)),
                ("or", (62, 64)),
                ("conventional", (65, 77)),
                (")", (77, 78)),
                ("NEAR/1", (79, 85)),
                ("(", (86, 87)),
                ("an$esthe*", (87, 96)),
                ("or", (97, 99)),
                ("analge*", (100, 107)),
                ("or", (108, 110)),
                ("approach", (111, 119)),
                ("or", (120, 122)),
                ("strategy", (123, 131)),
                ("or", (132, 134)),
                ("strategies", (135, 145)),
                ("or", (146, 148)),
                ("protocol$", (149, 158)),
                ("or", (159, 161)),
                ("regimen$", (162, 170)),
                (")", (170, 171)),
                (")", (171, 172)),
                ("or", (173, 175)),
                ("MITA", (176, 180)),
                ("or", (181, 183)),
                ("(", (184, 185)),
                ("(", (185, 186)),
                ("combination", (186, 197)),
                ("or", (198, 200)),
                ("combined", (201, 209)),
                (")", (209, 210)),
                ("NEAR/1", (211, 217)),
                ("(", (218, 219)),
                ("infusion*", (219, 228)),
                ("or", (229, 231)),
                ("injection*", (232, 242)),
                (")", (242, 243)),
                (")", (243, 244)),
                (")", (244, 245)),
                (")", (245, 246)),
            ],
        ),
        ("ne?t", [("ne?t", (0, 4))]),
    ],
)
def test_tokenization(query_string: str, tokens: tuple) -> None:
    print(query_string)
    print()
    wos_parser = WOSParser(query_string)
    wos_parser.tokenize()
    print(wos_parser.tokens)
    print(wos_parser.get_token_types(wos_parser.tokens, legend=True))
    print(tokens)
    assert wos_parser.tokens == tokens


@pytest.mark.parametrize(
    "source, query_string, expected",
    [
        (
            "https://www.cabidigitallibrary.org/doi/10.1079/searchRxiv.2024.00475",
            """TS=("eating disorder*" OR "disordered eating") AND TS=(autonom* OR Choice OR Agency OR "Self-efficacy" OR "Self efficacy") AND TS=(Consent OR Voluntary OR "Self- endorse*" OR "Self-initiate*" OR "Self-admi*" OR "Patient-controlled" OR Collaborat* OR Participat* OR "Client feedback" OR "Client perspective" OR "Lived experience") AND LA=(English) NOT TS=(animal*) NOT TS=(child*)""",
            """AND[OR[eating disorder*, disordered eating], OR[autonom*, Choice, Agency, Self-efficacy, Self efficacy], OR[Consent, Voluntary, Self- endorse*, Self-initiate*, Self-admi*, Patient-controlled, Collaborat*, Participat*, Client feedback, Client perspective, Lived experience], English, NOT[animal*], NOT[child*]]""",
        ),
        (
            "https://www.cabidigitallibrary.org/doi/10.1079/searchRxiv.2023.00382",
            """(((TS=(bamboo* OR Bambusa OR Dendrocalamus OR Gigantochloa OR Guadua OR Melocanna OR Ochlandra OR Phyllostachys OR Thyrsostachys OR Schizostachyum OR Arundinia OR Lingnania OR Oxytenthera OR Chusquea)) AND TS=(socioeconomic OR socio-economic OR rural OR empower* OR communit* OR econom* OR “value chain*” OR “cultural heritage” OR “traditional knowledge” OR industr* OR livelihood* OR financ* OR poverty OR income* OR inclus*)) AND TS=(Change* OR relation* OR develop* OR afect* OR project* OR program* OR interven* OR initiative* OR implement*)) AND TS=(Climat* OR outcome* OR result* OR impact* OR social* OR “food security” OR gender* OR environment* OR contribut* OR ecolog* OR evaluat* OR beneft* OR efect* OR “global warming” OR “land restoration” OR soil* OR water* OR air OR capacit* OR particip*)""",
            "AND[AND[AND[OR[bamboo*, Bambusa, Dendrocalamus, Gigantochloa, Guadua, Melocanna, Ochlandra, Phyllostachys, Thyrsostachys, Schizostachyum, Arundinia, Lingnania, Oxytenthera, Chusquea], OR[socioeconomic, socio-economic, rural, empower*, communit*, econom*, value chain*, cultural heritage, traditional knowledge, industr*, livelihood*, financ*, poverty, income*, inclus*]], OR[Change*, relation*, develop*, afect*, project*, program*, interven*, initiative*, implement*]], OR[Climat*, outcome*, result*, impact*, social*, food security, gender*, environment*, contribut*, ecolog*, evaluat*, beneft*, efect*, global warming, land restoration, soil*, water*, air, capacit*, particip*]]",
        ),
        (
            "https://www.cabidigitallibrary.org/doi/10.1079/searchRxiv.2024.00507",
            """TS=(orphan AND drug) AND (pric* OR value OR cost)""",
            "AND[AND[orphan, drug], OR[pric*, value, cost]]",
        ),
        (
            "https://www.cabidigitallibrary.org/doi/10.1079/searchRxiv.2024.00477",
            """("Health emergency communication" OR "Emergency health communication" OR "Crisis communication" OR "Public health messaging" OR "Emergency information dissemination" OR "Health promotion during emergencies" OR "Disease prevention communication" OR "Health behaviour change communication" OR "Emergency preparedness communication" OR "Disaster preparedness communication" OR "Emergency response communication") AND ("Community resilience" OR "Community mobilization" OR "Community mobilisation" OR "Community efforts for resilience" OR "Community collaboration for resilience" OR "Self-support within communities" OR "Social infrastructure resilience" OR "Building community resilience" OR "Strengthening community resilience" OR "Promoting community resilience" OR "Enhancing community resilience" OR "Fostering community resilience")""",
            "AND[OR[Health emergency communication, Emergency health communication, Crisis communication, Public health messaging, Emergency information dissemination, Health promotion during emergencies, Disease prevention communication, Health behaviour change communication, Emergency preparedness communication, Disaster preparedness communication, Emergency response communication], OR[Community resilience, Community mobilization, Community mobilisation, Community efforts for resilience, Community collaboration for resilience, Self-support within communities, Social infrastructure resilience, Building community resilience, Strengthening community resilience, Promoting community resilience, Enhancing community resilience, Fostering community resilience]]",
        ),
        (
            "https://www.cabidigitallibrary.org/doi/10.1079/searchRxiv.2024.00503",
            """((((Black*) AND (people* OR person* OR individual* OR popula* OR communit* OR folk* OR human* OR race OR racial* OR women OR woman OR female* OR men OR man)) OR Negro* OR ((African* OR Afro*) AND (American* OR Ancest*)) OR "African Continental Ancestry Group*") AND (DASH* OR "MIND diet*" OR ((Diet*) AND (hypertensi* OR "blood pressure" OR HBP)) OR (("weight loss*" OR "weight reduction" OR "low calor*" OR hypocalor* OR "low energy*" OR "low sodium*" OR "low salt*" OR saltless* OR "salt free*" OR "low fat*" OR "fat free*" OR "low lipid*" OR "low cholesterol*" OR "low sugar" OR "sugar free*" OR therap* OR modificat* OR intervention* OR treatment* OR reduc* OR restrict*) AND (diet* OR nutrition*)) OR ((fat OR fats OR salt* OR sodium* OR natrium OR diet* OR calor* OR oil OR oils OR sugar*) AND (restric*))))""",
            "AND[OR[AND[Black*, OR[people*, person*, individual*, popula*, communit*, folk*, human*, race, racial*, women, woman, female*, men, man]], Negro*, AND[OR[African*, Afro*], OR[American*, Ancest*]], African Continental Ancestry Group*], OR[DASH*, MIND diet*, AND[Diet*, OR[hypertensi*, blood pressure, HBP]], AND[OR[weight loss*, weight reduction, low calor*, hypocalor*, low energy*, low sodium*, low salt*, saltless*, salt free*, low fat*, fat free*, low lipid*, low cholesterol*, low sugar, sugar free*, therap*, modificat*, intervention*, treatment*, reduc*, restrict*], OR[diet*, nutrition*]], AND[OR[fat, fats, salt*, sodium*, natrium, diet*, calor*, oil, oils, sugar*], restric*]]]",
        ),
        (
            "https://www.cabidigitallibrary.org/doi/10.1079/searchRxiv.2024.00458",
            """((((TI=ICU OR AB=ICU) OR (TI=ICUS OR AB=ICUS) OR (TI="critical care*" OR AB="critical care*") OR (TI="intensive care*" OR AB="intensive care*") OR (TI="critical ill*" OR AB="critical ill*") OR (TI="critically ill*" OR AB="critically ill*")) AND ((TI=readmission* OR AB=readmission*) OR (TI=discharge* OR AB=discharge*) OR (TI=outpatient* OR AB=outpatient*) OR (TI="out patient*" OR AB="out patient*") OR (TI=Aftercare OR AB=Aftercare) OR (TI="after care" OR AB="after care") OR (TI=followup OR AB=followup) OR (TI="follow up" OR AB="follow up") OR (TI="after treatment*" OR AB="after treatment*") OR (TI="post treatment*" OR AB="post treatment*") OR (TI=postacute OR AB=postacute) OR (TI="post acute" OR AB="post acute"))) AND ((TI=rehab* OR AB=rehab*) OR (TI=habilit* OR AB=habilit*) OR (TI=therap* OR AB=therap*) OR (TI=ADL OR AB=ADL) OR (TI=ADLs OR AB=ADLs) OR (TI="activities of daily living" OR AB="activities of daily living") OR (TI="functional status" OR AB="functional status") OR (TI="self care" OR AB="self care"))) AND (((TI=utiliz* OR AB=utiliz*) OR (TI=use OR AB=use) OR (TI=uses OR AB=uses) OR (TI=usage* OR AB=usage*) OR (TI=accept* OR AB=accept*) OR (TI=participat* OR AB=participat*) OR (TI=involv* OR AB=involv*) OR (TI=engag* OR AB=engag*) OR (TI=access* OR AB=access*)))""",
            "AND[AND[AND[OR[OR[ICU, ICU], OR[ICUS, ICUS], OR[critical care*, critical care*], OR[intensive care*, intensive care*], OR[critical ill*, critical ill*], OR[critically ill*, critically ill*]], OR[OR[readmission*, readmission*], OR[discharge*, discharge*], OR[outpatient*, outpatient*], OR[out patient*, out patient*], OR[Aftercare, Aftercare], OR[after care, after care], OR[followup, followup], OR[follow up, follow up], OR[after treatment*, after treatment*], OR[post treatment*, post treatment*], OR[postacute, postacute], OR[post acute, post acute]]], OR[OR[rehab*, rehab*], OR[habilit*, habilit*], OR[therap*, therap*], OR[ADL, ADL], OR[ADLs, ADLs], OR[activities of daily living, activities of daily living], OR[functional status, functional status], OR[self care, self care]]], OR[OR[utiliz*, utiliz*], OR[use, use], OR[uses, uses], OR[usage*, usage*], OR[accept*, accept*], OR[participat*, participat*], OR[involv*, involv*], OR[engag*, engag*], OR[access*, access*]]]",
        ),
        (
            "https://www.cabidigitallibrary.org/doi/10.1079/searchRxiv.2023.00421",
            """(("problem based*" OR "problem centered*" OR "problem oriented*" OR "experiential learning*"OR PBL OR "case based learn*" OR "inquiry based learn*" OR "self directed learn*" OR "student centered learn*" OR "team based*" OR TBL OR "team learning*"OR "team approach*" OR Teamwork*) AND (clerkship* OR "professional education" OR "vocational education" OR "clinical apprenticeship*" OR "med ed*" OR GME OR "medical fellowship*" OR Residenc* OR resident* OR "house staff*" OR "medical intern*" OR "dental intern*" OR UME OR round* OR RN OR BSN OR MSN OR APRN OR DNP OR "educational nursing research*" OR "pharmacy intern*" OR "interprofessional education*" OR "interdisciplinary education*" OR ((clinical* OR didactic* OR health* OR medical* OR medicine* OR nurs* OR pharmac* OR "public health" OR dental* OR dentist* OR "physician assistant*" OR "physical therap*") AND (curricul* OR education* OR student* OR undergrad* OR gradua*))) AND (Communication* OR Miscommunication* OR Misinformation* OR "information seeking*" OR Language* OR Dialect* OR Literac* OR Illiterac* OR Narrati* OR Negotiat* OR "conflict resolution*" OR Mediat* OR Arbitrat* OR Diplomac* OR "verbal behavior*" OR Speech* OR "public speaking" OR Persuasion OR Brainwashing OR "group process*" OR "group think" OR "group meet*" OR Consensus OR "group dynamic*" OR Groupthink OR "organizational dynamic*" OR "organization dynamic*" OR "social loaf*" OR "organizational behavior*" OR "organization behavior*" OR "group pressure*" OR "social dynamic*" OR "group interaction*" OR "collective efficac*" OR "team efficac*" OR "group potenc*" OR "group structure*" OR "peer group*" OR "peer assessment*" OR "peer evaluation*" OR "peer learning*" OR "peer pressure" OR "peer influence*" OR "peer review*" OR Role* OR "sensitivity training group*" OR "group sensitivity training*" OR "T group*" OR Tgroup* OR "group encounter*"))""",
            "AND[OR[problem based*, problem centered*, problem oriented*, experiential learning*, PBL, case based learn*, inquiry based learn*, self directed learn*, student centered learn*, team based*, TBL, team learning*, team approach*, Teamwork*], OR[clerkship*, professional education, vocational education, clinical apprenticeship*, med ed*, GME, medical fellowship*, Residenc*, resident*, house staff*, medical intern*, dental intern*, UME, round*, RN, BSN, MSN, APRN, DNP, educational nursing research*, pharmacy intern*, interprofessional education*, interdisciplinary education*, AND[OR[clinical*, didactic*, health*, medical*, medicine*, nurs*, pharmac*, public health, dental*, dentist*, physician assistant*, physical therap*], OR[curricul*, education*, student*, undergrad*, gradua*]]], OR[Communication*, Miscommunication*, Misinformation*, information seeking*, Language*, Dialect*, Literac*, Illiterac*, Narrati*, Negotiat*, conflict resolution*, Mediat*, Arbitrat*, Diplomac*, verbal behavior*, Speech*, public speaking, Persuasion, Brainwashing, group process*, group think, group meet*, Consensus, group dynamic*, Groupthink, organizational dynamic*, organization dynamic*, social loaf*, organizational behavior*, organization behavior*, group pressure*, social dynamic*, group interaction*, collective efficac*, team efficac*, group potenc*, group structure*, peer group*, peer assessment*, peer evaluation*, peer learning*, peer pressure, peer influence*, peer review*, Role*, sensitivity training group*, group sensitivity training*, T group*, Tgroup*, group encounter*]]",
        ),
        (
            "test",
            """TS=(((opioid-free or opiate-free or opioid-sparing or opiate-sparing or opioid-reduced or opiate-reduced) AND (opioid-based or opiate-based or opioid-related or opiate-related or opioid-inclusive or opiate-inclusive or opioid-containing or opiate-containing)))""",
            """AND[OR[opioid-free, opiate-free, opioid-sparing, opiate-sparing, opioid-reduced, opiate-reduced], OR[opioid-based, opiate-based, opioid-related, opiate-related, opioid-inclusive, opiate-inclusive, opioid-containing, opiate-containing]]""",
        ),
    ],
)
def test_wos_query_parser(source: str, query_string: str, expected: str) -> None:
    """Test the translation of a search query to a WOS query"""

    # STRATEGIE
    # - Web-of-science und pubmed
    # - list format: https://www.cabidigitallibrary.org/doi/10.1079/searchRxiv.2024.00492

    print("--------------------")
    print(source)
    print()
    print(query_string)
    print()
    query = parse(query_string, query_type="wos")
    query_str = query.to_string()
    print(query_str)

    assert query_str == expected


@pytest.mark.parametrize(
    "source, query_string, expected",
    [
        (
            "https://www.cabidigitallibrary.org/doi/10.1079/searchRxiv.2023.00244",
            # """((Environment[Mesh:NoExp] OR "Environment health*"[tiab] OR "Environmental health*"[tiab] OR "planetary health*"[tiab] OR "planet health*"[tiab] OR "environmental issue*"[tiab] OR "environment issue*"[tiab] OR Ecolog*[tiab] OR "Carbon Footprint"[Mesh] OR "carbon footprint*"[tiab] OR Climate[Mesh:NoExp] OR Climat*[tiab] OR Ecosystem[Mesh:NoExp] OR Ecosystem*[tiab] OR Conservation*[tiab] OR "environment protection*"[tiab] OR "environmental protection*"[tiab] OR "environment remediation*"[tiab] OR "environmental remediation*"[tiab] OR "environment restoration*"[tiab] OR "environmental restoration*"[tiab] OR "sustainable develop*"[tiab] OR "environmental sustain*"[tiab] OR "environment sustain*"[tiab] OR Disasters[Mesh:NoExp] OR Disaster*[tiab] OR "Natural Disasters"[Mesh:NoExp] OR "Environmental Policy"[Mesh] OR "environmental polic*"[tiab] OR "environment polic*"[tiab] OR Environmentalism[Mesh] OR Environmentalism*[tiab] OR "Environmental Advocacy"[tiab] OR "Environmental Activism"[tiab] OR "Environmental justice"[tiab] OR "environment justice"[tiab] OR "environment awareness"[tiab] OR "environmental awareness"[tiab] OR "Energy-Generating Resources"[Mesh:NoExp] OR "energy generating resource*"[tiab] OR "Fossil Fuels"[Mesh:NoExp] OR "fossil fuel*"[tiab] OR "Natural Gas"[Mesh] OR "natural gas*"[tiab] OR "Renewable Energy"[Mesh:NoExp] OR "renewable energ*"[tiab] OR "sustainable energ*"[tiab] OR "Ecological and Environmental Phenomena"[Mesh:NoExp] OR "environmental phenomen*"[tiab] OR "Climate Change"[Mesh] OR "global warm*"[tiab] OR "Environmental Pollution"[Mesh:NoExp] OR Pollution*[tiab] OR "Air Pollution"[Mesh:NoExp] OR "Air Qualit*"[tiab] OR "Light Pollution"[Mesh] OR "Petroleum Pollution"[Mesh] OR "oil spill"[tiab] OR "Waste Products"[Mesh:NoExp] OR "waste product*"[tiab] OR "Water Pollution"[Mesh:NoExp] OR "acid rain"[tiab] OR "Environmental Health"[Mesh:NoExp] OR Ecotoxicology[Mesh] OR ecotoxicol*[tiab] OR "environmental toxic*"[tiab] OR "environment toxic*"[tiab] OR Sanitation[Mesh:NoExp] OR Sanitation[tiab] OR "Environmental Exposure"[Mesh:NoExp] OR "environmental exposure*"[tiab] OR "environment exposure*"[tiab] OR "Environmental Monitoring"[Mesh:NoExp] OR "environmental monitor*"[tiab] OR "environment monitor*"[tiab] OR "Environmental Biomarkers"[Mesh] OR "environmental biomarker*"[tiab] OR "Environmental Indicators"[Mesh] OR "environmental indicator*"[tiab] OR "environment indicator*"[tiab] OR "Water Quality"[Mesh] OR "water quality"[tiab] OR "sanitary survey*"[tiab] OR "Environmental Illness"[Mesh:NoExp] OR "environment illness*"[tiab] OR "environmental disease*"[tiab] OR "environmental illness*"[tiab] OR "environmental hypersensitivit*"[tiab]) AND (Literacy[Mesh] OR Literac*[tiab] OR Illiterac*[tiab] OR "Health Literacy"[Mesh] OR "Patient Education as Topic"[Mesh:NoExp] OR "patient education*"[tiab] OR "education of patient*"[tiab] OR "informal education*"[tiab] OR "Consumer Health Information"[Mesh:NoExp] OR "consumer health*"[tiab] OR "Health Knowledge, Attitudes, Practice"[Mesh] OR "health knowledge*"[tiab] OR "Health Communication"[Mesh] OR "health communication*"[tiab] OR "community-based participatory research"[Mesh] OR "participatory research*"[tiab] OR "citizen science*"[tiab]))""",
            """(Environment[Mesh:NoExp] OR "Environment health*"[tiab]) AND (Literacy[Mesh] OR Literac*[tiab])""",
            """AND[OR[Environment, Environment health*], OR[Literacy, Literac*]]""",
        )
    ],
)
def test_pubmed_query_parser(source: str, query_string: str, expected: str) -> None:
    """Test the translation of a search query to a Pubmed query"""

    # STRATEGIE
    # - Web-of-science und pubmed
    # - list format: https://www.cabidigitallibrary.org/doi/10.1079/searchRxiv.2024.00492

    print("--------------------")
    print(source)
    print()
    print(query_string)
    print()
    query = parse(query_string, query_type="pubmed")
    query_str = query.to_string()
    print(query_str)

    assert query_str == expected


@pytest.mark.parametrize(
    "source, query_string, expected",
    [
        (
            "https://www.cabidigitallibrary.org/doi/10.1079/searchRxiv.2023.00155",
            """1.	Clinical competence
2.	Professional practice
3.	Cultural competence
4.	Accreditation
5.	Interprofessional relations
6.	Professional education
7.	Professional licenses
8.	Standards
9.	Professional licensure examinations
10.	Professional standards
11.	Licenses
12.	Professional --law & legislation
13.	Professional --law & legislation (Search modes – SmartText searching Interface)
14.	License agreement
15.	Educational accreditation
16.	Interdisciplinary education
17.	National competency-based educational tests
18.	Globalization
19.	Certification
20.	Mutual recognition agreement
21.	Professional equivalenc*
22.	Interchangeability
23.	Internationally educated professionals
24.	Internationally educated health professionals
25.	(S1 OR S2 OR S3 OR S4 OR S5 OR S6 OR S7 OR S8 OR S9 OR S10 OR S11 OR S12 OR S13 OR S14 OR S15 OR S16 OR S17 OR S18 OR S19)
26.	(S20 OR S21 OR S22 OR S23 OR S24)
27.	(S25 AND S26)""",
            """AND[OR[Clinical competence, Professional practice, Cultural competence, Accreditation, Interprofessional relations, Professional education, Professional licenses, Standards, Professional licensure examinations, Professional standards, Licenses, Professional --law & legislation, Professional --law & legislation (Search modes – SmartText searching Interface), License agreement, Educational accreditation, Interdisciplinary education, National competency-based educational tests, Globalization, Certification], OR[Mutual recognition agreement, Professional equivalenc*, Interchangeability, Internationally educated professionals, Internationally educated health professionals]]""",
        )
    ],
)
def test_cinahl_query_parser(source: str, query_string: str, expected: str) -> None:
    """Test the translation of a search query to a CINAHL query"""

    print("--------------------")
    print(source)
    print()
    print(query_string)
    print()
    query = parse(query_string, query_type="cinahl")
    query_str = query.to_string()
    print(query_str)

    assert query_str == expected


@pytest.mark.parametrize(
    "source, query_string, expected",
    [
        (
            "https://www.cabidigitallibrary.org/doi/10.1079/searchRxiv.2024.00492",
            """1.	TI=((itch* or prurit*) or (ileus* or obstipat* or constipat*)) OR AB=((itch* or prurit*) or (ileus* or obstipat* or constipat*))
2.	TI=(((morphine NEAR/2 equ*) or MME)) OR AB=(((morphine NEAR/2 equ*) or MME))
3.	TI=( ("arrhythmia$" or "arrythmia$" or "disrhythmia$" or "dysrhythmia$" or "arrhytmia$" or "ectopic heart rhythm" or "ectopic rhythm" or "heart aberrant conduction" or "heart ectopic beat$" or "heart ectopic ventricle contraction" or "heart rhythm disease" or "heart rhythm disorder" or "heart rhythm problem$" or "atrial fibrillation" or "atrial flutter" or "atrioventricular block" or "bradycardia" or "bundle-branch block" or "cardiac sinus arrest" or "cardiopulmonary arrest" or "heart block" or "heart fibrillation" or "heart muscle conduction disturbance" or "interatrial block" or "long qt syndrome" or "sick sinus syndrome" or "sinoatrial block" or "tachycardia" or "ventricular fibrillation" or "ventricular flutter")) OR AB=( ("arrhythmia$" or "arrythmia$" or "disrhythmia$" or "dysrhythmia$" or "arrhytmia$" or "ectopic heart rhythm" or "ectopic rhythm" or "heart aberrant conduction" or "heart ectopic beat$" or "heart ectopic ventricle contraction" or "heart rhythm disease" or "heart rhythm disorder" or "heart rhythm problem$" or "atrial fibrillation" or "atrial flutter" or "atrioventricular block" or "bradycardia" or "bundle-branch block" or "cardiac sinus arrest" or "cardiopulmonary arrest" or "heart block" or "heart fibrillation" or "heart muscle conduction disturbance" or "interatrial block" or "long qt syndrome" or "sick sinus syndrome" or "sinoatrial block" or "tachycardia" or "ventricular fibrillation" or "ventricular flutter"))
4.	TI=(length NEAR/2 stay) OR AB=(length NEAR/2 stay)
5.	TI=(("enhanced recovery after surgery" or "accelerated recovery" or reduced side effect$ or ERAS or PONV or POCD or "patient reported outcome$" or PROM$ or "patient-reported treatment outcome" or "patientreported outcome" or "self-reported outcome" or "self-reported patient outcome" or "self-reported treatment outcome" or "selfreported outcome" or "patient-reported outcome" or "quality of recovery" or QoR or QoR15 or QoR40 or QoR-15 or QoR-40 or pain measurement$ or pain assessment$ or pain score$ or pain scale$ or pain intensit* or pain severity or "numeric rating scale" or NRS or "visual analogue scale" or VAS or "Richmond Agitation-Sedation Scale" or RASS)) OR AB=(("enhanced recovery after surgery" or "accelerated recovery" or reduced side effect$ or ERAS or PONV or POCD or "patient reported outcome$" or PROM$ or "patient-reported treatment outcome" or "patientreported outcome" or "self-reported outcome" or "self-reported patient outcome" or "self-reported treatment outcome" or "selfreported outcome" or "patient-reported outcome" or "quality of recovery" or QoR or QoR15 or QoR40 or QoR-15 or QoR-40 or pain measurement$ or pain assessment$ or pain score$ or pain scale$ or pain intensit* or pain severity or "numeric rating scale" or NRS or "visual analogue scale" or VAS or "Richmond Agitation-Sedation Scale" or RASS))
6.	TI=(((post-operative or post-operation or post-surgery or post-surgical or postoperation or postoperative or postsurgery or postsurgical or post-procedural or postprocedural or following surgery or after surgery or postop or post-op or post-anesthesia or post-anaesthesia or postanesthesia or postanaesthesia or postanesthetic or postanaesthetic or post-anesthetic or post-anaesthetic or surgery-associated or surgery-derived or surgery-induced or surgery-related) AND (pain or nausea or vomiting or outcome$ or complication$ or cognitive dysfunction$ or delirium or awakening or emergence or urinary retention or opioid consumption or opiate consumption or pulmonary complication$))) OR AB=(((post-operative or post-operation or post-surgery or post-surgical or postoperation or postoperative or postsurgery or postsurgical or post-procedural or postprocedural or following surgery or after surgery or postop or post-op or post-anesthesia or post-anaesthesia or postanesthesia or postanaesthesia or postanesthetic or postanaesthetic or post-anesthetic or post-anaesthetic or surgery-associated or surgery-derived or surgery-induced or surgery-related) AND (pain or nausea or vomiting or outcome$ or complication$ or cognitive dysfunction$ or delirium or awakening or emergence or urinary retention or opioid consumption or opiate consumption or pulmonary complication$)))
7.	#1 OR #2 OR #3 OR #4 OR #5 OR #6
8.	TI=((anesthesia or anaesthesia or analgesia or narcosis)) OR AB=((anesthesia or anaesthesia or analgesia or narcosis))
9.	TS=((((multimodal$ or multi-modal$ or unimodal$ or uni-modal$ or conventional) NEAR/1 (an$esthe* or analge* or approach or strategy or strategies or protocol$ or regimen$)) or MITA or ((combination or combined) NEAR/1 (infusion* or injection*))))
10.	TI=(((anesthetic$ or anaesthetic$ or analgesic$ or analgetic$) NEAR/2 (versus or comparison or compared or comparing or combined or combination or perioperative* or peri-operative* or intraoperative* or intra-operative*))) OR AB=(((anesthetic$ or anaesthetic$ or analgesic$ or analgetic$) NEAR/2 (versus or comparison or compared or comparing or combined or combination or perioperative* or peri-operative* or intraoperative* or intra-operative*)))
11.	TS=((narcotic-free or narcoticfree or narcotic-sparing or narcoticsparing or non-opioid or nonopioid or non-opiate or nonopiate or opioid-free or opioidfree or OFA or opiate-based or opiatebased or opioid-based or opioidbased or OBA or opioid-less or opioidless or opiate-less or opiateless or opioid-reduced or opiate-reduced or opiate-free or opiatefree or opioid-sparing or opioidsparing or opiate-sparing or opiatesparing or opioid management or opiate management))
12.	TI=(((opiate or opioid) NEAR/1 (reduc* or minimi* or decreas* or regimen or strateg*))) OR AB=(((opiate or opioid) NEAR/1 (reduc* or minimi* or decreas* or regimen or strateg*)))
13.	TS=(((opioid-free or opiate-free or opioid-sparing or opiate-sparing or opioid-reduced or opiate-reduced) AND (opioid-based or opiate-based or opioid-related or opiate-related or opioid-inclusive or opiate-inclusive or opioid-containing or opiate-containing)))
14.	#9 OR #10 OR #11 OR #12 OR #13
15.	#7 AND #8 AND #14""",
            """AND[OR[OR[OR[OR[itch*, prurit*], OR[ileus*, obstipat*, constipat*]], OR[OR[itch*, prurit*], OR[ileus*, obstipat*, constipat*]]], OR[OR[NEAR(2)[morphine, equ*], MME], OR[NEAR(2)[morphine, equ*], MME]], OR[OR[arrhythmia$, arrythmia$, disrhythmia$, dysrhythmia$, arrhytmia$, ectopic heart rhythm, ectopic rhythm, heart aberrant conduction, heart ectopic beat$, heart ectopic ventricle contraction, heart rhythm disease, heart rhythm disorder, heart rhythm problem$, atrial fibrillation, atrial flutter, atrioventricular block, bradycardia, bundle-branch block, cardiac sinus arrest, cardiopulmonary arrest, heart block, heart fibrillation, heart muscle conduction disturbance, interatrial block, long qt syndrome, sick sinus syndrome, sinoatrial block, tachycardia, ventricular fibrillation, ventricular flutter], OR[arrhythmia$, arrythmia$, disrhythmia$, dysrhythmia$, arrhytmia$, ectopic heart rhythm, ectopic rhythm, heart aberrant conduction, heart ectopic beat$, heart ectopic ventricle contraction, heart rhythm disease, heart rhythm disorder, heart rhythm problem$, atrial fibrillation, atrial flutter, atrioventricular block, bradycardia, bundle-branch block, cardiac sinus arrest, cardiopulmonary arrest, heart block, heart fibrillation, heart muscle conduction disturbance, interatrial block, long qt syndrome, sick sinus syndrome, sinoatrial block, tachycardia, ventricular fibrillation, ventricular flutter]], OR[NEAR(2)[length, stay], NEAR(2)[length, stay]], OR[OR[enhanced recovery after surgery, accelerated recovery, reduced side effect$, ERAS, PONV, POCD, patient reported outcome$, PROM$, patient-reported treatment outcome, patientreported outcome, self-reported outcome, self-reported patient outcome, self-reported treatment outcome, selfreported outcome, patient-reported outcome, quality of recovery, QoR, QoR15, QoR40, QoR-15, QoR-40, pain measurement$, pain assessment$, pain score$, pain scale$, pain intensit*, pain severity, numeric rating scale, NRS, visual analogue scale, VAS, Richmond Agitation-Sedation Scale, RASS], OR[enhanced recovery after surgery, accelerated recovery, reduced side effect$, ERAS, PONV, POCD, patient reported outcome$, PROM$, patient-reported treatment outcome, patientreported outcome, self-reported outcome, self-reported patient outcome, self-reported treatment outcome, selfreported outcome, patient-reported outcome, quality of recovery, QoR, QoR15, QoR40, QoR-15, QoR-40, pain measurement$, pain assessment$, pain score$, pain scale$, pain intensit*, pain severity, numeric rating scale, NRS, visual analogue scale, VAS, Richmond Agitation-Sedation Scale, RASS]], OR[AND[OR[post-operative, post-operation, post-surgery, post-surgical, postoperation, postoperative, postsurgery, postsurgical, post-procedural, postprocedural, following surgery, after surgery, postop, post-op, post-anesthesia, post-anaesthesia, postanesthesia, postanaesthesia, postanesthetic, postanaesthetic, post-anesthetic, post-anaesthetic, surgery-associated, surgery-derived, surgery-induced, surgery-related], OR[pain, nausea, vomiting, outcome$, complication$, cognitive dysfunction$, delirium, awakening, emergence, urinary retention, opioid consumption, opiate consumption, pulmonary complication$]], AND[OR[post-operative, post-operation, post-surgery, post-surgical, postoperation, postoperative, postsurgery, postsurgical, post-procedural, postprocedural, following surgery, after surgery, postop, post-op, post-anesthesia, post-anaesthesia, postanesthesia, postanaesthesia, postanesthetic, postanaesthetic, post-anesthetic, post-anaesthetic, surgery-associated, surgery-derived, surgery-induced, surgery-related], OR[pain, nausea, vomiting, outcome$, complication$, cognitive dysfunction$, delirium, awakening, emergence, urinary retention, opioid consumption, opiate consumption, pulmonary complication$]]]], OR[OR[anesthesia, anaesthesia, analgesia, narcosis], OR[anesthesia, anaesthesia, analgesia, narcosis]], OR[OR[NEAR(1)[OR[multimodal$, multi-modal$, unimodal$, uni-modal$, conventional], OR[an$esthe*, analge*, approach, strategy, strategies, protocol$, regimen$]], MITA, NEAR(1)[OR[combination, combined], OR[infusion*, injection*]]], OR[NEAR(2)[OR[anesthetic$, anaesthetic$, analgesic$, analgetic$], OR[versus, comparison, compared, comparing, combined, combination, perioperative*, peri-operative*, intraoperative*, intra-operative*]], NEAR(2)[OR[anesthetic$, anaesthetic$, analgesic$, analgetic$], OR[versus, comparison, compared, comparing, combined, combination, perioperative*, peri-operative*, intraoperative*, intra-operative*]]], OR[narcotic-free, narcoticfree, narcotic-sparing, narcoticsparing, non-opioid, nonopioid, non-opiate, nonopiate, opioid-free, opioidfree, OFA, opiate-based, opiatebased, opioid-based, opioidbased, OBA, opioid-less, opioidless, opiate-less, opiateless, opioid-reduced, opiate-reduced, opiate-free, opiatefree, opioid-sparing, opioidsparing, opiate-sparing, opiatesparing, opioid management, opiate management], OR[NEAR(1)[OR[opiate, opioid], OR[reduc*, minimi*, decreas*, regimen, strateg*]], NEAR(1)[OR[opiate, opioid], OR[reduc*, minimi*, decreas*, regimen, strateg*]]], AND[OR[opioid-free, opiate-free, opioid-sparing, opiate-sparing, opioid-reduced, opiate-reduced], OR[opioid-based, opiate-based, opioid-related, opiate-related, opioid-inclusive, opiate-inclusive, opioid-containing, opiate-containing]]]]""",
        )
    ],
)
def test_wos_list_query_parser(source: str, query_string: str, expected: str) -> None:
    """Test the translation of a search query to a WOS (list-format) query"""

    print("--------------------")
    # print(source)
    # print()
    print(query_string)
    print()
    parser = WOSListParser(query_string)
    parser.parse_list()
    print()
    print(parser.get_token_types(parser.tokens))
    query = parser.parse()
    query_str = query.to_string()
    print(query_str)
    print(query.to_string("structured"))

    assert query_str == expected
