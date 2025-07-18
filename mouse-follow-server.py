#!/usr/bin/env python3

import socket
import time
import os
import argparse
import pyautogui
import math
import platform
import sys
import select
import json
from screeninfo import get_monitors

def get_config_dir():
    if platform.system() == "Windows":
        base_dir = os.environ.get("APPDATA", os.path.expanduser("~\\AppData\\Roaming"))
    elif platform.system() == "Darwin":
        base_dir = os.path.expanduser("~/Library/Application Support")
    else:
        base_dir = os.path.expanduser("~/.config")

    config_dir = os.path.join(base_dir, "obs_zoommouse_socket")
    os.makedirs(config_dir, exist_ok=True)
    return config_dir

CONFIG_DIR = get_config_dir()

# Optional OBS WebSocket hotkey toggle
try:
    import obsws_python as obs
    OBS_AVAILABLE = True
except ImportError:
    OBS_AVAILABLE = False

# Platform-specific imports
if platform.system() == "Windows":
    import msvcrt
else:
    import tty
    import termios
    import select

def load_last_config(CONFIG_PATH=os.path.join(CONFIG_DIR, "last_config.json")):
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_last_config(args, last_config, Ignore=[], CONFIG_PATH=os.path.join(CONFIG_DIR, "last_config.json")):
    conf = dict(vars(args))
    for c in list(conf):
        if c in Ignore:
            del conf[c]
    try:
        if last_config != conf:
            with open(CONFIG_PATH, "w") as f:
                json.dump(conf, f, indent=2)
            print(f"Last cli args where saved to:\n> {CONFIG_PATH}")
    except Exception as e:
        print(f"Warning: Failed to save config: {e}")

def list_monitors():
    for idx, m in enumerate(get_monitors()):
        print(f"[{idx}] x={m.x} y={m.y} width={m.width} height={m.height}")

def str2bool(v):
    if isinstance(v, bool):
        return v
    return v.lower() in ("yes", "true", "t", "y", "1")

def parse_arguments():
    # Minimal parser to get the config file path early
    mini_parser = argparse.ArgumentParser(add_help=False)
    mini_parser.add_argument("-C", "--config-file", type=str, default=None)
    known_args, _ = mini_parser.parse_known_args()

    # Determine config file path
    default_config_file = os.path.join(CONFIG_DIR, "last_config.json")
    config_file = known_args.config_file or default_config_file

    last_config = load_last_config(config_file)
    last_config_copy = dict(last_config)

    parser = argparse.ArgumentParser(description="Send mouse position to OBS Zoom plugin via UDP; Most argument values will be saved")
    # here declare --config-file again to make it show in --help
    parser.add_argument("-c", "--config-file", type=str, default=config_file,
        help=f"Set the config file location (default; not stored: {default_config_file})")

    parser.add_argument("-i", "--ip", type=str, default=last_config.get("ip", "localhost"), help="OBS hostname or IP (default: localhost)")
    parser.add_argument("-p", "--port", type=int, default=last_config.get("port", 12345), help="UDP port (default: 12345)")
    parser.add_argument("-d", "--delay", type=int, default=last_config.get("delay", 10), help="Delay in ms (default: 10)")
    parser.add_argument("-R", "--rows", type=int, default=last_config.get("rows", 0), help="Divide screen into N rows")
    parser.add_argument("-C", "--columns", type=int, default=last_config.get("columns", 0), help="Divide screen into N columns")
    parser.add_argument("-l", "--listmonitors", action="store_true", help="List available monitors")
    parser.add_argument("-s", "--setmonitor", type=int, default=last_config.get("setmonitor", 0), help="Select monitor index to use")
    parser.add_argument("-z", "--zoomin", type=str2bool, default=False, nargs='?', const=True,
        help="Zoom in at start (default: false; set to true to zoom in at start)")
    parser.add_argument("-t", "--zoomtoggle", type=str2bool, default=False, nargs='?', const=True,
        help="Use older zoomtoggle behavior (default: false; set to true to enable)")
    parser.add_argument("-P", "--padding", type=float, default=last_config.get("padding", 0.45),
        help="Sticky border padding as a percentage (default: 0.45)")
    parser.add_argument("-f", "--factor", type=float, default=last_config.get("factor", 0.01), help="Smoothing factor (default: 0.01)")
    parser.add_argument("-m", "--minstep", type=float, default=last_config.get("minstep", 2.0), help="Minimum step size (default: 2.0)")
    parser.add_argument("-M", "--maxstep", type=float, default=last_config.get("maxstep", 75.0), help="Maximum step size (default: 75.0)")
    parser.add_argument("-Z", "--zoom", type=float, default=last_config.get("zoom", 2),
        help="What is your zoom setting (used for border distance; default 2; -1 to disable)")
    parser.add_argument("-w", "--wsport", type=int, default=last_config.get("wsport", 4455), help="OBS WebSocket port (default: 4455)")
    parser.add_argument("-W", "--wspassword", type=str, default=last_config.get("wspassword", ""), help="OBS WebSocket password (if set)")
    parser.add_argument("-k", "--keyfile", type=str, default=last_config.get("keyfile", ""), help="Path to a key input file (for automation)")
    parser.add_argument("-B", "--source-size", nargs=2, type=int, metavar=('WIDTH', 'HEIGHT'), default=last_config.get("source_size",[-1, -1]),
        help="Set obs source base size in pixels (default: Monitor Size; noted by xy; -1, -1)")
    parser.add_argument("-S", "--source-name", type=str, default=last_config.get("source_name"),
        help="Set obs source name; needed for zoom check.")

    args = parser.parse_args()

    if args.listmonitors:
        list_monitors()
        exit(0)

    if args.delay < 0:
        print("Delay can be below 0; Setting to 0")
        args.delay == 0

    # Save args for reuse in next run
    save_last_config(args, last_config_copy, Ignore=["listmonitors","config_file"])

    return args

