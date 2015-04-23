# gen_xcassets

Python script to automatically generate assets catalog for Xcode project.

## Example

	gen_xcassets -d pictures/ -o tmpout/

This will scan the folder `pictures` recursively, and create assets catalog for all found png files. The results will be saved in folder `tmpout`.

## Details

- Put all @3x png files into a folder.
- Name the png files, the name will used as the "code name" in your code.
- call `gen_xcassets.py`.
- The generated results are actually some folders which name ends with `.imageset`. That format is recorgnized by Xcode.
- Drag the generated `imageset` folders to your `.xcassets` folder in your project. Xcode will know them.

## check_xcassets.py

This is used to check the integrality of `*.xcassets`. If @3x images exist but missing @2x images, invoke `gen_xcassets.py` to fix it.

## behind the scenes

The `gen_xcassets` actually call `sips` to scale @3x image to @2x size.

## Prerequisites

Python 2.7
