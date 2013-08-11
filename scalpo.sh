#!/bin/sh

host=${HOST:-localhost}
port=${PORT:-8080}
jettyhome=${JETTYHOME:-jetty}
solrhome=${SOLRHOME:-$PWD}

case "$1" in
    jetty)
	cd $jettyhome && java -Djetty.port=$port -Dsolr.solr.home="$solrhome/solr" -jar start.jar
	;;
    crawl)
	scrapy crawl "$2" -o "$2.json" -t json
	;;
    index)
	curl "http://$host:$port/solr/scalpo/update?wt=json" --data-binary @"$2.json" -H 'Content-type:application/json'
	curl "http://$host:$port/solr/scalpo/update?softCommit=true"
	;;
    delete-remacle-indexes)
	curl "http://$host:$port/solr/scalpo/update?wt=json" --data-binary '{"delete":{"query":"ubuntu AND url:\"remacle.org\""}, "commit":{}}' -H 'Content-type:application/json'
	;;
    *)
	echo "Usage: scalpo.sh jetty|index|crawl [source]"
	;;
esac
