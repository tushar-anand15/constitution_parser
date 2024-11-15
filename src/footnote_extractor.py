import re
from bs4 import BeautifulSoup

class FootnoteExtractor:
    def __init__(self, combined_soup, extracted_data):
        self.combined_soup = combined_soup
        self.extracted_data = extracted_data
        self.global_footnote_counter = 0  # Global counter for unique footnote IDs

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

        # Create a map of footnote numbers to their text
        for footnote in extracted_footnotes:
            match = footnote_number_pattern.match(footnote)
            if match:
                footnote_number = match.group(1)
                if footnote_number not in footnote_map:
                    footnote_map[footnote_number] = []
                footnote_map[footnote_number].append(footnote)

        sup_tags = originating_tag.find_all('sup')
        mapped_footnotes = {}

        for sup_tag in sup_tags:
            footnote_number = sup_tag.get_text(strip=True)
            if footnote_number in footnote_map and footnote_map[footnote_number]:
                # Increment the global counter for a unique footnote ID
                self.global_footnote_counter += 1
                unique_key = f"fn_{self.global_footnote_counter}"

                # Map the first available footnote text to the superscript
                footnote_text = footnote_map[footnote_number].pop(0)
                mapped_footnotes[unique_key] = {
                    'mapped_p_tag': sup_tag,
                    'mapped_footnote_text': footnote_text
                }

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

def main(combined_soup, extracted_data):
    footnote_extractor = FootnoteExtractor(combined_soup, extracted_data)
    for data in extracted_data:
        p_tags = extract_p_tags_from_html(data['extracted_html'])
        footnotes = footnote_extractor.extract_footnotes_from_p_tags(p_tags)
        # Update the original dictionary with the footnotes
        data['footnotes'] = footnotes
    return extracted_data

if __name__ == "__main__":
    # This is a placeholder for testing purposes
    # You would typically pass the combined_soup and extracted_data from the main script
    pass