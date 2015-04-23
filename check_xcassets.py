#!/usr/bin/python

#
# Created by Albert Zhang on 4/10/15.
# Copyright (c) 2015 Albert Zhang. All rights reserved.
#

import os
import sys
import errno
import string
import subprocess
import re
import shutil
import random
import codecs
import json


isShowHelp = False
dirIndex = -1
outIndex = -1

for index, value in enumerate(sys.argv):
    if value in ['-h', '--help']:
        isShowHelp = True
    elif value == '-d':
        dirIndex = index + 1
    elif value == '-o':
        outIndex = index + 1

arglen = len(sys.argv)


if isShowHelp:
    print "--------------------------------------------------------------------------"
    print 'This script is used to check the missing @2x images in xcassets,'
    print 'and if the @3x image exist, fix them by invoking gen_xcassets.py'
    print "\n"
    print "Syntax:"
    print "    check_xcassets.py [-h] -d <dir_to_scan> -o <output_dir>"
    print "\n"
    print "If there is any fix happen, the generated results will be saved in the "
    print "directory specified, under the working directory."
    print "--------------------------------------------------------------------------"
    print "\n"
    quit()


if dirIndex < 0 or dirIndex >= arglen:
    print "\nSyntax error: No source dir specified.\n"
    quit()

if outIndex < 0 or outIndex >= arglen:
    print "\nSyntax error: No output dir specified.\n"
    quit()



xcassetsDir = sys.argv[dirIndex]
tmpOutputDir = sys.argv[outIndex]
tmpCopiedDir = tmpOutputDir +'/tmp_4_copy'

files = os.listdir(xcassetsDir)

fixedCount = 0
cannotfixCount = 0
goodCount = 0

fnull = open(os.devnull, 'w')


def mkdir_p(path):
    # http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise

def rmdir_e(path):
    if os.path.exists(path):
        shutil.rmtree(path)


for fn in files:
    #print fp
    fnLen = len(fn)
    if fnLen > 9: # length of '.xcassets' is 9
        last9 = fn[fnLen-9:fnLen]
        astName = fn[0:fnLen-9]
        #print last9
        if last9 == '.imageset':
            astDirP = xcassetsDir +'/'+ fn
            jsonp = astDirP +'/Contents.json'
            file2x = ''
            file3x = ''
            contentsJson = json.load(open(jsonp))
            for img in contentsJson[u'images']:
                try:
                    scl = img[u'scale']
                    if scl == u'2x':
                        file2x = img[u'filename']
                    if scl == u'3x':
                        file3x = img[u'filename']
                except Exception as ex:
                    pass

            file3xP = ''
            file2xP = ''

            if len(file3x) > 0:
                file3xP = astDirP +'/'+ file3x
            if len(file2x) > 0:
                file2xP = astDirP +'/'+ file2x

            if not os.path.exists(file3xP):
                file3x = '' # set to empty to indicate the file missing
            if not os.path.exists(file2xP):
                file2x = '' # set to empty to indicate the file missing

            if len(file2x) > 0 and len(file3x) > 0:
                # we are good
                print '- [   Good   ] '+ astName
                goodCount += 1
            else:
                # missing something
                if len(file3x) == 0:
                    print '- [Missing 3x] '+ astName +' ................... cannot fix'
                    cannotfixCount += 1
                else:
                    print '- [Missing 2x] '+ astName +' ................... fixing ....'
                    rmdir_e(tmpCopiedDir)
                    mkdir_p(tmpCopiedDir)

                    copiedFp = tmpCopiedDir +'/'+ astName +'.png'
                    shutil.copyfile(file3xP, copiedFp)
                    subprocess.check_call(['gen_xcassets.py', '-d', tmpCopiedDir, '-o', tmpOutputDir], stdout=fnull)
                    print '---- * fixed '+ astName
                    fixedCount += 1

rmdir_e(tmpCopiedDir)

print "\n"
print "Good: "+ str(goodCount) +", fixed: "+ str(fixedCount) +", cannot fix: "+ str(cannotfixCount) +"\n"
print "Note: you must manually copy the fix results from ["+ tmpOutputDir +"]"
print "\n\n"
