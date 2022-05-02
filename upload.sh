#!/bin/bash

echo WARNING!! Please make sure you have bumped the version number in the setup.cfg file!
echo Continuing in 2 seconds...
sleep 2
rm dist/*
python3 -m build
echo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
echo ENTER YOUR PASSWORD NOW
echo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
twine upload dist/*