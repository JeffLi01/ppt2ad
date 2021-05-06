#!/usr/bin/env python3
# -*- coding:utf-8 -*-
'''
Copyright (c) 2021 Inspur.com, Inc. All Rights Reserved

description

Author: Jeff Li <lijinfeng01@inspur.com>
Date: 2021/03/26 13:42:31
'''


import collections
import datetime
import os


Schedule = collections.namedtuple("Schedule", ["category", "week_days", "instance", "starttime", "stoptime", "minutes"])


BEFORE_CLASS_SCHEDULE = [
    Schedule("早读",   [0, 1, 2, 3, 4], 1,    "06:50:00", "08:00:00", None),
    Schedule("课间操", [0, 1, 2, 3, 4], 2,    "08:40:00", None,       30),
    Schedule("课间",   [0, 1, 2, 3, 4], 3,    "09:50:00", None,       10),
    Schedule("课间",   [0, 1, 2, 3, 4], 4,    "10:45:00", None,       10),
    Schedule("午休",   [0, 1, 2, 3,  ], 5,    "11:35:00", "13:30:00", None),
    Schedule("午休",   [            4], 5,    "11:35:00", "13:00:00", None),
    Schedule("课间",   [0, 1, 2, 3,  ], 6,    "14:10:00", None,       10),
    Schedule("课间",   [            4], 6,    "13:40:00", None,       10),
    Schedule("课间",   [0, 1, 2, 3,  ], 7,    "15:05:00", None,       10),
    Schedule("课间",   [0, 1, 2, 3,  ], 8,    "15:55:00", None,       10),
]

ELECTIVE_CLASS_SCHEDULE = Schedule("课程",   [             ], 7,    "15:15:00", None,       90)

CLASS_SCHEDULES = [
    Schedule("课程",   [0, 1, 2, 3, 4], 1,    "08:00:00", None,       40),
    Schedule("课程",   [0, 1, 2, 3, 4], 2,    "09:10:00", None,       40),
    Schedule("课程",   [0, 1, 2, 3, 4], 3,    "10:00:00", None,       45),
    Schedule("课程",   [0, 1, 2, 3, 4], 4,    "10:55:00", None,       40),
    Schedule("课程",   [0, 1, 2, 3   ], 5,    "13:30:00", None,       40),
    Schedule("课程",   [            4], 5,    "13:00:00", None,       40),
    Schedule("课程",   [0, 1, 2, 3   ], 6,    "14:20:00", None,       45),
    Schedule("课程",   [            4], 6,    "13:50:00", None,       45),
    Schedule("课程",   [0, 1, 2, 3   ], 7,    "15:15:00", None,       40),
    Schedule("课程",   [0, 1, 2, 3   ], 8,    "16:05:00", None,       40),
]


def get_schedule_before_class(week_day, instance):
    for schedule in BEFORE_CLASS_SCHEDULE:
        if week_day in schedule.week_days and instance == schedule.instance:
            category, _, instance, starttime, stoptime, minutes = schedule
            return Schedule(category, [week_day], instance, starttime, stoptime, minutes)
    raise ValueError("No suitable schedule found before 星期{}第{}节".format(week_day + 1, instance))


def get_class_schedule(week_day, instance):
    for schedule in CLASS_SCHEDULES:
        if week_day in schedule.week_days and instance == schedule.instance:
            category, _, instance, starttime, stoptime, minutes = schedule
            return Schedule(category, [week_day], instance, starttime, stoptime, minutes)
    raise ValueError("No suitable schedule found for 星期{}第{}节".format(week_day + 1, instance))


def calc_class_schedule_from_images(filenames):
    basename_list = [os.path.basename(filename) for filename in filenames]
    classes = set()
    for basename in basename_list:
        week_day_str, instance_str = os.path.splitext(basename)[0].split("-")
        classes.add((int(week_day_str) - 1, int(instance_str)))

    schedules = []
    for week_day, instance in sorted(classes):
        schedules.append(get_schedule_before_class(week_day, instance))
        schedules.append(get_class_schedule(week_day, instance))

    # 选修
    eighth_classes = [(week_day, instance) for week_day, instance in classes if instance == 8]
    if len(eighth_classes) > 0:
        week_days = [week_day for week_day, _ in eighth_classes]
        week_days_has_elective_class = set(range(4)) - set(week_days)
        for week_day in week_days_has_elective_class:
            replace_with_elective_class(schedules, week_day)

    # 放学
    add_schedule_after_class(schedules)

    return schedules