def clamp(val, minval, maxval):
    return max(minval, min(val, maxval))

def smooth_transition(current, target, factor=0.01):
    return current + (target - current) * factor

def hybrid_transition(current, target, factor=0.01, min_step=1.0, max_step=75.0):
    delta = target - current
    if delta == 0:
        return current, 0.0

    # Compute base step
    step = delta * factor

    # Apply min and max constraints
    step_abs = abs(step)
    direction = 1 if step > 0 else -1

    if step_abs < min_step:
        step = direction * min_step
    elif step_abs > max_step:
        step = direction * max_step

    # Prevent overshoot
    if abs(delta) < abs(step):
        return target, delta

    return current + step, step

def hybrid_transition_vector(current_x, current_y, target_x, target_y, factor=0.01, min_step=1.0, max_step=75.0):
    # Apply per-axis logic (but get raw step for later normalization)
    new_x, step_x = hybrid_transition(current_x, target_x, factor, min_step, max_step)
    new_y, step_y = hybrid_transition(current_y, target_y, factor, min_step, max_step)

    # Compute total step magnitude
    total_step = math.hypot(step_x, step_y)

    # If combined speed is too high, scale down both axes
    if total_step > max_step:
        scale = max_step / total_step
        step_x *= scale
        step_y *= scale
        new_x = current_x + step_x
        new_y = current_y + step_y

    return new_x, new_y

def vector_transition(current_x, current_y,
                      target_x,  target_y,
                      factor=0.01,
                      min_step=1.0,
                      max_step=75.0):

    # Compute delta vector
    dx = target_x - current_x
    dy = target_y - current_y

    # Distance to target
    dist = math.hypot(dx, dy)
    if dist == 0:
        return current_x, current_y

    # Compute step magnitude
    step = dist * factor
    # Clamp the step
    step = clamp(step, min_step, max_step)

    # If we'd overshoot, go straight to the target
    if step >= dist:
        return target_x, target_y

    # Move along the vector by 'step'
    ratio = step / dist
    new_x = current_x + dx * ratio
    new_y = current_y + dy * ratio

    return new_x, new_y

def clamp_to_visible(monitor_x, monitor_y, monitor_w, monitor_h, target_x, target_y, zoom):
    if zoom < 0:
        return target_x, target_y

    # Calculate half the visible width/height at the current zoom level
    half_width = monitor_w / (2 * zoom)
    half_height = monitor_h / (2 * zoom)

    # Compute min and max bounds the target can be centered at
    min_x = monitor_x + half_width
    max_x = monitor_x + monitor_w - half_width

    min_y = monitor_y + half_height
    max_y = monitor_y + monitor_h - half_height

    # Clamp the target to keep the zoomed area fully visible
    clamped_x = clamp(target_x, min_x, max_x)
    clamped_y = clamp(target_y, min_y, max_y)

    return clamped_x, clamped_y

def linear_transition(current, target, step_size=10):
    distance = target - current
    if abs(distance) <= step_size:
        return target
    return current + step_size if distance > 0 else current - step_size

def get_monitor_area(index):
    monitors = get_monitors()
    if index < 0 or index >= len(monitors):
        raise IndexError(f"Monitor index {index} out of range")
    mon = monitors[index]
    return mon.x, mon.y, mon.width, mon.height

