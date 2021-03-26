#!/usr/bin/env python3
# -*- coding:utf-8 -*-
'''
Copyright (c) 2021 Inspur.com, Inc. All Rights Reserved

description

Author: Jeff Li <lijinfeng01@inspur.com>
Date: 2021/03/21 13:24:08
'''

import datetime
import hashlib
import math
import os
import time
import xml.etree.ElementTree as ET

from . import helper_xml


LAST_ID = 0


def create_id():
    global LAST_ID
    if LAST_ID == 0:
        LAST_ID = math.floor(time.time())
    else:
        LAST_ID += 1
    return str(LAST_ID)


def get_file_digest(file_path):
    with open(file_path, "rb") as image:
        hasher = hashlib.md5()
        hasher.update(image.read())
        return hasher.hexdigest()


class TaskList:
    def __init__(self, name, startdate, stopdate):
        self.taskid = create_id()
        self.taskname = name
        self.tasktype = "loop"
        self.ver = ""
        self.filelist = {}
        self.programlist = []
        self.multi_task = MultiTask(0, startdate, stopdate)
        self.startdate = startdate
        self.stopdate = stopdate
        self.version = time.strftime("%Y%m%d %H%M%S")

    def save(self):
        root_dir = os.path.join(str(self.taskid), "Contents")
        os.makedirs(root_dir, exist_ok=True)
        tree = self.create_tasklist_xml()
        content = helper_xml.prettify_xml(tree)
        print(content)
        with open(os.path.join(root_dir, "tasklist.xml"), "w") as xml_file:
            xml_file.write(content)
        tree = self.create_filelist_xml()
        content = helper_xml.prettify_xml(tree)
        print(content)
        with open(os.path.join(root_dir, "filelist.xml"), "w") as xml_file:
            xml_file.write(content)
        tree = self.create_playlist_xml()
        content = helper_xml.prettify_xml(tree)
        print(content)
        with open(os.path.join(root_dir, "playlist.xml"), "w") as xml_file:
            xml_file.write(content)
        tree = self.create_tacticlist_xml()
        content = helper_xml.prettify_xml(tree)
        print(content)
        with open(os.path.join(root_dir, "tacticlist.xml"), "w") as xml_file:
            xml_file.write(content)

        img_dir = os.path.join(root_dir, "Files")
        os.makedirs(img_dir, exist_ok=True)
        for file_info in self.filelist.values():
            file_path = os.path.join(img_dir, file_info["name"])
            with open(file_path, "wb") as image_file:
                image_file.write(file_info["data"])

    def create_tasklist_xml(self):
        root = ET.Element("config")
        tree = ET.ElementTree(root)
        elm = self.to_et()
        root.append(elm)
        return root

    def consolidate(self):
        self.version = time.strftime("%Y%m%d %H%M%S")

    def load_filelist(self, xml_path):
        tree = ET.parse(xml_path)
        root = tree.getroot()
        file_elms = tree.findall("*/file")
        self.filelist.clear()
        for file_elm in tree.findall("*/file"):
            image_file = {
                "crc": file_elm.get("crc"),
                "name": file_elm.get("name"),
                "size": file_elm.get("size"),
            }
            image_path = os.path.join("Contents", "Files", image_file["name"])
            with open(image_path, "rb") as f:
                image_file["data"] = f.read()
            digest = get_file_digest(image_path)
            self.filelist[digest] = image_file

    def create_program(self, name, image_paths):
        program = Program(name)
        self.programlist.append(program)
        images = self.search_image(image_paths)
        program.create_imagerect(images)
        return program

    def search_image(self, file_path_list):
        images = []
        for file_path in file_path_list:
            digest = get_file_digest(file_path)
            print(file_path)
            image = self.filelist[digest]
            image["orig_name"] = os.path.basename(file_path)
            images.append(image)
        return images

    def add_schedule(self, program, starttime, week_days, stoptime=None, minutes=None):
        if stoptime is None:
            start = datetime.datetime.strptime(starttime, "%H:%M:%S")
            delta = datetime.timedelta(seconds=(minutes * 60 - 1))
            stop = start + delta
            stoptime = stop.strftime("%H:%M:%S")
        else:
            stop = datetime.datetime.strptime(stoptime, "%H:%M:%S")
            delta = datetime.timedelta(seconds=1)
            stop = stop - delta
            stoptime = stop.strftime("%H:%M:%S")
        self.multi_task.add_program(program, starttime, stoptime, week_days)

    def to_et(self):
        elm = ET.Element("tasklist")
        elm.set("taskid", self.taskid)
        elm.set("taskname", self.taskname)
        elm.set("tasktype", self.tasktype)
        elm.set("ver", ".".join([self.version] * 4))
        return elm

    def create_filelist_xml(self):
        root = ET.Element("config")
        filelist = ET.SubElement(root, "filelist")
        filelist.set("taskid", self.taskid)
        filelist.set("taskname", self.taskname)
        filelist.set("ver", self.version)
        for file_info in self.filelist.values():
            elm = ET.SubElement(filelist, "file")
            elm.set("crc", file_info["crc"])
            elm.set("name", file_info["name"])
            elm.set("size", file_info["size"])
        return root

    def create_playlist_xml(self):
        root = ET.Element("config")
        filelist = ET.SubElement(root, "programlist")
        filelist.set("taskid", self.taskid)
        filelist.set("taskname", self.taskname)
        filelist.set("ver", self.version)
        for program in self.programlist:
            root.append(program.to_et())
        elm = ET.SubElement(root, "meta")
        elm.append(ET.Element("files"))
        elm.append(ET.Element("fonts"))
        elm.append(ET.Element("tts"))
        return root

    def create_tacticlist_xml(self):
        root = ET.Element("config")
        attribute = {
            "taskid": self.taskid,
            "taskname": self.taskname,
            "ver": self.version,
        }
        root.append(ET.Element("task", attrib=attribute))
        root.append(self.multi_task.to_et())
        return root


