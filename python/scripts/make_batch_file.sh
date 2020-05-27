#!/usr/bin/env/sh

# This creates a batch script that
# downloads disclosures data and saves .csv & .png

input='../data/bluechips.txt'
output='bluechips'
start_dt='1-1-2019'
#end_date = None
#get first column=stock symbols; iterate per row
awk '{print $1}' $input | while read symbol; do echo ./get_disclosures $symbol -t1 $start_dt -v -s; done > $output'.batch'
echo 'Saved: '$output'.batch'
echo 'Run: cat '$output'.batch | parallel 2>&1 | tee '$output'.log'
