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
This is a fork of PyProcGame, meant to replace PyProcGame for users who wish to create LCD-based PyProcGame games that are powered by a P-ROC.

Traditional DMD support has been broken, in favor of supporting traditional PC display hardware (i.e., LCD display). Specifically this version enables full-color frames (with alpha and per-pixel alpha transparency) running resolutions far in excess of 128x32.  Hardware requirements moderate if hardware acceleration is available.

This release replaces the previous HD VGA fork of PyProcGame and it's functionality is a superset of that version.  This release has been re-written (and aggressively optimized) to leverage SDL2+PySDL2 graphics hardware acceleration features.  Many things are now possible with nominal overhead, including 'dot-filter', alpha transparency, per-pixel alpha, just to name a few.  The prior PyGame-based version remains for those who might need it for some reason or another.

Note: This version does not support the PyGame or Pyglet based desktop as the original PyProcGame does.  There are several ways to use this version for some games and have it live side-by-side with traditional, DMD-based games.  The easiest is to just include the procgame folder as a subfolder of your game.

## SkeletonGame

SkeletonGame is a collection of classes to speed up new game development, and is also included (and maintained) as part of this release.  If you are a new P-ROC developer, you should strongly consider using it.  If you have an existing codebase, you can migrate to this latest version of the HD Framework without using SkeletonGame, with minimal code changes.

SkeletonGame is meant to be a proper third tier on top of BasicGame; think of it as the logical continuation of Starter.py --that is, if starter were a class that people were expected to subclass.  SkeletonGame is just a bunch of additions to pyprocgame (many of which lifted from the JD sample game). It leverages everything that those of use who use PyProcGame know and love, and only intends to streamline some things for new users. It should help you make games faster.  Think of it as sucking out the best parts of the Judge Dredd sample game, modifying it to be generic, adding stuff to make developing games easier, and having the whole thing running on the latest HD VGA fork of PyProcGame. 

If SkeletonGame works, it means you (as the programmer) should:

- have VERY few lines of code in your game class.
- spend most of your time coding the logic for *modes*.
- be able to leverage fairly standard modes that have been written before.
- use helpers to create DMD content (in code) much easier.
- get started quickly.

## pyprocgame

