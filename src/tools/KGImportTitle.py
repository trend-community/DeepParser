import argparse, logging

from neo4jrestclient.client import GraphDatabase


db = GraphDatabase("http://10.153.152.253:7474", username="neo4j", password="work")

  #difficult to add parameter.
  #  https://github.com/versae/neo4j-rest-client/issues/133

def ImportProperty_rest(line):
    try:
        skuid, propertyvalue, propertyname = line.split('\t')
    except Exception:
        logging.warning("Wrong line:" + line)
        return
    logging.info("Start writing:" + skuid + "," + propertyname + "," + propertyvalue + ".")

    if skuid == "item_sku_id":
        return  #first line.

    # Cypher = "MATCH (n:产品{item_sku_id:`{sku}`}) "
    # Cypher += " MERGE (m:PRodAttrs{ name: `{sku_title}`, `{propertyename}`: `{propertyvalue}`}) "
    # Cypher += " MERGE (n)-[:TITLE]->(m);"
    #
    # db.query(Cypher, params={"sku":skuid,
    #                          "sku_title":skuid + "_TITLE,",
    #                          "propertyname":propertyname,
    #                          "propertyvalue":propertyvalue})
    #
    Cypher = "MATCH (n:产品{item_sku_id:'" + skuid + "' }) "
    Cypher += " MERGE (m:PRodAttrs{ name: '" + skuid + "_TITLE'}) "
    Cypher += " set  m += {" + propertyname + ": '" + propertyvalue.strip() + "'} "
    Cypher += " MERGE (n)-[:TITLE]->(m);"
    logging.info(Cypher)
    db.query(Cypher)



# #pip install neo4j-driver
# from neo4j.v1 import GraphDatabase
#
# uri = "bolt://10.153.152.253:7687"
# driver = GraphDatabase.driver(uri, auth=("neo4j", "password"))
#
# def ImportProperty_bolt(line):
#     try:
#         skuid, propertyvalue, propertyname = line.split('\t')
#     except Exception:
#         logging.warning("Wrong line:" + line)
#         return
#     logging.info("Start writing:" + skuid + "," + propertyname + "," + propertyvalue + ".")
#
#     if skuid == "item_sku_id":
#         return  #first line.
#
#     Cypher = "MATCH (n:产品{item_sku_id:`{sku}`}) "
#     Cypher += " MERGE (m:PRodAttrs{ name: `{sku_title}`, `{propertyename}`: `{propertyvalue}`}) "
#     Cypher += " MERGE (n)-[:TITLE]->(m);"
#
#     db.query(Cypher, params={"sku":skuid,
#                              "sku_title":skuid + "_TITLE,",
#                              "propertyname":propertyname,
#                              "propertyvalue":propertyvalue})


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
    parser = argparse.ArgumentParser()
    parser.add_argument("inputfile", help="input file")
    args = parser.parse_args()

    with open(args.inputfile, encoding="utf-8") as RuleFile:
        for line in RuleFile:
            if line.strip():
                ImportProperty_rest(line.strip())
