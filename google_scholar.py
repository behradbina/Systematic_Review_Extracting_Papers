from scholarly import scholarly
import csv 

def search_scholar(query, num_results=100):
    search_query = scholarly.search_pubs(query)
    results = []
    
    for i in range(num_results):
        print(i)
        try:
            article = next(search_query)
            
            results.append({
                "title" : article.get("bib").get("title"),
                "author" : article.get("bib").get("author"),
                "year" : article.get("bib").get("pub_year"),
                "abstract" : article.get("bib").get("abstract"),
                
            })
        except StopIteration:
            break
    
    return results

def save_to_csv(articles, filename="google_scholar_search.csv"):
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        writer.writerow(["Title", "Year", "Abstract", "Author"])

        for article in articles:
            writer.writerow([article['title'], article['year'], article['abstract'], article["author"]])
            
if __name__ == "__main__":
    keyword = "machine learning"
    articles = search_scholar(keyword, num_results=5)
    save_to_csv(articles)
    