def get_mouse_relative_to_monitor(monitor_x, monitor_y, monitor_w, monitor_h):
    mx, my = pyautogui.position()
    rx = clamp(mx - monitor_x, 0, monitor_w)
    ry = clamp(my - monitor_y, 0, monitor_h)
    return rx, ry

def snap_to_grid(x, y, w, h, cols, rows):
    if cols <= 0 and rows <= 0:
        return x, y

    cell_width = w / cols if cols > 0 else w
    cell_height = h / rows if rows > 0 else h

    col = int(x / cell_width)
    row = int(y / cell_height)

    target_x = int((col + 0.5) * cell_width)
    target_y = int((row + 0.5) * cell_height)

    return clamp(target_x, 0, w), clamp(target_y, 0, h)

def get_snap_target_with_padding(
    raw_x, raw_y,
    monitor_w, monitor_h,
    cols, rows,
    current_cell,
    padding_percent=0.45,
    c=1
):
    cell_w = monitor_w / cols
    cell_h = monitor_h / rows

    # If no cell locked yet, just snap directly
    if current_cell is None:
        col = clamp(int(raw_x / cell_w), 0, cols - 1)
        row = clamp(int(raw_y / cell_h), 0, rows - 1)
        return (col, row), ((col + 0.5) * cell_w, (row + 0.5) * cell_h)

    cur_col, cur_row = current_cell

    # Compute the full cell bounds
    cell_left   = cur_col * cell_w
    cell_right  = cell_left + cell_w
    cell_top    = cur_row * cell_h
    cell_bottom = cell_top + cell_h

    # Expand that box by padding_percent * cell_size on all sides
    pad_x = cell_w * padding_percent
    pad_y = cell_h * padding_percent

    zone_left   = cell_left   - pad_x
    zone_right  = cell_right  + pad_x
    zone_top    = cell_top    - pad_y
    zone_bottom = cell_bottom + pad_y

    if c % 100 == 0:
        #print(f"RAW: {raw_x}, {raw_y}")
        #print(f"STICKY ZONE: X({zone_left}–{zone_right}) Y({zone_top}–{zone_bottom})")
        #print(f"CUR CELL: {cur_col}, {cur_row}")
        pass

    in_x_zone = zone_left <= raw_x <= zone_right
    in_y_zone = zone_top <= raw_y <= zone_bottom

    if c % 100 == 0:
        #print(f"in_x_zone: {in_x_zone}, in_y_zone: {in_y_zone}")
        pass

    # If still within this *expanded* zone, stay in current cell
    if in_x_zone and in_y_zone:
        return current_cell, ((cur_col + 0.5) * cell_w, (cur_row + 0.5) * cell_h)

    # Otherwise, truly crossed out of the hysteresis zone — pick the new cell
    new_col = clamp(int(raw_x / cell_w), 0, cols - 1)
    new_row = clamp(int(raw_y / cell_h), 0, rows - 1)

    if c % 100 == 0:
        #print(f"NEW CELL: {new_col}, {new_row}")
        pass

    return (new_col, new_row), ((new_col + 0.5) * cell_w, (new_row + 0.5) * cell_h)

def is_zoomed_in(obs_client, source_name, w, h, crop_filter_name="obs-zoom-to-mouse-crop"):
    if not source_name:
        print("source_name not set use the argument --source-name NAME, to detect the zoom-state")
        return None
    try:
        filter_resp = obs_client.send("GetSourceFilter", {
            "sourceName": source_name,
            "filterName": crop_filter_name
        })

        if not hasattr(filter_resp, "filter_settings"):
            print("Error: filter_settings not found in filter response.")
            return None

        crop = filter_resp.filter_settings
        crop_cx = crop.get("cx", 0)
        crop_cy = crop.get("cy", 0)
        crop_left = crop.get("left", 0)
        crop_top = crop.get("top", 0)

        # Get original source size
        source_w, source_h = w, h
        if source_w is None or source_h is None:
            print("Could not determine source base size.")
            return None

        # Consider "zoomed" if:
        # - crop has an offset
        # - or dimensions smaller than source
        # Allow 1px tolerance for floating point rounding
        zoomed = (
            crop_left > 0 or crop_top > 0 or
            crop_cx < w - 1 or crop_cy < h - 1
        )

        return zoomed

    except Exception as e:
        print(f"Error checking zoom state: {e}")
        return None

