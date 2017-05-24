#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
import sys
import re
import gpxpy
import gpxpy.gpx
import great_circles
from osmwriter import OSMWriter

MAX_DIST=100

def get_next_candidat(poi,last_point,list_newarest_points,cur_name):
  prefer_next_name=get_prefery_next_ref(cur_name,1)
  prefer_prev_name=get_prefery_next_ref(cur_name,-1)
  
  print("предполагаемые следующие имена: '%s' и '%s'"%(prefer_next_name,prefer_prev_name))
  print("Ближайшие точки к poi c именем '%s' по расстоянию:"%cur_name)
           
  candidat=None
  for poi_id in list_newarest_points:
    print("%s"%poi[poi_id]["name"])
    if poi[poi_id]["name"]==prefer_next_name or poi[poi_id]["name"]==prefer_prev_name:
      # ищем ближайшую опору с предполагаемым именем:
      candidat=poi[poi_id]
      print("нашли ближайшую подходящую по имени с ref=%s"%candidat["name"])
      break;
  #if candidat==None:
    # просто берём ближайшую точку:
    #candidat=poi[list_newarest_points[0]]
    #print("по имени не нашли, просто берём ближайшую с ref=%s"%candidat["name"])
  #print("candidat ref=%s"%candidat["name"])
  return candidat


def get_begin_candidat(poi,last_point,list_all_newarest_points,cur_name):
  begin_ref=get_prefery_begin(cur_name)
  if begin_ref==None:
    print("не смог вычислить начальное имя для '%s' - пропуск"%cur_name)
    return None
    
  print("предполагаем следующее имя начала: '%s'"%begin_ref)
  
  print("Ближайшие точки к poi c именем '%s' по расстоянию:"%cur_name)
           
  candidat=None
  for poi_id in list_all_newarest_points:
    print("%s"%poi[poi_id]["name"])
    if poi[poi_id]["name"]==begin_ref:
      # ищем ближайшую опору с предполагаемым именем:
      candidat=poi[poi_id]
      print("нашли ближайшую подходящую по имени с ref=%s"%candidat["name"])
      break;
  if candidat==None:
    print("по имени не нашли - пропуск")
  else:
    print("candidat ref=%s"%candidat["name"])
  return candidat


  



def get_poi(filename):
  data={}
  gpx_file = open(filename, 'r')
  gpx = gpxpy.parse(gpx_file)
  poi_id=1
  for waypoint in gpx.waypoints:
    item={}
    item["name"]=waypoint.name
    item["lat"]=waypoint.latitude
    item["lon"]=waypoint.longitude
    item["poi_id"]=poi_id
    #print("waypoint %s -> (%f,%f)"%(waypoint.name, waypoint.latitude, waypoint.longitude))
    data[poi_id]=item
    poi_id+=1
      
  # There are many more utility methods and functions:
  # You can manipulate/add/remove tracks, segments, points, waypoints and routes and
  # get the GPX XML file from the resulting object:

  #print 'GPX:', gpx.to_xml()
  return data

def get_prefery_begin(ref):
  index_is_digit=True
  result_ref=None
  s=ref[len(ref)-1]
  if s.isdigit():
    index_is_digit=True
  else:
    index_is_digit=False
  print("index_is_digit=",index_is_digit)

  for index in range(len(ref)-1,-1,-1):
    s=ref[index]
    print("index=%d"%index)
    print("s=%s"%ref[index])
    if s.isdigit() and index_is_digit:
      continue
    elif not s.isdigit() and not index_is_digit: 
      continue 
    elif s=='/' or s=='\\':
      result_ref=ref[0:index]
      break
    else:
      result_ref=ref[0:index+1]
      break
  print("result_ref=%s"%result_ref)
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

def write_osm(poi,ways):
  xml = OSMWriter("out.osm")
  for node_id in poi:
    node=poi[node_id]
    xml.node(node_id, node["lat"] , node["lon"], {"power": "pole", "source":"survey","note":"сконвертировано с помощью gpx2osm", "voltage":"400", "ref":node["name"]}, version=1)
    
  for way_id in ways:
    xml.way(way_id, {'power': 'minor_line',"source":"survey","voltage":"400","note":"сконвертировано с помощью gpx2osm"}, ways[way_id], version=1)
#xml.relation(1, {'type': 'boundary'}, [('node', 1), ('way', 2, 'outer')])
  xml.close()

# main:
#print(get_prefery_begin("2/21а4"))
#sys.exit(0)

poi=get_poi(sys.argv[1])

ways={}
way_id=1
print("len(poi)=%d"%len(poi))
for poi_id in poi:
  item=poi[poi_id]
  last_point=item
  first_point=item
  processed_flow=1

  print("process poi_d=%s"%poi_id)
  print("process poi ref=%s"%item["name"])

  # первая точка в линии:
  if "way_id" not in item:
    print("1")
    # если точку ещё не добавляли в линию:
    if way_id not in ways:
      print("2")
      ways[way_id]=[]
    item["way_id"]=way_id
    ways[way_id].append(poi_id)

    while True:
      print("3")
      end_line=False
      dist=0
      # следующие точки в линии:
      cur_name=last_point["name"]
      print("=========  Ищем ближайшие точки для: '%s'"%cur_name)
      list_newarest_points=get_nearest_points(last_point["lat"], last_point["lon"],poi,MAX_DIST)
      print("len(list_newarest_points)=%d"%len(list_newarest_points))

      if len(list_newarest_points)==0:
        # будем заканчивать линию:
        end_line=True
      else:
        candidat=get_next_candidat(poi,last_point,list_newarest_points,cur_name)
        if candidat==None:
          end_line=True
        else:
          dist=great_circles.get_dist(last_point["lon"],last_point["lat"],candidat["lon"],candidat["lat"])

      if dist>MAX_DIST or end_line==True:
        # пробуем прикрепить к началу (к части другой линии):
        print("пробуем прикрепить к началу:")
        list_all_newarest_points=get_all_nearest_points(last_point["lat"], last_point["lon"],poi,MAX_DIST)
        candidat=get_begin_candidat(poi,last_point,list_all_newarest_points,cur_name)
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
          way_id+=1
          break
      else:
        # добавляем точку в линию:
        print("добавляем точку с ref='%s' как следующую для точки с ref='%s'"%(candidat["name"],cur_name))
        if processed_flow==1:
          ways[way_id].append(candidat["poi_id"])
        else:
          ways[way_id].insert(0,candidat["poi_id"])

        candidat["way_id"]=way_id

        # перескакиваем на добавленную точку:
        last_point=candidat

write_osm(poi,ways)
        
        
