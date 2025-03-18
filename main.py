from retrieve_papers import PubmedArticles

def main():
    pubmed_search_query = (
        '("Streptozotocin"[Mesh Terms] OR streptozotocin[Title/Abstract] OR STZ[Title/Abstract]) AND ("Intracerebroventricular Injections"[Mesh Terms] OR intracerebroventricular[Title/Abstract] OR ICV[Title/Abstract]) AND ("Rodentia"[Mesh Terms] OR rodent[Title/Abstract] OR mice[Title/Abstract] OR mouse[Title/Abstract] OR "Mus musculus"[Mesh Terms] OR rat[Title/Abstract] OR rats[Title/Abstract] OR "Rattus norvegicus"[Mesh Terms] OR "Rattus rattus"[Mesh Terms])'
    )
    PubmedArticles(query=pubmed_search_query, email="behradbina@gmail.com", retmax=600, output_file_path="search_result.csv")

if __name__ == "__main__":
    main()