def main():
    args = parse_arguments()
    host = args.ip
    port = args.port
    wsport = args.wsport
    wspassword = args.wspassword
    delay = args.delay / 1000.0
    rows = args.rows
    cols = args.columns
    zoomin = args.zoomin
    zoomtoggle = args.zoomtoggle
    source_name = args.source_name

    if args.keyfile:
        keyfile_path = (
            os.path.abspath(args.keyfile)
            if os.path.isabs(args.keyfile)
            else os.path.join(CONFIG_DIR, args.keyfile)
        )
    else:
        keyfile_path = None

    monitor_x, monitor_y, monitor_w, monitor_h = get_monitor_area(args.setmonitor)
    source_w, source_h = args.source_size
    if source_w < 0:
        source_w = monitor_w
    if source_h < 0:
        source_h = monitor_h

    key_follow = "y"
    key_zoom = "x"
    print("\n-----------------------------------")
    print(" OBS Zoom Mouse Remote - Python")
    print("-----------------------------------")
    print(f"Sending to {host}:{port}, delay={args.delay}ms")
    print(f"Selected monitor: x={monitor_x}, y={monitor_y}, w={monitor_w}, h={monitor_h}")
    if cols > 0 or rows > 0:
        print(f"Snapping to grid: {cols} columns x {rows} rows")
    print(f"Press [{key_follow}] To toggle following.")
    print(f"Press [{key_zoom}] To toggle obs zoom.")
    if keyfile_path:
        print(f"You can also save [{key_follow}] or [{key_zoom}] to the following file to toggle it:\n> {keyfile_path}")
    print("Press Ctrl+C to quit.\n")


    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    current_x, current_y = get_mouse_relative_to_monitor(monitor_x, monitor_y, monitor_w, monitor_h)

    following = True
    obs_client = None

    if OBS_AVAILABLE:
        try:
            obs_client = obs.ReqClient(
                host=host,
                port=wsport,
                password=wspassword
            )
        except Exception as e:
            print(f"Warning: Could not connect to OBS WebSocket: {e}")
            obs_client = None

    c = 0 # For debug printing
    current_cell = None  # Start with no cell locked
    raw_x = None
    raw_y = None

    is_unix = platform.system() != "Windows"
    if is_unix:
        fd = sys.stdin.fileno()
        old_termios = termios.tcgetattr(fd)
        tty.setcbreak(fd)

    # if "zoomin is true", "zoom in" else "zoom out"
    if obs_client:
        ret_zoomed = is_zoomed_in(obs_client, source_name, source_w, source_h)
        if ret_zoomed != None:
            print(f"In your obs setup the zoom-state can be detected, it is {"Zoomed" if ret_zoomed else "Unzoomed"}")
        else:
            print(f"In your obs setup the zoom-state can't be detected, please make shure the correct --source-name arg is given")

        if zoomtoggle or ret_zoomed != None:
            if ret_zoomed and not zoomin:
                hotkey_name = "toggle_zoom_hotkey"
            elif ret_zoomed == False and zoomin:
                hotkey_name = "toggle_zoom_hotkey"
            else:
                hotkey_name = ""
        elif zoomin:
            hotkey_name = "zoom_in_hotkey"
        else:
            hotkey_name = "zoom_out_hotkey"

        try:
            if hotkey_name:
                resp = obs_client.send("TriggerHotkeyByName", {
                    "hotkeyName": hotkey_name
                }, raw=True)
            if hotkey_name == "toggle_zoom_hotkey":
                m = f", Its now {"Zoomed" if zoomin else "Unzoomed"}"
                print(f"[{key_zoom}] Zoom toggle hotkey was triggered{m}")
            elif hotkey_name:
                print(f"[{key_zoom}] Zoom {"in" if zoomin else "out"} hotkey triggered, We are now: {"Zoomed" if zoomin else "Unzoomed"}")
            else:
                print(f"[{key_zoom}] Zoom-state is already correct, skipped obs hotkey trigger")
        except Exception as e:
            print(f"OBS hotkey error: {e}")

        # at this point "zoomin true" would say we are "zoomed in" otherwise we are "zoomed out"

    try:
        while True:
            c += 1

            # Get raw mouse relative to selected monitor if follow is active
            if following or raw_x == None or raw_y == None:
                raw_x, raw_y = get_mouse_relative_to_monitor(monitor_x, monitor_y, monitor_w, monitor_h)

            if cols > 0 and rows > 0:
                current_cell, (target_x, target_y) = get_snap_target_with_padding(
                    raw_x, raw_y,
                    monitor_w, monitor_h,
                    cols, rows,
                    current_cell,
                    padding_percent=args.padding,
                    c=c
                )
            else:
                target_x, target_y = raw_x, raw_y

            target_x, target_y = clamp_to_visible(0, 0, monitor_w, monitor_h, target_x, target_y, args.zoom)

            # Smooth *towards the target*
            current_x, current_y = vector_transition(
                current_x, current_y,
                target_x, target_y,
                factor=args.factor,
                min_step=args.minstep,
                max_step=args.maxstep
            )

            if c % 100 == 0:
                #print(f"x: {current_x:.2f}, y: {current_y:.2f}")
                #print("Raw:", raw_x, raw_y)
                #print("SnapTarget:", target_x, target_y)
                #print("Smoothed:", int(current_x), int(current_y))
                pass

            # Round for consistent UDP string
            msg = f"{int(current_x)} {int(current_y)}"
            client.sendto(msg.encode(), (host, port))

            # 1) Try keyfile:
            key = None
            if keyfile_path:
                try:
                    with open(keyfile_path, "r+") as f:
                        c = f.read(1)
                        if c:
                            key = c.lower()
                            f.seek(0); f.truncate()
                except Exception as e:
                    print(f"Keyfile I/O error: {e}")

            # 2) Fallback to stdin:
            if not key and is_unix:
                if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                    key = sys.stdin.read(1)

            elif not key and not is_unix:
                if msvcrt.kbhit():
                    key = msvcrt.getwch().lower()

            if key and isinstance(key, str) and key[0] == key_follow:
                following = not following
                if following:
                    print(f"[{key}] Mouse Follow was toggled and is now: Enabled")
                else:
                    print(f"[{key}] Mouse Follow was toggled and is now: Disabled")

            elif key and isinstance(key, str) and key[0] == key_zoom:
                if obs_client:
                    # check if we are zoomed in
                    ret_zoomed = is_zoomed_in(obs_client, source_name, source_w, source_h)
                    # request the inverted state
                    if ret_zoomed != None:
                        zoomin = not bool(ret_zoomed)
                    else:
                        zoomin = not zoomin
                    if zoomtoggle or ret_zoomed != None:
                        hotkey_name = "toggle_zoom_hotkey"
                    elif zoomin:
                        hotkey_name = "zoom_in_hotkey"
                    else:
                        hotkey_name = "zoom_out_hotkey"

                    try:
                        resp = obs_client.send("TriggerHotkeyByName", {
                            "hotkeyName": hotkey_name
                        }, raw=True)
                        if zoomtoggle or ret_zoomed != None:
                            a = f", We are now: {"Zoomed" if zoomin else "Unzoomed"}"
                            print(f"[{key}] Zoom toggle hotkey was triggered{a}")
                        else:
                            print(
                                f"[{key}] Zoom {"in" if zoomin else "out"} hotkey triggered, We are now: {"Zoomed" if zoomin else "Unzoomed"}"
                            )
                    except Exception as e:
                        print(f"OBS hotkey error: {e}")

                else:
                    print(f"[{key}] Cant zoom with WebSocket, obs client not avalible")

            if delay > 0:
                time.sleep(delay)

    except KeyboardInterrupt:
        print("\nDisconnected.")
    except Exception as e:
        print(f"Unknown socket error: {e}")
    finally:
        if obs_client:
            ret_zoomed = is_zoomed_in(obs_client, source_name, source_w, source_h)
            if ret_zoomed:
                zoomin = False

                if zoomtoggle or ret_zoomed != None:
                    if ret_zoomed and not zoomin:
                        hotkey_name = "toggle_zoom_hotkey"
                    elif ret_zoomed == False and zoomin:
                        hotkey_name = "toggle_zoom_hotkey"
                    else:
                        hotkey_name = ""
                elif zoomin:
                    hotkey_name = "zoom_in_hotkey"
                else:
                    hotkey_name = "zoom_out_hotkey"

                try:
                    if hotkey_name:
                        resp = obs_client.send("TriggerHotkeyByName", {
                            "hotkeyName": hotkey_name
                        }, raw=True)
                    if hotkey_name == "toggle_zoom_hotkey":
                        m = f", Its now {"Zoomed" if zoomin else "Unzoomed"}"
                        print(f"[{key_zoom}] Zoom toggle hotkey was triggered{m}")
                    elif hotkey_name:
                        print(f"[{key_zoom}] Zoom {"in" if zoomin else "out"} hotkey triggered, We are now: {"Zoomed" if zoomin else "Unzoomed"}")
                    else:
                        print(f"[{key_zoom}] Zoom-state is already correct, skipped obs hotkey trigger")
                except Exception as e:
                    print(f"OBS hotkey error: {e}")

        client.close()
        try:
            if obs_client:
                obs_client.disconnect()
        except Exception as e:
            print(f"OBS disconnect error: {e}")

        print("\nAll Sockets where closed, exiting.")

        # Restore terminal on Unix
        if is_unix:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_termios)

if __name__ == "__main__":
    main()
