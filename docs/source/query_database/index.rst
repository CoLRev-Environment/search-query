Query database
===========================

.. datatemplate:json:: query_overview.json

    {{ make_list_table_from_mappings(
        [("Identifier", "identifier"),
         ("Platform", "platform"),
         ("Title", "title"),
         ("Keywords", "keywords")],
        data,
        title='Available predefined queries',
        columns=[20, 6, 20, 20]
    ) }}

.. raw:: html

    <script>
    $(document).ready(function() {
        var tables = $('table');
        tables.addClass('sortable');
        tables.DataTable({
            "pageLength": 50,
            "order": []
        });
    });
    </script>


.. toctree::
   :hidden:
   :maxdepth: 1
   :glob:

   queries/*
