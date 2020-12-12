if [ $# -lt 1 ]; then
   FILE=buildout.cfg
else
   FILE=$1
fi
[ ! -f bin/pip ] && virtualenv .
bin/pip install --upgrade pip setuptools==33.1.1  zc.buildout==2.12.0
bin/buildout -c $FILE annotate | tee annotate.txt | grep -E 'setuptools *= *[0-9][^ ]*|zc.buildout *= *[0-9][^ ]*'| sed 's/= /==/' > requirements.txt
#cat annotate.txt
cat requirements.txt
bin/pip install --upgrade -r requirements.txt
