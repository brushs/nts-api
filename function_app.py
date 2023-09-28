import azure.functions as func
import logging
from shapely.geometry import Polygon
import os, pickle
import json

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

pname='nts_optimized.pic'
if os.path.isfile(pname):
    pn=pickle.load(open(pname,'rb')) 
else:
    print(pname+' file is either missing or not in path; run gen_gts_pickle.py or change your working directory or copy the file')


@app.route(route="HttpTriggerNts")
def HttpTriggerNts(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    keys = req.params.keys()
    to_nts = False
    if 'bbox' in keys:
        bbox = req.params.get('bbox')
        polygon = process_input(bbox)
        to_nts = True
        #return func.HttpResponse(f"bbox:{bbox}")
    elif 'polygon' in keys:
        polygon = req.params.get('polygon')
        polygon = process_input(polygon, type="polygon")
        to_nts = True
        #return func.HttpResponse(f"polygon:{polygon}")
    if to_nts:
        ntsn = polygon_to_nts(pn, polygon)
        return func.HttpResponse(json.dumps(ntsn), mimetype="application/json")
    else:
        return func.HttpResponse(
             "Please input parametes.sample: ?bbox=-66.08,-65.25,66.42,66.08 or ?polygon=(-110,54),(-118,54),(-118,55),(-120,55),(-120,60),(-110,60),(-110,54)",
             status_code=200
        )

def process_input(input, type="bbox"):
    if type == "bbox":
        #-66.08,-65.25,66.42,66.08
        print(f'bbox:{input}')
        bbox = eval('[' + input + ']')
        if len(bbox)>4:
            print('Error: more than 4 coordinates')
            pol=None
        if len(set(bbox[:2]))!=len(bbox[:2]):
            print('Error: WE bbox coordinates not unique')
            pol=None
        if len(set(bbox[2:]))!=len(bbox[2:]):
            print('Error: NS bbox coordinates not unique')
            pol=None
        pol=Polygon([(bbox[0],bbox[2]),(bbox[1],bbox[2]),(bbox[1],bbox[3]),(bbox[0],bbox[3]),(bbox[0],bbox[2])])
    elif type == "polygon":
        # polygon vertices in (lon,lat) pairs separated by commas (ex.: (-110,54),(-118,54),(-118,55),(-120,55),(-120,60),(-110,60),(-110,54) \n')
        print(f'polygon:{input}')
        tpol = eval('[' + input + ']')
        pol = Polygon(tpol)
    return pol

def polygon_to_nts(pn, pol):
    if pol is None:
        return None
    ntsn=[[],[],[]]
    d2=pn[0][2] #we're only finding overlaps with 1:50k scale NTS codes, the other scale codes will be determined by truncating the 1:50k NTS codes
    name=pn[1]
    for j,x in enumerate(d2): #loop through NTS 1:50k rectangles
     if x.intersects(pol) and x.intersection(pol).area>0:
      ntsn[2].append(name[2][j]) #append names of overlapping NTS boxes
    
    nts1,nts0=[],[]

    for nts in ntsn[2]:
        nts1.append(nts[0:4]) #truncate 1:50k codes to make them 1:250k
    ntsn[1]=list(set(nts1)) #get unique list of 1:250k codes

    for nts in ntsn[1]:
         nts0.append(nts[0:3]) #truncate 1:250k codes to make them 1:1M
    ntsn[0]=list(set(nts0)) #get unique list of 1:1M codes
     
    for i in range(0,3):
        ntsn[i].sort() #sort each code list
        print('level '+str(i))
        print(';'.join(ntsn[i]))
    return ntsn