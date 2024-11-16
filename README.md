# Constitution of India Data Extraction

This project is designed to extract and process data from the Constitution of India, specifically focusing on extracting articles and their associated footnotes from the HTML content. 

## Project Structure

### Data Files

- **constitutionIndia_convertedHTML.html**: This file contains the converted HTML from the PDF available at [Constitution of India](https://legislative.gov.in/constitution-of-india/). 

- **extracted_articles_data.json**: This JSON file contains the extracted data for each article, including the footnotes associated with each article. 

- **test_acts_markup.html**: A custom markup file created for manual verification purposes. 

### Source Code (src directory)


- **article_extractor.py**: Handles the extraction of article names and content from the HTML.

- **contents_page_parser.py**: Extracts the contents page from the HTML, which is used to identify the structure and order of articles.

- **footnote_extractor.py**: Extracts footnotes associated with each article, ensuring that they are correctly mapped to their respective articles.

- **markup_html.py**: Contains logic for creating the HTML markup.

- **constitution_html_parser_v2.py**: This is the first iteration of the logic, which has been refactored into other files. 

- **main.py**: The main script. 
