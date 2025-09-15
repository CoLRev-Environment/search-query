Block: Treatment as usual
=========================

**Identifier**: ``blocks_bmi_343``

**Platform**: ``PubMed``

**Keywords**: ``EBSCO/CINAHL; EBSCO/PsycInfo (PI); EMbase.com (EM); PubMed (PM); Study types; Therapy``

**Authors**: ``Ket JCF``

**License**: ``Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License.``

**License**: original drafts by Sarah Dawson, Cochrane CCDAN group, 21 Jun 2016. TAU-filters may retrieve other comparative studies than RCTs, the comparison here being 'treatment as usual', in stead of placebo or gold standard therapy. See also 'no treatment'. For CINAHL the 'Treatment as usual'-filter is integrated in the RCT-filter.

Load
-----------

.. code-block:: python

    from search_query.database import load_query

    query = load_query("blocks_bmi_343.json")

    print(query.to_string())
    # (treatment*[tiab] AND usual[tiab]) OR (standard[tiab] AND care[tiab]) OR (standa...


Search String
-------------

.. raw:: html

    <pre style="white-space: pre-wrap; word-break: break-word;">
    (treatment*[tiab] AND usual[tiab]) OR (standard[tiab] AND care[tiab]) OR (standard[tiab] AND treatment[tiab]) OR (routine[tiab] AND care[tiab]) OR (usual[tiab] AND medication*[tiab]) OR (usual[tiab] AND care[tiab]) OR tau[tiab] OR waitlist*[tiab] OR wait list*[tiab] OR waiting list*[tiab] OR (waiting[tiab] AND (condition[tiab] OR control[tiab])) OR wlc[tiab] OR (delay*[tiab] AND (start[tiab] OR treatment*[tiab])) OR "no intervention"[tiab] OR non treatment*[tiab] OR nontreatment*[tiab] OR (minim*[tiab] AND treatment*[tiab]) OR untreated group*[tiab] OR untreated control*[tiab] OR "without any treatment"[tiab] OR (untreated[tiab] AND (patients[tiab] OR participants[tiab] OR subjects[tiab] OR group*[tiab] OR control*[tiab])) OR non intervention*[tiab] OR ("without any"[tiab] AND intervention*[tiab]) OR (receiv*[tiab] AND nothing[tiab]) OR "did not receive"[tiab] OR standard control[tiab] OR non therap*[tiab] OR nontherap*[tiab] OR nonpsychotherap*[tiab] OR (minim*[tiab] AND therap*[tiab]) OR pseudotherap*[tiab] OR pseudo therap*[tiab] OR (therap*[tiab] AND as usual[tiab]) OR usual therap*[tiab] OR reference group[tiab] OR observation group[tiab] OR (convention*[tiab] AND treatment[tiab]) OR conventional therap*[tiab] OR standard treatment*[tiab] OR (standard[tiab] AND therap*[tiab])
    </pre>


Suggest to `improve this query <https://github.com/CoLRev-Environment/search-query/blob/main/search_query/json_db/blocks_bmi_343.json>`_.
