#!/usr/bin/python

#"C:\Python\Python\python.exe" "C:\Python\SuSl_PPS\Gcode_modifiers\Gcode_fuzzy_skin.py" "C:\Python\SuSl_PPS\Front_halve_fuzzy.py";

import sys
import os
import re
import importlib.util
import math
import random


INWARDS = -1
DEFAULT = 0
OUTWARDS = 1

filename = sys.argv[-1]

modifier_file_name = sys.argv[-2]

spec = importlib.util.spec_from_file_location("fuzzy_skin_conditions", modifier_file_name)
modifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(modifier)

nozzle_diameter = float(os.environ["SLIC3R_NOZZLE_DIAMETER"])
fuzzy_skin_point_dist = os.environ["SLIC3R_FUZZY_SKIN_POINT_DIST"]
if fuzzy_skin_point_dist[-1] == "%":
    fuzzy_skin_point_dist = 0.01 * nozzle_diameter * float(fuzzy_skin_point_dist[:-1:])
else:
    fuzzy_skin_point_dist = float(fuzzy_skin_point_dist)

fuzzy_skin_thickness = os.environ["SLIC3R_FUZZY_SKIN_THICKNESS"]
if fuzzy_skin_thickness[-1] == "%":
    fuzzy_skin_thickness = 0.01 * nozzle_diameter * float(fuzzy_skin_thickness[:-1:])
else:
    fuzzy_skin_thickness = float(fuzzy_skin_thickness)

first_layer_height = os.environ["SLIC3R_FIRST_LAYER_HEIGHT"]
if first_layer_height[-1] == "%":
    first_layer_height = 0.01 * nozzle_diameter * float(first_layer_height[:-1:])
else:
    first_layer_height = float(first_layer_height)

layer_height = float(os.environ["SLIC3R_LAYER_HEIGHT"])


perimeter_reverse = bool(os.environ["SLIC3R_PERIMETER_REVERSE"])

objects = {}

def layer_parity(z_height) -> float:
    return 1 - (round((z_height - first_layer_height) / layer_height) % 2) * 2.0

def coord_distance(coords_1: list, coords_2: list):
    return math.sqrt((coords_1[0] - coords_2[0]) ** 2 + (coords_1[1] - coords_2[1]) ** 2)


