#!/bin/bash

path=$(pwd)

echo "7z-JTR Decrypt Script";
if [ $# -ne 2 ];then
	echo "Usage $0 <7z> <wordlist>";
	exit;
fi

JTR_OPTS="--wordlist=$2 --rules --stdout"

count=0
for i in $(john $JTR_OPTS);do
        let count++
	echo -ne "\n[$count] trying \"$i\" \n" 
	7z x -p$i $1 > /dev/null 2>&1 
	STATUS=$?
	if [ $STATUS -eq 0 ]; then
		echo -e "\nArchive password is: \"$i\"" 
		break
	else
          rm $path/123.txt
        fi
done
