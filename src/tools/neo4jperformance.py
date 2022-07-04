from neo4jrestclient.client import GraphDatabase, Node
import logging

Q = [
    "MATCH (s:产品 {item_sku_id:'6157068'})-[r]-> (o:ProdAttrs) WHERE any(key in keys(o) WHERE key CONTAINS '底座') return s, TYPE(r), o limit 2",
    "MATCH (b:品牌 {brandname_full:'创维（Skyworth）'})<-[r1]-(s:产品 {item_third_cate_name:'平板电视'})-[r2]-> (o:ProdAttrs) WHERE any(key in keys(o) WHERE key CONTAINS '底座') RETURN s, b, o limit 5",
    "MATCH (s:产品 {item_third_cate_name:'手机'})-[r]-> (o:ProdAttrs) WHERE any(key in keys(o) WHERE key CONTAINS '这个手机') RETURN s, TYPE(r), o limit 5",    #timeout query
    "match (s:产品 {item_third_cate_name:'迷你音响'})-[r1]->(o1:ProdAttrs), (s)-[:BELONG_TO_BRAND]->(o2 {brandname_cn:'飞利浦'}) WHERE any(key in keys(o1) WHERE o1[key] ='蓝色') return s, o1, o2 limit 2",
    "match (s:产品 {item_third_cate_name:'手机'})-[r]->(o:ProdAttrs) WHERE any(key in keys(o) WHERE key='前置摄像头' AND o[key] contains '900万像素') return s, o limit 2"
    ]


def SpeedTest():
    qcount = "match(n) return count(n)"
    results1 = db.query(qcount, returns=int)
    logging.warning("There are (%s) nodes" % (results1[0]))

    for q in Q:
        results1 = db.query(q, returns=(Node, str, Node))
        logging.info("done with q:" + q)
        print(len(results1))

def warmup():
    q = 'MATCH (n)-[r]->(m)   RETURN n, type(r), m limit 20'
    results1 = db.query(q, returns=(Node, str, Node))
    for r in results1:
        print("(%s)-[%s]->(%s)" % (r[0].id, r[1], r[2].labels))

#neo4jserver = "10.182.8.14"
#db = GraphDatabase("http://" + neo4jserver + ":80", username="neo4j", password="work")
neo4jserver = "10.153.152.254"
db = GraphDatabase("http://" + neo4jserver + ":7474", username="neo4j", password="work")

QClean = """MATCH (n) WHERE size((n)--())=0    DELETE (n)"""    #delete isolate nodes
QDuplicate = "MATCH (n) with n as map limit 1000000 CREATE (copy) set copy=map "

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    logging.info("Connected:")
    #db.query(QClean)

    for i in range(1000):
        SpeedTest()
        #db.query(QDuplicate)
    SpeedTest()


