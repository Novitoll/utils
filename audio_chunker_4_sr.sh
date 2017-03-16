#!/bin/bash
# Requirement: install ffmpeg (https://www.ffmpeg.org/)
# Example: ./audio_chunker_4_sr.sh 10 my_video.mp4 flac
# Output: my_video_part_0.flac my_video_part_1.flac .. my_video_part_n.flac, where n = duration / defined threshold

threshold=$1  # seconds
file=$2
target_format=$3
sample_rate=$4
channels=$5

duration=`ffprobe -i $file -show_entries format=duration -v quiet -of csv="p=0" | awk '{ rnd=sprintf("%.0f", $1); print rnd }'`

parts_amount=$((duration / threshold))
remainder=$((duration % threshold))

if ((remainder > 0)); then
    ((parts_amount+=1))
fi

for ((i=0;i<=$parts_amount;i++)); do
    ffmpeg -i $file -ss $((i * threshold)) -t $threshold -ar ${sample_rate:-16000} -ac ${channels:-1} ${file%.*}_part_${i}.$target_format
done