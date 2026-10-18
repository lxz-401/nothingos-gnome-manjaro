#!/usr/bin/env python3
"""Wait for a usable, settled X11 desktop before creating Conky windows."""
import os
import sys
import time


def probe_desktop():
    # Query the same X11 server Conky uses. No GTK display lifecycle is involved.
    import ctypes as C
    from ctypes.util import find_library
    x = C.CDLL(find_library('X11') or 'libX11.so.6')
    x.XOpenDisplay.argtypes = [C.c_char_p]
    x.XOpenDisplay.restype = C.c_void_p
    x.XDefaultScreen.argtypes = [C.c_void_p]
    x.XDefaultScreen.restype = C.c_int
    x.XRootWindow.argtypes = [C.c_void_p, C.c_int]
    x.XRootWindow.restype = C.c_ulong
    x.XInternAtom.argtypes = [C.c_void_p, C.c_char_p, C.c_int]
    x.XInternAtom.restype = C.c_ulong
    x.XGetSelectionOwner.argtypes = [C.c_void_p, C.c_ulong]
    x.XGetSelectionOwner.restype = C.c_ulong
    for name in ['XDisplayWidth', 'XDisplayHeight']:
        getattr(x, name).argtypes = [C.c_void_p, C.c_int]
        getattr(x, name).restype = C.c_int
    x.XGetWindowProperty.argtypes = [
        C.c_void_p, C.c_ulong, C.c_ulong, C.c_long, C.c_long, C.c_int,
        C.c_ulong, C.POINTER(C.c_ulong), C.POINTER(C.c_int),
        C.POINTER(C.c_ulong), C.POINTER(C.c_ulong),
        C.POINTER(C.POINTER(C.c_ubyte))]
    x.XGetWindowProperty.restype = C.c_int
    x.XFree.argtypes = [C.c_void_p]
    x.XCloseDisplay.argtypes = [C.c_void_p]
    display_name = os.environ.get('DISPLAY')
    if not display_name:
        return None
    display = x.XOpenDisplay(display_name.encode())
    if not display:
        return None
    try:
        screen = x.XDefaultScreen(display)
        root = x.XRootWindow(display, screen)
        compositor = x.XGetSelectionOwner(
            display, x.XInternAtom(display, f'_NET_WM_CM_S{screen}'.encode(), 0))
        if not compositor:
            return None
        actual_type, count, remaining = C.c_ulong(), C.c_ulong(), C.c_ulong()
        fmt = C.c_int()
        data = C.POINTER(C.c_ubyte)()
        status = x.XGetWindowProperty(
            display, root, x.XInternAtom(display, b'_NET_SUPPORTING_WM_CHECK', 0),
            0, 1, 0, 0, C.byref(actual_type), C.byref(fmt), C.byref(count),
            C.byref(remaining), C.byref(data))
        try:
            wm = (C.cast(data, C.POINTER(C.c_ulong))[0]
                  if status == 0 and fmt.value == 32 and count.value == 1 and data else 0)
        finally:
            if data:
                x.XFree(data)
        width, height = x.XDisplayWidth(display, screen), x.XDisplayHeight(display, screen)
        if not wm or width <= 0 or height <= 0:
            return None
        overview = None
        if 'GNOME' in os.environ.get('XDG_CURRENT_DESKTOP', '').upper():
            from gi.repository import Gio, GLib
            bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
            reply = bus.call_sync(
                'org.gnome.Shell', '/org/gnome/Shell',
                'org.freedesktop.DBus.Properties', 'Get',
                GLib.Variant('(ss)', ('org.gnome.Shell', 'OverviewActive')),
                None, Gio.DBusCallFlags.NO_AUTO_START, 1000, None)
            overview = reply.unpack()[0]
        return wm, compositor, width, height, overview
    finally:
        x.XCloseDisplay(display)


def wait_for_desktop(probe=probe_desktop, timeout=45, settle=3,
                     now=time.monotonic, sleep=time.sleep):
    deadline = now() + timeout
    previous = None
    stable_since = None
    last_error = 'desktop not ready'
    while now() < deadline:
        try:
            state = probe()
        except Exception as error:
            state = None
            last_error = str(error)
        if state is None:
            previous = None
            stable_since = None
        elif state != previous:
            previous = state
            stable_since = now()
        elif stable_since is not None and now() - stable_since >= settle:
            print('Conky: X11 compositor and desktop geometry settled; starting blocks.', flush=True)
            return True
        sleep(0.5)
    print(f'Conky: desktop readiness timed out: {last_error}', file=sys.stderr, flush=True)
    return False


if __name__ == '__main__':
    print('Conky: waiting for X11 compositor and stable desktop...', flush=True)
    sys.exit(0 if wait_for_desktop() else 1)
