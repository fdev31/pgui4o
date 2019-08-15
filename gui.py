#!/bin/env python

import os
import sys
import time
import math

import pygame

from printer import PrintCommands

DRY_RUN = os.getenv('DRYRUN', False) # If True do not do anything (no HTTP requests)
DEBUG_UI = os.getenv('DEBUG', False) # Show additional debugging information
THEME = os.getenv('THEME', 'default')

class UIOptions:
    def __init__(self, opts):
        self._opts = opts

    def __getattr__(self, name):
        return self._opts.get(name, False)

try:
    FileNotFoundError
except NameError: # make python2 accept python3 exceptions
    FileNotFoundError = IOError

try:
    PRINT_API_KEY = open('API_KEY.txt').read().strip() # octoprint API key to generate from settings
except FileNotFoundError:
    print('ERROR: Write your API key in "API_KEY.txt" and retry please.')
    sys.exit(-1)

PORT = os.getenv('PRINTER_PORT', '/dev/ttyACM0') # Printer port (USB serial on the Raspberry)
BAUD = int(os.getenv('PRINTER_SPEED', 115200)) # Serial baud rate
OCTOPRINT_HOSTNAME = os.getenv('OCTOPRINT_HOST', '127.0.0.1') # add /some_suffix if any

RESX, RESY = (480, 320) # window size (pixels) - should match the LCD size
PRINTER_POLLING_INTERVAL = 2.0 # seconds between periodic http requests

MIN_SWIPE_DISTANCE = 40 # minimum distance to travel to consider a swipe move
SWIPE_ANIM_SPEED = 6000.0 # some factor applied to the render time

# long click configuration
REPEAT_INITIAL_DELAY = 600
REPEAT_DELAY = 300

EVENT_REPEAT = pygame.USEREVENT + 1

def getResourcesPath(filename):
    paths = [os.path.join('themes', THEME, filename), os.path.join('assets', filename)]
    for p in paths:
        p = os.path.abspath(p)
        if os.path.exists(p):
            return p
    return filename

