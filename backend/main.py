from openai import OpenAI
import search
import similarity

if __name__ == '__main__':
    client = OpenAI()
    query = 'Attention is all you need에 대해서 알고싶어요'
    search_Query, user_Request = search.KeywordAndTranslate(query, client)

    result = search.FindBySearchQuery(search_Query)
    print(result)
    
    search_Query, user_Request = search.KeywordAndTranslate(query, client)
    print(search_Query, user_Request)

    json_Data = search.FindBySearchQuery(search_Query)

    results = similarity.SetData(json_Data)

    sim = similarity.CheckSimilarity(results)
    for data in sim:
        print(data.page_content)