from bs4 import BeautifulSoup
from contents_page_parser import main as parse_contents
from article_extractor import main as extract_articles
from markup_html import main as generate_markup
from footnote_extractor import main as extract_footnotes
import re
from difflib import SequenceMatcher

def extract_paragraphs_as_soup(soup, start_section=3, end_section=46):
    """
    Gets a cleaner version of the HTML with only the desired text, including <p> and <h> tags.
    """
    # List to store extracted paragraphs and headers as strings
    extracted_elements = []

    # Iterate over each section from start_section to end_section
    for n in range(start_section, end_section + 1):
        section_class = f'WordSection{n}'
        section = soup.find('div', class_=section_class)
        
        if section:
            # Find all <p> and <h> tags within the section
            elements = section.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            for element in elements:
                # Append the element HTML to the list
                extracted_elements.append(str(element))
        print(f'processed {section_class}')

    # Join all element strings into one HTML string
    combined_html = ''.join(extracted_elements)

    # Parse the combined HTML string into a new BeautifulSoup object
    combined_soup = BeautifulSoup(combined_html, 'lxml')

    # Define the elements to look for
    first_element_text = '1. Ins. by the Constitution (Fifty-eighth Amendment) Act, 1987, s. 2 (w.e.f. 9-12-1987).'
    second_element_text = '2. Art 394A, Ins. by s. 3, ibid. (w.e.f. 9-12-1987). 252'

    # Truncate the combined_soup at the point where the specified pattern is found
    elements = combined_soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    for i, element in enumerate(elements):
        # Preprocess the element text
        element_text = preprocess_text(element.get_text())
        if SequenceMatcher(None, element_text, preprocess_text(first_element_text)).ratio() > 0.8:
            # Check for the second element immediately after the first
            next_element = elements[i + 1] if i + 1 < len(elements) else None
            if next_element:
                next_element_text = preprocess_text(next_element.get_text())
                if SequenceMatcher(None, next_element_text, preprocess_text(second_element_text)).ratio() > 0.8:
                    # Truncate the soup
                    combined_soup = BeautifulSoup(''.join(str(e) for e in elements[:i+2]), 'lxml')
                    print("Truncating combined_soup at specified pattern.")
                    break

    return combined_soup

def preprocess_text(text):
    """
    Preprocesses text by removing special characters and normalizing whitespace.
    """
    # Remove special characters and normalize whitespace
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces/newlines with a single space
    text = re.sub(r'[^\w\s]', '', text)  # Remove all non-word characters
    return text.strip().lower()

def main():
    # Parse contents
    organized_structure = parse_contents()
    organized_texts = []
    for parts in organized_structure.values():
        for chapters in parts.values():
            organized_texts.extend(chapters)

    organized_texts = [text for text in organized_texts if text.strip() and re.search(r'\d', text)]

    # Read HTML content
    with open('../data/constitutionIndia_convertedHTML.html', 'r') as file:
        html_content = file.read()

    # Extract paragraphs as soup
    combined_soup = extract_paragraphs_as_soup(BeautifulSoup(html_content, 'lxml'))

    # Extract articles
    extracted_data = extract_articles(combined_soup, organized_texts)

    # extract footnotes
    extracted_data = extract_footnotes(combined_soup, extracted_data)

    # Generate markup
    extracted_data = generate_markup(combined_soup, extracted_data, output_filename='../data/test_acts_markup.html')

if __name__ == "__main__":
    main()