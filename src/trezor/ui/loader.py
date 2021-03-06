import utime
from trezor import ui


DEFAULT_LOADER = {
    'bg-color': ui.BLACK,
    'fg-color': ui.WHITE,
    'icon': None,
    'icon-fg-color': None,
}
DEFAULT_LOADER_ACTIVE = {
    'bg-color': ui.BLACK,
    'fg-color': ui.LIGHT_GREEN,
    'icon': None,
    'icon-fg-color': None,
}

LOADER_MSEC = const(1000)


class Loader():

    def __init__(self, normal_style=None, active_style=None):
        self.start_ticks_ms = None
        self.normal_style = normal_style or DEFAULT_LOADER
        self.active_style = active_style or DEFAULT_LOADER_ACTIVE

    def start(self):
        self.start_ticks_ms = utime.ticks_ms()
        ui.display.bar(0, 0, 240, 240 - 48, ui.BLACK)

    def stop(self):
        ui.display.bar(0, 0, 240, 240 - 48, ui.BLACK)
        ticks_diff = utime.ticks_ms() - self.start_ticks_ms
        self.start_ticks_ms = None
        return ticks_diff >= LOADER_MSEC

    def render(self):
        if self.start_ticks_ms is None:
            return False

        progress = min(utime.ticks_ms() - self.start_ticks_ms, LOADER_MSEC)
        if progress == LOADER_MSEC:
            style = self.active_style
        else:
            style = self.normal_style

        if style['icon'] is None:
            ui.display.loader(progress, style['fg-color'], style['bg-color'])
        elif style['icon-fg-color'] is None:
            ui.display.loader(
                progress, style['fg-color'], style['bg-color'], style['icon'])
        else:
            ui.display.loader(
                progress, style['fg-color'], style['bg-color'], style['icon'], style['icon-fg-color'])

        return True
