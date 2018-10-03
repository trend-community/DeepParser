import os, sys, csv, logging

def CatMapping(keyword, cid_3):
    mapping={}
    mapping["空调"] = {("商品问题", "基础属性") :
                    ["区别", "尺寸", "颜色", "无霜", "型号", "制冷", "功能", "控制", "空气开关", "什么功能", "冷暖", "外机", "定频 | 变频", "遥控器", "扫风方式",
                     "匹数", "大匹", "制冷类型", "定频区别", "清洁", "自动清洁", "清洁功能", "度电", "省电", "耗电", "几度电",
                     "电", "耗电量", "适用面积 | 适用面积", "平方", "效果", "wifi"],

                ("活动优惠", "商品价格"):
                    ["价格", "便宜", "费用", "前", "降价", "价", "什么价格"],

                ("活动优惠", "活动咨询"):
                    ["活动", "优惠", "赠品", "什么优惠", "送", "什么活动", "优惠券", "减", "优惠活动", "什么赠品", "价格优惠", "买优惠", "礼品", "活动搞"],

                ("购买方式","下单问题"):
                    ["付款", "购买", "下单", "货到付款", "买", "收费", "现货", "白条"],

                ("物流问题", "配送工作时间"):
                    ["发货", "到货", "送货", "送到"],

                ("物流问题","送货上门"):
                    ["送货上门","送到"],

                ("政策问题", "价保条件"):
                    ["保价","延保"],

                ("政策问题", "发票问题"):
                    ["发票开", "发票"],

                ("政策问题", "联系方式"):
                    ["联系", "电话"],

                ("政策问题", "退换货政策"):
                    ["退货", "退"],

                ("政策问题", "保修返修"):
                    ["保修", "质保", "质量", "售后"],

                ("政策问题", "家电安装"):
                    ["安装费用", "安装", "装", "安装来", "时间安装", "安装师傅", "安装送货", "预约", "高空作业", "明天安装", "安装预约", "送货安装", "支架", "外机支架"],

                ("政策问题", "库存状态"):
                    ["没货"],

                # ("其他问题", "推荐"):
                #     ["推荐"],
                #
                # ("其他问题", "新款"):
                #     ["新款"],

                ("其他问题", "上市时间"):
                    ["上市"],

                ("其他问题", "其他"):
                    ["other", "推荐", "新款"]
                }

    mapping["洗衣机"] = {("商品问题", "基础属性"):
                          ["定频", "烘干", "烘干功能", "产品尺寸", "脱水", "尺寸", "上排水", "下排水","自动断电", "洗", "衣服洗", "什么颜色",
                           "噪音", "皮带", "预约功能", "功率", "被子洗", "电机", "单独脱水", "排水", "电池容量", "添衣", "脱水功能", "颜色",
                           "智能控制", "桶自洁", "功能", "长宽高", "脱水转速", "洗净比", "底座", "洗衣液放", "时间", "毛衣洗", "全自动",
                           "添衣功能","滑轮", "漂洗"],

                      ("活动优惠", "商品价格"):
                          ["优惠", "价格", "便宜", "费用", "前", "降价", "价", "什么价格"],

                      ("活动优惠", "活动咨询"):
                          ["优惠", "赠品", "活动", "什么优惠", "送", "什么活动", "优惠券", "减", "优惠活动", "什么赠品", "价格优惠", "买优惠", "礼品",
                           "活动搞"],

                      ("购买方式", "下单问题"):
                          ["货到付款", "购买", "买", "收费", "下单", "现货", "白条"],

                      ("物流问题", "配送工作时间"):
                          ["发货", "到货", "送货", "送到", "到货安装"],

                      ("政策问题", "价保条件"):
                          ["保价", "延保"],

                      ("政策问题", "发票问题"):
                          ["发票开", "发票"],

                      ("政策问题", "联系方式"):
                          ["联系", "电话"],

                      ("政策问题", "退换货政策"):
                          ["退货", "退"],

                      ("政策问题", "保修返修"):
                          ["保修", "质保", "质量", "售后"],

                      ("政策问题", "家电安装"):
                          ["安装费用", "安装", "装", "安装来", "时间安装", "安装师傅", "安装送货", "预约", "高空作业", "明天安装", "安装预约", "送货安装", "支架",
                           "外机支架"],

                      ("政策问题", "库存状态"):
                          ["没货"],

                      ("其他问题", "推荐"):
                          ["推荐"],

                      ("其他问题", "新款"):
                          ["新款"],

                      ("其他问题", "上市时间"):
                          ["上市"],

                      ("其他问题", "其他"):
                          ["Other"]
                      }

    for cid in mapping:
        for m in mapping[cid]:
            if keyword in mapping[cid][m]:
                return m

    return "其他问题", "其他"


