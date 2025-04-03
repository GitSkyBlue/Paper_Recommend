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

    result = search.FindBySearchQuery(search_Query)
    # print('=='* 80)
    # print(result)
    # print('=='* 80)

    json_Data = search.FindBySearchQuery(search_Query)
    # print('=='* 80)
    # print(json_Data)
    # print('=='* 80)
    results = similarity.SetData(json_Data)

    sim_list = similarity.CheckSimilarity(search_Query, results)
    # for data in sim_list:
    #     print(data.page_content)

    # print('여기에요' * 100)
    # print(sim_list)
    paper_infos = summary.FindIDAndURL(sim_list, result)
    print(paper_infos)
    summary.DownloadPDF(paper_infos)
    summary.Summarize(client)