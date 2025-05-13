Submit a Query
===========================

We welcome contributions of queries and predefined query filters to the `search-query` database.

To submit a query:

1. **Fork and clone** the repository:
   https://github.com/CoLRev-Environment/search-query

2. **Create a JSON file** describing your query with the standard structure (see below).

3. **Save your file** in the directory:
   `search_query/json_db/`

4. **Open a Pull Request** with a short description of your query and its purpose.

Once your PR is merged, your query will be **automatically included and rendered** in the documentation.

JSON Structure
---------------------------

Your `.json` file should follow this structure:

.. code-block:: json

   {
      "record_info": {},
      "authors": [{"name": "Gerit Wagner"}],
      "date": {"data_entry": "2025-05-12"},
      "platform": "wos",
      "type": "filter",
      "database": [],
      "search_string": "SO=(\"European Journal of Information Systems\" OR \"Information Systems Journal\" OR \"Information Systems Research\" OR \"Journal of the Association for Information Systems\" OR \"Journal of Information Technology\" OR \"Journal of Management Information Systems\" OR \"Journal of Strategic Information Systems\" OR \"MIS Quarterly\") OR IS=(0960-085X OR 1476-9344 OR 1350-1917 OR 1365-2575 OR 1047-7047 OR 1526-5536 OR 1536-9323 OR 0268-3962 OR 1466-4437 OR 0742-1222 OR 1557-928X OR 0963-8687 OR 1873-1198 OR 0276-7783 OR 2162-9730)",
      "title": "Search filter: AIS Senior Scholars Basket",
      "description": "Search filter for the AIS Senior Scholars Basket of Journals (eight)",
      "keywords": "AIS, journals, information systems",
      "license": "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License."
   }

Guidelines
---------------------------

- Use `platform` to specify the query syntax (e.g., `"wos"`, `"pubmed"`).
- The `search_string` should be a valid query string for that platform.
- Ensure that your `title`, `description`, and `keywords` are concise and accurate.
- Use an appropriate open license (e.g., Creative Commons).

Questions?
---------------------------

Feel free to open an issue if you are unsure about formatting, structure, or syntax:
https://github.com/CoLRev-Environment/search-query/issues
