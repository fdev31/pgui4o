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
SWIPE_ANIM_SPEED = 10 # in px/ frame

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
        self.pages = len(widgets)
        self._running = True
        self._cur_page = 0
        self.last_update = 0
        self.size = [RESX, RESY]
        pygame.init()
        self._screen = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF)
        self._backgrounds = [pygame.image.load(getResourcesPath('screen%d.png'%(i+1))).convert() for i in range(self.pages)]
        self.set_font(20)
        self.event_queue = 0
        self.grab_mode = False
        self.dirty = False
        self.printer = PrintCommands('http://%s/'%OCTOPRINT_HOSTNAME, PRINT_API_KEY, PORT, BAUD)
        self.mouse_pos = (0, 0)
        self.default_text_color = (0, 0, 0)

        if DRY_RUN:
            self.printer.http = None
        else:
            if not DEBUG_UI:
                self.ui_toggle_fullscreen()

        self.ui_actions = { 'quit': self.quit }

    def set_font(self, size=20):
        self._font_size = size
        self.font = pygame.font.Font(getResourcesPath("impact.ttf"), self._font_size)
        #self.font = pygame.font.SysFont("impact", self._font_size)

    def ui_toggle_fullscreen(self):
        pygame.display.toggle_fullscreen()

    def ui_main_page(self):
        self._cur_page = 0

    def ui_next_page(self):
        self._cur_page = (self._cur_page+1)%self.pages
        if self._cur_page == 0:
            self._cur_page = 1 # avoids showing splash

    def get_next_page(self, offset):
        if offset < 0:
            if self._cur_page == 1:
                return self.pages-1
            return self._cur_page - 1
        else:
            if self._cur_page + 1 >= self.pages:
                return 1
            else:
                return self._cur_page + 1

    def on_click_release(self, x, y):
        old_pos = self.click_grab_start

        dist = math.sqrt((x-old_pos[0])**2+ (y-old_pos[1])**2)
        if dist > MIN_SWIPE_DISTANCE:
            if old_pos[0] > x:
                new_page = self.get_next_page(1)
                direction = -1
            elif old_pos[0] < x:
                new_page = self.get_next_page(-1)
                direction = 1
            else:
                direction = 0
                new_page = self._cur_page # don't change by default

            # animate the rest of the scrolling
            if direction:
                if direction < 0:
                    r = range(x, self.click_grab_start[0]-self.size[0],  direction*SWIPE_ANIM_SPEED)
                else:
                    r = range(x, self.click_grab_start[0]+self.size[0], direction*SWIPE_ANIM_SPEED)
                for xo in r:
                    self.click_grab_cur = (xo, 0)
                    self.draw_ui()
            self._cur_page = (new_page%self.pages)
            self.dirty = True
        else:
            for coords, name in self.actions[self._cur_page].items():
                if x > coords[0] and x < coords[2] and y > coords[1] and y < coords[3]:
                    if name.startswith('ui_'):
                        fn = getattr(self, name, None)
                    else:
                        fn = getattr(self.printer, name, None)

                    if fn:
                        try:
                            action = fn()
                        except Exception as e:
                            self.event_processed = -1
                            print("Error while running %s: %s"%(name, e))
                        else:
                            self.dirty = True
                            self.event_processed = True
                            if self.event_queue < 200:
                                self.event_queue += 50
                            if isinstance(action, set):
                                for act in action:
                                    self.ui_actions[act]()
                    else:
                        print("No such command: %s"%name)
                    break # stop on first match

        self.grab_mode = False

    def on_click(self, x, y):
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
                elif event.unicode == '+':
                    self.set_font(self._font_size +1)
                    self.event_processed = True
                elif event.unicode == '-':
                    self.set_font(self._font_size -1)
                    self.event_processed = True
                elif event.unicode == 'f':
                    self.ui_toggle_fullscreen()
                    self.event_processed = True
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.on_click(*event.pos)
        elif event.type == pygame.MOUSEBUTTONUP:
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
            color = self.default_text_color
        text = self.font.render(text, True, color)
        self._screen.blit(text, (x, y))

    def draw_ui(self):
        if self.grab_mode:
            ox = self.click_grab_cur[0] - self.click_grab_start[0]
        else:
            ox = 0

        if ox > 0:
            self._screen.blit(self._backgrounds[self.get_next_page(-1)], (ox-self.size[0], 0))
        elif ox < 0:
            self._screen.blit(self._backgrounds[self.get_next_page(1)], (ox+self.size[0], 0))

        self._screen.blit(self._backgrounds[self._cur_page], (ox, 0))

        for text in self.widgets[self._cur_page]['texts']:
            self.render_text(text[2](self), ox + text[0], text[1])

        for rect in self.widgets[self._cur_page]['rects']:
            pos, color = rect(self)
            pos = list(pos)
            pos[0] += ox
            pygame.draw.rect(self._screen, color, pos)

        # Debugging overlay
        if DEBUG_UI and not self.grab_mode:
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

    def quit(self):
        self._running = False

    def run(self):
        while( self._running ):
            self.event_processed = False
            for event in pygame.event.get():
                self.process_event(event)
            self.update()
            if self.dirty or self.event_processed or self.event_queue or self.grab_mode or DEBUG_UI=='repaint':
                self.draw_ui()
                self.dirty = False
                if self.event_queue:
                    self.event_queue -= 10
            else:
                pygame.time.wait(200)
        pygame.quit()

if __name__ == "__main__" :
    fp = getResourcesPath('screens.py')
    # TODO: cleaner theme loading
    exec(open(fp).read())
    theApp = App(actions = actions, widgets = widgets)
    theApp.default_text_color = text_color
    theApp.run()

