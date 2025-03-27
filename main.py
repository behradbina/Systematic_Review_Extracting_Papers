from retrieve_papers import PubmedArticles, GoogleScholar, Scopus

def main():
    pubmed_search_query = (
        '("Streptozotocin"[Mesh Terms] OR streptozotocin[Title/Abstract] OR STZ[Title/Abstract]) AND ("Intracerebroventricular Injections"[Mesh Terms] OR intracerebroventricular[Title/Abstract] OR ICV[Title/Abstract]) AND ("Rodentia"[Mesh Terms] OR rodent[Title/Abstract] OR mice[Title/Abstract] OR mouse[Title/Abstract] OR "Mus musculus"[Mesh Terms] OR rat[Title/Abstract] OR rats[Title/Abstract] OR "Rattus norvegicus"[Mesh Terms] OR "Rattus rattus"[Mesh Terms])'
    )
    
    base_file = "search_result.csv"
    
    #PubmedArticles(query=pubmed_search_query, email="behradbina@gmail.com", retmax=600, output_file_path=base_file)
    
    #google_scholar_query = "streptozotocin AND STZ AND intracerebroventricular AND (rat OR mice OR mouse)"
    
    #GoogleScholar(query=google_scholar_query, limit=5, base_file=base_file, output_file= 'google_scholar.csv')

    scopus_query = "Machine Learning"
    
    Scopus(query=scopus_query, base_file=base_file)

    
if __name__ == "__main__":
    main()
