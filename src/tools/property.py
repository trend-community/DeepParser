#>/export/App/neo4j-community-3.3.2/bin/cypher-shell -a bolt://localhost:22087 "MATCH (p:大家电)-[r]->(o) where (o:ExAttrs OR o:ProdAttrs) and p.item_valid_flag='1' and p.sku_valid_flag='1' RETURN p.item_sku_id, o limit 1000000" > dajiadianattr1m.txt
#>/export/App/neo4j-community-3.3.2/bin/cypher-shell -a bolt://localhost:22087 "MATCH (p:大家电)-[r]->(o) where (o:ExAttrs OR o:ProdAttrs) and p.item_valid_flag='1' and p.sku_valid_flag='1' RETURN p.item_sku_id, o skip 1000000 limit 1000000" > dajiadianattr1m.2.txt
#>/export/App/neo4j-community-3.3.2/bin/cypher-shell -a bolt://localhost:22087 "MATCH (p:大家电)-[r]->(o) where (o:ExAttrs OR o:ProdAttrs) and p.item_valid_flag='1' and p.sku_valid_flag='1' RETURN p.item_sku_id, o skip 2000000 limit 1000000" > dajiadianattr1m.3.txt

import logging, argparse, re
propertypair = set()
propertyset = set()

def ImportProperty(oneline):
    innerline = re.match("\(:.* {(.*)}\)", oneline)
    if innerline:
        inner = innerline.group(1)
        pairs = re.findall("(\S*?): \"(.*?)\"", inner)
        for pair in pairs:
            #print("{}\t{}".format(pair[0], pair[1]))
            key = pair[0].strip()
            propertypair.add("{}\t{}".format(key, pair[1].strip()))
            propertyset.add(key)
        pairs = re.findall("(\S*?): \[(.*?)\]", inner)
        for pair in pairs:
            #print("{}\t{}".format(pair[0], pair[1]))
            key = pair[0].strip()
            values = pair[1].split(",")
            for v in values:
                v = v.strip().strip("\"").strip()
                propertypair.add("{}\t{}".format(key, v))
            propertyset.add(key)

def GetSkuKV(oneline):
    innerline = re.match(".* {(.*)}\)", oneline)
    if innerline:
        inner = innerline.group(1)
        skuid = re.match("\"(\d*)\"", oneline).group(1)
        pairs = re.findall("(\S*?): \"(.*?)\"", inner)
        for pair in pairs:
            key = pair[0].strip()
            v = pair[1].strip()
            if key and v:
                print("{}\t{}\t{}".format(skuid, pair[0].strip(), pair[1].strip()))
        pairs = re.findall("(\S*?): \[(.*?)\]", inner)
        for pair in pairs:
            #print("{}\t{}".format(pair[0], pair[1]))
            key = pair[0].strip()
            values = pair[1].split(",")
            for v in values:
                v = v.strip().strip("\"").strip()
                if key and v:
                    print("{}\t{}\t{}".format(skuid, key, v))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    parser = argparse.ArgumentParser()
    parser.add_argument("inputfile", help="input file")
    args = parser.parse_args()

    with open(args.inputfile, encoding="utf-8") as RuleFile:
        for line in RuleFile:
            if line.strip():
                GetSkuKV(line.strip())

    # for x in sorted(propertypair):
    #     print(x)

    # print("property set:")
    # for p in sorted(propertyset):
    #     print(p)
