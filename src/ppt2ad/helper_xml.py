#!/usr/bin/env python3
# -*- coding:utf-8 -*-
'''
Copyright (c) 2021 Inspur.com, Inc. All Rights Reserved

description

Author: Jeff Li <lijinfeng01@inspur.com>
Date: 2021/03/21 19:04:16
'''


from xml.etree import ElementTree
from xml.dom import minidom


def prettify_xml(root):
    """
    Serialize ElementTree with builtiful indentation
    """
    original_bytes = ElementTree.tostring(root, encoding="utf-8")
    original_text = original_bytes.decode(encoding="utf-8")
    dom = minidom.parseString(original_text)
    return dom.toprettyxml(indent="    ", encoding="utf-8").decode(encoding="utf-8")
