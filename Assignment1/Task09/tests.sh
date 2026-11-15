#!/bin/bash
# Functional and failure tests for the university API (run while it is up on port 8000)
U=http://localhost:8000
t() { echo "\$ $*"; "$@" -s -w ' [HTTP %{http_code}]\n'; echo; }
t curl $U/health
t curl $U/api/results/S1001
t curl $U/api/results/S9999
t curl $U/api/fees/S1001
t curl -X POST -H 'Content-Type: application/json' -d '{"regno":"S1001","amount":15000}' $U/api/fees/pay
t curl -X POST -H 'Content-Type: application/json' -d '{"regno":"S1001","amount":-5}' $U/api/fees/pay
t curl "$U/api/library/search?q=cloud"
t curl $U/nothing
