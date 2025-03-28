from retrieve_papers import PubmedArticles, GoogleScholar, Scopus, ScienceDirect

def main():
    base_file = "data/search_result.csv"
    
    pubmed_search_query = (
        '("Streptozotocin"[Mesh Terms] OR streptozotocin[Title/Abstract] OR STZ[Title/Abstract]) AND ("Intracerebroventricular Injections"[Mesh Terms] OR intracerebroventricular[Title/Abstract] OR ICV[Title/Abstract]) AND ("Rodentia"[Mesh Terms] OR rodent[Title/Abstract] OR mice[Title/Abstract] OR mouse[Title/Abstract] OR "Mus musculus"[Mesh Terms] OR rat[Title/Abstract] OR rats[Title/Abstract] OR "Rattus norvegicus"[Mesh Terms] OR "Rattus rattus"[Mesh Terms])'
    )
    #PubmedArticles(query=pubmed_search_query, email="behradbina@gmail.com", retmax=600, output_file_path=base_file)
    
    #google_scholar_query = "streptozotocin AND STZ AND intracerebroventricular AND (rat OR mice OR mouse)"   
    #GoogleScholar(query=google_scholar_query, limit=5, base_file=base_file, output_file= 'google_scholar.csv')

    scopus_query = r'TITLE-ABS-KEY("Streptozotocin" OR "Streptozocin" OR streptozotocin OR stz) AND TITLE-ABS-KEY("Intracerebroventricular Injections" OR intracerebroventricular OR icv) AND TITLE-ABS-KEY(rodent OR mice OR mouse OR "Mus musculus" OR rat OR rats OR "Rattus norvegicus" OR "Rattus rattus") AND PUBYEAR > 2014 AND PUBYEAR < 2026'
    #Scopus(query=scopus_query, base_file=base_file)
    
    ScienceDirect_query = scopus_query    
    ScienceDirect(query=ScienceDirect_query, base_file=base_file)

    
if __name__ == "__main__":
    main()
