import sys
import csv
from pybliometrics.scopus import ScopusSearch

def extract_year(cover_date):
    """
    Extracts the year from the cover date (format: 'YYYY-MM-DD' or similar).
    """
    if cover_date and isinstance(cover_date, str):
        return cover_date.split("-")[0]
    return ""

def main():    
    query = "Machine Learning"
    print(f"Searching Scopus for: {query}\n")
    
    try:
        s = ScopusSearch(query)
    except Exception as e:
        print(f"Error while searching Scopus: {e}")
        sys.exit(1)
    
    results = s.results
    print(f"Found {len(results)} results.")
    
    with open('scopus_results.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Title', 'Year', 'Journal', 'DOI']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        count = 0
        limit = 10
        for item in results:
            
            title = getattr(item, 'title', '')            
            year = extract_year(getattr(item, 'coverDate', ''))            
            journal = getattr(item, 'publicationName', '')
            doi = getattr(item, 'doi', '')
            
            # Only write records that have a DOI
            if doi:
                writer.writerow({
                    'Title': title,
                    'Year': year,
                    'Journal': journal,
                    'DOI': doi
                })
                print(f"Saved: {title} with DOI: {doi}")
                count += 1
            
            if count >= limit:
                break

    print("Results saved in scopus_results.csv")

if __name__ == '__main__':
    main()
