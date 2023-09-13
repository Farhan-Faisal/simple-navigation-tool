"""
@File   : client.py
@Time   : 2021 April
@Author : Tianyu Zhang
@Contact: tzhang6@ualberta.ca
@License: Copyright (c) Tianyu Zhang.
          This code is presented in an educational context for personal use
          and study and should not be shared, distributed, or sold in print or
          digitally outside the course without permission.

          The above copyright notice and this permission notice shall be
          included in all copies or substantial portions of the code.
"""

import math
import time
import sys
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame

python_input = input
python_print = print


def print(*objects):
    output_str = ""
    for obj in objects:
        output_str += str(obj) + ' '
    outpipe.write(output_str.rstrip(' ') + '\n')
    python_print(output_str.rstrip(' '))
    outpipe.flush()


def input(*objects):
    input_str = ""
    while True:
        char = inpipe.read(1)
        if char == '\n':
            break
        input_str += char
    python_print(input_str)
    return input_str


def deg2pixel(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    x_pixel = int(((lon_deg + 180.0) / 360.0 * n - map_tile_default[zoom][0]) * 256)
    y_pixel = int(((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n - map_tile_default[zoom][2]) * 256)
    return x_pixel, y_pixel


def pixel2deg(x_pixel, y_pixel, zoom):
    n = 2.0 ** zoom
    lon_deg = (x_pixel / 256 + map_tile_default[zoom][0]) / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * (y_pixel / 256 + map_tile_default[zoom][2]) / n)))
    lat_deg = math.degrees(lat_rad)
    return lat_deg, lon_deg


class Dot:
    def __init__(self, x_pixel, y_pixel, zoom, color):
        self.__lat, self.__lon = pixel2deg(x_pixel, y_pixel, zoom)
        self.__color = color

    def update(self, zoom, current_map):
        pygame.draw.circle(current_map, self.__color, deg2pixel(self.__lat, self.__lon, zoom), 5)

    def get_geo(self):
        return int(self.__lat * 100000), int(self.__lon * 100000)

    def __repr__(self):
        return "%.6f %.6f" % (self.__lat, self.__lon)


class Route:
    def __init__(self, waypoints_geolocation, zoom, color):
        self.__waypoints = waypoints_geolocation
        self.__zoom = zoom
        self.__color = color

    def update(self, zoom, current_map):
        waypoints_pixel = [deg2pixel(*point, zoom) for point in self.__waypoints]
        pygame.draw.lines(current_map, self.__color, False, waypoints_pixel, 2)


class Map:
    def __init__(self, init_zoom, init_location):
        self.__zoom = init_zoom
        self.__backup_map = pygame.image.load(os.path.join(base_path, "map/%d.png" % init_zoom)).convert()
        self.__current_map = self.__backup_map.copy()
        self.__offsets = list(deg2pixel(*init_location, init_zoom))
        self.__display_range = (500, 500)
        self.__display_limit = (deg2pixel(map_boundary[0], map_boundary[2], init_zoom))
        self.__size = (deg2pixel(map_boundary[1], map_boundary[2], init_zoom),
                       deg2pixel(map_boundary[0], map_boundary[3], init_zoom))
        self.__font = pygame.font.SysFont('arial', 60)
        self.__dots = list()
        self.__routes = list()
        self.__color_index = 0
        self.__report = False

        self.__default_control = {pygame.K_w: (0, -1),
                                  pygame.K_s: (0, 1),
                                  pygame.K_a: (-1, 0),
                                  pygame.K_d: (1, 0)}

    def show(self):
        screen.blit(self.__current_map, (0, 0), (self.__offsets, self.__display_range))
        self.show_location()
        self.show_msg("Zoom: %d" % (self.__zoom - 10))

    def move_map(self, keys):
        for key in self.__default_control:
            if keys[key]:
                for i in range(2):
                    self.__offsets[i] = min(self.__size[1][i] - self.__display_range[i],
                                            max(self.__size[0][i],
                                                self.__offsets[i] + self.__default_control[key][i]
                                                )
                                            )

    def drag_map(self, buttons):
        if buttons[0]:
            movement = pygame.mouse.get_rel()
            for i in range(2):
                self.__offsets[i] = min(self.__size[1][i] - self.__display_range[i],
                                        max(self.__size[0][i],
                                            self.__offsets[i] - movement[i]
                                            )
                                        )

    def add_dot(self, cursor):
        new_dot = Dot(cursor[0] + self.__offsets[0],
                      cursor[1] + self.__offsets[1],
                      self.__zoom,
                      colors[self.__color_index])
        new_dot.update(self.__zoom, self.__current_map)
        self.__dots.append(new_dot)
        self.__report = True

    def get_mouse_lat_lon(self):
        cursor = pygame.mouse.get_pos()
        return pixel2deg(cursor[0] + self.__offsets[0], cursor[1] + self.__offsets[1], self.__zoom)

    def generate_text_img(self, text):
        text = self.__font.render(text, True, pygame.Color('white'), pygame.Color('black'))
        multiplier = (screen.get_height() - self.__display_range[1]) / text.get_height()
        return pygame.transform.scale(text, (int(text.get_width() * multiplier), 20))

    def show_location(self):
        lat_lon = self.get_mouse_lat_lon()
        text = self.generate_text_img("%.6f, %.6f" % (lat_lon[0], lat_lon[1]))
        screen.blit(text, (0, self.__display_range[1]))

    def show_msg(self, msg):
        text = self.generate_text_img(msg)
        screen.blit(text, (screen.get_width() - text.get_width(), self.__display_range[1]))

    def dot_monitor(self):
        if not self.__dots or len(self.__dots) % 2 or not self.__report:
            return False

        self.__report = False
        self.__color_index = (self.__color_index + 1) % len(colors)
        return self.__dots[-2:]

    def add_route(self, waypoints):
        route = Route(waypoints, self.__zoom, colors[self.__color_index - 1])
        route.update(self.__zoom, self.__current_map)
        self.__routes.append(route)

    def map_refresh(self):
        self.__current_map = self.__backup_map.copy()
        self.__dots = list()
        self.__routes = list()

    def change_zoom(self, button):
        if (button != 4 or self.__zoom == 15) and (button != 5 or self.__zoom == 11):
            return
        self.show_msg("Loading ...")
        pygame.display.update()
        cursor = pygame.mouse.get_pos()
        lat_lon = self.get_mouse_lat_lon()
        self.__zoom -= button * 2 - 9
        self.__backup_map = pygame.image.load(os.path.join(base_path, "map/%d.png" % self.__zoom)).convert()
        self.__current_map = self.__backup_map.copy()
        self.__size = (deg2pixel(map_boundary[1], map_boundary[2], self.__zoom),
                       deg2pixel(map_boundary[0], map_boundary[3], self.__zoom))
        pixel = deg2pixel(*lat_lon, self.__zoom)
        for i in range(2):
            self.__offsets[i] = min(self.__size[1][i] - self.__display_range[i],
                                    max(self.__size[0][i], pixel[i] - cursor[i]))
        for dot in self.__dots:
            dot.update(self.__zoom, self.__current_map)
        for route in self.__routes:
            route.update(self.__zoom, self.__current_map)


