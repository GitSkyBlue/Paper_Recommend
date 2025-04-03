import arxiv

query = 'attention is all you need'

search = arxiv.Search(
    query=query,
    max_results=10,
    sort_order=arxiv.SortOrder.Descending
)

client = arxiv.Client()
papers = list(client.results(search))

paper_data = []
for paper in papers:
    paper_data.append({
        "title": paper.title,
        "abstract": paper.summary,
        "url": paper.entry_id,
        "pdf_url": paper.pdf_url
    })

for data in paper_data:
    print('Title :', data['title'])
    print('Abstract :', data['abstract'])
