This codebase exists for folks looking to code their own rules for pinball machines powered by either the P-ROC or P3-ROC, available from [pinballcontrollers.com](http://pinballcontrollers.com).  This framework is a fork of [PyProcGame](http://www.github.com/preble/pyprocgame), a Python based pinball programming framework.  Rather than traditional DMD hardware, it supports traditional PC display hardware (i.e., LCD) for high-resolution, full-color display via SDL2/OpenGL based hardware acceleration (PyProcGameHD) and tries to reduce the amount of code you have to write to create a new game with 'typical components' (via SkeletonGame).

The code, documentation, and this page itself are a work in progress.  Please bear with me.  Please report bugs, issues, problems, etc.  Either use the GitHub issue tracker, or go to the thread on the PinballControllers forum, [here](http://www.pinballcontrollers.com/forum/index.php?topic=1500.0).  

Thank you.  

![screenshot](https://dl.dropboxusercontent.com/u/254844/pyprocgamehd.png)

#  PyProcGame-HD + SkeletonGame
## Contents: ##

* [Overview](#overview)
* [Installation](#installation)
* [SkeletonGame](#skeletongame-big-picture)
* [Event Flow, theory, etc.](#game-event-flow)
* [Getting Started with SkeletonGame](#getting-started)
* [Change Log](#change-log)

# Overview
## PyProcGame-HD
A fork of PyProcGame, meant to replace PyProcGame for users who wish to create LCD-based PyProcGame games that are powered by a P-ROC.

Traditional DMD support has been removed in favor of supporting LCD displays. This version enables full-color frames (with alpha and per-pixel alpha transparency) running resolutions far in excess of 128x32.  Hardware requirements are moderate if OpenGL hardware acceleration is available.

This release replaces the previous HD VGA fork of PyProcGame and it's functionality is a superset of that version.  It has been re-written (and aggressively optimized) to leverage SDL2 (OpenGL) graphics hardware acceleration features.  Many things are now possible with nominal overhead, including 'dot-filter', alpha transparency, per-pixel alpha, just to name a few.  The prior PyGame-based version is available for those who might need it for some reason or another.

Note: If you wish to have projects running on different versions of PyProcGame, the easiest way is to just include the appropriate version of PyProcGame's procgame folder as a subfolder named procgame in your game folder.

A Display Architecture Tutorial for both PyProcGameHD specifics and PyProcGame, in general, is provided [here](http://mjocean.github.io/PyProcGameHD-SkeletonGame/DMD_Tutorial.html).


## SkeletonGame

SkeletonGame is a collection of classes to speed up new game development that is also included (and maintained) as part of this release.  If you are a new P-ROC developer, you should strongly consider using it.  

SkeletonGame is a logical extension of the BasicGame class --it is a bunch of additions to pyprocgame (many of which lifted from the JD sample game).  The idea being that most games all have the same core functionality, and that you shouldn't need to code those things.

If SkeletonGame works, it means you (as the programmer) should:

- have VERY few lines of code in your game class.
- spend most of your time coding the logic for *modes*.
- be able to leverage fairly standard modes that have been written before.
- use helpers to create DMD content (in code) much easier.
- get started quickly.

A Sample game that has been provided, [here](https://github.com/mjocean/PyProcGameHD-SkeletonGame/tree/master/SampleGame)

It leverages everything that those of use who use PyProcGame know and love, and only intends to streamline some things for new users. It should help you make games faster.  If you have an existing PyProcGame project, you may choose to forgo SkeletonGame in order to migrate to the HD Framework with very minimal code changes.

## pyprocgame

Again, this work is built on top of (and would be nothing without) pyprocgame, which is a high-level pinball development framework for use with P-ROC (Pinball Remote Operations Controller).  Pyprocgame was written by Adam Preble and Gerry Stellenberg.  More information about P-ROC is available at [pinballcontrollers.com](http://pinballcontrollers.com/).  See the [pyprocgame site](http://pyprocgame.pindev.org/) for the full pyprocgame documentation.

# Installation

## Prerequisites

pyprocgame requires the following libraries.  Before installing any of these, follow the installation guide, below.

- [Python 2.6](http://python.org/)
- [pypinproc](http://github.com/preble/pypinproc) -- native Python extension enabling P-ROC hardware access and native DMD frame manipulation.
- [setuptools](http://pypi.python.org/pypi/setuptools) -- required for procgame script installation.  Also adds easy\_install, a helpful installer tool for popular Python modules.
- [pyyaml](http://pyyaml.org/) -- YAML parsing.
- One of the Python graphics and sound modules:
  - [pygame](http://www.pygame.org/)
- [Python Imaging Library](http://www.pythonware.com/products/pil/) (PIL)

Additionally, this version requires:
- [SDL2 32bit (only use 64 if you are using the 64bit Python --you probably aren't).](https://www.libsdl.org/download-2.0.php
- [SDL2 TTF (Font support, also 32bit)](http://www.libsdl.org/projects/SDL_ttf/)
- [PySDL2 32-bit (x86)](http://pysdl2.readthedocs.org/en/latest/install.html)
- [PyOSC 0.3.5b-5294.zip](https://pypi.python.org/pypi/pyOSC)
- *Optional:* For MP4 support install OpenCV and libffmpeg

## Installation Guide

1.  Run a ["OneClickInstall"](http://proctools.catster.net/) from Jimmy (note, there is no one-click installer for OSX at this time)
  *test that it worked* --from a command-prompt run ``python`` and run the following instructions:  

```python
import pinproc
import procgame
import pygame
print pinproc.EventTypeBurstSwitchOpen
```

The first three lines should return the prompt with no feedback.  The last should print ``6``.  This is how you know it worked.
*TODO: post debugging instructions.*

2. Install the PyProcGame*HD* SDL2 dependencies.  
	2. Download and install [PySDL2 for your platform]
	(http://pysdl2.readthedocs.org/en/latest/install.html)
	1. Install the 32-bit (x86) versions of the SDL2 and the SDL2_TTF libraries -- 
	For windows, put them in a directory called ``C:\Python26\DLLs\sdl2``.  
  	- [sdl2](https://www.libsdl.org/download-2.0.php)
  	- [sdl2_ttf](http://www.libsdl.org/projects/SDL_ttf/)
	1.  Download and install [pyOSC-0.3.5b-5294.zip](https://pypi.python.org/pypi/pyOSC)
	1.  Either set the PYSDL2_DLL_PATH (as per the instructions, [here](http://pysdl2.readthedocs.org/en/latest/integration.html) or add a ``PYSDL2_DLL_PATH`` in the game's ``config.yaml``.
	1. *Optional:* For MP4 support install OpenCV and libffmpeg

3. Install the SkeletonGame version of PyProcGameHD along-side the One-Click installed pyprocgame.  Download the ZIP of the GitHub project here, and extract it to somewhere other than your existing pyprocgame-master folder (e.g., C:\P-ROC\pyprocgame-hd\).  From a command-prompt within that directory, from the command line run:

```python setup.py develop```

This will install SkeletonGame in 'develop' mode, such that when you import pyprocgame from any python script, it will use this version, from the current location.

	import procgame.game

It will also update the "procgame" command line tool into a system-dependent location.  The updated version works with the color file formats.  On Linux and Mac OS X systems this will probably be in your path such that you can type, from the command line:

	procgame

and see a list of available commands.  If it is not in your path you can invoke it directly, or modify your PATH environment variable.  Note that on Windows the procgame script is typically located in C:\Python26\Scripts.

### *Optional:* the graphical switch tester: ###
The graphical switch tester allows you to use an image of your playfield, layout the buttons and lamps on that image, and then test your machine by interacting with a GUI on top of that image.  

2. Download the switchMatrixClient.py and put it in the main game folder.  
[https://github.com/mjocean/OscSwitchMatrixGUI](https://github.com/mjocean/OscSwitchMatrixGUI)

1. Download/install (wxPython)[http://www.wxpython.org/download.php]  --for windows, this is wxPython3.0-win32-3.0.2.0-py26.exe

3. Run the switch matrix client on the command line as as follows:

```
python switchMatrixClient.py -y config/t2.yaml -p 9000 -i t2_SM.jpg -l t2.layout
```

where:
  * `` config/t2.yaml`` is the path to the machine configuration file
  * ``t2_SM.jpg`` is a playfield image shrunk to fit the screen.
  * ``t2.layout`` is a layout file saved from this tool (the first run will not include this ``-l t2.layout`` argument)


# SkeletonGame: Big Picture
## Overview

Having worked on a few P-ROC projects now, I've tried to distill the common bits from each of those games so that I can avoid rewriting the same lines again and again.  It also tries to organize and automatically handle the flow of the larger 'game' events (game starting, ball starting, ball ending, etc.).

A game class that is subclassed from SkeletonGame should be very short.  The example provided is fewer than 60 lines if you exclude imports, comments and whitespace.  Most of your code should be present in your mode classes, instead.

## SkeletonGame includes: 

- the class ``SkeletonGame`` (which is a subclass of `BasicGame`).  This class will serve as the new superclass for your game. This class includes the following (by default):
    - tracking ball counts, ball time, game counts, game time, loads/saves settings and data
    - assetManager (all your images, sounds, music, fonts, lampshows are pre-loaded by defining a yaml file)
    - a better `Player` class: supports player state tracking built in with appropriate methods for access. 
    - `soundController` mode auto created and loaded 
    - OSC mode auto loaded (though apparently based on an old version..oops)
    - Built-in (already working) trough, ballsave, ballsearch, and tilt/slam tilt modes (all based on Gerry/Adam's versions)
    -  ... a VERY simple attract mode that's based on a simple, yet powerful yaml file/format
    -  ... service mode (basically Adam's) that senses dmd size
    -  ... high score entry (based on Adam's but in color) that senses dmd size
    -  ... high score frame generation for display in attract mode
    -  ... score display essentially based on Adam's but updated to use color fonts, background animations, etc. 
    -  ... bonus helper (just like score: `bonus(tag, quantity)`) and a built-in bonus tally mode that kicks in at the end of the ball and shows any bonuses awarded to the player during their ball
- `dmdHelper` "mode" that generates a message on screen shown over a single image/animation, or a stack of them. It makes using the DMD extremely painless.  It's usage is: ```displayText(text, key)``` 
If key is a list, it builds a grouped layer for all the keys. If text is a list instead of single string, all the text is shown on the frame. A single line is centered vertically, two lines are shown at 1/3, and 2/3, three lines at 1/4,2/4, and 3/4... You get the idea. 
- Automatic state progressions without having to code for it in your game.  No more calls to `start_ball()`, `end_ball()`, etc.  
- A new optional-Mode superclass called `AdvancedMode`;  AdvancedMode offers:
    - a "lifecycle type" (ball, game, system, or custom) --modes are auto added/removed based on that type. They only need to be created by importing them in the game code and creating them in init. Skeleton game adds/removed them as per their type 
    - a refined set of game progress events that get sent to AdvancedModes, in priority order, prior to the actual event occuring. Now modes themselves can respond directly to `evt_game_starting`, `evt_ball_starting`, `evt_ball_ending`, `evt_game_ending`, `evt_player_added`, `evt_tilt`, and `evt_tilt_ball_ending` events. Modes can also request to postpone the event propagation (i.e., the calling of the next event handler) by returning a number of seconds that the mode needs to 'finish up' (e.g., play a special animation or sound) or can delay and stop further propegation by returning a tuple of the delay in seconds and the second entry is `True`
- A small and hopefully well commented example game based on T2.

### Coming Soon: ###

- automatic handling of AC Relay coils (from yaml markup, only)
- match mode
- more features to the bonus mode: using a yaml file to define about valid bonuses, score per award, Max numbers to allow of said award, etc. the tally is still in progress --this is not totally done.

## Game event flow
(changes from PyProcGame, etc.)

Your game class should not call game_start, ball_end, etc.  It should also not need to override these methods.  If you feel you need to, you should contact me so I can change the framework.  As designed, SkeletonGame (and its constiutent parts, including the attract and bonus modes) will handle the successive event progression.  

In a typical game, this looks like:

### Your game class iniializes itself in main()... ###
Behind the scenes, ``super(SkeletonGame,self).__init__()`` does the following:

- initializes the sound controller
- finds the DMD settings from the config.yaml and sets up your display
- creates a lampshow controller
- loads all your assets from the asset_list.yaml file (shows the player a graphical loading bar)
- initializes and connects the ball_save and trough modes
- loads the OSC mode, bonus mode, score display 

Then, any AdvancedMode derived modes that you initialize are automatically added to skeletonGame's 'known modes' so it can add/remove them for you, based on their mode_type (game, ball, system, custom).  

### When you call reset(): ###

The SkeletonGame version of reset() protects the modes that need to be in the game.  The old reset method would remove ALL modes from the game, but reset() in skeletonGame's will re-add modes that should not be removed and protect certain modes (e.g., the OSC controller) from being removed at all.

The last thing your reset() method should do is call: ``self.start_attract_mode()``

Then, SkeletonGame takes over again, initiating the attract mode from the yaml file.
When the player presses the switch with the name ``startButton``, SkeletonGame will automatically:

- ensure that the correct number of balls are in the trough, if not, a message is displayed and a ball-search is initiated.  If the balls are present (or found later), it goes on to...
- find modes with method *evt_game_starting* and call those methods in the order of their mode priority (a mode that needs more time can return a positive number to delay calling the next such method for that many seconds).  When completed, it goes on to... 
- find modes with method *evt_player_added* and call them.  This allows modes to perform any player specific data storage at this time.  Then
- find modes with method *evt_ball_starting* and call them as above.
- finally, add a ball to the shooter lane; if the ball does not actually close the ``shooterlane`` switch, the logic will continue to try to re-feed the shooter lane.  The ball is not considered successfully launched or in-play until that switch has been closed.

Your modes hopefully do something here :)

When a ball drains (i.e., the trough is full again), SkeletonGame will automatically:

- finds modes with method *evt_ball_ending* and calls them
- show the 'end of ball' and bonus sequence (if bonuses were awarded)
- if the balls number is *less than* the quantity specified in the machine yaml
    * find modes with method *evt_ball_starting* and call them (repeating the cycle)
- if the ball number is *greater than* the quantity specified in the machine yaml
    * finds modes with method *evt_game_ending* and calls them
    * checks the players score against the high scores.  If greater, the player may enter his/her scores
    * attract mode is shown again

So, the available events are:

Event | when fired:
------|--------------
``evt_player_added(player)`` | fired when a player is added; may be player 1, 2
``evt_game_starting`` | fired before the game starts.  This is your chance to do something prior to game start
``evt_ball_starting`` | fired before the ball is kicked into the shooter lane
``evt_ball_ending(shoot_again, last_ball)`` | fired as the ball is ending (i.e., the trough is full).  shoot_again will be true if the player has an extra ball lined up to follow this one; last_ball indicates that this is the last ball prior to this player's game ending
``evt_game_ending`` | the player's game is about to end.
``evt_tilt`` | the player has tilted the machine (exceeded all warnings on the plumb bob)
``evt_tilt_ball_ending`` | all balls are accounted for following the player tilting the machine (exceeded all warnings on the plumb bob)


# Making your first SkeletonGame-based game:
## Getting Started 

Note that a [sample 'empty' game](https://github.com/mjocean/PyProcGameHD-SkeletonGame/tree/master/SampleGame) is provided in the GitHub repository

0. Get everything installed and working as per the installation guide, above.

1. Create your project workspace (folder structure):

    Assuming I put my game in a folder called ``MyGame`` my directory structure should look like:

        MyGame/
        |
        +--config/      [this is where most yaml files live]
        |
        +--assets/      [your asset_list.yaml is here as well as individual dmds, sounds, lampshows]
        |
        +--my_modes/    [.py files for the modes that you add to your game]
        |
        +--MyGame.py    [your game class]
        |
        +--config.yaml  [these are the settings for your game: dmd size, resolution, etc.]

    Before we can really begin, you need a ``config.yaml`` file and a machine yaml file.

2. ``config.yaml``

  This file lives in the root of your game folder.  It is the only yaml file that isn't placed in the config folder.  It defines the paths to the asset files your game will need (images, lampshows, sounds), SkeletonGame specific settings (which modes to enable or disable), DMD specific settings (resolution, fps), window settings (border, scale, dot-effect), whether to connect to the real P-ROC hardware or not ('FakePinProc'), and finally a mapping of keyboard keys to switch numbers (for testing when the real P-ROC is not connected).

  The Sample Game's [config.yaml file](https://raw.githubusercontent.com/mjocean/PyProcGameHD-SkeletonGame/master/SampleGame/config.yaml) should help.  

3. ``config/machine.yaml``

    This is the machine definition file.  It maps all the switches, lamps and coils in your machine to easier to use logical names.  Some samples are available, including the [T2.yaml example in the Sample Game](https://raw.githubusercontent.com/mjocean/PyProcGameHD-SkeletonGame/master/SampleGame/config/T2.yaml)

    You **must** adhere to a few naming conventions:
        
      - your trough switches should be named ``trough1``, ``trough2``, .. ``troughN`` where N==num trough switches.
      - your start button should be called ``startButton``
      - your shooter lane switch should be called ``shooter``
      - your (bob) tilt switch should be called ``tilt``
      - your slam-tilt switch should be called ``slamTilt`` 
      - ball search is handled differently!  switches and coils should be tagged for ball search, as shown in the example.

4. Build your ``config/asset_list.yaml``

    The assetmanager class and the asset list yaml file is arguably one of the most powerful additions to SkeletonGame/PyProcGameHD over PyProcGame.

    The asset_list.yaml file defines a number of things for your game:
      1. Loader User Interface: The visual layout of the asset loading screen that will be shown while your assets are being pre-loaded (on game launch)
      2. LampShows: a mapping of lamp show file names and logical names (i.e., keys) by which they will be defined.  Defining a lampshow in this file causes the lampshow to be parsed and validated during asset loading, so if there is in error in the lampshow you will find out immediately instead of when your code eventually goes to play the lampshow.
      3. Animations: a list of images and animations to be used in your game; minimally their file names and their logical names (i.e., keys).  By including an entry the image or animation will be pre-loaded, ready for use in your game's mode code.  Supported formats include the 'dmd' format, many common single frame formats: jpg, gif, png (per pixel alpha supported), and some animation formats such as gif (for animated gifs) and single frame file sequences (e.g., a file range from my_image000.png through my_image029.png would be specified with the file name ``my_image0%3d.png`` and all 30 would be loaded as the frames of a single animation).
      4. HDFonts: Native system fonts (TTF) and aliases for specific sizes of those fonts
      5. Fonts: Bitmap fonts, based on the PyProcGame font format
      6. Audio, Music, Voice: Audio files named via key (wav or ogg format).

    [The sample file will hopefully help clear up a lot about this file and its format](https://raw.githubusercontent.com/mjocean/PyProcGameHD-SkeletonGame/master/SampleGame/config/asset_list.yaml).

    SkeletonGame requires a few conventions in your asset_list, that allow you to tweak/customize certain properties.  You must be sure you define a few things:

      - A Font or HDFont named: `tilt-font-big`, `tilt-font-small`, `settings-font-small`, `high_score_entry_inits`, `high_score_entry_msg` `high_score_entry_letters`
      - blah blah..?  TODO: Figure out hte complete list, for here!
      - something else that's vital...

5. Other important yaml files:

    ###config/score_display.yaml###

    If you wish to tweak the visual appearance of the score display in your game, you can do so by editing the score_display yaml file.  An example (the same included with the Sample Game) is included below:

```yaml
    ScoreLayout:
      Fonts:
            bottom_info:                  # the bottom info Credits/Ball Num
                  Font: score_sub         # value corresponds to a font key in asset_list.yaml
                  FontStyle: blueish      # FontStyles are also in asset_list and OPTIONAL
            single_player:                # Fonts/Styles for single player play
                  10_digits:
                        Font: score_activeL # corresponds to keys in asset_list.yaml
                  11_digits:
                        Font: score_activeM
                  12plus:
                        Font: score_activeS
            multiplayer:                 # Fonts/Styles for multiplayer play
                  active:                 # style for the active player
                        7_digits: 
                              Font: score_activeL
                        8_digits: 
                              Font: score_activeM
                        9plus: 
                              Font: score_activeS
                  inactive:               # style for the inactive player(s)
                        7_digits: 
                              Font: score_inactive
                        8_digits: 
                              Font: score_inactive
                        9plus: 
                              Font: score_inactive

```

###attract.yaml###
  
  The attract.yaml file allows you to change the attract sequence contents with a great degree of flexibility without having to jump into the code.  Consider the following example:

```yaml
        Sequence:
        - Combo:
            Text:
                - "MOcean"
                - ""
                - "Presents"
            Font: large
            lampshow: attract_show_1
            duration: 2.0
        - Animation:
            Name: t800-war
        - Combo:
            Text:
                - "Terminator"
                - ""
                - "2.0"
            Font: large
            Animation: chrome
            FontStyle: blueish
            lampshow: attract_show_2
            duration: 2.0
        - HighScores:
            Font: large
            Background: chrome
            Order:
                - player
                - category
                - score
            duration: 1.0
```

### Steps to making your game: ###

## 1. Look at the Sample game that has been provided, [here](https://github.com/mjocean/PyProcGameHD-SkeletonGame/tree/master/SampleGame)

## 2. Look at the Display Architecture Tutorial, [here](http://mjocean.github.io/PyProcGameHD-SkeletonGame/DMD_Tutorial.html)

TODO: This...

# PyProcGame Documentation

Please see the [pyprocgame Documentation](http://pyprocgame.pindev.org/) site for the pyprocgame Manual and detailed API documentation.


## License

New components are Copyright (c) 2014-2015 Michael Ocean and Josh Kugler
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
