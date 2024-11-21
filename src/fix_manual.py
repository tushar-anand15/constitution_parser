import pandas as pd
import json
from colorama import init, Fore, Style
import re

# Initialize colorama
init(autoreset=True)

def display_issue(row):
    """
    Display the contents of a row with issues in a readable format.
    """
    print(Fore.CYAN + "\n--- Article Information ---")
    print(Fore.YELLOW + f"Contents Page Text: {row['contents_page_text']}")
    print(Fore.YELLOW + f"Extracted Article Text: {row['extracted_article_text']}")
    
    # Parse the footnotes JSON string
    footnotes = row['footnotes']
    footnotes_dict = json.loads(footnotes)
    print(Fore.YELLOW + f"Number of Footnotes: {len(footnotes_dict)}")
    for footnote_id, footnote_text in footnotes_dict.items():
        print(Fore.YELLOW + f"{footnote_id}: {footnote_text}")

def fix_extracted_text_issues(df):
    """
    Iterate through rows with extracted text issues and allow the user to confirm fixes.
    """
    for index, row in df[df['issues'] == 'extracted_text_issue'].iterrows():
        display_issue(row)
        
        # Prompt the user to confirm if they have finished editing
        input(Fore.GREEN + "Please edit the extracted article text in your preferred program. Press Enter when you have finished editing.")
        
        # Mark the issue as addressed
        df.at[index, 'issues'] = 'addressed_extracted_text_issue'
        
        # Save the updated DataFrame to a new Excel file after each change
        df.to_excel('test_constitution_checked_fixed.xlsx', index=False)

def get_max_footnote_key(df):
    """
    Find the maximum footnote key in the DataFrame.
    """
    max_key = 0
    for footnotes in df['footnotes']:
        footnotes_dict = json.loads(footnotes)
        for key in footnotes_dict.keys():
            match = re.match(r'fn_(\d+)', key)
            if match:
                num = int(match.group(1))
                if num > max_key:
                    max_key = num
    return max_key

def fix_footnotes(df):
    """
    Automate the footnote fixing process.
    """
    max_key = get_max_footnote_key(df)
    print(Fore.CYAN + f"Starting footnote fixing. Current max footnote key: fn_{max_key}")

    for index, row in df[df['issues'] == 'footnotes_issue'].iterrows():
        display_issue(row)
        
        # Prompt the user to confirm if they have finished editing footnotes
        input(Fore.GREEN + "Please edit the footnotes in your preferred program. Press Enter when you have finished editing.")
        
        # Mark the issue as addressed
        df.at[index, 'issues'] = 'addressed_footnotes_issue'
        
        # Save the updated DataFrame to a new Excel file after each change
        df.to_excel('test_constitution_checked_fixed.xlsx', index=False)

def main():
    # Read the Excel file
    df = pd.read_excel('test_constitution_checked.xlsx')

    # Check if manual inputs are complete
    complete = input(Fore.GREEN + "Are manual inputs complete? (yes/no): ").strip().lower()
    if complete == 'yes':
        # Ask if the user wants to fix extracted text issues
        fix_extracted_text_choice = input(Fore.GREEN + "Do you want to fix extracted text issues? (yes/no): ").strip().lower()
        if fix_extracted_text_choice == 'yes':
            print(Fore.CYAN + "Starting to fix extracted text issues...")
            fix_extracted_text_issues(df)
        
        # Ask if the user wants to fix footnotes
        fix_footnotes_choice = input(Fore.GREEN + "Do you want to fix footnotes issues? (yes/no): ").strip().lower()
        if fix_footnotes_choice == 'yes':
            fix_footnotes(df)
    else:
        print(Fore.RED + "Please complete the manual inputs before proceeding.")

if __name__ == "__main__":
    main()