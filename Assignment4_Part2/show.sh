#!/bin/bash
awk -v n="$2" 'BEGIN{b=1} /SCREENSHOT NOW/{b++; next} b==n && !/^=====/ && NF' "$1"
