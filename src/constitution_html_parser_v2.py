import re
from collections import defaultdict
from bs4 import BeautifulSoup
from difflib import SequenceMatcher
import unicodedata
import string
import pandas as pd

class ContentsPageParser:
    def __init__(self, filepath):
        self.filepath = filepath
        self.soup = self.read_html_constitution()

    def read_html_constitution(self):
        """
        Reads in the input file
        """
        soup = BeautifulSoup(open(self.filepath).read(), 'lxml')
        return soup

    def extract_contents_page(self):
        # Find the <h4> tag with the text "CONTENTS"
        start_tag = self.soup.find('h4', text='CONTENTS')

        # Define the end tag as the <p> tag with the text "SCHEDULES" and alignment "center"
        end_tag = self.soup.find('p', text='SCHEDULES', align='center')

        # Initialize a list to store the extracted text
        extracted_texts = []

        # Traverse the document starting from the start_tag
        current_tag = start_tag.find_next_sibling()

        while current_tag and current_tag != end_tag:
            if current_tag.name == 'p':
                extracted_texts.append(current_tag.get_text(strip=True))
            current_tag = current_tag.find_next_sibling()

        # Find the <div> with class "WordSection2" and extract <p> tags and table contents
        word_section_div = self.soup.find('div', class_='WordSection2')
        if word_section_div:
            current_tag = word_section_div.find('p')
            while current_tag and current_tag != end_tag:
                if current_tag.name == 'p':
                    extracted_texts.append(current_tag.get_text(strip=True))
                elif current_tag.name == 'table':
                    for row in current_tag.find_all('tr'):
                        row_text = [cell.get_text(strip=True) for cell in row.find_all('td')]
                        extracted_texts.append(' | '.join(row_text))
                current_tag = current_tag.find_next_sibling()

        return extracted_texts

    def organize_p_tags_contents_page(self, p_tags):
        """
        Expects a list of p tags extracted from the contents page, returns the sections, parts, and articles in order.
        """
        # Regular expression patterns
        part_pattern = re.compile(r'^PART\s+[A-Z]+\b')
        chapter_pattern = re.compile(r'^CHAPTER\b')
        article_pattern = re.compile(r'\b\d+[A-Z]*\.')

        # Initialize the structure
        organized_structure = defaultdict(lambda: defaultdict(list))
        current_part = None
        current_chapter = None

        for tag in p_tags:
            # Check if the tag is a part
            if part_pattern.match(tag):
                current_part = tag.strip()
                current_chapter = None  # Reset chapter when a new part starts

            # Check if the tag is a chapter
            elif chapter_pattern.match(tag):
                if current_part:  # Ensure a part is set before setting a chapter
                    current_chapter = tag.strip()

            # Check if the tag is an article
            elif article_pattern.search(tag):
                if current_part:
                    # Split the tag into multiple articles if necessary
                    articles = re.split(r'(?=\b\d+[A-Z]*\.)', tag.strip())
                    for article in articles:
                        if current_chapter:
                            organized_structure[current_part][current_chapter].append(article.strip())
                        else:
                            # If there's no chapter, add articles directly under the part
                            organized_structure[current_part]['No Chapter'].append(article.strip())

        return organized_structure