KeywordList = {}
def LoadKeywordlist(filelocation):
    with open(filelocation, 'r', encoding="utf-8") as keyfile:
        for line in keyfile:
            try:
                sentence, keyword = line.split("\t")
                KeywordList[sentence] = keyword.strip()
            except Exception:
                logging.warning("Failed to split line {}".format(line))


#if the input file has only 1 column that is keyword column, so the output has the cat1 and cat2
#if the input file has 3 columns, that is sku/Q/A. (for SKU related)
#otherwise, the input file should be the standard questionair format.
if __name__ == "__main__":

    if len(sys.argv) < 5:
        print(
            "Usage: python3 qa_converttoimport.py  [inputfile] [outputfile] [cid3] [brand] (referencefile optional)")
        exit(1)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

    csvfile2 = open(sys.argv[2], 'a', encoding="utf-8")
    fieldnames = ["question", "tag","shopid", "brand", "cid3", "sku", "anSwer", "cat1",
                  "cat2", "profession", "source"]
    csvwriter = csv.DictWriter(csvfile2, fieldnames=fieldnames)
    csvwriter.writeheader()

    brand = sys.argv[4] #美的
    cid3 = sys.argv[3]  #空调/洗衣机/冰箱
    rowcounter = 0
    writecounter = 0

    ShopIDs={"美的": 1000001452, "海尔": 1000001782, "西门子": 1000001421}

    if len(sys.argv) == 6:
        LoadKeywordlist(sys.argv[5])

    with open(sys.argv[1], 'r', encoding="utf-8") as csvfile:
        firstline = csvfile.readline()
        delimiter = ','
        if "\t" in firstline:
            delimiter='\t'
        elif "," in firstline:
            delimiter=','

        csvfile.seek(0, 0)
        rows = csv.reader(csvfile, delimiter=delimiter)
        for row in rows:
            rowcounter += 1
            if len(row) == 0:
                csvwriter.writerow({'cat1': '其他问题', 'cat2': '其他'})
            elif len(row) == 1:   #only have one row (keyword), so output the cat1 and cat2
                writecounter += 1
                cat1, cat2 = CatMapping(row[0], cid3)
                csvwriter.writerow({ 'cat1': cat1, 'cat2': cat2})
            elif len(row) == 3:
                writecounter += 1
                sku, Q, A = row
                if Q in KeywordList:
                    cat1, cat2 = ("商品问题", "基础属性")
                    csvwriter.writerow(
                        {'question': Q, 'tag': KeywordList[Q], 'shopid': ShopIDs[brand], 'brand': brand,
                         'cid3': cid3,
                         'anSwer': A, 'cat1': cat1, 'cat2': cat2, 'sku': sku})
                else:
                    logging.warning("This Q is not in KeywordList: {}".format(Q))

            elif len(row) == 9:
                if row[5] == "1" and row[6] != "1" and row[7] != "1" and row[4] != "1":
                    writecounter += 1
                    cat1, cat2 = CatMapping(row[1], cid3)
                    csvwriter.writerow({'question': row[2], 'tag': row[1], 'shopid': ShopIDs[brand] , 'brand': brand, 'cid3': cid3,
                                     'anSwer': row[3], 'cat1': cat1, 'cat2': cat2})
            else:
                logging.error("Wrong format: there are {} columns in this line {} \n{}".format(len(row), rowcounter, row))
    csvfile2.close()
    logging.info("Read {} lines; Wrote {} lines".format(rowcounter, writecounter))
