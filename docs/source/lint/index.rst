.. _lint:

Lint
====================

Search-query implements various syntax validation checks (aka. linters) and prints instructive messages about potential issues.
These checks help to prevent errors—an important step given that previous studies have found high error rates in search queries (Li & Rainer, 2023; Salvador-Oliván et al., 2019; Sampson & McGowan, 2006).

.. code-block:: python

    from search_query.parser import parse

    query_string = '("digital health"[Title/Abstract]) AND ("privacy"[Title/Abstract]'
    query = parse(query_string, platform="pubmed")

    # Output:
    # ❌ Fatal: unbalanced-parentheses (PARSE_0002)
    #   - Unbalanced opening parenthesis
    #   Query: ("digital health"[Title/Abstract]) AND ("privacy"[Title/Abstract]
    #                                                ^^^

.. include:: errors_index.rst

**References**

.. parsed-literal::

    Li, Z., & Rainer, A. (2023). Reproducible Searches in Systematic Reviews: An Evaluation and Guidelines.
      IEEE Access, 11, 84048–84060. IEEE Access. doi: `10.1109/ACCESS.2023.3299211 <https://doi.org/10.1109/ACCESS.2023.3299211>`_

    Salvador-Oliván, J. A., Marco-Cuenca, G., & Arquero-Avilés, R. (2019).
      Errors in search strategies used in systematic reviews and their effects on information retrieval.
      Journal of the Medical Library Association : JMLA, 107(2), 210. doi: `10.5195/jmla.2019.567 <https://doi.org/10.5195/jmla.2019.567>`_

    Sampson, M., & McGowan, J. (2006). Errors in search strategies were identified by type and frequency.
      Journal of Clinical Epidemiology, 59(10), 1057–1063. doi: `10.1016/j.jclinepi.2006.01.007 <https://doi.org/10.1016/j.jclinepi.2006.01.007>`_