class ArticleExtractor:
    def __init__(self, soup):
        self.soup = soup

    def preprocess_text(self, text):
        """
        Preprocesses text by removing punctuation, normalizing, and replacing newlines with spaces.
        """
        # Replace newlines and multiple spaces with a single space
        text = re.sub(r'\s+', ' ', text)
        # Remove punctuation
        text = text.translate(str.maketrans('', '', string.punctuation))
        # Remove annotations and superscripts
        text = re.sub(r'\[\d+\]', '', text)  # Remove patterns like [3]
        return text.lower().strip()
    
    def check_article_in_tag(self, p_tag):
        """
        Checks if a <p> tag contains an article and returns the extracted text, original text, and the tag itself.
        """
        # Regular expression pattern for articles
        article_pattern = re.compile(r'(\d+\[?\d*[A-Z]*\.)')  # Matches "1.", "22A.", "22ZA.", "3[23A.", etc.

        # Extract text, ignoring any initial superscript
        text = ''.join(
            element.get_text(strip=True) for element in p_tag.contents
            if not (element.name == 'sup' and element == p_tag.contents[0])
        ).strip()

        # Check if the <p> tag contains any <span> with font-size:7.5pt or 8.0pt
        has_small_font = any('font-size:7.5pt' in span.get('style', '') or 'font-size:8.0pt' in span.get('style', '') for span in p_tag.find_all('span'))

        # Exclude the <p> tag if it contains any <span> with font-size:7.5pt or 8.0pt
        if has_small_font:
            return None

        # Check if the article pattern is found within the first 30 characters
        if article_pattern.search(text[:30]):
            # Preprocess the text to remove unwanted characters and normalize it
            cleaned_text = self.preprocess_text(text)
            
            # Additional cleaning to handle specific cases
            cleaned_text = re.sub(r'\[|\]', '', cleaned_text)  # Remove square brackets
            cleaned_text = re.sub(r'—', '-', cleaned_text)  # Normalize em dashes to hyphens

            return {'extracted_text_from_p_tag': cleaned_text, 'actual_p_tag': p_tag, 'original_text': text}

        return None
    
    def extract_articles_with_tags(self):
        """
        Loops through all <p> tags in the soup and returns a list of articles.
        """
        extracted_articles = []

        # Find all <p> tags in the soup
        p_tags = self.soup.find_all('p')

        for p in p_tags:
            result = self.check_article_in_tag(p)
            if result:
                extracted_articles.append(result)

        return extracted_articles

    def find_best_mapping_with_tags(self, extracted_articles, organized_texts):
        best_mappings = []
        last_matched_index = -1

        for organized_text in organized_texts:
            # Preprocess the organized text
            preprocessed_organized_text = self.preprocess_text(organized_text)

            # Extract the section number from the organized text
            section_number = self.extract_section_number(preprocessed_organized_text)

            # Determine the search range based on the last matched index
            search_start = max(0, last_matched_index + 1)
            search_end = min(len(extracted_articles), search_start + 30)  # Expanded window size

            best_match = None
            best_ratio = 0
            best_index = -1

            for index in range(search_start, search_end):
                article = extracted_articles[index]
                preprocessed_extracted_text = article['extracted_text_from_p_tag']

                # Extract the section number from the extracted text
                extracted_section_number = self.extract_section_number(preprocessed_extracted_text)

                # Check for section number similarity
                if section_number and extracted_section_number:
                    section_similarity = SequenceMatcher(None, section_number, extracted_section_number).ratio()
                    if section_similarity > 0.8:  # Threshold for section number similarity
                        # Calculate similarity ratio for the rest of the text
                        min_length = min(len(preprocessed_organized_text), len(preprocessed_extracted_text))
                        text_similarity = SequenceMatcher(None, preprocessed_organized_text[:min_length], preprocessed_extracted_text[:min_length]).ratio()
                        
                        if text_similarity > best_ratio:
                            best_ratio = text_similarity
                            best_match = article
                            best_index = index

            if best_match:
                last_matched_index = best_index
                best_mappings.append({
                    'organized_texts_contents_page': organized_text,
                    'extracted_text_from_p_tag': best_match['extracted_text_from_p_tag'],
                    'actual_p_tag': best_match['actual_p_tag'],
                    'original_text': best_match['original_text'],
                    'similarity_ratio': best_ratio
                })

        return best_mappings

    def extract_section_number(self, text):
        """
        Extracts the section number from the text.
        """
        match = re.match(r'(\d+[A-Z]*)', text)
        return match.group(0) if match else None

    def extract_text_for_mapping(self, start_tag, end_tag):
        """
        Extracts text and HTML content between the start and end tags.
        """
        text_content = []
        html_content = []
        # Include the start_tag's text and HTML content
        if start_tag.name in ['p',] :
            text_content.append(start_tag.get_text(strip=True))
            html_content.append(str(start_tag))

        # Start from the next sibling of the start_tag
        current_tag = start_tag.find_next_sibling()

        while current_tag and current_tag != end_tag:
            if current_tag.name in ['p']:
                text_content.append(current_tag.get_text(strip=True))
                html_content.append(str(current_tag))
            current_tag = current_tag.find_next_sibling()

        return ' '.join(text_content), ''.join(html_content)

    def extract_text_between_markers(self, soup, mappings):
        """
        Loops through mappings and extracts text and HTML content between markers.
        """
        extracted_data = []

        for i, mapping in enumerate(mappings):
            start_tag = mapping['actual_p_tag']
            # Determine the end_tag as the next mapping's actual_p_tag, or None if it's the last mapping
            end_tag = mappings[i + 1]['actual_p_tag'] if i + 1 < len(mappings) else None

            extracted_text, extracted_html = self.extract_text_for_mapping(start_tag, end_tag)

            extracted_data.append({
                'organized_texts_contents_page': mapping['organized_texts_contents_page'],
                'extracted_text': extracted_text,
                'extracted_html': extracted_html
            })

        return extracted_data
    def extract_footnote_from_tag(self, p_tag, combined_soup):
        """
        Extracts footnotes from a given <p> tag if they exist.
        """
        # Find all <sup> tags within the <p> tag
        sup_tags = p_tag.find_all('sup')
        footnotes = []

        for sup_tag in sup_tags:
            footnote_number = sup_tag.get_text(strip=True)
            if not footnote_number.isdigit():
                continue  # Skip if the footnote number is not a digit

            # Find the corresponding footnote in the combined_soup
            footnote_tag, footnote_text = self.find_footnote_by_number(footnote_number, combined_soup)
            if footnote_tag and footnote_text:
                footnotes.append({'footnote_tag': footnote_tag, 'footnote_text': footnote_text})

        return footnotes

    def find_footnote_by_number(self, footnote_number, combined_soup):
        """
        Finds the footnote in the combined_soup by matching the footnote number.
        """
        # Regular expression to match the footnote number
        footnote_pattern = re.compile(rf'^{footnote_number}\.')

        # Find the first marker in the combined_soup
        marker_pattern = re.compile(r'^_+$')
        marker_tag = None
        for h2 in combined_soup.find_all('h2'):
            if marker_pattern.match(h2.get_text(strip=True)):
                marker_tag = h2
                break

        if not marker_tag:
            return None, None

        # Start searching for footnotes after the marker
        current_tag = marker_tag.find_next_sibling()
        while current_tag:
            if current_tag.name == 'p':
                # Check for <span> tags with font-size:8.0pt
                spans = current_tag.find_all('span', style=lambda value: value and 'font-size:8.0pt' in value)
                for span in spans:
                    # Check if the footnote number matches
                    if footnote_pattern.match(span.get_text(strip=True)):
                        footnote_text = current_tag.get_text(strip=True)
                        return current_tag, footnote_text
            current_tag = current_tag.find_next_sibling()

        return None, None

    def extract_footnotes(self, extracted_html, combined_soup):
        """
        Loops through each <p> tag in the extracted_html and extracts footnotes.
        """
        soup = BeautifulSoup(extracted_html, 'html.parser')
        footnotes = []

        for p_tag in soup.find_all('p'):
            footnotes.extend(self.extract_footnote_from_tag(p_tag, combined_soup))

        return footnotes
 
    def find_tag_by_attrs_and_text(self, soup, tag, attrs, text):
        for element in soup.find_all(tag, attrs=attrs):
            if element.get_text(strip=True) == text:
                return element
        return None


