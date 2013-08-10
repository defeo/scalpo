#!/bin/sh

port=8080
jettyhome=jetty
wd=$PWD

case "$1" in
    jetty)
	cd $jettyhome && java -Djetty.port=$port -Dsolr.solr.home="$wd/solr" -jar start.jar
	;;
    crawl)
	scrapy crawl "$2" -o "$2.json" -t json
	;;
    index)
	curl "http://localhost:$port/solr/remacle/update?wt=json" --data-binary @"$2.json" -H 'Content-type:application/json'
	curl "http://localhost:$port/solr/remacle/update?softCommit=true"
	;;
    *)
	echo "Usage: scalpo.sh jetty|index|crawl [source]"
	;;
esac
