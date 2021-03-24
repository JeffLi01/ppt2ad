import argparse
import collections
import os
import pkgutil
import re
import time

from . import core


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


Schedule = collections.namedtuple("Schedule", ["starttime", "stoptime", "week_days"])


SCHEDULE = {
    "早读": [
        Schedule("06:50:00", "07:59:59", range(5))
    ],
    "课间": [
        Schedule("08:40:00", "08:49:59", range(5)),
        Schedule("10:45:00", "10:54:59", range(5)),
        Schedule("14:10:00", "14:19:59", range(4)),
        Schedule("13:40:00", "13:49:59", [4]),
        Schedule("15:05:00", "15:14:59", range(4)),
        Schedule("15:55:00", "16:04:59", range(1, 4)),
    ],
    "课间操": [
        Schedule("09:30:00", "09:59:59", range(5)),
    ],
    "午休": [
        Schedule("11:35:00", "13:29:59", range(4)),
        Schedule("11:35:00", "12:59:59", [4]),
    ],
    "放学": [
        Schedule("16:45:00", "17:29:59", range(4)),
        Schedule("14:30:00", "14:59:59", [4]),
    ]
}


def tasklist_add_by_name(tasklist, name):
    program = tasklist.create_program(name, image_paths=get_image_paths(name))
    for schedule in SCHEDULE[name]:
        tasklist.add_schedule(program, starttime=schedule.starttime, stoptime=schedule.stoptime, week_days=schedule.week_days)


def tasklist_add_class(tasklist, index, starttime, stoptime, week_days):
    for week_day in week_days:
        name = "周{}第{}节".format("一二三四五"[week_day], "零一二三四五六七八"[index])
        category = "{}-{}".format(week_day + 1, index)
        program = tasklist.create_program(name, image_paths=get_image_paths(category))
        tasklist.add_schedule(program, starttime=starttime, stoptime=stoptime, week_days=[week_day])


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

    tasklist_add_by_name(tasklist, "早读")
    tasklist_add_class(tasklist, 1, starttime="08:00:00", stoptime="08:39:59", week_days=range(5))
    tasklist_add_by_name(tasklist, "课间")
    tasklist_add_class(tasklist, 2, starttime="08:50:00", stoptime="09:29:59", week_days=range(5))
    tasklist_add_by_name(tasklist, "课间操")
    tasklist_add_class(tasklist, 3, starttime="10:00:00", stoptime="10:44:59", week_days=range(5))
    tasklist_add_class(tasklist, 4, starttime="10:55:00", stoptime="11:34:59", week_days=range(5))
    tasklist_add_by_name(tasklist, "午休")
    tasklist_add_class(tasklist, 5, starttime="13:30:00", stoptime="14:09:59", week_days=range(4))      # 周一至周四
    tasklist_add_class(tasklist, 5, starttime="13:00:00", stoptime="13:39:59", week_days=[4])           # 周五
    tasklist_add_class(tasklist, 6, starttime="14:20:00", stoptime="15:04:59", week_days=range(4))      # 周一至周四
    tasklist_add_class(tasklist, 6, starttime="13:50:00", stoptime="14:34:59", week_days=[4])           # 周五
    tasklist_add_class(tasklist, 7, starttime="15:15:00", stoptime="16:29:59", week_days=[0])           # 周一
    tasklist_add_class(tasklist, 7, starttime="15:15:00", stoptime="15:54:59", week_days=range(1, 4))   # 周二至周四
    tasklist_add_class(tasklist, 8, starttime="16:05:00", stoptime="16:34:59", week_days=range(1, 4))   # 周二至周四
    tasklist_add_by_name(tasklist, "放学")

    tasklist.consolidate()
    tasklist.save()


if __name__ == "__main__":
    main()
