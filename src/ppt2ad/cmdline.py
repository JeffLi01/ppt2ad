import argparse
import collections
import os
import pkgutil
import re
import time

from . import core
from . import sched


def get_image_paths_from_folders(folders):
    image_paths = []
    for folder in folders:
        image_dir = os.path.join("images", folder)
        filenames = os.listdir(image_dir)
        filepaths = [os.path.join(image_dir, filename) for filename in filenames if filename.endswith(".JPG")]
        image_paths.extend(filepaths)
    return image_paths


def get_image_paths(category):
    image_paths = []
    mapping = {
        "早读": ["早读"],
        "午休": ["午休"],
        "课间": ["课间", "通用"],
        "课间操": ["课间操", "通用"],
        "放学": ["放学", "通用"],
    }
    if category in mapping.keys():
        folders = mapping.get(category)
        image_paths.extend(get_image_paths_from_folders(folders))
    else:
        if re.match("\d-\d", category):
            image_paths.append(os.path.join("images", "课程", category + ".JPG"))
            image_paths.extend(get_image_paths_from_folders(["班级文化"]))
    return image_paths


def main():
    """Entry point"""
    parser = argparse.ArgumentParser(prog="ppt2ad")
    version = pkgutil.get_data(__package__, "VERSION.txt").decode(encoding="utf-8")
    parser.add_argument ("-v", "--version", action="version", version=version)

    args = parser.parse_args()

    startdate = time.strptime("2021-03-15", "%Y-%m-%d")
    stopdate = time.strptime("2021-04-15", "%Y-%m-%d")
    taskname = time.strftime("%Y%m%d%H%M%S")
    tasklist = core.TaskList(taskname, startdate=startdate, stopdate=stopdate)
    tasklist.load_filelist(os.path.join("Contents", "filelist.xml"))

    programs = {}
    class_image_paths = get_image_paths_from_folders(["课程"])
    schedules = sched.calc_class_schedule_from_images(class_image_paths)
    for schedule in schedules:
        category, week_days, instance, starttime, stoptime, minutes = schedule
        if category in ["早读", "课间", "课间操", "午休", "放学"]:
            program_name = category
            program = programs.setdefault(program_name, tasklist.create_program(program_name, image_paths=get_image_paths(program_name)))
        elif category == "课程":
            program_name = "周{}第{}节".format("一二三四五"[week_days[0]], "零一二三四五六七八"[instance])
            image_category = "{}-{}".format(week_days[0] + 1, instance)
            program = programs.setdefault(program_name, tasklist.create_program(program_name, image_paths=get_image_paths(image_category)))
        tasklist.add_schedule(program, starttime=starttime, stoptime=stoptime, week_days=week_days, minutes=minutes)

    tasklist.consolidate()
    tasklist.save()


if __name__ == "__main__":
    main()
