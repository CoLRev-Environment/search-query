Filter: AIS Senior Scholars List of Premier Journals
====================================================

**Identifier**: ``ais_senior_scholars_list_of_premier_journals``

**Platform**: ``wos``

**Keywords**: ``AIS, journals, information systems``

**Authors**: ``Gerit Wagner``

**License**: ``Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License.``

**License**: Search filter for the AIS Senior Scholars List of Premier Journals (eleven), see https://aisnet.org/page/SeniorScholarListofPremierJournals

Load
-----------

.. code-block:: python

    from search_query.database import load_query

    query = load_query("ais_senior_scholars_list_of_premier_journals.json")

    print(query.to_string())
    # SO=("European Journal of Information Systems" OR "Information Systems Journal" O...


Search String
-------------

.. raw:: html

    <pre style="white-space: pre-wrap; word-break: break-word;">
    SO=("European Journal of Information Systems" OR "Information Systems Journal" OR "Information Systems Research" OR "Journal of the Association for Information Systems" OR "Journal of Information Technology" OR "Journal of Management Information Systems" OR "Journal of Strategic Information Systems" OR "MIS Quarterly" OR "Decision Support Systems" OR "Information & Management" OR "Information and Organization") OR IS=(0960-085X OR 1476-9344 OR 1350-1917 OR 1365-2575 OR 1047-7047 OR 1526-5536 OR 1536-9323 OR 0268-3962 OR 1466-4437 OR 0742-1222 OR 1557-928X OR 0963-8687 OR 1873-1198 OR 0276-7783 OR 2162-9730 OR 0167-9236 OR 1873-5797 OR 0378-7206 OR 1872-7530 OR 1471-7727 OR 1873-7919)
    </pre>


Suggest to `improve this query <https://github.com/CoLRev-Environment/search-query/blob/main/search_query/json_db/ais_senior_scholars_list_of_premier_journals.json>`_.
