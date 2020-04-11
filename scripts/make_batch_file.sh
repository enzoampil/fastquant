#!/usr/bin/env/sh

intput='../data/stocklist.txt'
output='get_disclosures'
start_dt='1-1-2015'
#end_date = None
#get first column=stock symbols; iterate per row
awk '{print $1}' ../data/stocklist.txt | while read symbol; do echo ./get_disclosures $symbol -t1 $start_dt -v; done > $output'.batch'
echo 'Saved: '$output'.batch'
echo 'Run: cat '$output'.batch | parallel 2>&1 | tee '$output'.log'