class MarkupHTML:
    def __init__(self, combined_soup, extracted_data, output_filename):
        self.combined_soup = combined_soup
        self.extracted_data = extracted_data
        self.output_filename = output_filename
        self.color_dict = {
            'article_name': 'rgba(0, 255, 255, 0.8)',  # Cyan with 80% transparency
            'article_text': 'rgba(0, 255, 255, 0.8)',  # Cyan with 80% transparency
            'footnote': 'rgba(0, 128, 0, 0.8)'         # Green with 80% transparency
        }

    def find_tag_by_attrs_and_text(self, soup, tag, attrs, text):
        for element in soup.find_all(tag, attrs=attrs):
            if element.get_text(strip=True) == text:
                return element
        return None

    def highlight_articles(self):
        """
        Highlights the actual_p_tags in best_mappings with the specified color.
        """
        for data in self.extracted_data:
            article_name = data.get('organized_texts_contents_page', '')
            found_tag = self.find_tag_by_attrs_and_text(self.combined_soup, 'p', {}, article_name)
            if found_tag:
                self.apply_style(found_tag, 'article_name')

    def highlight_article_text(self):
        """
        Highlights the article text in the specified color.
        """
        for data in self.extracted_data:
            soup = BeautifulSoup(data['extracted_html'], 'html.parser')
            for p_tag in soup.find_all('p'):
                found_tag = self.find_tag_by_attrs_and_text(self.combined_soup, 'p', p_tag.attrs, p_tag.get_text(strip=True))
                if found_tag:
                    self.apply_style(found_tag, 'article_text')

    def highlight_footnotes(self):
        """
        Highlights footnotes in the specified color.
        """
        for data in self.extracted_data:
            footnotes = data.get('footnotes', {})
            for sup_tag, footnote_text in footnotes.items():
                found_tag = self.find_tag_by_attrs_and_text(self.combined_soup, 'p', {}, footnote_text)
                if found_tag:
                    self.apply_style(found_tag, 'footnote')

    def apply_style(self, tag, style_key):
        """
        Applies the specified style to the tag.
        """
        if 'style' in tag.attrs:
            if not tag['style'].strip().endswith(';'):
                tag['style'] += ';'
            tag['style'] += f' background-color: {self.color_dict[style_key]};'
        else:
            tag['style'] = f'background-color: {self.color_dict[style_key]};'

    def save_markup(self):
        """
        Saves the modified HTML to a file.
        """
        with open(self.output_filename, 'w', encoding='utf-8') as file:
            file.write(self.combined_soup.prettify())

    def apply_markup(self):
        """
        Applies markup to the HTML and saves it to a file.
        """
        self.highlight_articles()
        self.highlight_article_text()
        self.highlight_footnotes()
        self.save_markup()



