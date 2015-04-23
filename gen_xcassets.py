#!/usr/bin/python

#
# Created by Albert Zhang on 1/1/15.
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
    print "\n"
    print "--------------------------------------------------------------------------"
    print "[gen_xcassets.py]"
    print "    Automatically generate the assets catalog (*.xcassets) for Xcode."
    print "    You specify a source folder, this script will scan all PNG files"
    print "    in it and create images for all of them in the format of xcassets."
    print "    The PNG files' name will used in the generated results, and all"
    print "    [^0-9a-zA-Z] chars will be replaced by '-'"
    print "\n"
    print "Syntax:"
    print "    gen_xcassets.py [-h] -d <dir_to_scan> -o <output_dir>"
    print "\n"
    print "The generated results will be saved in the directory specified,"
    print "under the working directory."
    print "--------------------------------------------------------------------------"
    print "\n"
    quit()
#    raw_input("Press Enter to continue, or Ctlr-C to abort if you are not ready ...")



if dirIndex < 0 or dirIndex >= arglen:
    print "\nSyntax error: No source dir specified.\n"
    quit()

if outIndex < 0 or outIndex >= arglen:
    print "\nSyntax error: No output dir specified.\n"
    quit()



currentDir = sys.argv[dirIndex]
outputDir = sys.argv[outIndex]


totalSuccess = 0
totalFailed = 0
totalSkipped = 0


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

def fileNameIsPNG(fn):
    print "----------------------------------------------------------------------------\n["+ fn + "]"
    
    isPNG = False
    fnLen = len(fn)
    if fnLen > 4: # > x.png
        fext = fn[fnLen-4:fnLen]
        if fext == ".png":
            isPNG = True
    return isPNG

def fileSize(fp):
    statinfo = os.stat(fp)
    sz = statinfo.st_size
    return sz


def getImagePropertyIntViaSips(fp, prop):
    sipsOut = subprocess.check_output(["sips", "-g", prop, fp])
    sipsOutLines = re.split(r"[\r\n]", sipsOut)
    if len(sipsOutLines) >= 2:
        sipsOutLine2 = sipsOutLines[1]
        if string.find(sipsOutLine2, prop) != -1:
            propVal = int(re.sub(r"[^0-9]", "", sipsOutLine2))
            return propVal
    raise Exception("Unable to get property "+ prop)


def resizeImageViaSips(fp, w, h):
    fnull = open(os.devnull, 'w')
    subprocess.check_call(["sips", "-z", str(h), str(w), fp], stdout=fnull)


def reducePNGViaPngquant(fp):
    fnull = open(os.devnull, 'w')
    subprocess.check_call(["pngquant", "--force", "--speed", "1", "--output", fp, fp], stdout=fnull)


def handlePNGFile(fp):
    fn = os.path.basename(fp)
    fnfixNoExt = re.sub(r"[^0-9a-zA-Z]", "-", fn[0:len(fn)-4])
    
    outDir = outputDir +"/"+ fnfixNoExt +".imageset"
    rmdir_e(outDir)
    mkdir_p(outDir)
    
    outJSONFilePath = outDir +"/Contents.json"
    
    outBaseFileName = "f"+ str(random.randint(100, 100000))
    out3xFileName = outBaseFileName +"3x.png"
    out2xFileName = outBaseFileName +"2x.png"
    out3xFilePath = outDir +"/"+ out3xFileName
    out2xFilePath = outDir +"/"+ out2xFileName
    
    shutil.copyfile(fp, out3xFilePath)
    
    orgSz = fileSize(out3xFilePath)
    
    reducePNGViaPngquant(out3xFilePath)
    
    fnlSz = fileSize(out3xFilePath)
    reducePerc = 100
    if orgSz != 0:
        reducePerc = int(float(fnlSz) / orgSz * 100)
    print "size: "+ str(orgSz) +" => "+ str(fnlSz)  +" ("+ str(reducePerc) +"%)"
    
    shutil.copyfile(out3xFilePath, out2xFilePath)
    
    png3xW = getImagePropertyIntViaSips(out3xFilePath, "pixelWidth")
    png3xH = getImagePropertyIntViaSips(out3xFilePath, "pixelHeight")
    
    png2xW = int(png3xW * 0.66666666667);
    png2xH = int(png3xH * 0.66666666667);
    
    if png2xW < 1:
        png2xW = 1
    if png2xH < 1:
        png2xH = 1
    
    resizeImageViaSips(out2xFilePath, png2xW, png2xH)
    print "dimension: "+ str(png3xW) +":"+ str(png3xH) +" => " +str(png2xW) + ":"+ str(png2xH)
    
    JSONTemplate = '''{
  "images" : [
    {
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "idiom" : "universal",
      "scale" : "2x",
      "filename" : "<2xName>"
    },
    {
      "idiom" : "universal",
      "scale" : "3x",
      "filename" : "<3xName>"
    }
  ],
  "info" : {
    "version" : 1,
    "author" : "xcode"
  }
}'''
    jsonVal = string.replace(JSONTemplate, "<3xName>", out3xFileName)
    jsonVal = string.replace(jsonVal, "<2xName>", out2xFileName)
    with codecs.open(outJSONFilePath, 'w', encoding='utf8') as f:
        f.write(jsonVal)


def scanPNGFilesInDir(targetDir, level=0):
    global totalSuccess
    global totalFailed
    global totalSkipped
    
    printPrefix = "    " * level
    #print "\n"+ printPrefix +">>>>>>"+ targetDir
    files = os.listdir(targetDir)
    for fn in files:
        fp = targetDir +"/"+ fn
        #print printPrefix +"=> "+ fn
        if os.path.isdir(fp):
            #print printPrefix +"    -> DIR: "+ fn
            scanPNGFilesInDir(fp, level + 1)
        else:
            if fileNameIsPNG(fn):
                try:
                    handlePNGFile(fp)
                    totalSuccess += 1
                except Exception as ex:
                    print "***ERROR: ", ex
                    totalFailed += 1
            else:
                totalSkipped += 1
    pass


print "\n"
print "Scanning directory ["+ currentDir +"] ....\n\n"
scanPNGFilesInDir(currentDir)

print "\nDone"
print "success: "+ str(totalSuccess) +", failed: "+ str(totalFailed) +", skipped: "+ str(totalSkipped)
print "\n"
print "Note: even if the failed is 0, you should also to check the error message above."
print "\n"

