import sys
import csv
import requests
from scholarly import scholarly
import pandas as pd

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
            return data["message"]["items"][0].get("DOI")
    except Exception as e:
        print(f"Error querying CrossRef for title: {title}\n{e}")
    return None

def scraping_articles_google_scholar(query, limit: int):    
    have_doi_articles = {
        'Title' : [],
        'Year' : [],
        'Journal' : [],
        'Doi' : []
    }
    
    no_doi_found = {
        'Title' : [],
        'Year' : [],
        'Journal' : [],
        'Doi' : []
    }
    
    print(f"Searching Google Scholar for: {query}\n")

    search_query = scholarly.search_pubs(query)
    
    doi_count = 0
    
    for pub in search_query:
        bib = pub.get('bib', {})
        title = bib.get('title', '')
        year = bib.get('pub_year') or bib.get('year', '')
        journal = bib.get('venue', '') # The journal name 
        
        if not title:
            continue
        
        doi = get_doi_from_crossref(title)
        if doi :
            have_doi_articles['Title'].append(title)
            have_doi_articles['Year'].append(year)
            have_doi_articles['Journal'].append(journal)
            have_doi_articles['Doi'].append('https://doi.org/'+doi)    
        else: 
            no_doi_found['Title'].append(title)
            no_doi_found['Year'].append(year)
            no_doi_found['Journal'].append(journal)
            no_doi_found['Doi'].append(None)
             
        print(f"Saved paper: with DOI: {doi}")
        doi_count += 1

        if doi_count >= limit:
            break

    have_doi_articles = pd.DataFrame(have_doi_articles)
    no_doi_found = pd.DataFrame(no_doi_found)
    return have_doi_articles , no_doi_found

def process_found_articles(have_doi_articles , no_doi_found):
    search_df = pd.read_csv('search_result.csv', usecols=['Doi', 'Title'])

    have_doi_articles = have_doi_articles.drop_duplicates()
    have_doi_articles = have_doi_articles[~have_doi_articles['Doi'].isin(search_df['Doi'])]
    
    no_doi_found = no_doi_found.drop_duplicates()
    no_doi_found = no_doi_found[~no_doi_found['Title'].isin(search_df['Title'])]

    combined_df = pd.concat([have_doi_articles, no_doi_found], ignore_index=True)

    combined_df.to_csv('google_scholar.csv', index=False)
    

def main():
    query = "Streptozotocin AND streptozotocin AND STZ AND Intracerebroventricular AND intracerebroventricular AND rat"
    
    have_doi_articles , no_doi_found = scraping_articles_google_scholar(query, 2)
    process_found_articles(have_doi_articles , no_doi_found)

if __name__ == '__main__':
    main()