class Program:
    def __init__(self, name):
        self.program_id = create_id()
        self.name = name
        self.state = "play"
        self.width = "1080"
        self.height = "1920"
        self.imagerects = []

    def create_imagerect(self, images):
        imagerect = ImageRect()
        imagerect.add_images(images)
        self.imagerects.append(imagerect)
        return imagerect

    def to_et(self):
        attribute = {
            "height": self.height,
            "id": self.program_id,
            "name": self.name,
            "state": self.state,
            "width": self.width,
        }
        elm = ET.Element("program", attrib=attribute)
        for imagerect in self.imagerects:
            elm.append(imagerect.to_et())
        return elm


class ImageRect:
    def __init__(self):
        self.rectid = create_id()
        self.rectname = "Image"
        self.interactive = "off"
        self.jump = "0"
        self.layer = "1"
        self.nH = "1920"
        self.nW = "1080"
        self.nX = "0"
        self.nY = "0"
        self.img_list = []

    def add_images(self, images):
        self.img_list.clear()
        self.img_list.extend(images)

    def to_et(self):
        attribute = {
            "interactive": self.interactive,
            "jump": self.jump,
            "layer": self.layer,
            "nH": self.nH,
            "nW": self.nW,
            "nX": self.nX,
            "nY": self.nY,
            "rectid": self.rectid,
            "rectname": self.rectname,
        }
        elm = ET.Element("imagerect", attrib=attribute)
        for index, file_info in enumerate(self.img_list):
            attribute = {
                "cutin": "normal",
                "effecttime": "2",
                "name": file_info["orig_name"],
                "path": file_info["name"],
                "position": "full",
                "scroll": "normal",
                "seq": str(index),
                "showtime": "5",
                "swap": "normal",
            }
            elm.append(ET.Element("img", attrib=attribute))
        return elm


class MultiTask:
    def __init__(self, multi_task_id, startdate, stopdate):
        self.multi_task_id = multi_task_id
        self.startdate = startdate
        self.stopdate = stopdate
        self.day_tasks = [DayTask(day_task_id=0, seq=index+1) for index in range(7)]

    def add_program(self, program, starttime, stoptime, week_days):
        start_week_day = self.startdate.tm_wday
        for index, day_task in enumerate(self.day_tasks):
            week_day = (start_week_day + index) % 7
            if week_day in week_days:
                day_task.add_program(program, starttime, stoptime)

    def to_et(self):
        attribute = {
            "id": str(self.multi_task_id),
            "startdate": time.strftime("%Y-%m-%d", self.startdate),
            "stopdate": time.strftime("%Y-%m-%d", self.stopdate),
        }
        elm = ET.Element("multi_task", attrib=attribute)
        for day_task in self.day_tasks:
            elm.append(day_task.to_et())
        return elm


class DayTask:
    def __init__(self, day_task_id, seq):
        self.day_task_id = day_task_id
        self.seq = seq
        self.pro_serial_list = []

    def add_program(self, program, starttime, stoptime):
        pro_serial = None
        for pro_serial_temp in self.pro_serial_list:
            if pro_serial_temp.starttime == starttime and pro_serial_temp.stoptime == stoptime:
                pro_serial = pro_serial_temp
                break
        if pro_serial is None:
            pro_serial = ProSerial(self.day_task_id, starttime, stoptime)
            self.pro_serial_list.append(pro_serial)
        pro_serial.add_program(program.program_id)

    def to_et(self):
        attribute = {
            "id": str(self.day_task_id),
            "seq": str(self.seq),
        }
        elm = ET.Element("day_task", attrib=attribute)
        for pro_serial in sorted(self.pro_serial_list, key=lambda k: k.starttime):
            elm.append(pro_serial.to_et())
        return elm


class ProSerial:
    def __init__(self, pro_serial_id, starttime, stoptime):
        self.pro_serial_id = pro_serial_id
        self.starttime = starttime
        self.stoptime = stoptime
        self.program_ids = []

    def add_program(self, program_id):
        self.program_ids.append(program_id)

    def to_et(self):
        attribute = {
            "id": str(self.pro_serial_id),
            "starttime": self.starttime,
            "stoptime": self.stoptime,
        }
        elm = ET.Element("pro_serial", attrib=attribute)
        for program_id in self.program_ids:
            attribute = {
                "id": str(program_id),
                "play_count": "0",
            }
            elm.append(ET.Element("program", attrib=attribute))
        return elm