class FootnoteExtractor:
    def __init__(self, combined_soup, extracted_data):
        self.combined_soup = combined_soup
        self.extracted_data = extracted_data

    def find_tag_by_attrs_and_text(self, tag, attrs, text):
        for element in self.combined_soup.find_all(tag, attrs=attrs):
            if element.get_text(strip=True) == text:
                print(f"Found the tag: {element}")
                return element
        return None

    def find_next_footnotes(self, originating_tag):
        found_tag = self.find_tag_by_attrs_and_text(originating_tag.name, originating_tag.attrs, originating_tag.get_text(strip=True))
        
        if not found_tag:
            return None

        marker_pattern = re.compile(r'^_+$')
        start_iterating = False
        for tag in self.combined_soup.find_all(True):
            if tag == found_tag:
                start_iterating = True
                print("Starting to iterate from the found element in combined_soup.")
                continue

            if start_iterating:
                if tag.name == 'h2' and marker_pattern.match(tag.get_text(strip=True)):
                    print("Footnote marker pattern found.")
                    current_tag = tag.find_next_sibling()
                    footnotes = []

                    while current_tag:
                        if current_tag.name == 'h2' and marker_pattern.match(current_tag.get_text(strip=True)):
                            print("Another footnote marker found. Stopping search.")
                            break

                        if current_tag.name == 'p':
                            spans = current_tag.find_all('span')
                            for span in spans:
                                style = span.get('style', '')
                                if 'font-size:8.0pt' in style:
                                    footnote_text = current_tag.get_text(strip=True)
                                    footnotes.append(footnote_text)
                                    print(f"Footnote text: {footnote_text}")
                                    break
                        current_tag = current_tag.find_next_sibling()

                    return footnotes

        return None

    def map_sup_to_footnotes(self, originating_tag, extracted_footnotes):
        footnote_number_pattern = re.compile(r'^(\d+)\.')
        footnote_map = {}
        for footnote in extracted_footnotes:
            match = footnote_number_pattern.match(footnote)
            if match:
                footnote_number = match.group(1)
                footnote_map[footnote_number] = footnote

        sup_tags = originating_tag.find_all('sup')
        mapped_footnotes = {}
        for sup_tag in sup_tags:
            footnote_number = sup_tag.get_text(strip=True)
            if footnote_number in footnote_map:
                mapped_footnotes[sup_tag] = footnote_map[footnote_number]

        return mapped_footnotes

    def extract_footnotes_from_p_tags(self, p_tags):
        footnotes = {}
        for p_tag in p_tags:
            extracted_footnotes = self.find_next_footnotes(p_tag)
            if extracted_footnotes:
                mapped_footnotes = self.map_sup_to_footnotes(p_tag, extracted_footnotes)
                if mapped_footnotes:
                    footnotes.update(mapped_footnotes)
        return footnotes

