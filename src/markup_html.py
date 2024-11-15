from bs4 import BeautifulSoup

class MarkupHTML:
    def __init__(self, combined_soup, extracted_data, output_filename):
        self.combined_soup = combined_soup
        self.extracted_data = extracted_data
        self.output_filename = output_filename

    def filter_and_extract_text(self, html_content, footnotes):
        """
        Filters out <p> tags with all caps text and small text, then extracts text from the remaining tags.
        Replaces superscript tags with footnote IDs.
        """
        soup = BeautifulSoup(html_content, 'html.parser')

        def is_all_uppercase(text):
            letters_only = ''.join(filter(str.isalpha, text))
            return letters_only.isupper()

        extracted_text = []

        # Process <p> tags and extract text if not marked to be skipped
        for p_tag in soup.find_all('p'):
            if not is_all_uppercase(p_tag.get_text(strip=True)) and not any(
                'font-size:7.5pt' in span.get('style', '') or 'font-size:8.0pt' in span.get('style', '') for span in p_tag.find_all('span')
            ):
                # Replace superscript tags with footnote IDs
                for sup_tag in p_tag.find_all('sup'):
                    for footnote_id, footnote_data in footnotes.items():
                        if sup_tag == footnote_data['mapped_p_tag']:
                            sup_tag.replace_with(f"[{footnote_id}]")
                            break
                extracted_text.append(p_tag.get_text(strip=True))

        return ' '.join(extracted_text)

    def create_article_div(self, data):
        """
        Creates a div for each article with the specified structure.
        """
        article_div = BeautifulSoup(features="html.parser").new_tag('div', **{'class': 'article'})

        # Article Name
        article_name_div = BeautifulSoup(features="html.parser").new_tag('div', **{'class': 'article_name'})
        article_name_div.string = data['organized_texts_contents_page']
        article_div.append(article_name_div)

        # Article Contents
        filtered_text = self.filter_and_extract_text(data['extracted_html'], data['footnotes'])
        article_contents_div = BeautifulSoup(features="html.parser").new_tag('div', **{'class': 'article_contents'})
        article_contents_div.string = filtered_text
        article_div.append(article_contents_div)

        # HTML Content
        html_content_div = BeautifulSoup(features="html.parser").new_tag('div', **{'class': 'html_content'})
        html_content_soup = BeautifulSoup(data['extracted_html'], 'html.parser')
        html_content_div.append(html_content_soup)
        article_div.append(html_content_div)

        # Footnotes
        footnotes_div = BeautifulSoup(features="html.parser").new_tag('div', **{'class': 'footnotes'})
        footnotes_div.append(BeautifulSoup("<strong>Footnotes:</strong>", 'html.parser'))
        for footnote_id, footnote_data in data.get('footnotes', {}).items():
            footnote_text_div = BeautifulSoup(features="html.parser").new_tag('div', **{'class': 'footnote-text'})
            footnote_text_div.string = f"[{footnote_id}] {footnote_data['mapped_footnote_text']}"
            footnotes_div.append(footnote_text_div)
        article_div.append(footnotes_div)

        return article_div

    def apply_markup(self):
        """
        Applies markup to the HTML and saves it to a file.
        """
        # Create a new BeautifulSoup object for the output HTML
        output_soup = BeautifulSoup(features="html.parser")
        html_tag = output_soup.new_tag('html')
        output_soup.append(html_tag)

        # Add a head with styles
        head_tag = output_soup.new_tag('head')
        style_tag = output_soup.new_tag('style')
        style_tag.string = """
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
        }
        .article {
            margin-bottom: 40px;
            padding: 10px;
            border: 1px solid #ccc;
            border-radius: 5px;
        }
        .article_name {
            font-size: 1.5em;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .article_contents {
            margin-bottom: 10px;
        }
        .footnotes {
            margin-top: 10px;
            font-size: 0.9em;
            color: #555;
        }
        .footnote-text {
            background-color: rgba(173, 216, 230, 0.2);
            padding: 5px;
            border-radius: 3px;
            display: inline-block;
            margin-bottom: 5px;
        }
        """
        head_tag.append(style_tag)
        html_tag.append(head_tag)

        # Add body
        body_tag = output_soup.new_tag('body')
        html_tag.append(body_tag)

        # Add each article to the body
        for data in self.extracted_data:
            article_div = self.create_article_div(data)
            body_tag.append(article_div)

        # Save the output HTML
        with open(self.output_filename, 'w', encoding='utf-8') as file:
            file.write(output_soup.prettify())

def main(combined_soup, extracted_data, output_filename):
    markup = MarkupHTML(combined_soup, extracted_data, output_filename)
    markup.apply_markup()
    return extracted_data

if __name__ == "__main__":
    # This is a placeholder for testing purposes
    # You would typically pass the combined_soup, extracted_data, and output_filename from the main script
    pass