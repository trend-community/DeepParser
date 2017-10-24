#!/bin/sh

for ((i=6000;i<=6010;i++));
do
  python RestfulService.py $i > ../log/restfulservice.log &

done