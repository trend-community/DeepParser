import os, sys, csv, logging

def CatMapping(keyword):
    #mapping={}
    mapping = {("商品问题", "基础属性") :
                    ["型号", "制冷", "功能", "控制", "空气开关", "什么功能", "冷暖", "外机", "定频 | 变频", "遥控器", "扫风方式", "匹数", "大匹", "制冷类型", "定频区别", "清洁", "自动清洁", "清洁功能", "度电", "省电", "耗电", "几度电", "电", "耗电量", "适用面积 | 适用面积", "平方", "效果", "wifi"],

                ("活动优惠", "商品价格"):
                    ["价格", "便宜", "费用", "前", "降价", "价", "什么价格"],

                ("活动优惠", "活动咨询"):
                    ["优惠", "赠品", "活动", "什么优惠", "送", "什么活动", "优惠券", "减", "优惠活动", "什么赠品", "价格优惠", "买优惠", "礼品", "活动搞"],

                ("购买方式","下单问题"):
                    ["货到付款", "买", "收费", "下单", "现货", "质保", "质量", "白条"],

                ("物流问题", "配送工作时间"):
                    ["发货", "到货", "送货", "送到"],

                ("物流问题","送货上门"):
                    ["送货上门"],

                ("政策问题", "价保条件"):
                    ["保价"],

                ("政策问题", "发票问题"):
                    ["发票开", "发票"],

                ("政策问题", "联系方式"):
                    ["联系", "电话"],

                ("政策问题", "保修返修及退换货政策"):
                    ["保修", "售后", "退货", "退"],

                ("政策问题", "家电安装"):
                    ["安装费用", "安装", "装", "安装来", "时间安装", "安装师傅", "安装送货", "预约", "高空作业", "明天安装", "安装预约", "送货安装", "支架", "外机支架"],

                ("政策问题", "库存状态"):
                    ["没货"]
    }

    for m in mapping:
        if keyword in mapping[m]:
            return m

    return "other", "other"



if __name__ == "__main__":

    if len(sys.argv) < 5:
        print(
            "Usage: python3 qa_converttoimport.py  [inputfile] [outputfile] [cid3] [brand]")
        exit(1)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

    csvfile2 = open(sys.argv[2], 'w', encoding="utf-8")
    fieldnames = ["question", "tag","shopid", "brand", "cid3", "sku", "anSwer", "cat1",
                  "cat2", "profession", "source"]
    csvwriter = csv.DictWriter(csvfile2, fieldnames=fieldnames)
    csvwriter.writeheader()

    brand = sys.argv[4] #美的
    cid3 = sys.argv[3]  #空调/冰箱
    rowcounter = 0
    writecounter = 0

    with open(sys.argv[1], 'r', encoding="utf-8") as csvfile:
        rows = csv.reader(csvfile)
        for row in rows:
            rowcounter += 1
            if row[5] == "1" and row[6] != "1" and row[7] != "1" and row[4] != 1:
                writecounter += 1
                cat1, cat2 = CatMapping(row[1])
                csvwriter.writerow({'question': row[2], 'tag': row[1], 'brand': brand, 'cid3': cid3,
                                 'anSwer': row[3], 'cat1': cat1, 'cat2': cat2})

    csvfile2.close()
    logging.info("Read {} lines; Wrote {} lines".format(rowcounter, writecounter))
