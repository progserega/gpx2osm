#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
import sys
import logging
import re
import os
import gpxpy
import gpxpy.gpx
import great_circles
from osmwriter import OSMWriter
import argparse

MAX_DIST=100

def close_polygon(osm):
  for way_id in osm:
    way=osm[way_id]
    begin_node_id=way[0]
    way.append(begin_node_id)
  return osm

# проверяем, подключён ли данный конец линии к другим:
def check_connected(ways,check_way_id,check_poi_id):
  log.debug("check_connected()")
  for way_id in ways:
    if way_id == check_way_id:
      continue
    if check_poi_id in ways[way_id]:
      return True
  return False

def remove_index(ref):
  log.debug("remove_index()")
  result=""
  parsed=parse_ref(ref)
  if parsed==None:
    log.warning("parse_ref()")
    return None
  log.debug(parsed)
  parsed_len=len(parsed)
#  log.debug("parsed_len=%d"%parsed_len)
  if len(parsed)<2:
    return None
  else:
    removed=parsed[0:parsed_len-1]
    log.debug("1: removed=")
    log.debug(removed)
    if parsed_len>=3:
#      print("check: %s"%parsed[parsed_len-2])
      if check_symbol_type(parsed[parsed_len-2])==-1:
        # разделители тоже надо убрать:
        removed=parsed[0:parsed_len-2]
        log.debug("2: removed=")
        log.debug(removed)
    # собираем ref:
    for i in removed:
      if type(i) is int:
        result+=str(i)
      else:
        result+=i
    return result
  return None
    
def get_begin_of_way(way,poi):
  base_begin=way[0]
  base_end=way[len(way)-1]
  begin_parsed=parse_ref(poi[base_begin]["name"])
  end_parsed=parse_ref(poi[base_end]["name"])

  if begin_parsed == None and end_parsed != None:
    return base_end
  if begin_parsed != None and end_parsed == None:
    return base_begin
  if begin_parsed == None and end_parsed == None:
    return None

  begin_index=begin_parsed[len(begin_parsed)-1]
  end_index=begin_parsed[len(end_parsed)-1]

  if check_symbol_type(begin_index) == 0 and check_symbol_type(end_index) == 0:
    if begin_index < end_index:
      return base_begin
    else:
      return base_end
  elif check_symbol_type(begin_index) == 1 and check_symbol_type(end_index) == 1:
    begin_last_symbol=begin_index[len(begin_index)-1]
    end_last_symbol=end_index[len(end_index)-1]
    if ord(begin_last_symbol) < ord(end_last_symbol):
      return base_begin
    else:
      return base_end
  else:
    # то ли разные типы, то ли разделители - это ошибка
    return None

def check_symbol_type(s):
  log.debug("check_symbol_type()")
  index_type=-1 # 0 - digit, 1 - text, -1 - unknown  (symbols / - etc)
  if type(s) is int:
    index_type=0
  else:
    if s.isdigit():
      index_type=0
    elif re.search(r'[а-я]',s.lower()) !=None or re.search(r'[a-z]',s.lower()) !=None:
      index_type=1
    else:
      index_type=-1
  return index_type

def connect_ways(ways,poi):
  log.debug("connect_ways()")
  for way_id in ways:
    selected_begin=False
    way=ways[way_id]
    check_list=[]
    begin_poi_id=get_begin_of_way(way,poi)
    if begin_poi_id != None:
      selected_begin=True
      check_list.append(begin_poi_id)
      if begin_poi_id == way[0]:
        check_list.append(way[len(way)-1])
      else:
        check_list.append(way[0])
    else:
      check_list.append(way[0])
      check_list.append(way[len(way)-1])
    for cur_node_id in check_list:
      if check_connected(ways,way_id,cur_node_id) == False or selected_begin == True:
        # пробуем если никуда не подключён, или если определили, что это начало отпайки
        # пробуем подсоединить:
        log.debug("try connect poi with ref=%s"%poi[cur_node_id]["name"])
        new_ref=remove_index(poi[cur_node_id]["name"])
        log.debug("try find new_ref=%s"%new_ref)
        # ищем такую опору:
        for node_id in poi:
          if poi[node_id]["name"] == new_ref:
            log.debug("found ref=%s"%new_ref)
            cur_node=poi[cur_node_id]
            if node_id not in way:
              # ещё не добавляли эту точку в эту линию
              candidat=poi[node_id]
              dist=great_circles.get_dist(cur_node["lon"],cur_node["lat"],candidat["lon"],candidat["lat"])
              log.debug("dist=%f"%dist)
              if dist < MAX_DIST:
                log.debug("not far - accept node!")
                # не слишком далеко, значит присоединяем:
                if cur_node_id == way[0]:
                  # вставляем в начало:
                  way.insert(0,candidat["poi_id"])
                  break
                else:
                  # добавляем в конец
                  way.append(candidat["poi_id"])
                  break

  return ways

