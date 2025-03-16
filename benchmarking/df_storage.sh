#!/bin/zsh



echo "[neo4j]\n $(df -kT /var/lib/neo4j/data/databases/neo4j)"
echo "[sqlite]\n $(df -kT /home/annie/django-ecommerce/django-ecommerce/db.sqlite3)"
