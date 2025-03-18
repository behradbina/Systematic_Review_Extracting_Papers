import sys
import csv
import requests
from scholarly import scholarly

def get_doi_from_crossref(title):
    """
    Given a paper title, query CrossRef for its DOI.
    """
    url = "https://api.crossref.org/works"
    params = {"query.title": title, "rows": 1}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data["message"]["items"]:
            # Return the DOI if found (may be None if not available)
            return data["message"]["items"][0].get("DOI")
    except Exception as e:
        print(f"Error querying CrossRef for title: {title}\n{e}")
    return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py <search keywords>")
        sys.exit(1)

    # Combine all arguments to form the query string.
    query = " ".join(sys.argv[1:])
    print(f"Searching Google Scholar for: {query}\n")
    
    # Use scholarly to search publications
    search_query = scholarly.search_pubs(query)
    
    # Open a CSV file to store the results.
    with open('results.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Title', 'Year', 'Journal', 'Doi']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        doi_count = 0
        # Process each publication; adjust or remove the limit as needed.
        for pub in search_query:
            bib = pub.get('bib', {})
            title = bib.get('title', '')
            # Try to get the publication year from possible keys.
            year = bib.get('pub_year') or bib.get('year', '')
            # The journal name is usually provided under the 'venue' key.
            journal = bib.get('venue', '')
            
            if not title:
                continue
            
            doi = get_doi_from_crossref(title)
            
            writer.writerow({
                'Title': title,
                'Year': year,
                'Journal': journal,
                'Doi': 'https://doi.org/'+doi
            })
            print(f"Saved paper: with DOI: {doi}")
            doi_count += 1

            
            # For demonstration, limit to 10 results; adjust as needed.
            if doi_count >= 10:
                break

    print("Results saved in results.csv")

if __name__ == '__main__':
    main()