def get_prefery_next_ref(ref,inc):
  log.debug("get_prefery_next_ref(%s,%d)"%(ref,inc))
  parsed=parse_ref(ref)
  if parsed==None:
    log.warning("parse_ref(ref)")
    return None
  last_index=len(parsed)-1
  last_word=parsed[last_index]
  last_type=check_symbol_type(last_word)

  if last_type == 0:
    parsed[last_index]=last_word+inc
  elif last_type == 1:
    len_word=len(last_word)
    index_symbol=last_word[len_word-1]
    new_index_symbol=chr(ord(index_symbol)+inc)
    # собираем слово (т.к. нельзя поменять символ в слове простым присвоением):
    new_word=last_word[0:len_word-1]+new_index_symbol
    parsed[last_index]=new_word
  else:
    # ref заканчивается на символы разделители
    return None
  # собираем ref:
  result=""
  for i in parsed:
    if type(i) is int:
      result+=str(i)
    else:
      result+=i
  return result
    
    
def parse_ref(ref):
  result=[]
  tmp_result=""
  ref_index=0
  razryad=0
  delimiter=""

  ref=ref.strip()
  if len(ref)==0:
    log.warning("ref is empty!")
    return None
  s=ref[len(ref)-1]
  cur_block_type=check_symbol_type(s)

  for index in range(len(ref)-1,-1,-1):
    s=ref[index]
    cur_symbol_type=check_symbol_type(s)

#    log.debug("index=%d"%index)
#    log.debug("s=%s"%ref[index])
#    log.debug("cur_block_type=%d"%cur_block_type)
#    log.debug("cur_symbol_type=%d"%cur_symbol_type)

    if cur_symbol_type != cur_block_type:
      if cur_block_type != -1:
        if cur_block_type==0:
          result.insert(0,ref_index)
        elif cur_block_type==1:
          result.insert(0,tmp_result)
      else:
        result.insert(0,delimiter)
      # сбрасываем временные переменные:
      ref_index=0
      razryad=0
      tmp_result=""
      cur_block_type=cur_symbol_type
      delimiter=""

    if cur_symbol_type == cur_block_type:
      if cur_block_type == 0: # цифры
        ref_index=ref_index+pow(10,razryad)*int(s)
        razryad+=1
      elif cur_block_type == 1: # буквы
        tmp_result=s+tmp_result
      else:
        # пропуск разделителей:
        delimiter=s+delimiter

    if index==0: # последний символ обработали
      if cur_block_type != -1:
        if cur_block_type==0:
          result.insert(0,ref_index)
        elif cur_block_type==1:
          result.insert(0,tmp_result)
      else:
        result.insert(0,delimiter)

  return result
    

def get_next_candidat(poi,last_point,list_newarest_points,cur_name):
  log.debug("get_next_candidat()")
  prefer_next_name=get_prefery_next_ref(cur_name,1)
  prefer_prev_name=get_prefery_next_ref(cur_name,-1)
  
  log.debug("предполагаемые следующие имена: '%s' и '%s'"%(prefer_next_name,prefer_prev_name))
  log.debug("Ближайшие точки к poi c именем '%s' по расстоянию:"%cur_name)
           
  candidat=None
  for poi_id in list_newarest_points:
    log.debug("%s"%poi[poi_id]["name"])
    if poi[poi_id]["name"]==prefer_next_name or poi[poi_id]["name"]==prefer_prev_name:
      # ищем ближайшую опору с предполагаемым именем:
      candidat=poi[poi_id]
      log.debug("нашли ближайшую подходящую по имени с ref=%s"%candidat["name"])
      break;
  #if candidat==None:
    # просто берём ближайшую точку:
    #candidat=poi[list_newarest_points[0]]
    #print("по имени не нашли, просто берём ближайшую с ref=%s"%candidat["name"])
  #print("candidat ref=%s"%candidat["name"])
  return candidat