class Line_Analiser():
    def __init__(self):
        self.coords_start = [0, 0]
        self.coords_end = [0, 0]
        self.z_height = 0
        self.layer_height = 0
        self.feature_type = "Custom"
        self.e = 0
        self.z = 0
        self.retracted = False
        self.gcode_commands = []
        self.object_id = ""
        self.seed = 0
        self.parity = 0

    def analyse_gcode_line(self, line: str):
        match_comment = re.search(r"^;[^;\n]*?$", line)
        if match_comment:
            self.analyse_gcode_comment(line)

        match_g_code = re.search(r"^G(1|92) [^;\n]*$", line)
        if match_g_code:
            self.analyse_gcode_g_code(line)

        if not match_comment and not match_g_code:
            self.gcode_commands = [line]

    def analyse_gcode_comment(self, line: str):
        match = re.search(r"^; object(.+)$", line)
        if match:
            match = re.search(r'"id":"([^"]*?)"', line)
            if match:
                object_id = match.group(1)
            match = re.search(r'"object_center":\[(\d*(\.\d*)?),(\d*(\.\d*)?)', line)
            if match:
                object_center_x = float(match.group(1))
                object_center_y = float(match.group(3))
            objects[object_id] = [object_center_x, object_center_y]

        match = re.search(r"^; printing object ([^;\n]*)$", line)
        if match:
            self.object_id = match.group(1)
            random.seed(self.seed)

        match = re.search(r"^;TYPE:(.+)$", line)
        if match:
            self.feature_type = match.group(1)

        match = re.search(r"^;Z:(\d*(\.\d*)?)$", line)
        if match:
            self.z_height = float(match.group(1))
            self.set_z()
            self.seed += 1
            self.parity = layer_parity(self.z_height)

        match = re.search(r"^;HEIGHT:(\d*(\.\d*)?)$", line)
        if match:
            self.layer_height = float(match.group(1))
            self.set_z()

        self.gcode_commands = [line]

    def set_z(self):
        self.z = self.z_height - 0.5 * self.layer_height

    def analyse_gcode_g_code(self, line:str):
        is_travel_move = False
        match = re.search(r"^G92 [^;\n]*?E(\d*(\.\d*)?)[^;\n]*$", line)
        if match:
            self.e = float(match.group(1))
            self.gcode_commands = [line]
            return

        match = re.search(r"^G1 [^E;\n]*?Z(\d*(\.\d*)?)[^E;\n]*$", line)
        if match:
            self.gcode_commands = [line]
            return

        match = re.search(r"^G1 [^;\n]*?X(\d*(\.\d*)?)[^;\n]*$", line)
        if match:
            self.coords_start[0] = self.coords_end[0]
            self.coords_end[0] = float(match.group(1))

        match = re.search(r"^G1 [^;\n]*?Y(\d*(\.\d*)?)[^;\n]*$", line)
        if match:
            self.coords_start[1] = self.coords_end[1]
            self.coords_end[1] = float(match.group(1))

        match = re.search(r"^G1 [^;\n]*?E(-?\d*(\.\d*)?)[^;\n]*$", line)
        if match:
            self.e = float(match.group(1))
            if self.e <= 0:
                self.retracted = True
                self.gcode_commands = [line]
                return
            else:
                match = re.search(r"X|Y", line)
                if not match:
                    self.retracted = False
                    self.gcode_commands = [line]
                    return

        else:
            self.gcode_commands = [line]
            return

        if self.object_id == "":
            self.gcode_commands = [line]
            return

        self.gcode_commands = []
        coords_start = [self.coords_start[i] - objects[self.object_id][i] for i in range(2)]
        coords_end = [self.coords_end[i] - objects[self.object_id][i] for i in range(2)]
        segments = modifier.fuzzy_skin_conditions(coords_start, coords_end, self.z, self.feature_type)
        dist = coord_distance(self.coords_start, self.coords_end)
        if dist < 0.000_000_1:
            self.gcode_commands = [line]
            return
        inv_dist = 1 / dist
        section = self.e * inv_dist # area of the cross section
        normal = [(self.coords_end[1] - self.coords_start[1]) * inv_dist, (self.coords_start[0]-self.coords_end[0]) * inv_dist]
        lamda = 0
        amplitude_prev = 0
        for segment in segments:
            if segment[1]:
                #if line segment has fuzzy skin applied
                segment_length = (segment[0] - lamda) * dist
                fs_segments = max(2, round(segment_length / fuzzy_skin_point_dist))
                fs_length = segment_length / fs_segments
                for fs_segment in range(1, fs_segments):
                    amplitude = (2.0 * random.random() - 1) * fuzzy_skin_thickness
                    if segment[2] == INWARDS:
                        amplitude = abs(amplitude) * self.parity
                    if segment[2] == OUTWARDS:
                        amplitude = -abs(amplitude) * self.parity
                    fs_segment_length = math.sqrt((amplitude - amplitude_prev) ** 2 + fs_length ** 2)
                    e = fs_segment_length * section
                    theta = lamda + (segment[0] - lamda) * fs_segment / fs_segments
                    x = theta * self.coords_end[0] + (1 - theta) * self.coords_start[0] + amplitude * normal[0]
                    y = theta * self.coords_end[1] + (1 - theta) * self.coords_start[1] + amplitude * normal[1]
                    self.gcode_commands.append(f"G1 X{x:.3f} Y{y:.3f} E{e:.5f}\n")
                    amplitude_prev = amplitude
                fs_segment_length = math.sqrt(amplitude_prev ** 2 + fs_length ** 2)
                e = fs_segment_length * section
                x = segment[0] * self.coords_end[0] + (1 - segment[0]) * self.coords_start[0]
                y = segment[0] * self.coords_end[1] + (1 - segment[0]) * self.coords_start[1]
                self.gcode_commands.append(f"G1 X{x:.3f} Y{y:.3f} E{e:.5f}\n")
            else:
                #if line segment remains straight
                x = segment[0] * self.coords_end[0] + (1 - segment[0]) * self.coords_start[0]
                y = segment[0] * self.coords_end[1] + (1 - segment[0]) * self.coords_start[1]
                e = (segment[0] - lamda) * self.e
                self.gcode_commands.append(f"G1 X{x:.3f} Y{y:.3f} E{e:.5f}\n")
            lamda = segment[0]
        


with open(filename, "r") as file:
    lines = file.readlines()

print(f"Original file: {len(lines)} lines\n")

milestones = [round(0.1 * (len(lines) - 1) * i) for i in range(1, 11)]

line_analiser = Line_Analiser()

with open(filename, "w") as file:
    for i,line in enumerate(lines):
        if i in milestones:
            print("\u2588\u2588", end="")
        line_analiser.analyse_gcode_line(line)
        file.writelines(line_analiser.gcode_commands)

print()
print("==================================================")