def test_calc_class_schedule_from_images():
    filenames = ["1-7", "1-8"]
    schedules = calc_class_schedule_from_images(filenames)
    expected_schedules = [
        Schedule(category='课间', week_days=[0], instance=7, starttime='15:05:00', stoptime=None, minutes=10),
        Schedule(category='课程', week_days=[0], instance=7, starttime='15:15:00', stoptime=None, minutes=40),
        Schedule(category='课间', week_days=[0], instance=8, starttime='15:55:00', stoptime=None, minutes=10),
        Schedule(category='课程', week_days=[0], instance=8, starttime='16:05:00', stoptime=None, minutes=40),
        Schedule(category='课程', week_days=[1], instance=7, starttime='15:15:00', stoptime=None, minutes=90),
        Schedule(category='课程', week_days=[2], instance=7, starttime='15:15:00', stoptime=None, minutes=90),
        Schedule(category='课程', week_days=[3], instance=7, starttime='15:15:00', stoptime=None, minutes=90),
        Schedule(category='放学', week_days=[0], instance=None, starttime='16:45:00', stoptime=None, minutes=30),
        Schedule(category='放学', week_days=[1], instance=None, starttime='16:45:00', stoptime=None, minutes=30),
        Schedule(category='放学', week_days=[2], instance=None, starttime='16:45:00', stoptime=None, minutes=30),
        Schedule(category='放学', week_days=[3], instance=None, starttime='16:45:00', stoptime=None, minutes=30),
    ]
    assert schedules == expected_schedules


def replace_with_elective_class(schedules, week_day):
    unneeded_schedules = []
    for schedule in schedules:
        if week_day in schedule.week_days:
            if (schedule.category == "课程" and schedule.instance in [7, 8]) or (schedule.category == "课间" and schedule.instance in [8]):
                unneeded_schedules.append(schedule)
    if len(unneeded_schedules) >= 0:
        for schedule in unneeded_schedules:
            schedules.remove(schedule)
        category, _, instance, starttime, stoptime, minutes = ELECTIVE_CLASS_SCHEDULE
        schedules.append(Schedule(category, [week_day], instance, starttime, stoptime, minutes))
    return schedules


def test_replace_with_elective_class():
    schedules = [
        Schedule("课间",   [0,           ], 7,    "15:05:00", None,       40),
        Schedule("课程",   [0,           ], 7,    "15:15:00", None,       40),
        Schedule("课间",   [0,           ], 8,    "15:55:00", None,       10),
        Schedule("课程",   [0,           ], 8,    "16:05:00", None,       40),
    ]
    replace_with_elective_class(schedules, 0)
    expected_schedules = [
        Schedule("课间",   [0,           ], 7,    "15:05:00", None,       40),
        Schedule("课程",   [0,           ], 7,    "15:15:00", None,       90),
    ]
    assert schedules == expected_schedules


def add_schedule_after_class(schedules):
    fmt = "%H:%M:%S"
    last_stoptimes = {}
    for schedule in schedules:
        category, week_days, instance, starttime, stoptime, minutes = schedule
        if stoptime is None:
            last_stop = datetime.datetime.strptime(starttime, fmt) + datetime.timedelta(minutes=minutes)
        else:
            last_stop = datetime.datetime.strptime(stoptime, fmt)
        week_day = week_days[0]
        if week_day not in last_stoptimes or last_stop > last_stoptimes[week_day]:
            last_stoptimes[week_day] = last_stop

    for week_day, last_stop in last_stoptimes.items():
        schedule = Schedule("放学", [week_day], None, last_stop.strftime(fmt), None, 45)
        schedules.append(schedule)


def test_add_schedule_after_class():
    schedules = [
        Schedule("课程",   [            4], 6,    "13:50:00", None,       45),
    ]
    add_schedule_after_class(schedules)
    expected_schedules = [
        Schedule("课程",   [            4], 6,    "13:50:00", None,       45),
        Schedule("放学",   [            4], None, "14:35:00", None,       30),
    ]
    assert schedules == expected_schedules


if __name__ == "__main__":
    import itertools
    a = itertools.product(range(1, 6), range(1,9))
    b = ["{}-{}.JPG".format(d,i) for d,i in a]
    b.remove('1-8.JPG')
    b.remove('5-7.JPG')
    b.remove('5-8.JPG')
    schedules = calc_class_schedule_from_images(b)
    for schedule in schedules:
        print(schedule)
