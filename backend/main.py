from openai import OpenAI
import search
import similarity
import summary

if __name__ == '__main__':
    client = OpenAI()
    query = 'Attention is all you need에 대해서 알고싶어요'
    search_Query, user_Request = search.KeywordAndTranslate(query, client)
    print('Search Query :', search_Query)
    print('User Request :', user_Request)

    json_Data = search.FindBySearchQuery(search_Query)
    ###################################################

    results = similarity.SetData(json_Data)

    sim_list = similarity.CheckSimilarity(search_Query, results)

    paper_infos = summary.FindIDAndURL(sim_list, json_Data)
    print(paper_infos)
    summary.DownloadPDF(paper_infos)
    summary.Summarize(client)