This work is built on top of (and would be nothing without) pyprocgame, which is a high-level pinball development framework for use with P-ROC (Pinball Remote Operations Controller).  Pyprocgame was written by Adam Preble and Gerry Stellenberg.  More information about P-ROC is available at [pinballcontrollers.com](http://pinballcontrollers.com/).  See the [pyprocgame site](http://pyprocgame.pindev.org/) for the full pyprocgame documentation.

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

2. Install the SkeletonGame/HD VGA SDL2 dependencies.  
	2. Download and install [PySDL2 for your platform]
	(http://pysdl2.readthedocs.org/en/latest/install.html)
	1. Install the 32-bit (x86) versions of the SDL2 and the SDL2_TTF libraries -- 
	For windows, put them in a directory called ``C:\Python26\DLLs\sdl2``.  
  	- [sdl2](https://www.libsdl.org/download-2.0.php)
  	- [sdl2_ttf](http://www.libsdl.org/projects/SDL_ttf/)
	1.  Download and install [pyOSC-0.3.5b-5294.zip](https://pypi.python.org/pypi/pyOSC)
	1.  Either set the PYSDL2_DLL_PATH (as per the instructions, [here](http://pysdl2.readthedocs.org/en/latest/integration.html) or add a ``PYSDL2_DLL_PATH`` in the game's ``config.yaml``.
	1. *Optional:* For MP4 support install OpenCV and libffmpeg

3. Install the SkeletonGame version of PyProcGame along-side the One-Click installed pyprocgame.  Download the ZIP of the files here, and extract it to somewhere other than your existing pyprocgame-master folder (e.g., C:\P-ROC\pyprocgame-hd\).  Within that directory, from the command line run:

```python setup.py develop```

This will install SkeletonGame in 'develop' mode, such that when you import pyprocgame from any python script, it will use this version, from the current location.

	import procgame.game

It will also update the "procgame" command line tool into a system-dependent location.  The updated version works with the color file formats.  On Linux and Mac OS X systems this will probably be in your path such that you can type, from the command line:

	procgame

and see a list of available commands.  If it is not in your path you can invoke it directly, or modify your PATH environment variable.  Note that on Windows the procgame script is typically located in C:\Python26\Scripts.

### *Optional:* the graphical switch tester: ###
1. Download/install wxPython (for windows, this is wxPython3.0-win32-3.0.2.0-py26.exe)
http://www.wxpython.org/download.php 
2. Download the switchMatrixClient.py and put it in the main game folder.  
https://github.com/mjocean/OscSwitchMatrixGUI
3. Running the switch matrix client is as follows:

```
python switchMatrixClient.py -y config/t2.yaml -p 9000 -i t2_SM.jpg -l t2.layout
```

where:
  * `` config/t2.yaml`` is the path to the machine configuration file
  * ``t2_SM.jpg`` is a playfield image shrunk to fit the screen.
  * ``t2.layout`` is a layout file saved from this tool (the first run will not include this ``-l t2.layout`` argument)


# SkeletonGame: Big Picture
## Overview

Module       | Layer
-------------------|----
SkeletonGame       | (L3)
BasicGame          | (L2)
libpinproc/pinproc | (L1)


Motivation: Most people who learn PyProcGame programming have done so by looking at existing open-source games and there are many good ones to learn from.  Unfortunately, the copy/paste/merge process is fairly error prone. I've done it a few times now and it gets dangerous with sequence dependant, asynchronous (i.e., event-driven) code that spans multiple files. Suppose 'project A' assumes that the attract mode will call `start_ball()`, but 'project B' assumes that `start_ball()` is called by the trough handler --depending on what you grab and from where, you may wind up with no balls in the trough or two balls.  Worse I've seen and encountered plenty of instances of the game appearing to be hung or crashing because some event doesn't occur due to functions being called in the wrong order as a result of copy/paste/merge-fail. Having worked on a few P-ROC projects now, I've tried to distill the common bits from each of those games so that I can avoid rewriting the same lines again and again.

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

A game class that is subclassed from SkeletonGame should be very short.  The example provided is fewer than 60 lines if you exclude imports, comments and whitespace.  Most of your code should be present in your mode classes, instead.

Your game class should not call game_start, ball_end, etc.  It should also not need to subclass these methods.  You can, of course, do so, but you should not HAVE to.  SkeletonGame (and its constiutent parts, including the attract and bonus modes) will handle the successive event progression.  In a typical game, this looks like:

### Your game class iniializes itself in main()... ###
 Behind the scenes, super(SkeletonGame,self).__init__ does the following:

- initializes the sound controller
- finds the DMD settings from the config.yaml and sets up your display
- creates a lampshow controller
- loads all your assets from the asset_list.yaml file (shows the player a graphical loading bar)
- initializes and connects the ball_save and trough modes
- loads the OSC mode, bonus mode, score display 

Then, any AdvancedMode derived modes that you initialize are automatically added to skeletonGame's 'known modes' so it can add/remove them for you, based on their mode_type (game, ball, system, custom).  

### When you call reset(): ###

The SkeletonGame version of reset() protects the modes that need to be in the game.  The old reset method would remove ALL modes from the game, but reset() in skeletonGame's will re-add modes that should not be removed and protect certain modes (e.g., the OSC controller) from being removed at all.

The last thing your reset() method should do is call: self.start_attract_mode()

Then, SkeletonGame takes over again, initiating the attract mode from the yaml file.
When the player presses the switch with the name 'startButton', SkeletonGame will automatically:

- find modes with method *evt_game_starting* and call them 
- find modes with method *evt_player_added* and call them
- find modes with method *evt_ball_starting* and call them 
- add a ball to the shooter lane.

Your modes hopefully do something here :)

When the ball drains and the trough is full, SkeletonGame will automatically:

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

    Use the default provided.  TODO: Paste documetnation from pinballcontrollers forum

3. ``machine.yaml``

    This is the machine definition file.  It defines all the switches, lamps and coils in your machine.  Some samples are available.

    You **must** adhere to a few naming conventions:
        
      - your trough switches should be named ``trough1``, ``trough2``, .. ``troughN`` where N==num trough switches.
      - your start button should be called ``startButton``
      - your shooter lane switch should be called ``shooter``
      - your (bob) tilt switch should be called ``tilt``
      - your slam-tilt switch should be called ``slamTilt`` 
      - ball search is handled differently!  switches and coils should be tagged for ball search, as shown in the example.

4. Build your ``asset_list.yaml``

    TODO: quite a lot to write about the format.  The example is probably good to reporoduce here.  

    You must be sure you define a few things:

      - A Font or HDFont named: `tilt-font-big`, `tilt-font-small`, `settings-font-small`, `high_score_entry_inits`, `high_score_entry_msg` `high_score_entry_letters`
      - blah blah
      - something else that's vital...

5. Other important yaml files:

    ###score_display.yaml###

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



### steps to making your game: ###

3.  I put the T2-SkelGame files at C:\P-ROC\pyprocgame-master\games\T2-SkelGame
12.  I removed the dmd_fonts section from C:\P-ROC\pyprocgame-master\games\T2-SkelGame\config\asset_list.yaml
13.  From config.yaml, I removed references to dropbox, sof (buffy), etc.

Okay now time to make my pinbot game!

1.  Copy T2-SkelGame folder in its entirety and rename.  I chose to rename Pinbot-SkelGame.
2.  Copy and rename T2Game.py.  I chose PinbotGame.py.
2A.  Search and Replace the class name T2Game with PinbotGame.
2B.  Remove gunMode and LaneChangeMode (anything not used by Pinbot) from the "from my_modes import "
2C.  Remove the instantiation of any modes previously removed (#self.gun_mode = gunMode(game=self), etc.)
2D.  Change the trough count and osc closed switches if different from T2 (I have a 4 ball trough).
2E.  Rename the switches and coils in doBallSearch() and reset() to fit your game.
2F.  Change reference to config/T2.yaml to config/Pinbot.yaml.  One note, since I've already got a fully-working yaml file I get to skip the step of creating a new yaml file, which would take a while for somebody just starting out.

4.  Now for modes.  To keep things clean I decided to delete gunMode.py and LaneChangeMode.py from the my_modes folder.  Also needed to delete these modes from my_modes/_init_.py
5.  Speaking of modes, there are going to be quite a lot of references to switch, lamp, and coil names in the my_modes files.  I changed the references in attact, BaseGameMode, ExampleBlankMode, SkillshotMode to only reference similar switches, lamps, and coils that are actually present in my game.

## Change Log ##
Issues fixed/addressed:
### 4/24/2015 ###

1. Config/yaml parser fixed to be more resilient to missing/bad tags.
2. ``enable_alphanumeric_flippers()`` checks for a PRCoil entry in machine yaml called ``flipperEnable``; does nothing but warn if none is present
3. removed ``print()`` from ``msg_over()`` in ``dmdhelper.py``
4. moved startButton/serviceButton monitoring to a new mode: ``switchmonitor``.py, so they wouldn't look as out of place in dmdhelper
6. moved starting a game from attract mode out of attract mode.  Now switchmonitor does this.  Much cleaner in the code
**still need to investigate/fix starting the game without a full trough
7. added 'reset' functionality to ``score_display.py``, otherwise multiplayer style score display would still show after ending a multiplayer game and starting single player
** still need to make multiplayer score display not ugly.
8. *may* have fixed the lamps flashing after exiting attract mode.  More testing required.

### 4/26/2015 ###
1. Added a ballsearch mode that is modified from the stock ballsearch; notable changes include that there is no longer a separate section PRBallSearch required in the machine yaml.  Instead, tag the switches with ballsearch to indicate whether or not they are included in the ballsearch and tag coils as to whether or not they should be fired on search
2. The game will attempt to locate balls (i.e., a full trough) prior to starting a game.
3. ``.set_status`` is now intended for 'alert' style messages, it has a background box to indicate that it is an alert
4. ``.set_status``, ``.genFrame`` and ``displayText`` all support a flashing argument, which indicates the number of frames to flash for (default is None, for non-flashing text).

# Documentation

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