def get_begin_candidat(poi,last_point,list_all_newarest_points,cur_name):
  log.debug("get_begin_candidat()")
  begin_ref=get_prefery_begin(cur_name)
  if begin_ref==None:
    log.debug("не смог вычислить начальное имя для '%s' - пропуск"%cur_name)
    return None
    
  log.debug("предполагаем следующее имя начала: '%s'"%begin_ref)
  
  log.debug("Ближайшие точки к poi c именем '%s' по расстоянию:"%cur_name)
           
  candidat=None
  for poi_id in list_all_newarest_points:
    log.debug("%s"%poi[poi_id]["name"])
    if poi[poi_id]["name"]==begin_ref:
      # ищем ближайшую опору с предполагаемым именем:
      candidat=poi[poi_id]
      log.debug("нашли ближайшую подходящую по имени с ref=%s"%candidat["name"])
      break;
  if candidat==None:
    log.debug("по имени не нашли - пропуск")
  else:
    log.debug("candidat ref=%s"%candidat["name"])
  return candidat


  

def is_poi_exist(poi_list,poi):
  for poi_id in poi_list:
    item=poi_list[poi_id]
    if item["name"]==poi["name"] and\
      item["lat"]==poi["lat"] and\
      item["lon"]==poi["lon"]:
      return True
  return False

def get_poi(filename,skip_dubles=False):
  log.debug("get_poi()")
  data={}
  gpx_file = open(filename, 'r')
  gpx = gpxpy.parse(gpx_file)
  poi_id=-1
  for waypoint in gpx.waypoints:
#    print(waypoint)
#    sys.exit()
    item={}
    if waypoint.name == None:
      item["name"]=""
    else:
      item["name"]=waypoint.name.strip()
    item["lat"]=waypoint.latitude
    item["lon"]=waypoint.longitude
    if waypoint.elevation == None:
      item["ele"]=0
    else:
      item["ele"]=waypoint.elevation
    item["poi_id"]=poi_id
    #print("waypoint %s -> (%f,%f)"%(waypoint.name, waypoint.latitude, waypoint.longitude))
    if skip_dubles == True:
      if is_poi_exist(data,item)==True:
        continue
    data[poi_id]=item
    poi_id-=1
      
  # There are many more utility methods and functions:
  # You can manipulate/add/remove tracks, segments, points, waypoints and routes and
  # get the GPX XML file from the resulting object:

  #print 'GPX:', gpx.to_xml()
  return data

def get_prefery_begin(ref):
  ref=ref.strip()
  index_is_digit=True
  result_ref=None
  ref_index=0
  razryad=0
  if len(ref)==0:
    return None
  s=ref[len(ref)-1]
  if s.isdigit():
    index_is_digit=True
  else:
    index_is_digit=False
#  print("index_is_digit=",index_is_digit)

  for index in range(len(ref)-1,-1,-1):
    s=ref[index]
#    print("index=%d"%index)
#    print("s=%s"%ref[index])
    if s.isdigit() and index_is_digit:
      ref_index=ref_index+pow(10,razryad)*int(s)
      razryad+=1
      continue
    elif not s.isdigit() and not index_is_digit: 
      continue 
    elif s=='/' or s=='\\' or s=='-' or s==' ':
      result_ref=ref[0:index]
      break
    else:
      result_ref=ref[0:index+1]
      break
  if ref_index!=1 and index_is_digit:
    # значит это конец отпайки и его не надо соединять с началом линии:
    result_ref=None
#  print("result_ref=%s"%result_ref)
  if result_ref!=None:
    result_ref=result_ref.strip()
  return result_ref

def get_nearest_points(lat, lon, poi, max_dist):
  ids_list={}
  dist_list=[]
  result=[]
  for poi_id in poi:
    item=poi[poi_id]
    if "way_id" in item:
      # пропускаем все точки, которые уже включены в какую-либо линию
      continue
    if lon==item["lon"] and lat==item["lat"]:
      # пропускаем дубли:
      continue
    dist=great_circles.get_dist(lon,lat,item["lon"],item["lat"])
    if dist < max_dist:
      dist_list.append(dist)
      ids_list[dist]=poi_id
  dist_list.sort()
  for dist in dist_list:
    result.append(ids_list[dist])
  return result

