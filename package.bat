@echo off

rd /s /q dist
python \python27\pyinstaller-4c90fa4\pyinstaller.py thievery.py
xcopy /s /k /i data dist\thievery\data
copy readme.txt dist\thievery
copy \src\avbin\v5\avbin.dll dist\thievery
md dist\thievery\src
copy *.py dist\thievery\src
