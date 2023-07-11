#!/bin/bash
rm -rf dist
/home/chris/bin/pyinstaller-1.5.1/pyinstaller.py thievery.py
cp -RPpv data dist/thievery
cat readme.txt |tr -d '\r' >dist/thievery/readme.txt
cp -RPpv /usr/lib/libavbin.so* dist/thievery
find dist/thievery -name '*~' |xargs rm
chmod a-x dist/thievery/*.so*
rm dist/thievery/gdiplus.dll

pushd dist
tar cvzf thievery-linux2.tgz thievery

mkdir thievery-source
cd thievery-source
cp -RPpv ../../data .
cp ../../*.py .
cp ../../readme.txt .
find . -name '*~' |xargs rm
cd ..
tar cvzf thievery-source2.tgz thievery-source
popd

mv dist/*.tgz .
