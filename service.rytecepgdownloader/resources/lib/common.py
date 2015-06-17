#!/usr/bin/python
# -*- coding: utf-8 -*-
import xbmcaddon
import xbmc
import xbmcvfs
import gzip
import os
import base64
import time

id = 'service.rytecepgdownloader'
addon = xbmcaddon.Addon(id=id)

def get_descriptions():
    descriptions = []
    set = [addon.getSetting('xmltv_1'), addon.getSetting('xmltv_2'), addon.getSetting('xmltv_3')]
    for s in set:
        if not s == 'None':
            descriptions.append(s)
    return descriptions

def load_local_xml(epg_url):
    ret = False
    name = epg_url.split('/')[-1]
    xml_file = get_xml_file(name)
    if os.path.exists(xml_file):
        ret = check_date(xml_file)
    return ret

def get_description_url(description):
    epg_url = None
    try:
        epg_url = bdecode(addon.getSetting(description))
    except:
        print '[Rytec EPG Downloader]: no epg url found in settings', description
    return epg_url

def save_epg_url(epg_url, description):
    addon.setSetting(description, bencode(epg_url))

def get_xml_path():
    xml_path = addon.getSetting('path').decode('utf-8')
    if not xml_path:
        addon.openSettings()
        xml_path = addon.getSetting('path').decode('utf-8')
    return xml_path

def get_xml_file(name):
    xml_path = get_xml_path()
    xml_file = os.path.join(xml_path, name)
    return xml_file

def bencode(original_string):
    encoded_string = base64.b64encode(original_string)
    return encoded_string

def bdecode(encoded_string):
    decoded_string = base64.b64decode(encoded_string)
    return decoded_string

def check_date(file):
    cache_days = 3
    modified_time = round(os.stat(file).st_mtime)
    current_time = round(time.time())
    t = current_time - modified_time
    if (t / 3600) < 24*cache_days:
        return True

def download_allowed(a):
    gmt = time.gmtime()
    if gmt.tm_hour > 2 and gmt.tm_hour < 7:
        if not a:
            print '[Rytec EPG Downloader]: epg download not allowed between 3 and 7 GMT'
        return False
    else:
        return True
        
def get_counter():
    counter = addon.getSetting('counter')
    if not counter:
        counter = '0'
    return counter

def blocked(a):
    counter = int(get_counter())
    ct = round(time.time())
    if counter == 0:
        counter += 1
        addon.setSetting('counter', str(counter))
        addon.setSetting('bt', str(ct).split('.')[0])
        return False
    elif counter == 1:
        counter += 1
        addon.setSetting('counter', str(counter))
        return False
    elif counter > 1:
        bt = int(addon.getSetting('bt'))
        t = ct - bt
        if (t / 3600) > 23:
            addon.setSetting('counter', '0')
            return False
        else:
            if not a:
                print '[Rytec EPG Downloader]: %sh blocked' % (24 - (t / 3600))
            return True
    else:
        return True

def get_activation_code():
    ac = addon.getSetting('ac')
    if bencode(ac) == 'MzAyNQ==':
        return True
    else:
        addon.openSettings()
        ac = addon.getSetting('ac')
        if bencode(ac) == 'MzAyNQ==':
            return True
        else:    
            return False

def merge_epg():
    # code from enen92. thank you
    print '[Rytec EPG Downloader]: merge epg' 
    xml_path = get_xml_path()
    temp = os.path.join(xml_path,'temp')
    if not os.path.isdir(temp):
        os.mkdir(temp)
    out = os.path.join(xml_path,'merged_epg.xml')
    if xbmcvfs.exists(out): os.remove(out)
    print '[Rytec EPG Downloader]: start extracting files' 
    dirs, files = xbmcvfs.listdir(os.path.join(xml_path))
    for f in files:
        if f.endswith('.gz'):
            inF = gzip.GzipFile(os.path.join(xml_path,f), 'rb')
            s = inF.read()
            inF.close()
            outF = file(os.path.join(temp,f.replace('.gz','.xml')),'wb')
            outF.write(s)
            outF.close()
    print '[Rytec EPG Downloader]: extracting files done'
    print '[Rytec EPG Downloader]: start merging files'
    dirs, xmltv_list = xbmcvfs.listdir(os.path.join(temp))
    i=1
    total = len(xmltv_list)
    for xmltv in xmltv_list:
        if xmltv.endswith('.xml'):
            if i==1:
                f = open(os.path.join(temp,xmltv), "r")
                text = f.read()
                f.close()
                with open(out, "a") as myfile:
                    myfile.write(text.replace('</tv>',''))
            elif i==total:
                o = open(out,"a")
                f = open(os.path.join(temp,xmltv),"r")
                lines = f.readlines()
                f.close()
                li = 0
                for line in lines:
                    if li == 0 or li == 1: pass
                    else: o.write(line)
                    li += 1
                o.close()
            else:
                o = open(out,"a")
                f = open(os.path.join(temp,xmltv),"r")
                lines = f.readlines()
                total_lines = len(lines)
                f.close()
                li = 0
                for line in lines:
                    if li == 0 or li == 1: pass
                    elif li == (total_lines -1): pass
                    else: o.write(line)
                    li += 1
                o.close()
            os.remove(os.path.join(temp,xmltv))
            i += 1
    print '[Rytec EPG Downloader]: merging files done'