def extract_p_tags_from_html(extracted_html):
    return BeautifulSoup(extracted_html, 'lxml').find_all('p')


def preprocess_text(text):
    """
    Preprocesses text by removing special characters and normalizing whitespace.
    """
    # Remove special characters and normalize whitespace
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces/newlines with a single space
    text = re.sub(r'[^\w\s]', '', text)  # Remove all non-word characters
    return text.strip().lower()

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

    # Save the modified HTML to a file
    with open('test.html', 'w', encoding='utf-8') as file:
        file.write(combined_soup.prettify())
    
    return combined_soup


def test_mappings(best_mappings):
    df = pd.DataFrame(best_mappings)
    df.to_csv('test_acts.csv')
    return df

def verify_tags_in_soup(soup, mappings):
    """
    Verifies that all actual_p_tags exist in the soup object.
    """
    def find_tag_by_attrs_and_text(soup, tag, attrs, text):
        for element in soup.find_all(tag, attrs=attrs):
            if element.get_text(strip=True) == text:
                return element
        return None

    found_tags_count, not_found_tags_count = 0, 0

    for i, mapping in enumerate(mappings):
        actual_p_tag = mapping['actual_p_tag']
        # Find the tag in the soup using both attributes and text
        found_tag = find_tag_by_attrs_and_text(soup, 'p', actual_p_tag.attrs, actual_p_tag.get_text(strip=True))
        
        if found_tag:
            found_tags_count += 1
        else:
            not_found_tags_count += 1
    print(f'Found {found_tags_count}; not found {not_found_tags_count}, total = {len(mappings)}')


def main():
    contents_parser = ContentsPageParser('../data/constitutionIndia_convertedHTML.html')
    contents_page_p_tags = contents_parser.extract_contents_page()
    extracted_article_structure_contents_page = contents_parser.organize_p_tags_contents_page(contents_page_p_tags)
    
    organized_texts = []
    for parts in extracted_article_structure_contents_page.values():
        for chapters in parts.values():
            organized_texts.extend(chapters)

    organized_texts = [text for text in organized_texts if text.strip() and re.search(r'\d', text)]

    with open('../data/constitutionIndia_convertedHTML.html', 'r') as file:
        html_content = file.read()

    combined_soup = extract_paragraphs_as_soup(BeautifulSoup(html_content, 'lxml'))
    article_extractor = ArticleExtractor(combined_soup)
    extracted_articles = article_extractor.extract_articles_with_tags()
    best_mappings = article_extractor.find_best_mapping_with_tags(extracted_articles, organized_texts)
    verify_tags_in_soup(combined_soup, best_mappings)
    extracted_data = article_extractor.extract_text_between_markers(combined_soup, best_mappings)
    
    footnote_extractor = FootnoteExtractor(combined_soup, extracted_data)
    
    for data in extracted_data:
        p_tags = extract_p_tags_from_html(data['extracted_html'])
        footnotes = footnote_extractor.extract_footnotes_from_p_tags(p_tags)
        # Update the original dictionary with the footnotes
        data['footnotes'] = footnotes
    
    for data in extracted_data:
        print(f"Organized Text: {data['organized_texts_contents_page']}\n"
              f"Extracted Text: {data['extracted_text']}\n"
              f"Extracted HTML: {data['extracted_html']}\n"
              f"Footnotes: {data['footnotes']}\n")
    
    markup = MarkupHTML(combined_soup, extracted_data, output_filename='test_acts_markup.html')
    markup.apply_markup()
    # create_custom_markup(extracted_data=extracted_data)

if __name__ == "__main__":
    main()


