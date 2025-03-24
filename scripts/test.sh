#!/bin/bash
set -e

rm -rf do-not-commit
rm -rf artefacts
mkdir -p do-not-commit/some-git-repo
cd ./do-not-commit/some-git-repo
git init
touch README.md
git add README.md
for n in $(seq 1 101)
do
  echo "$n"
  echo "$n " >> README.md
  git commit -am "Add line $n to README.md"
done

cd ../..

./scripts/run-on-commit-history.sh  --script=./scripts/count-words-in-readme.sh --repo=./do-not-commit/some-git-repo --max-commits=3

cat artefacts/metadata.json
cat artefacts/metadata.json | grep "Add line 101"
cat artefacts/metadata.json | grep "Add line 50"
cat artefacts/metadata.json | grep "Add line 1"