def get_all_nearest_points(lat, lon, poi, max_dist):
  ids_list={}
  dist_list=[]
  result=[]
  for poi_id in poi:
    item=poi[poi_id]
    if lat==item["lat"] and lon==item["lon"]:
      # пропуск точки по тем же координатам:
      continue
    dist=great_circles.get_dist(lon,lat,item["lon"],item["lat"])
    if dist < max_dist:
      dist_list.append(dist)
      ids_list[dist]=poi_id
  dist_list.sort()
  for dist in dist_list:
    result.append(ids_list[dist])
  return result

def write_osm(out_file_name,poi,ways,tags,skip_relation_creation=False,source="survey",note="converted by gpx2osm",operator="Abonent"):
  xml = OSMWriter(out_file_name)
  # nodes:
  for node_id in poi:
    node=poi[node_id]
    if tags["power"]=="minor_line":
      xml.node(node_id, node["lat"] , node["lon"], {"power": "pole", "ele":"%f"%node["ele"], "source":source,"note":tags["name"], "voltage":"%d"%tags["voltage"], "ref":node["name"],"operator":operator}, version=1)
    elif tags["power"]=="line":
      xml.node(node_id, node["lat"] , node["lon"], {"power": "tower", "ele":"%f"%node["ele"], "source":source,"note":tags["name"], "voltage":"%d"%tags["voltage"], "ref":node["name"], "operator":operator}, version=1)
    elif tags["power"]=="cable":
      xml.node(node_id, node["lat"] , node["lon"], {"source":source,"note":tags["name"], "ref":node["name"], "operator":operator}, version=1)
    elif tags["power"]=="sub_station":
      if "voltage" in tags:
        xml.node(node_id, node["lat"] , node["lon"], {"power": "sub_station", "ele":"%f"%node["ele"], "source":source,"note":note, "operator":operator, "voltage":"%d"%tags["voltage"], "ref":node["name"]}, version=1)
      else:
        xml.node(node_id, node["lat"] , node["lon"], {"power": "sub_station", "ele":"%f"%node["ele"], "source":source,"note":note, "operator":operator, "ref":node["name"]}, version=1)
    elif tags["power"]=="station":
      xml.node(node_id, node["lat"] , node["lon"], {"ele":"%f"%node["ele"], "source":source, "operator":operator,"note":tags["name"]}, version=1)
    else:
      log.error("unknown type of power object - exit!")
      return False
    
  # ways:
  if skip_relation_creation==True:
    name_tag="name"
  else:
    name_tag="alt_name"
  for way_id in ways:
    if tags["power"]=="minor_line" or tags["power"]=="line" or tags["power"]=="cable":
      xml.way(way_id, {name_tag:tags['name'],'power': tags['power'],"source":source,"voltage":"%d"%tags['voltage'], "operator":operator,"note":note}, ways[way_id], version=1)
    elif tags["power"]=="station":
      xml.way(way_id, {'name':tags['name'],'power': tags['power'],"source":source,"voltage":"%d"%tags['voltage'], "operator":operator,"note":note}, ways[way_id], version=1)
    else:
      log.info("not write way-data to osm for this type of power-object")
   
  # relation
  if skip_relation_creation!=True:
    relation_members=[]
    for way_id in ways:
      relation_members.append(('way',way_id,''))

    if tags["power"]=="minor_line" or tags["power"]=="line" or tags["power"]=="cable":
      xml.relation(-1, {'power':tags['power'],'note':note, "operator":operator,'source':'survey','type': 'route','route':'power','voltage':"%d"%tags['voltage'],'name':tags['name']},relation_members, version=1 )
  xml.close()
  return True

