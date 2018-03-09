#!/usr/bin/python3

#Import graphInfo.txt into SQLite db
#AttributeList: ID, AttrName;
#ValueList: ID, Value;
#ProductAttribute: ProductID, AttrID, ValueID

#create table AttributeList (ID INTEGER PRIMARY KEY AUTOINCREMENT, AttrName TEXT , AttrTypeID INT, CONSTRAINT attrtype UNIQUE(AttrName, AttrTypeID) );
#create table ValueList (ID INTEGER PRIMARY KEY AUTOINCREMENT, Value TEXT UNIQUE);
#create table ProductAttribute (ProductID INT, AttrID INT, ValueID INT);
#create table AttributeType (ID INTEGER PRIMARY KEY AUTOINCREMENT, AttrType TEXT UNIQUE);

import sqlite3, logging, re

DBCon = sqlite3.connect('KGInfo.db')
cur = DBCon.cursor()

productid = 0
with open("graphInfo.txt", encoding='utf-8') as dictionary:
    cur.execute("delete from ProductAttribute")
    for line in dictionary:
        try:
            _, attributes, values = re.split("\"  \"", line.strip())
        except ValueError:
            logging.error("Failed to split line:" + line)
            continue
        if not values:
            continue
        attrs = [x.strip('\"') for x in attributes.split(",")]
        vs = [x.strip('\"') for x in values.split(",")]

        pair = {}
        for i in range(len(attrs)):
            pair[attrs[i]] = vs[i]

        if not pair['name']:
            logging.warning("There is no name in this line: " + line)
            continue
        #Attribute Type "name"
        strsql = "INSERT OR IGNORE into AttributeType (AttrType) values(?)"
        cur.execute(strsql, [pair['name']])
        strsql = "SELECT ID from AttributeType where AttrType=? limit 1"
        cur.execute(strsql, [pair['name']])
        attrtypeidlist = cur.fetchall()
        attrtypeid = attrtypeidlist[0][0]

        for a in attrs:
            if a == "name":
                continue
            strsql = "INSERT OR IGNORE into AttributeList (AttrName, AttrTypeID) values( ?, ? ) "
            #logging.warning(strsql)
            cur.execute(strsql, [a, attrtypeid])

        for v in vs:
            strsql = "INSERT OR IGNORE into ValueList (Value) values( ? ) "
            cur.execute(strsql, [v])

        for i in range(len(attrs)):
            strsql = "INSERT into ProductAttribute values (?, " \
                    + " (select ID from AttributeList where AttrName=?), " \
                    + " (select ID from ValueList where Value=?) ) "
            cur.execute(strsql, [productid, attrs[i], vs[i]])

        productid += 1


#create table ShopList (ID INTEGER PRIMARY KEY AUTOINCREMENT, ShopName TEXT  UNIQUE );
with open("Shops.txt", encoding='utf-8') as dictionary:
    for line in dictionary:
        try:
            _, attributes, values = re.split("\"  \"", line.strip())
        except ValueError:
            logging.error("Failed to split line:" + line)
            continue
        if not values:
            continue
        attrs = [x.strip('\"') for x in attributes.split(",")]
        vs = [x.strip('\"') for x in values.split(",")]

        pair = {}
        for i in range(len(attrs)):
            pair[attrs[i]] = vs[i]

        if not pair['shop_name']:
            logging.warning("There is no shop_name in this line: " + line)
            continue
        #Attribute Type "name"
        strsql = "INSERT OR IGNORE into ShopList (ShopName) values(?)"
        cur.execute(strsql, [pair['shop_name']])



#create table BrandList (ID INTEGER PRIMARY KEY AUTOINCREMENT, BrandName_en TEXT  , BrandName_cn TEXT , CONSTRAINT brandname UNIQUE (BrandName_cn, BrandName_en) );
with open("Brands.txt", encoding='utf-8') as dictionary:
    for line in dictionary:
        try:
            _, attributes, values = re.split("\"  \"", line.strip())
        except ValueError:
            logging.error("Failed to split line:" + line)
            continue
        if not values:
            continue
        attrs = [x.strip('\"') for x in attributes.split(",")]
        vs = [x.strip('\"') for x in values.split(",")]

        pair = {}
        for i in range(len(attrs)):
            pair[attrs[i]] = vs[i]

        if not pair['barndname_cn']:
            logging.warning("There is no barndname_cn in this line: " + line)
            continue
        #Attribute Type "name"
        strsql = "INSERT OR IGNORE into BrandList (BrandName_en, BrandName_cn) values(?, ?)"
        cur.execute(strsql, [pair['barndname_en'], pair['barndname_cn']])


cur.close()
DBCon.commit()
DBCon.close()
