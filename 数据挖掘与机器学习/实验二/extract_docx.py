# -*- coding: utf-8 -*-
import zipfile
import xml.etree.ElementTree as ET
import re

path = r'上机实验报告02-学号姓名.docx'
z = zipfile.ZipFile(path, 'r')
xml_content = z.read('word/document.xml')
z.close()
root = ET.fromstring(xml_content)
ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

def get_text(elem):
    texts = []
    for t in elem.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
        if t.text: texts.append(t.text)
    return ''.join(texts).strip()

for p in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
    line = get_text(p)
    if line:
        print(line)