def create_line(poi):
  ways={}
  way_id=-1
  for poi_id in poi:
    item=poi[poi_id]
    last_point=item
    first_point=item
    processed_flow=1

    log.debug("process poi_d=%s"%poi_id)
    log.debug("process poi ref=%s"%item["name"])

    # первая точка в линии:
    if "way_id" not in item:
      # если точку ещё не добавляли в линию:
      if way_id not in ways:
        ways[way_id]=[]
      item["way_id"]=way_id
      ways[way_id].append(poi_id)

      while True:
        end_line=False
        dist=0
        # следующие точки в линии:
        cur_name=last_point["name"]
        log.debug("=========  Ищем ближайшие точки для: '%s'"%cur_name)
        list_newarest_points=get_nearest_points(last_point["lat"], last_point["lon"],poi,MAX_DIST)
        log.debug("len(list_newarest_points)=%d"%len(list_newarest_points))
        for i in list_newarest_points:
          log.debug("id:%d, ref:%s"%(i,poi[i]["name"]))

        if len(list_newarest_points)==0:
          # будем заканчивать линию:
          end_line=True
        else:
          candidat=get_next_candidat(poi,last_point,list_newarest_points,cur_name)
          if candidat==None:
            end_line=True
          else:
            dist=great_circles.get_dist(last_point["lon"],last_point["lat"],candidat["lon"],candidat["lat"])
          log.debug("candidat=")
          log.debug(candidat)

        log.debug("dist=%f"%dist)

        if dist>MAX_DIST or end_line==True:
          # пробуем прикрепить к началу (к части другой линии):
          log.debug("пробуем прикрепить к началу:")
          list_all_newarest_points=get_all_nearest_points(last_point["lat"], last_point["lon"],poi,MAX_DIST)
          candidat=get_begin_candidat(poi,last_point,list_all_newarest_points,cur_name)
          # FIXME
          candidat=None
          if candidat!=None:
            if processed_flow==1:
              ways[way_id].append(candidat["poi_id"])
            else:
              ways[way_id].insert(0,candidat["poi_id"])
            candidat["way_id"]=way_id
          
          if processed_flow==1:
            # мы прошли линию только в одну сторону от начальной точки.
            # пробуем во вторую сторону от начальной точки:
            last_point=first_point
            processed_flow=2
          else:
            # заканчиваем линию:
            way_id-=1
            break
        else:
          # добавляем точку в линию:
          log.debug("добавляем точку с ref='%s' как следующую для точки с ref='%s'"%(candidat["name"],cur_name))
          if processed_flow==1:
            ways[way_id].append(candidat["poi_id"])
          else:
            ways[way_id].insert(0,candidat["poi_id"])

          candidat["way_id"]=way_id

          # перескакиваем на добавленную точку:
          last_point=candidat
  ways=connect_ways(ways,poi)
  return ways

def parse_file_name(path_name):
  result=None

  log.debug("path input file=%s"%path_name)
  name=os.path.basename(path_name).strip()
  log.debug("file name=%s"%name)

  if "_line." in name and re.search(r'^вл ',name.lower()) != None:
    result={}
    # vl
    words=name.split(' ')
    if words[1].isdigit():
      result["voltage"]=int(words[1]) * 1000
    elif re.match("^\d+?\.\d+?$", words[1].replace(',','.')) is not None:
      result["voltage"]=int(float(words[1].replace(',','.')) * 1000)
    result["name"]=re.sub(r'_line\..*','',name)
    result["power"]="line"
  elif "_line." in name and (re.search(r'^квл ',name.lower()) != None or re.search(r'^кл ',name.lower()) != None):
    result={}
    # vl
    words=name.split(' ')
    if words[1].isdigit():
      result["voltage"]=int(words[1]) * 1000
    result["name"]=re.sub(r'_line\..*','',name)
    result["power"]="cable"
  elif "_line04." in name:
    result={}
    result["voltage"]=400
    result["name"]=re.sub(r'_line04\..*','',name)
    result["power"]="minor_line"
    # minor_line
  elif "_station." in name and re.search(r'^пс ',name.lower()) != None:
    # ps
    result={}
    words=name.split(' ')
    
    if words[1].isdigit():
      result["voltage"]=int(words[1]) * 1000
    else:
      voltage_str=re.sub(r'_.*','',words[1])
      if voltage_str.isdigit():
        result["voltage"]=int(voltage_str) * 1000
      else:
        log.error("error get voltage from name of station")
        return None
    result["name"]=re.sub(r'_station\..*','',name).replace('_','/')
    result["power"]="station"
  elif "_substation." in name:
    #tp
    result={}
    result["power"]="sub_station"
  else:
    # error
    log.error("no type of data in name of gpx-file!")
  return result

