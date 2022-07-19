SkeletonGameDMD is a fork of [PyProcGameHD-SkeletonGame](http://skeletongame.com/) which is itself a fork of [pyprocgame](http://pyprocgame.pindev.org/).

pyprocgame is a Python-based programming framework that can be used to code custom rules for pinball machines powered by either the P-ROC or P3-ROC, available from [Multimorphic](https://www.multimorphic.com/)

PyProcGameHD-SkeletonGame augments pyprocgame with support for traditional PC display hardware (i.e., LCD) for high-resolution, full-color display via SDL2/OpenGL based hardware acceleration (PyProcGameHD) and tries to reduce the amount of code you have to write to create a new game with 'typical components' (via SkeletonGame). Traditional DMD screens are no longer supported.

SkeletonGameDMD keeps all features of PyProcGameHD-SkeletonGame and adds back support for monochome DMD screens driven by the P-ROC.

Please see the [Official PyProcGameHD/SkeletonGame website](http://skeletongame.com/) site for the all-in-one installer, programming help, and assorted documentation.

## DMD Support

To enable the display on the DMD driven by the P-ROC controller, set the following options in config.yaml

    ```
    proc_dmd: True
    dmd_dots_w: 128
    dmd_dots_h: 32
    ```

See ./EmptyGameDMD for an example of very simple game using a physical monochrome DMD driven by the P-ROC controller, from which to start a new game.
In particular, EmptyGameDMD shows how to configure the lower resolution ScoreDisplay and a very simple attract mode formatted for the size of the DMD.


## License

SkeletonGameDMD is Copyright (c) 2022 Clement Pellerin
Content unchanged from PyProcGameHD-SkeletonGame remain Copyright (c) 2014-2015 Michael Ocean and Josh Kugler
Content unchanged from PyProcGame remain Copyright (c) 2009-2011 Adam Preble and Gerry Stellenberg

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
