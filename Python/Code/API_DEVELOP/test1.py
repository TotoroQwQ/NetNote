import test
import json
from elasticsearch import Elasticsearch

es = Elasticsearch('20.0.0.252:9200', http_auth=('elastic', 'saftop9854'))
""" datas = [
    {
        'title': '美国留给伊拉克的是个烂摊子吗',
        'url': 'http://view.news.qq.com/zt2011/usa_iraq/index.htm',
        'date': '2011-12-16'
    },
    {
        'title': '公安部：各地校车将享最高路权',
        'url': 'http://www.chinanews.com/gn/2011/12-16/3536077.shtml',
        'date': '2011-12-16'
    },
    {
        'title': '中韩渔警冲突调查：韩警平均每天扣1艘中国渔船',
        'url': 'https://news.qq.com/a/20111216/001044.htm',
        'date': '2011-12-17'
    },
    {
        'title': '中国驻洛杉矶领事馆遭亚裔男子枪击 嫌犯已自首',
        'url': 'http://news.ifeng.com/world/detail_2011_12/16/11372558_0.shtml',
        'date': '2011-12-18'
    }
]
 
for data in datas:
    es.index(index='test', doc_type='_doc', body=data) """

dsl = {
    'query': {
        'match': {
            'title': '中国领事馆'
        }
    }
}

print(type(dsl))
test_all = es.search(index='test')

print(test_all)

print('---------------------------')
test_wordsSearch = es.search(index='test', body=dsl)

print(test_wordsSearch)

data = test_wordsSearch['hits']['hits']
print('---------------------------')

print(len(data))

results = []
for item in data:
    results.append(item['_source']) 
print(results)

print(json.dumps(results,ensure_ascii=False))
