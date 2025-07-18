# OBS-Zoom-To-Mouse-Remote

An OBS Lua script to zoom a video source to focus on the mouse.
Now with different **remote tracking support** via a Python server, and zoom in/out hotkeys.

## Fork Information

This is a fork of [BlankSourceCode's obs-zoom-to-mouse](https://github.com/BlankSourceCode/obs-zoom-to-mouse).

* **Main repo**: [codeberg.org/marvin1099/obs-zoom-to-mouse-remote](https://codeberg.org/marvin1099/obs-zoom-to-mouse-remote)
* **Backup repo**: [github.com/marvin1099/obs-zoom-to-mouse-remote](https://github.com/marvin1099/obs-zoom-to-mouse-remote)
* **Tested on**: OBS 31.1.1
* Any code added by me is licensed under the **AGPLv3**
* Check the **commit history** to see what was added
* The server files (not .lua files) contain **only my code**, licensed entirely under AGPLv3
* This fork adds:
  * A **zoom in/out hotkey** to the zoom lua
  * A **rewritten Python-based remote server**
    * Inspired by [BlankSourceCode's Node.js version](https://github.com/BlankSourceCode/obs-zoom-to-mouse-remote/blob/main/src/server.js)
    * Supports **custom mouse regions** and other enhancements
    * See the [Mouse Follow Server section](#mouse-follow-server) for full details

## Example
<img src="obs-zoom-to-mouse.gif" alt="Usage Demo" width="60%">

## Install
1. Git clone the repo (or just save a copy of `obs-zoom-to-mouse.lua`)  
   - Download From [Releases](https://codeberg.org/marvin1099/obs-zoom-to-mouse-remote/releases) (or [GitHub backup](https://github.com/marvin1099/obs-zoom-to-mouse-remote/releases))
   - Get `ljsocket.lua`, and `mouse-follow-server.py` for the remote support as well
   - Place `ljsocket.lua` in the same folder as `obs-zoom-to-mouse.lua`
2. Launch OBS
3. In OBS, add a `Display Capture` source (if you don't have one already)
4. In OBS, open Tools -> Scripts
5. In the Scripts window, press the `+` button to add a new script
6. Find and add the `obs-zoom-to-mouse.lua` script
7. For best results use the following settings on your `Display Capture` source
   * Transform:
      * Positional Alignment - `Top Left`
      * Bounding Box type -  `Scale to inner bounds`
      * Alignment in Bounding Box - `Top Left`
      * Crop - All **zeros**
   * If you want to crop the display, add a new Filter -> `Crop/Pad`
      * Relative - `False`
      * X - Amount to crop from left side
      * Y - Amount to crop form top side
      * Width - Full width of display minus the value of X + amount to crop from right side
      * Height - Full height of display minus the value of Y + amount to crop from bottom side
8. Follow the [Mouse Follow Server](#mouse-follow-server) to use the **remote mouse tracking server**
   
   **Note:** If you don't use this form of setup for your display source (E.g. you have bounding box set to `No bounds` or you have a `Crop` set on the transform), the script will attempt to **automatically change your settings** to zoom compatible ones. 
   This may have undesired effects on your layout (or just not work at all).

   **Note:** If you change your desktop display properties in Windows (such as moving a monitor, changing your primary display, updating the orientation of a display), you will need to re-add your display capture source in OBS for it to update the values that the script uses for its auto calculations. You will then need to reload the script.

## Usage
1. You can customize the following settings in the OBS Scripts window:
   * **Zoom Source**: The display capture in the current scene to use for zooming
   * **Zoom Factor**: How much to zoom in by
   * **Zoom Speed**: The speed of the zoom in/out animation
   * **Auto follow mouse**: True to track the cursor automatically while you are zoomed in, instead of waiting for the `Toggle follow` hotkey to be pressed first
   * **Follow outside bounds**: True to track the cursor even when it is outside the bounds of the source
   * **Follow Speed**: The speed at which the zoomed area will follow the mouse when tracking
   * **Follow Border**: The %distance from the edge of the source that will re-enable mouse tracking
   * **Lock Sensitivity**: How close the tracking needs to get before it locks into position and stops tracking until you enter the follow border
   * **Auto Lock on reverse direction**: Automatically stop tracking if you reverse the direction of the mouse.
   * **Show all sources**: True to allow selecting any source as the Zoom Source - Note: You **MUST** set manual source position for non-display capture sources
   * **Set manual source position**: True to override the calculated x/y (topleft position), width/height (size), and scaleX/scaleY (canvas scale factor) for the selected source. This is essentially the area of the desktop that the selected zoom source represents. Usually the script can calculate this, but if you are using a non-display capture source, or if the script gets it wrong, you can manually set the values.
   * **X**: The coordinate of the left most pixel of the source
   * **Y**: The coordinate of the top most pixel of the source
   * **Width**: The width of the source (in pixels)
   * **Height**: The height of the source (in pixels)
   * **Scale X**: The x scale factor to apply to the mouse position if the source is not 1:1 pixel size (normally left as 1, but useful for cloned sources that have been scaled)
   * **Scale Y**: The y scale factor to apply to the mouse position if the source is not 1:1 pixel size (normally left as 1, but useful for cloned sources that have been scaled)
   * **Monitor Width**: The width of the monitor that is showing the source (in pixels)
   * **Monitor Height**: The height of the monitor that is showing the source (in pixels)
   * **More Info**: Show this text in the script log
   * **Enable debug logging**: Show additional debug information in the script log

1. In OBS, open File -> Settings -> Hotkeys 
   * Add a hotkey for `Toggle zoom to mouse` to zoom in and out
     * You can also use `Zoom In to Mouse` to only zoom in
     * In that case you probaly want `Zoom Out from Mouse` to just zoom out as well
   * Add a hotkey for `Toggle follow mouse during zoom` to turn mouse tracking on and off (*Optional*)

## Remote Tracking Support (Dual Machine Support)

This fork includes **remote mouse tracking** capabilities using a new Python-based server.

1. First follow [Install](#install) to setup the lua files.

2. In OBS script settings, the following options will be available:
   * **Enable remote mouse listener**
   * **Port** to listen on
   * **Poll Delay** for mouse position updates
   * Recomended settings for full function of the python server
     * Auto Follow Mouse [x]  
     * Follow speed = 1.00  
     * Follow border = 50  
     * Lock Sensitivity = 1  
     * Allow any zoom source [x]  
     * Enable remote mouse listener [x]  ; Needed for capture card / ndi souces  
     * Poll Delay = 10
   * The rest you can set how you want it

4. Then follow the setup instructions in the [Mouse Follow Server section](#mouse-follow-server) to:
   * Launch the Python server
   * Connect your remote system
   * Define custom regions and tracking behavior

The Python server is inspired by the original Node.js version from [BlankSourceCode's Node.js version](https://github.com/BlankSourceCode/obs-zoom-to-mouse-remote/blob/main/src/server.js) but is written from scratch and uses **custom behavior** written by me.

## More information on how mouse tracking works
When you press the `Toggle zoom` hotkey the script will use the current mouse position as the center of the zoom. The script will then animate the width/height values of a crop/pan filter so it appears to zoom into that location. If you have `Auto follow mouse` turned on, then the x/y values of the filter will also change to keep the mouse in view as it is animating the zoom. Once the animation is complete, the script gives you a "safe zone" to move your cursor in without it moving the "camera". The idea was that you'd want to zoom in somewhere and move your mouse around to highlight code or whatever, without the screen moving so it would be easier to read text in the video.

When you move your mouse to the edge of the zoom area, it will then start tracking the cursor and follow it around at the `Follow Speed`. It will continue to follow the cursor until you hold the mouse still for some amount of time determined by `Lock Sensitivity` at which point it will stop following and give you that safe zone again but now at the new center of the zoom.

How close you need to get to the edge of the zoom to trigger the 'start following mode' is determined by the `Follow Border` setting. This value is a pertentage of the area from the edge. If you set this to 0%, it means that you need to move the mouse to the very edge of the area to trigger mouse tracking. Something like 4% will give you a small border around the area. Setting it to full 50% causes it to begin following the mouse whenever it gets closer than 50% to an edge, which means it will follow the cursor *all the time* essentially removing the "safe zone".

You can also modify this behavior with the `Auto Lock on reverse direction` setting, which attempts to make the follow work more like camera panning in a video game. When moving your mouse to the edge of the screen (how close determined by `Follow Border`) it will cause the camera to pan in that direction. Instead of continuing to track the mouse until you keep it still, with this setting it will also stop tracking immediately if you move your mouse back towards the center.

### More information on 'Show All Sources'
If you enable the `Show all sources` option, you will be able to select any OBS source as the `Zoom Source`. This includes **any** non-display capture items such as cloned sources, browsers, or windows (or even things like audio input - which really won't work!).

Selecting a non-display capture zoom source means the script will **not be able to automatically calculate the position and size of the source**, so zooming and tracking the mouse position will be wrong!

To fix this, you MUST manually enter the size and position of your selected zoom source by enabling the `Set manual source position` option and filling in the `X`, `Y`, `Width`, and `Height` values. These values are the pixel topleft position and pixel size of the source on your overall desktop. You may also need to set the `Scale X` and `Scale Y` values if you find that the mouse position is incorrectly offset when you zoom, which is due to the source being scaled differently than the monitor you are using.

Example 1 - A 500x300 window positioned at the center of a single 1000x900 monitor, would need the following values:
   * X = 250 (center of monitor X 500 - half width of window 250)
   * Y = 300 (center of monitor Y 450 - half height of window 150)
   * Width = 500 (window width)
   * Height = 300 (window height)

Example 2 - A cloned display-capture source which is using the second 1920x1080 monitor of a two monitor side by side setup:
   * X = 1921 (the left-most pixel position of the second monitor because it is immediately next to the other 1920 monitor)
   * Y = 0 (the top-most pixel position of the monitor)
   * Width = 1920 (monitor width)
   * Height = 1080 (monitor height)

Example 3 - A cloned scene source which is showing a 1920x1080 monitor but the scene canvas size is scaled down to 1024x768 setup:
   * X = 0 (the left-most pixel position of the monitor)
   * Y = 0 (the top-most pixel position of the monitor)
   * Width = 1920 (monitor width)
   * Height = 1080 (monitor height)
   * Scale X = 0.53 (canvas width 1024 / monitor width 1920)
   * Scale Y = 0.71 (canvas height 768 / monitor height 1080)

I don't know of an easy way of getting these values automatically otherwise I would just have the script do it for you.

Note: If you are also using a `transform crop` on the non-display capture source, you will need to manually convert it to a `Crop/Pad Filter` instead (the script has trouble trying to auto convert it for you for non-display sources).

## Known Limitations
* Only works on `Display Capture` sources (automatically)
   * In theory it should be able to work on window captures too, if there was a way to get the mouse position relative to that specific window.
   * You can now enable the [`Show all sources`](#More-information-on-'Show-All-Sources') option to select a non-display capture source, but you MUST set manual source position values.
   * Fork info: I dind not need to set manual source position values even though im using a other pc, but i think it depents on the obs video size settings, set it if you have issues.

* Using Linux:
   * You may need to install the [loopback package](https://obsproject.com/forum/threads/obs-no-display-screen-capture-option.156314/) to enable `XSHM` display capture sources. This source acts most like the ones used by Windows and Mac so the script can auto calculate sizes for you.
   * The script will also work with `Pipewire` sources, but you will need to enable `Allow any zoom source` and `Set manual source position` since the script cannot get the size by itself.

* Using Mac:
   * When using `Set manual source position` you may need to set the `Monitor Height` value as it is used to invert the Y coordinate of the mouse position so that it matches the values of Windows and Linux that the script expects.

## Development Setup
* Clone this repo
* Edit `obs-zoom-to-mouse.lua`
* For socket changes edit `ljsocket.lua`
* Click `Reload Scripts` in the OBS Scripts window



--- 



# Mouse Follow Server

This is the companion **Python-based remote tracking server** for the [`Main section`](#obs-zoom-to-mouse-remote). It sends mouse position updates to OBS over **UDP**, allowing **remote mouse tracking and zooming**, even from other machines or monitor setups.

> Fully standalone and licensed under the **AGPLv3**  
> Requires **Python 3.7+**  
> Works cross-platform: Linux, Windows, macOS  

## Features

* Sends live mouse position to OBS zoom script over UDP
* Tracks a specific monitor (even multi-monitor setups)
* Divide screen into custom **rows and columns** (optional)
* Optional **OBS WebSocket** integration for additional automation
* Saves and reuses settings via config files
* Fast updates with adjustable smoothing and motion parameters

## Download 

Git clone the repo with branch server (or just save a copy of `start-mouse-follow-server.py`)  
- Download From [Releases](https://codeberg.org/marvin1099/obs-zoom-to-mouse-remote/releases) (or [GitHub backup](https://github.com/marvin1099/obs-zoom-to-mouse-remote/releases))
  - Get `start-mouse-follow-server.sh` (On unix like systems) or `start-mouse-follow-server.bat` (on Windows) as well.
  - The launcher files will activate a venv for you and install any needed python packages (recomended).

## Installation

Open the terminal or cmd (Windows)

### On Linux/macOS

To use the included Bash launcher:

```bash
./start-mouse-follow-server.sh
```
Use the full path if your working directory if not at the script root (or cd to the script root)

### On Windows

Or for use of the provided batch script:

```bat
start-mouse-follow-server.bat
```
Use the full path if your working directory if not at the script root (or cd to the script root)

## Configuration

You can pass options via command line or save them for reuse in a JSON file (default: `~/.config/obs-zoom-to-mouse/last_config.json`).

### Example usage:

```bash
python mouse-follow-server.py \
  --ip 192.168.1.42 \
  --port 12345 \
  --delay 10 \
  --setmonitor 1 \
  --rows 3 \
  --columns 4 \
  --zoomin true \
  --source-name "Game Source" \
  --source-size 1920 1080
```

---

## Usage

```
usage: mouse-follow-server.py [-h] [-c CONFIG_FILE] [-i IP] [-p PORT] [-d DELAY] [-R ROWS] [-C COLUMNS] [-l] [-s SETMONITOR] [-z [ZOOMIN]] [-t [ZOOMTOGGLE]] [-P PADDING] [-f FACTOR] [-m MINSTEP] [-M MAXSTEP] [-Z ZOOM] [-w WSPORT] [-W WSPASSWORD] [-k KEYFILE] [-B WIDTH HEIGHT] [-S SOURCE_NAME]

Send mouse position to OBS Zoom plugin via UDP; Most argument values will be saved

options:
-h, --help            show this help message and exit
-c, --config-file CONFIG_FILE
                      Set the config file location (default; not stored: ~/.config/obs_zoommouse_socket/last_config.json)
-i, --ip IP           OBS hostname or IP (default: localhost)
-p, --port PORT       UDP port (default: 12345)
-d, --delay DELAY     Delay in ms (default: 10)
-R, --rows ROWS       Divide screen into N rows
-C, --columns COLUMNS
                      Divide screen into N columns
-l, --listmonitors    List available monitors
-s, --setmonitor SETMONITOR
                      Select monitor index to use
-z, --zoomin [ZOOMIN]
                      Zoom in at start (default: false; set to true to zoom in at start)
-t, --zoomtoggle [ZOOMTOGGLE]
                      Use older zoomtoggle behavior (default: false; set to true to enable)
-P, --padding PADDING
                      Sticky border padding as a percentage (default: 0.45)
-f, --factor FACTOR   Smoothing factor (default: 0.01)
-m, --minstep MINSTEP
                      Minimum step size (default: 2.0)
-M, --maxstep MAXSTEP
                      Maximum step size (default: 75.0)
-Z, --zoom ZOOM       What is your zoom setting (used for border distance; default 2; -1 to disable)
-w, --wsport WSPORT   OBS WebSocket port (default: 4455)
-W, --wspassword WSPASSWORD
                      OBS WebSocket password (if set)
-k, --keyfile KEYFILE
                      Path to a key input file (for automation)
-B, --source-size WIDTH HEIGHT
                      Set obs source base size in pixels (default: Monitor Size; noted by xy; -1, -1)
-S, --source-name SOURCE_NAME
                      Set obs source name; needed for zoom check.
```

---

## Monitor Info

To list monitors and their indexes:

```bash
python mouse-follow-server.py --listmonitors
```

Example output:

```
Monitor 0: 1920x1080
Monitor 1: 2560x1440
```

Then you can use `--setmonitor 1` to track monitor 1.

---

## Config Files

All options (except `--config-file`) are saved after first run.
You can reuse saved config automatically, or specify a different file:

```bash
python mouse-follow-server.py --config-file mypreset.json
```

---

## Licensing

All code in this `server` branch is released under the **GNU AGPLv3** license.

---

## Related Project

Be sure to check out the OBS script that uses this server:

[`Main section`](#obs-zoom-to-mouse-remote)

