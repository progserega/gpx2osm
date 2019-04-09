#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
import sys
import logging
import re
import gpxpy
import gpxpy.gpx
import great_circles
from osmwriter import OSMWriter

MAX_DIST=100

# проверяем, подключён ли данный конец линии к другим:
def check_connected(ways,check_way_id,check_poi_id):
  for way_id in ways:
    if way_id == check_way_id:
      continue
    if check_poi_id in ways[way_id]:
      return True
  return False

def check_symbol_type(s):
  index_type=-1 # 0 - digit, 1 - text, -1 - unknown  (symbols / - etc)
  if s.isdigit():
    index_type=0
  elif re.search(r'[а-я]',s.lower()) !=None or re.search(r'[a-z]',s.lower()) !=None:
    index_type=1
  else:
    index_type=-1
  return index_type

def parse_ref(ref):
  result=[]
  tmp_result=""
  ref_index=0
  razryad=0

  ref=ref.strip()
  s=ref[len(ref)-1]
  cur_block_type=check_symbol_type(s)

  for index in range(len(ref)-1,-1,-1):
    s=ref[index]
    cur_symbol_type=check_symbol_type(s)

    log.debug("index=%d"%index)
    log.debug("s=%s"%ref[index])
    log.debug("cur_block_type=%d"%cur_block_type)
    log.debug("cur_symbol_type=%d"%cur_symbol_type)

    if cur_symbol_type != cur_block_type:
      if cur_block_type != -1:
        if cur_block_type==0:
          result.insert(0,ref_index)
        elif cur_block_type==1:
          result.insert(0,tmp_result)
      # сбрасываем временные переменные:
      ref_index=0
      razryad=0
      tmp_result=""
      cur_block_type=cur_symbol_type

    if cur_symbol_type == cur_block_type:
      if cur_block_type == 0: # цифры
        ref_index=ref_index+pow(10,razryad)*int(s)
        razryad+=1
      elif cur_block_type == 1: # буквы
        tmp_result=s+tmp_result
      else:
        # пропуск разделителей:
        delimiter=s

    if index==0: # последний символ обработали
      if cur_block_type != -1:
        if cur_block_type==0:
          result.insert(0,ref_index)
        elif cur_block_type==1:
          result.insert(0,tmp_result)

  return result
    

def get_begin_poi_id(poi,way):
  ref1=poi[way[0]]["ref"]
  ref2=poi[way[len(way)-1]]["ref"]
  if int(ref1[len(ref1)-1]) < int(ref2[len(ref2)-1]):
    последний
  return way[0]

def get_begin_poi_id(way):
  return way[0]


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


  



def get_poi(filename):
  log.debug("get_poi()")
  data={}
  gpx_file = open(filename, 'r')
  gpx = gpxpy.parse(gpx_file)
  poi_id=-1
  for waypoint in gpx.waypoints:
    item={}
    item["name"]=waypoint.name.strip()
    item["lat"]=waypoint.latitude
    item["lon"]=waypoint.longitude
    item["poi_id"]=poi_id
    #print("waypoint %s -> (%f,%f)"%(waypoint.name, waypoint.latitude, waypoint.longitude))
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

def get_prefery_next_ref(ref,inc):
  result_ref=""
  ref_index=0
  ref_new_index=0
  ref_prefix=""
  ref_postfix=""
  razryad=0
  for index in range(len(ref)-1,-1,-1):
    s=ref[index]
#   print("index=%d"%index)
#   print("s=%s"%ref[index])
    if s.isdigit():
      ref_index=ref_index+pow(10,razryad)*int(s)
      razryad+=1
    else:
      if ref_index==0:
        ref_postfix=s+ref_postfix
        continue
      # индекс закончился:
      # получаем префикс индекса:
      ref_prefix=ref[0:index+1]
#     print("ref_prefix=%s"%ref_prefix)
      ref_new_index=ref_index+inc
      result_ref=ref_prefix+str(ref_new_index)+ref_postfix
      break
  if result_ref=="":
    result_ref=ref_prefix+str(ref_index+inc)+ref_postfix
#print("result_ref=%s"%result_ref)
  return result_ref.strip()

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

def write_osm(out_file_name,poi,ways):
  xml = OSMWriter(out_file_name)
  for node_id in poi:
    node=poi[node_id]
    xml.node(node_id, node["lat"] , node["lon"], {"power": "pole", "source":"survey","note":"converted by gpx2osm", "voltage":"400", "ref":node["name"]}, version=1)
    
  for way_id in ways:
    xml.way(way_id, {'power': 'minor_line',"source":"survey","voltage":"400","note":"converted by gpx2osm"}, ways[way_id], version=1)
#xml.relation(1, {'type': 'boundary'}, [('node', 1), ('way', 2, 'outer')])
  xml.close()

def create_line(poi,line_name):
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

        log.debug("dist=%f"%dist)
        log.debug("candidat=")
        log.debug(candidat)

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

if __name__ == '__main__':
  debug=True

  log=logging.getLogger("gpx2osm")
  if debug:
    log.setLevel(logging.DEBUG)
  else:
    log.setLevel(logging.INFO)

  formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
  # log to file:
#  fh = logging.FileHandler(conf.log_path)
#  fh.setFormatter(formatter)
  # add handler to logger object
#  log.addHandler(fh)

  if debug:
    # логирование в консоль:
    #stdout = logging.FileHandler("/dev/stdout")
    stdout = logging.StreamHandler(sys.stdout)
    stdout.setFormatter(formatter)
    log.addHandler(stdout)


  log.info("Program started")


  print(parse_ref("z155_в_-333"))
  sys.exit()

  in_file_name=sys.argv[1]
  out_file_name=in_file_name+".osm"
  poi=get_poi(in_file_name)

  log.debug("len(poi)=%d"%len(poi))

  osm=create_line(poi,"test_line")

  write_osm(out_file_name,poi,osm)
          
  log.info("Program end")
        
