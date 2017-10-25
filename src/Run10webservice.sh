#!/bin/bash

for ((i=6000;i<=6030;i++));
do
  nohup python RestfulService.py --thisport $i 2>&1 > ../log/restfulservice.log &

done