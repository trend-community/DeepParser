#!/bin/sh

for ((i=5002;i<=5062;i++));
do
  python RestfulService.py $i

done