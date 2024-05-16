#!/usr/bin/python

#"C:\Python\Python\python.exe" "C:\Python\SuSl_PPS\Gcode_remove_lines.py" "C:\Python\SuSl_PPS\Dice_tower\Dice_tower.py";

import enum
import sys
import os
import re
import importlib.util

print("==================================================")

filename = sys.argv[-1]

modifier_file_name = sys.argv[-2]

spec = importlib.util.spec_from_file_location("print_conditions", modifier_file_name)
modifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(modifier)

def get_retract_value(variable:str, default_value:float):
    temp = os.environ["SLIC3R_FILAMENT_" + variable.capitalize()]
    if temp == "nil":
        temp = os.environ["SLIC3R_" + variable.capitalize()]
        if temp == "nil":
            temp = default_value
    return float(temp)

retract_length = get_retract_value("retract_length", 0)
retract_speed = get_retract_value("retract_speed", 40)
retract_restart_extra = get_retract_value("retract_restart_extra", 0)
deretract_speed = get_retract_value("deretract_speed", 40)

travel_speed = float(os.environ["SLIC3R_TRAVEL_SPEED"])

objects = {}

class Line_Analiser():
    def __init__(self):
        self.coords_start = [0, 0]
        self.coords_end = [0, 0]
        self.z_height = 0
        self.layer_height = 0
        self.feature_type = "Custom"
        self.e = 0
        self.speed = 0
        self.z = 0
        self.retracted = False
        self.gcode_commands = []
        self.object_id = ""

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

        match = re.search(r"^;TYPE:(.+)$", line)
        if match:
            self.feature_type = match.group(1)

        match = re.search(r"^;Z:(\d*(\.\d*)?)$", line)
        if match:
            self.z_height = float(match.group(1))
            self.set_z()

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

        match = re.search(r"^G1 [^;\n]*?F(\d*(\.\d*)?)[^;\n]*$", line)
        if match:
            self.speed = float(match.group(1))

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
        segments = modifier.print_conditions(coords_start, coords_end, self.z, self.feature_type)
        lamda = 0
        for segment in segments:
            if segment[1]: # if line segment stays
                if self.retracted:
                    x = lamda * self.coords_end[0] + (1 - lamda) * self.coords_start[0]
                    y = lamda * self.coords_end[1] + (1 - lamda) * self.coords_start[1]
                    self.gcode_commands.append(f"G1 F{60 * travel_speed}\n")
                    self.gcode_commands.append(f"G1 X{x:.3f} Y{y:.3f}\n")
                    self.gcode_commands.append(f"G1 E{(retract_length + retract_restart_extra):.5f} F{60 * deretract_speed}\n")
                    self.gcode_commands.append(f"G1 F{self.speed}\n")
                    self.retracted = False
                x = segment[0] * self.coords_end[0] + (1 - segment[0]) * self.coords_start[0]
                y = segment[0] * self.coords_end[1] + (1 - segment[0]) * self.coords_start[1]
                self.gcode_commands.append(f"G1 X{x:.3f} Y{y:.3f} E{((segment[0] - lamda) * self.e):.5f}\n")
                lamda = segment[0]
            else: # if line segment is removed
                if not self.retracted:
                    self.gcode_commands.append(f"G1 E{(-retract_length):.5f} F{60 * retract_speed}\n")
                    self.retracted = True
                lamda = segment[0]
        


with open(filename, "r") as file:
    lines = file.readlines()

print(f"Original file: {len(lines)} lines\n")

milestones = [round(0.1 * (len(lines) - 1) * i) for i in range(1, 11)]

line_analiser = Line_Analiser()

with open(filename, "w") as file:
    for i, line in enumerate(lines):
        if i in milestones:
            print("\u2588\u2588", end="")
        line_analiser.analyse_gcode_line(line)
        file.writelines(line_analiser.gcode_commands)

print()
print("==================================================")