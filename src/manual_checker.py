import pandas as pd
import json

def display_row(row):
    """
    Display the contents of a row in a readable format.
    """
    print("\n--- Article Information ---")
    print(f"Contents Page Text: {row['contents_page_text']}")
    print(f"Extracted Article Text: {row['extracted_article_text']}")
    
    # Parse the footnotes JSON string
    footnotes = row['footnotes']
    footnotes_dict = json.loads(footnotes)
    print(f"Number of Footnotes: {len(footnotes_dict)}")
    for footnote_id, footnote_text in footnotes_dict.items():
        print(f"{footnote_id}: {footnote_text}")

def check_data(df):
    """
    Iterate through each row and allow the user to check and update the data.
    """
    for index, row in df.iterrows():
        display_row(row)
        
        # Get user input
        print("\nEnter 'e' if the extracted text is incorrect.")
        print("Enter 'f' if the footnotes are incorrect.")
        print("Enter 'n' for no issues.")
        user_input = input("Enter your choice: ").strip().lower()

        # Record issues based on user input
        if user_input == 'e':
            df.at[index, 'issues'] = 'extracted_text_issue'
        elif user_input == 'f':
            df.at[index, 'issues'] = 'footnotes_issue'
        elif user_input == 'ef':
            df.at[index, 'issues'] = 'extracted_text_issue, footnotes_issue'
        elif user_input == 'n':
            df.at[index, 'issues'] = 'no_issues'
        else:
            print("Invalid input. No issues recorded.")
            df.at[index, 'issues'] = 'invalid_input'

        # Save the updated DataFrame to a new Excel file after each input
        df.to_excel('test_constitution_checked.xlsx', index=False)

def main():
    # Read the Excel file
    df = pd.read_excel('test_constitution.xlsx')

    # Initialize the 'issues' column if it doesn't exist
    if 'issues' not in df.columns:
        df['issues'] = None

    # Check the data and update the DataFrame
    check_data(df)

if __name__ == "__main__":
    main()