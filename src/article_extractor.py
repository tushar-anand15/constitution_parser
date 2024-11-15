import re
from bs4 import BeautifulSoup
from difflib import SequenceMatcher
import string

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
       
        def is_all_uppercase(text):
        # Remove whitespace and check if remaining text is uppercase
            letters_only = ''.join(filter(str.isalpha, text))
            return letters_only.isupper()            
    # Include the start_tag's text and HTML content if not all uppercase
        if start_tag.name == 'p' and not is_all_uppercase(start_tag.get_text(strip=True)):
            text_content.append(start_tag.get_text(strip=True))
            html_content.append(str(start_tag))
        # Start from the next sibling of the start_tag
        current_tag = start_tag.find_next_sibling()

        while current_tag and current_tag != end_tag:
            if current_tag.name == 'p' and not is_all_uppercase(current_tag.get_text(strip=True)):

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

def main(soup, organized_texts):
    article_extractor = ArticleExtractor(soup)
    extracted_articles = article_extractor.extract_articles_with_tags()
    best_mappings = article_extractor.find_best_mapping_with_tags(extracted_articles, organized_texts)
    extracted_data = article_extractor.extract_text_between_markers(soup, best_mappings)
    return extracted_data

if __name__ == "__main__":
    # This is a placeholder for testing purposes
    # You would typically pass the soup and organized_texts from the main script
    main()