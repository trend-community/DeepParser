#!/usr/bin/python3

#Import graphInfo.txt into SQLite db
#AttributeList: ID, AttrName;
#ValueList: ID, Value;
#ProductAttribute: ProductID, AttrID, ValueID

#create table AttributeList (ID INTEGER PRIMARY KEY AUTOINCREMENT, AttrName TEXT UNIQUE);
#create table ValueList (ID INTEGER PRIMARY KEY AUTOINCREMENT, Value TEXT UNIQUE);
#create table ProductAttribute (ProductID INT, AttrID INT, ValueID INT);

import sqlite3, logging, re

DBCon = None
DBCon = sqlite3.connect('KGAttribute.db')
cur = DBCon.cursor()

productid = 0
with open("graphInfo.txt", encoding='utf-8') as dictionary:
    cur.execute("delete from ProductAttribute")
    for line in dictionary:
        try:
            _, attributes, values = re.split("\"  \"", line.strip())
            if not values:
                continue
            attrs = [x.strip('\"') for x in attributes.split(",")]
            vs = [x.strip('\"') for x in values.split(",")]

            for a in attrs:
                strsql = "INSERT OR IGNORE into AttributeList (AttrName) values( ? ) "
                #logging.warning(strsql)
                cur.execute(strsql, [a])

            for v in vs:
                strsql = "INSERT OR IGNORE into ValueList (Value) values( ? ) "
                cur.execute(strsql, [v])

            for i in range(len(attrs)):
                strsql = "INSERT into ProductAttribute values (?, " \
                        + " (select ID from AttributeList where AttrName=?), " \
                        + " (select ID from ValueList where Value=?) ) "
                cur.execute(strsql, [productid, attrs[i], vs[i]])

            productid += 1
        except ValueError:
            logging.error("Failed to split line:" + line)
cur.close()
DBCon.commit()
DBCon.close()
