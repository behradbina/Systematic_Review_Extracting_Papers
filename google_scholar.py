from scholarly import scholarly

def search_scholar(query, num_results=10):
    search_query = scholarly.search_pubs(query)
    results = []
    
    for i in range(num_results):
        try:
            article = next(search_query)
            # print(i)
            # print("---------------")
            # print(article)
            results.append({
                "title" : article.get("bib").get("title"),
                "author" : article.get("bib").get("author"),
                "year" : article.get("bib").get("pub_year"),
                "abstract" : article.get("bib").get("abstract"),
                
            })
        except StopIteration:
            break
    
    return results

# Example usage:
if __name__ == "__main__":
    keyword = "machine learning"
    articles = search_scholar(keyword, num_results=5)
    for idx, article in enumerate(articles, start=1):
        print(f"Title: {article['title']}")
        print(f"Authors: {article['author']}")
        print(f"Year: {article['year']}")
        print(f"Abstract: {article['abstract']}")
