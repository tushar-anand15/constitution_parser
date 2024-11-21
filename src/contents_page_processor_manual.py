import re
import pandas as pd

class ConstitutionContentsParser:
    def __init__(self, contents_text):
        self.contents_text = contents_text
        self.data = []
        self.df = None

    def parse(self):
        # Regular expressions to match parts, chapters, and articles
        part_pattern = re.compile(r'PART\s+[IVXLCDM]+\b')
        chapter_pattern = re.compile(r'CHAPTER\s+[IVXLCDM]+\.\s+[A-Z ]+')
        article_pattern = re.compile(r'(\[\d+[A-Z]*[-]?[A-Z]*\]|\d+[A-Z]*[-]?[A-Z]*\.)\s')

        current_part = None
        current_part_name = None
        current_chapter = None
        current_subchapter = None

        # Split the text into lines
        lines = self.contents_text.splitlines()

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for a new part
            part_match = part_pattern.match(line)
            if part_match:
                current_part = line
                current_part_name = None
                current_chapter = None
                current_subchapter = None
                continue

            # Check for part name (all caps)
            if current_part and line.isupper() and not chapter_pattern.match(line):
                current_part_name = line
                continue

            # Check for a new chapter
            chapter_match = chapter_pattern.match(line)
            if chapter_match:
                current_chapter = line
                current_subchapter = None
                continue

            # Check for an article
            article_match = article_pattern.match(line)
            if article_match or 'omitted' in line.lower():
                article_number = article_match.group(1).strip('[]') if article_match else ''
                article_title = line
                self.data.append({
                    'Part': current_part,
                    'Part Name': current_part_name,
                    'Chapter': current_chapter,
                    'Subchapter': current_subchapter,
                    'Article Number': article_number,
                    'Article Title': article_title
                })
                continue

            # Check for subchapter name (not all caps and not an article)
            if current_part and not line.isupper() and not article_pattern.match(line):
                current_subchapter = line
                continue

        self.df = pd.DataFrame(self.data)

    def clean_data(self):
        def extract_article_number(row):
            if row['Article Number'] == '':
                return row['Article Title'].split('.')[0].replace('[', '').strip()
            return row['Article Number']

        # Apply the function to fill in missing article numbers
        self.df['Article Number'] = self.df.apply(extract_article_number, axis=1)

        # Manual cleanup for some erroneous data
        self.df.at[259, 'Part'] = 'PART VII'
        self.df.at[259, 'Part Name'] = 'PART VII. Omitted'
        self.df.at[259, 'Chapter'] = 'THE STATES IN PART B OF THE FIRST SCHEDULE'
        self.df.at[259, 'Article Number'] = '238'
        self.df.at[259, 'Article Title'] = '[238. Omitted.]'

        # Drop the now redundant row
        self.df = self.df.drop(260).reset_index(drop=True)

    def get_dataframe(self):
        return self.df

def main():
    # Read the contents from the file
    with open('../data/contents_page_text.txt', 'r', encoding='utf-8') as file:
        contents_text = file.read()

    parser = ConstitutionContentsParser(contents_text)
    parser.parse()
    parser.clean_data()

    # Return the DataFrame
    return parser.get_dataframe()

if __name__ == "__main__":
    df = main()
    print(df)