if __name__ == '__main__':
  debug=False

  # init parse args:
  parser = argparse.ArgumentParser(description='Convertor gpx to osm (OpenStreetMap)',add_help=True)
  parser.add_argument("--input","-i",action='store', type=str, help="""input gpx file.
Имя должно состоять из полей:

Для ВЛ:
ВЛ <напряжение> <имя линии>_line.gpx

Для низковольтных фидеров:
<имя линии>_line04.gpx

Для подстанций:
<имя подстанции>_station.gpx

Для ТП:
<имя>_substation.gpx

Например:
ВЛ 6 ф.Строительство ЦРП ПГРЭС_line.gpx
ф.1_line04.gpx
ПС 110_10 Троица_station.gpx
КТП 6104 Быт_substation.gpx
""")
  parser.add_argument("--output","-o",action='store', help="output osm file")
  parser.add_argument("--verbose","-v",action='count', help="debug logging")
  parser.add_argument('--skip_relation_creation', "-r", action='store_true', help="do not create relation for lines")
  parser.add_argument("--source","-s",action='store', help="value of 'source' tag 'survey' by default")
  parser.add_argument("--note","-n",action='store', help="value of 'note' tag 'converted by gpx2osm' by default")
  parser.add_argument("--operator","-p",action='store', help="value of 'operator' tag 'Abonent' by default")
  parser.add_argument('--not_skip_dubles', "-d", action='store_false', help="Do not skip dubles of poi (same name and some lat and lon) - default False")
  parser.add_argument("--max_dist","-m",action='store', default=100, help="max distance between towers (default 100 meters)")
  args = parser.parse_args()

  # init logging system:
  log=logging.getLogger("gpx2osm")
  if args.verbose==None:
    log.setLevel(logging.ERROR)
  elif args.verbose==1:
    log.setLevel(logging.WARNING)
  elif args.verbose==2:
    log.setLevel(logging.INFO)
  elif args.verbose>2:
    log.setLevel(logging.DEBUG)

  formatter = logging.Formatter('%(asctime)s - %(name)s - %(filename)s:%(lineno)d - %(funcName)s() %(levelname)s - %(message)s')
  # log to file:
#  fh = logging.FileHandler(conf.log_path)
#  fh.setFormatter(formatter)
  # add handler to logger object
#  log.addHandler(fh)

  # логирование в консоль:
  #stdout = logging.FileHandler("/dev/stdout")
  stdout = logging.StreamHandler(sys.stdout)
  stdout.setFormatter(formatter)
  log.addHandler(stdout)

  try:
    MAX_DIST=int(args.max_dist)
  except:
    log.error("--max_dist must be integer! See --help")
    sys.exit(1)
  log.debug("max_dist=%s"%args.max_dist)

  log.info("Program started")
#  print(remove_index("106"))
#  sys.exit()

  if args.output == None or args.input == None:
    log.error("need 2 params, try --help")
    sys.exit(1)

  in_file_name=args.input
  out_file_name=args.output

  poi=get_poi(in_file_name,skip_dubles=args.not_skip_dubles)

  log.debug("len(poi)=%d"%len(poi))

  tags=parse_file_name(in_file_name)
  if tags == None:
    log.error("parse input file name - see help")
    sys.exit(1)
  
  osm=None

  if tags["power"]=="line" or tags["power"]=="minor_line":
    osm=create_line(poi)

  if tags["power"]=="station":
    osm=create_line(poi)
    if close_polygon(osm) == None:
      log.error("close_polygon()")
      sys.exit(1)

  if tags["power"]=="sub_station":
    osm={}

  if args.source != None:
    source=args.source
  else:
    source="survey"
  if args.note != None:
    note=args.note
  else:
    note="converted by gpx2osm"
  if args.operator != None:
    operator=args.operator
  else:
    operator="Abonent"

  if osm == None:
    log.error("error type of input file - see help")
    if "power" in tags:
      log.info("power=%s"%tags["power"])
    else:
      log.error("no tag power in tags")
    sys.exit(1)

  write_osm(out_file_name,poi,osm,tags,args.skip_relation_creation,source=source,note=note,operator=operator)
          
  log.info("Program end")
        