class Window:

    def __init__(self):
        self.timer = pygame.time.Clock()
        self.terminate = False
        self.map = Map(initial_zoom, initial_top_left)
        self.mouse_down_pos = None

    def run(self):
        while not self.terminate:
            self.handle_events()
            self.frame_update()
            self.show_current_frame()
            self.timer.tick(60)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.terminate = True
            elif event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
                if len(test_default[sys.argv[1]]) == 0:
                    self.terminate = True
                else:
                    for dot in test_default[sys.argv[1]].pop(0):
                        self.map.add_dot(dot)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                pygame.mouse.get_rel()
                if event.button == 1:
                    self.mouse_down_pos = event.pos
                self.map.change_zoom(event.button)
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and self.mouse_down_pos == event.pos:
                    # python_print("This is:", event.pos)
                    self.map.add_dot(event.pos)
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_r:
                    self.map.map_refresh()
                elif event.key == pygame.K_q:
                    self.map.change_zoom(4)
                elif event.key == pygame.K_e:
                    self.map.change_zoom(5)

    def frame_update(self):
        if pygame.key.get_focused():
            self.map.move_map(pygame.key.get_pressed())
        if pygame.mouse.get_focused():
            self.map.drag_map(pygame.mouse.get_pressed())
        dots = self.map.dot_monitor()
        if dots:
            self.map.show_msg("Calculating Route ...")
            pygame.display.update()
            self.msg_printing(*dots)

    def msg_printing(self, start, end):
        python_print("+++++++ Sending to the client +++++++")
        print(str(start) + '\n' + str(end))
        python_print("+++++ Receiving from the client +++++")

        route = list()
        while True:
            waypoint = input().split(' ')
            if waypoint == ["E"]:
                if len(route) != 1:
                    break
                else:
                    print("No enough waypoints. Please start over")
                    route = list()
                    continue
            try:
                waypoint = tuple(map(float, waypoint))
                if len(waypoint) != 2:
                    raise ValueError
            except ValueError:
                print("Wrong format or invalid position.")
            else:
                route.append(waypoint)
        
        python_print("+++++++++++++++ Done! +++++++++++++++")

        if len(route):
            self.map.add_route(route)

    def show_current_frame(self):
        screen.fill(0)
        self.map.show()
        pygame.display.update()


if __name__ == '__main__':
    initial_zoom = 12
    if len(sys.argv) == 2 and sys.argv[1] == "stdin":
        print = python_print
        input = python_input
    else:
        outpipe = open("inpipe", 'w')

        while not os.path.exists("outpipe"):
            python_print("Waiting for the creation of outpipe")
            time.sleep(1)

        inpipe = open("outpipe")

    map_tile_default = {10: (188, 189, 330, 331),
                        11: (377, 379, 660, 663),
                        12: (754, 759, 1321, 1326),
                        13: (1508, 1518, 2643, 2653),
                        14: (3016, 3036, 5286, 5307),
                        15: (6032, 6072, 10573, 10614),
                        16: (12065, 12144, 21147, 21229)}
    
    initial_top_left = [53.55, -113.57]

    map_boundary = (53.398, 53.655, -113.711, -113.295)

    colors = ((242, 92, 172), (24, 213, 185), (255, 82, 61), (255, 100, 64), (255, 0, 0))

    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = ''

    pygame.init()
    screen = pygame.display.set_mode((500, 520))
    pygame.display.set_caption("Navigation - Plotter")

    Window().run()
    pygame.quit()

    print("Q")

    if print is not python_print:
        inpipe.close()
        outpipe.close()
