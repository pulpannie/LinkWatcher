#!/bin/zsh



echo "[neo4j]\n $(du -bc /var/lib/neo4j/data/)"
echo "[neo4j data]\n $(du -bc /var/lib/neo4j/data/databases/neo4j/*store.db*)"
echo "[neo4j logs]\n $(du -bc /var/log/neo4j/)"
#echo "[neo4j?]\n $(du -bc /home/annie/django-ecommerce/django-ecommerce)"
echo "[sqlite]\n $(du -bc ~/django-ecommerce/StackOverFlow--Clone/db.sqlite3)"
