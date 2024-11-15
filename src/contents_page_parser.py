import re
from collections import defaultdict
from bs4 import BeautifulSoup

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

def main():
    parser = ContentsPageParser('../data/constitutionIndia_convertedHTML.html')
    contents_page_p_tags = parser.extract_contents_page()
    organized_structure = parser.organize_p_tags_contents_page(contents_page_p_tags)
    return organized_structure

if __name__ == "__main__":
    main()