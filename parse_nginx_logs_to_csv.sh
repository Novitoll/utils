#!/usr/bin/env bash

set -e

main_dir=$1

function parse_log()
{
	local log=$1
	local csv=$2.csv

	echo -e "[ ] Parsing ----- $log"
	# slice log per detail position. Also process some parts:
	# $1 - ip
	# $4$5 - datetimetimezone
	# $9 - http code
	# $10/1048576 - http request payload size divided to Megabyte
	# $11 - referrer
	# $7 - video slug from HTTP request URL

	# - divide chunk size to Megabyte (1048576)
	# - delete trash in GET URL and leave the video slug between /video/file/<slug>/mp4/*	
	# - delete routes after hostname in referrer
	# - delete brackets, doublq-quoates
	sliced=$(gawk '{ print $1","$4 $5","$9","$10/1048576","$11","$7 }' $log | sed -e 's/\/video\/file\///' -e 's/\/mp4.*//' -e 's/\.com.*"/.com/' -e 's/"//' -e 's/\[//' -e 's/\]//') || echo "[-] Error on $log"
	echo -e "$sliced" >> $csv || echo "[-] Can not write to $csv for $log"
}

for f in $main_dir/*.tar.bz2; do
	dir_name="${f%.tar.bz2}"
	result_csv=$(basename $dir_name)

	echo "[ ] $result_csv"

	mkdir $main_dir/tmp_$result_csv

	# temp vars
	tmp_dir=$main_dir/tmp_$result_csv
	log_dir="$tmp_dir/nginx*"

	tar -xjf $f -C $tmp_dir  # decompress to temp dir

	access_log_files=`ls $log_dir`

	# move decompressed results with conditions to output dir
	# condition 1. move only access logs
	for log in $access_log_files/access*; do
		if [[ $log != *"access"* ]] && [[ $log == *"error"* ]] && [[ $log != *"debug"* ]]; then
			echo "[ ] Skipping $log_dir/$log.."
			continue
		fi

		if [ ! -f $log_dir/$log ]; then
			echo "[ ] Skipping $log_dir/$log.."
			continue
		fi

		# condition 2. if logfile is archive, then decompress it
		case $log in
			*.gz)
				gzip -d $log_dir/$log
				parse_log $log_dir/"${log%.gz}" $result_csv;;
			*)
				parse_log $log_dir/$log $result_csv;;
		esac
		echo "[+] OK"
	done

	echo -e "[+] $result_csv - Done\n"
done

exit $?