class App: # View

    # Binding UI items to controller commands (click dispatcher)
    # X1, Y1, X2, Y2 (top-left & bottom-right coordinates): handler function name

    def __init__(self, actions, widgets):
        self.actions = actions
        self.widgets = widgets
        self.page_count = len(widgets)
        self._running = True
        self._cur_page = 0
        self.last_update = 0
        self.size = [RESX, RESY]
        pygame.init()
        self._screen = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF)
        self._backgrounds = [pygame.image.load(getResourcesPath('screen%d.png'%(i+1))).convert() for i in range(self.page_count)]
        self.set_font(20)
        self.event_queue = 0
        self.grab_mode = False
        self.dirty = False
        self.printer = PrintCommands('http://%s/'%OCTOPRINT_HOSTNAME, PRINT_API_KEY, PORT, BAUD)
        self.mouse_pos = (0, 0)
        self.key_presses = {}
        self.last_action_failed = False
        self._ui_draw_time = 1

        if DRY_RUN:
            class _DummyHttpModule:
                def __getattr__(self, name):
                    return self
                def __call__(self, *args, **kw):
                    print("Dummy HTTP %s %s"%(args, kw))
                    raise RuntimeError('Dry run... calls will fail')

            self.printer.http = _DummyHttpModule()
        else:
            if not DEBUG_UI and not os.getenv('NOFS'):
                self.ui_toggle_fullscreen()

        self.ui_actions = { 'quit': self.quit }

    def set_font(self, size=20):
        if not getattr(self, '_font_size', None) or size != self._font_size:
            self._font_size = size
            try:
                self.font = pygame.font.SysFont("impact", self._font_size)
                print("Found the system font")
            except Exception:
                self.font = pygame.font.Font(getResourcesPath("impact.ttf"), self._font_size)

    def ui_toggle_fullscreen(self):
        pygame.display.toggle_fullscreen()

    def ui_main_page(self):
        self._cur_page = 0

    def ui_next_page(self):
        self._cur_page = (self._cur_page+1)%self.page_count
        if self._cur_page == 0:
            self._cur_page = 1 # avoids showing splash

    @property
    def available_pages(self):
        # Starts at 1 to always avoid the splash screen
        # TODO: make it configurable in the theme layout !
        available_pages = list(range(1, self.page_count))
        if self.printer.status_text == 'Printing':
            return available_pages[1:]  # first screen is MOVE, don't allow while printing
        return available_pages

    def get_next_page(self, offset, current=None):
        if current is None:
            current = self._cur_page
        elif current < 0:
            return self.get_next_page(offset, self.page_count)

        if offset < 0:
            if current == 0:
                page = self.page_count-1
            else:
                page = current - 1
        else:
            if current + 1 >= self.page_count:
                page = 0
            else:
                page = current + 1

        if page not in self.available_pages:
            return self.get_next_page(offset, page)
        else:
            return page

    def is_swiping(self, x, y):
        old_pos = self.click_grab_start
        dist = math.sqrt((x-old_pos[0])**2+ (y-old_pos[1])**2)
        if dist > MIN_SWIPE_DISTANCE:
            if (self.options.vertical_swipe and old_pos[1] > y) or (not self.options.vertical_swipe and old_pos[0] > x):
                return -1
            else:
                return 1
        return 0

    def ui_pause_popup(self, x, y):
        self.printer.pause()
        # show the popup
        self.add_popup({
            'actions' : ['pause', 'restart_print', 'cancel_print', ''],
            'captions' : ['resume', 'restart', 'cancel', 'close popup'],
            })

    def ui_remove_popup(self):
        self._popups.pop(0)
        self.set_font()

    def add_popup(self, popup):
        popups = getattr(self, '_popups', [])
        popups.append(popup)
        self._popups = popups

    def run_action_at(self, x, y):

        def action_match(name, coords):
            if x > coords[0] and x < coords[2] and y > coords[1] and y < coords[3]:
                if not name: # Allow "no op" actions
                    return True
                if name.startswith('ui_'):
                    fn = getattr(self, name, None)
                else:
                    fn = getattr(self.printer, name, None)

                if fn:
                    try:
                        try:
                            action = fn(x, y)
                        except TypeError:
                            action = fn()
                        self.event_processed = True
                        self.last_action_failed = False
                        return True # stop on first match
                    except Exception as e:
                        self.last_action_failed = True
                        action = None
                        self.event_processed = -1
                        print("Error while running %s: %s"%(name, e))
                        return True
                    finally:
                        self.dirty = True
                        if self.event_queue < 100:
                            self.event_queue += 50
                        if isinstance(action, set):
                            for act in action:
                                self.ui_actions[act]()
            return False

        if self._popups:
            actions = self._popups[0]['actions']
            height = self.size[1]/len(actions)
            for i, action in enumerate(actions):
                if action_match(action, (i, height*i, self.size[0], height*(i+1))):
                    self.ui_remove_popup()
                    break
        else:
            for coords, name in self.actions[self._cur_page].items():
                if action_match(name, coords):
                    break


    def on_click_release(self, x, y):
        direction = self.is_swiping(x, y)

        if direction and not self._repeated: # Swiping !
            new_page = self.get_next_page(-direction)

            delta = max(1, int(self._ui_draw_time * SWIPE_ANIM_SPEED))

            # animate the rest of the scrolling
            if self.options.vertical_swipe:
                if direction < 0:
                    r = range(y, self.click_grab_start[1]-self.size[1],  direction*delta)
                else:
                    r = range(y, self.click_grab_start[1]+self.size[1], direction*delta)
                for yo in r:
                    self.click_grab_cur = (0, yo)
                    self.draw_ui()
            else:
                if direction < 0:
                    r = range(x, self.click_grab_start[0]-self.size[0],  direction*delta)
                else:
                    r = range(x, self.click_grab_start[0]+self.size[0], direction*delta)
                for xo in r:
                    self.click_grab_cur = (xo, 0)
                    self.draw_ui()
            self._cur_page = (new_page%self.page_count)
        else:
            self.run_action_at(x, y)

        self.dirty = True
        self.grab_mode = False

    def on_repeat(self, x, y):
        if self.grab_mode: # first repeat
            self.grab_mode = self.is_swiping(x, y) # give swipe a last chance
            if self.grab_mode: # give up on repeat, let grab mode go
                self._repeated = False
                pygame.time.set_timer(EVENT_REPEAT, 0) # stop
                return
            else:
                self._repeated = True # turn on repeat
                pygame.time.set_timer(EVENT_REPEAT, REPEAT_DELAY) # repeat every 0.3s

        # normal repeat
        self.run_action_at(x, y)

    def on_click(self, x, y):
        self._repeated = False

        if DEBUG_UI:
            print("%d , %d"%((x, y)))
            a = getattr(self, '_seq', [])
            a.extend((x,y))
            if len(a) > 4:
                a[:] = a[-4:]
                print(tuple(a))
            self._seq = a

        self.grab_mode = True
        self.click_grab_cur = self.click_grab_start = (x, y)

    def process_event(self, event):
        if event.type == pygame.QUIT:
            self._running = False
            self.event_processed = True
        elif event.type == pygame.KEYDOWN:
            if event.unicode:
                if event.unicode in 'qQ':
                    self._running = False
                    self.event_processed = True
                elif event.unicode == 'f':
                    self.ui_toggle_fullscreen()
                    self.event_processed = True
        elif event.type == EVENT_REPEAT:
            self.on_repeat(*self.click_grab_cur)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            pygame.time.set_timer(EVENT_REPEAT, REPEAT_INITIAL_DELAY) # start repeating after 1s
            if event.button == 1:
                self.on_click(*event.pos)
        elif event.type == pygame.MOUSEBUTTONUP:
            pygame.time.set_timer(EVENT_REPEAT, 0) # remove click repeat
            self.on_click_release(*event.pos)
        elif event.type == pygame.MOUSEMOTION:
            self.mouse_pos = event.pos
            if DEBUG_UI:
                self.dirty = True
            if self.grab_mode:
                self.click_grab_cur = event.pos

    def update(self):
        if time.time() - self.last_update > PRINTER_POLLING_INTERVAL:
            self.last_update = time.time()
            self.printer_info = self.printer.fetch_status()
            self.dirty = True

    def render_text(self, text, x, y, color=None):
        if not color:
            color = self.options.default_text_color
        text = self.font.render(text, True, color)
        self._screen.blit(text, (x, y))

    def render_image(self, name, x, y):
        cache = getattr(self, '_image_cache', dict())
        if name in cache:
            image = cache[name]
        else:
            image = pygame.image.load(getResourcesPath('%s.png'%name)).convert_alpha()
            cache[name] = image

        self._screen.blit(image, (x, y))
        return image

    def draw_ui(self):
        t0 = time.time()

        # Popups

        special_mode = False
        if self._popups:
            pygame.draw.rect(self._screen, (100, 100, 120), (0, 0, self.size[0], self.size[1]))

            options = self._popups[0]['captions']
            sz = int(self.size[1]/len(options))
            self.set_font(sz-20)
            for i, label in enumerate(options):
                self.render_text(label, 20, i*sz)

            special_mode = True

        if not special_mode and self.grab_mode:
            if self.options.vertical_swipe:
                ox = 0
                oy = self.click_grab_cur[1] - self.click_grab_start[1]
            else:
                ox = self.click_grab_cur[0] - self.click_grab_start[0]
                oy = 0
        else:
            ox = 0
            oy = 0

        if not special_mode:
            if ox > 0:
                self._screen.blit(self._backgrounds[self.get_next_page(-1)], (ox-self.size[0], 0))
            elif ox < 0:
                self._screen.blit(self._backgrounds[self.get_next_page(1)], (ox+self.size[0], 0))

            if oy > 0:
                self._screen.blit(self._backgrounds[self.get_next_page(-1)], (0, oy-self.size[1]))
            elif oy < 0:
                self._screen.blit(self._backgrounds[self.get_next_page(1)], (0, oy+self.size[1]))

            self._screen.blit(self._backgrounds[self._cur_page], (ox, oy))

            for x, y, icon in self.widgets[self._cur_page]['icons']:
                pic = icon(self)
                if pic:
                    if self.options.keep_icons_on_swipe:
                        self.render_image(pic, x, y)
                    else:
                        self.render_image(pic, ox+x, oy+y)

            for text in self.widgets[self._cur_page]['texts']:
                self.render_text(text[2](self), ox + text[0], oy + text[1])

            for rect in self.widgets[self._cur_page]['rects']:
                pos, color = rect(self)
                pos = list(pos)
                pos[0] += ox
                pos[1] += oy
                pygame.draw.rect(self._screen, color, pos)

        # Event feedback
        if self.event_queue:
            if self.event_queue > 10:
                pygame.draw.circle(self._screen, (200, 78, 50, 0.1) if self.last_action_failed else (111, 199, 232, 0.1), self.click_grab_start, min(70, int(self.event_queue)))

        # Debugging overlay
        if DEBUG_UI and not (self.grab_mode or special_mode):
            for coords, name in self.actions[self._cur_page].items():
                s = pygame.Surface((coords[2]-coords[0], coords[3]-coords[1]))
                s.set_alpha(128)
                s.fill( (250, 250, 50) )
                self._screen.blit(s, coords[:2])
            if len(getattr(self, '_seq', [])) > 2:
                try:
                    s = pygame.Surface((self._seq[2]-self._seq[0], self._seq[3]-self._seq[1]))
                except Exception:
                    pass
                else:
                    s.set_alpha(200)
                    s.fill( (100,100, 250) )
                    self._screen.blit(s, self._seq[:2])

            pygame.draw.rect(self._screen, (0, 0, 0), (0, self.mouse_pos[1], self.size[0], 1))
            pygame.draw.rect(self._screen, (0, 0, 0), (self.mouse_pos[0], 0, 1, self.size[1]))

        pygame.display.flip()
        self._ui_draw_time = (self._ui_draw_time + (time.time()-t0))/2.0

    def quit(self):
        self._running = False

    def run(self):
        self._popups = []
        self._pending_actions = []
        while( self._running ):
            self.event_processed = False
            for event in pygame.event.get():
                self.process_event(event)
            self.update()
            if self.dirty or self.event_processed or self.event_queue or self.grab_mode or DEBUG_UI=='repaint':
                self.draw_ui()
                self.dirty = False
                if self.event_queue:
                    self.event_queue = max(0, self.event_queue - (self._ui_draw_time*100))
            else:
                pygame.time.wait(200)
        pygame.quit()

if __name__ == "__main__" :
    fp = getResourcesPath('layout.py')
    # TODO: cleaner theme loading
    exec(open(fp).read())
    for widget in widgets:
        for item in 'rects texts icons'.split():
            if item not in widget:
                widget[item] = []
    theApp = App(actions = actions, widgets = widgets)
    theApp.options = UIOptions(options)
    theApp.run()

