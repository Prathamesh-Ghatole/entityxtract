This parser is designed to extract structured data from PDFs using LLMs.

Basic worflow will be as follows:
1. Pass a PDF to extractor
2. Pass a configuration object to the extractor
    - This configuration object can be declared very easily using a JSON schema that contains a list of tables to be extracted
    - It would include the following
      - Table name
      - Example [columns, types, a few rows of data]
      - Additional instructions [page numbers, hand written instructions]
      - Enrichment instructions [additional columns to be created, data transformations]