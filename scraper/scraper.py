import re
import shutil

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def capture_snapshot(url, output_file):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # Launch browser in headless mode
        page = browser.new_page()
        page.goto(url)
        html_content = page.content()  # Get the full HTML content of the page
        
        # Save the HTML content to a file
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        browser.close()

def extract_eligibility_requirements(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find the first <a> tag with id="eligibility-requirements"
    eligibility_link = soup.find('a', id="eligibility-requirements")

    if eligibility_link:
        # Find the parent of this link which is an <h3> tag
        h3_tag = eligibility_link.find_parent('h3')

        # Start collecting content after this <h3> tag
        eligibility_section_text = []
        eligibility_section_links = []
        
        # Loop through the next siblings of the <h3> tag
        sibling = h3_tag.find_next_sibling()
        
        while sibling:
            # Stop if we encounter another <h3> tag (start of new section)
            if sibling.name == 'h3':
                break
            
            # Collect text content from <h4> and <ul> elements
            if sibling.name == 'h4':
                eligibility_section_text.append(sibling.get_text(strip=True))
            elif sibling.name == 'ul':
                # Collect list items <li> within the <ul>
                for li in sibling.find_all('li'):
                    eligibility_section_text.append(li.get_text(strip=True))

                    for a_tag in li.find_all('a', href=True):
                        eligibility_section_links.append(a_tag['href'])
            # Move to the next sibling
            sibling = sibling.find_next_sibling()

        # Join the collected content into one big string for the text content
        text_content = '\n'.join(eligibility_section_text)
        link_content = '\n'.join(eligibility_section_links)

        # Store extracted data
        extracted_data = {
            "text": text_content,
            "links": link_content
        }
        return extracted_data

def save_extracted_data(extracted_data, output_file):
    if extracted_data:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("Eligibility Requirements:\n")
            f.write(f"Text Content:\n{extracted_data['text']}\n")
            f.write(f"Links:\n{extracted_data['links']}\n")
            f.write("\n\n")
    else:
        print("No data to save.")

# Example usage:
capture_snapshot("https://www.albme.gov/licensing/pa-aa/license-registration/", "website_snapshot.html")

# After the snapshot is captured, read the HTML file
with open("website_snapshot.html", "r", encoding="utf-8") as f:
    html_content = f.read()

# Extract the Eligibility Requirements section using id="eligibility-requirements"
extracted_data = extract_eligibility_requirements(html_content)

# Save the extracted data to a new file
save_extracted_data(extracted_data, "eligibility_requirements_new.txt")

print("Extraction complete! Check the 'eligibility_requirements_old.txt' file for the results.")


###############################istahp
import os
import shutil
import difflib

def get_file_diff(old_file, new_file):
    """
    Compare old and new files and return added and removed lines.
    """
    if not os.path.exists(old_file):
        old_lines = []
    else:
        with open(old_file, "r", encoding="utf-8") as f:
            old_lines = [line.rstrip() for line in f.readlines()]

    with open(new_file, "r", encoding="utf-8") as f:
        new_lines = [line.rstrip() for line in f.readlines()]

    diff = list(difflib.ndiff(old_lines, new_lines))

    added = []
    removed = []

    for line in diff:
        if line.startswith("+ "):
            added.append(line[2:])
        elif line.startswith("- "):
            removed.append(line[2:])

    return added, removed

def generate_diff_html_email(added, removed, output_html):
    """
    Generate an HTML file summarizing added and removed lines for email.
    """
    html_content = """
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; }
            h2 { color: #2F4F4F; }
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #ddd; padding: 8px; }
            th { background-color: #4CAF50; color: white; }
            tr.added { background-color: #d4edda; }      /* Green for added */
            tr.removed { background-color: #f8d7da; }    /* Red for removed */
        </style>
    </head>
    <body>
        <h2>Eligibility Requirements Changes Detected</h2>
        <table>
            <tr>
                <th>Change Type</th>
                <th>Old Value</th>
                <th>New Value</th>
            </tr>
    """
#secret
    for line in removed:
        html_content += f"""
            <tr class="removed">
                <td>Removed</td>
                <td>{line}</td>
                <td></td>
            </tr>
        """

    for line in added:
        html_content += f"""
            <tr class="added">
                <td>Added</td>
                <td></td>
                <td>{line}</td>
            </tr>
        """

    html_content += """
        </table>
    </body>
    </html>
    """

    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"HTML email template generated: {output_html}")

# -------------------------
# Usage Example
# -------------------------

old_file = "eligibility_requirements.txt"
new_file = "eligibility_requirements_new.txt"
output_html = "eligibility_changes_email.html"

# Step 1: Compare files
added, removed = get_file_diff(old_file, new_file)

# Step 2: Only generate HTML if there are changes
if added or removed:
    generate_diff_html_email(added, removed, output_html)
else:
    print("No changes detected. HTML email will not be generated.")

# Step 3: Update old file for next run
shutil.copy(new_file, old_file)
print(f"Old file '{old_file}' updated with latest snapshot.")
