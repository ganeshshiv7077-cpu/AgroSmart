import os
import requests
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_folder=".", static_url_path="")
API_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
API_KEY = os.environ.get("DATA_GOV_IN_API_KEY", "").strip()
STATES = ["Maharashtra", "Karnataka", "Gujarat", "Madhya Pradesh", "Telangana", "Goa"]
CROPS = {
"Tomato":["Tomato"],"Potato":["Potato"],"Onion":["Onion"],"Cabbage":["Cabbage"],
"Cauliflower":["Cauliflower"],"Brinjal":["Brinjal","Eggplant"],"Okra":["Bhindi","Ladies Finger","Okra"],
"Cucumber":["Cucumbar","Cucumber","Kheera"],"Carrot":["Carrot"],"Spinach":["Spinach"],
"Green Chilli":["Green Chilli","Chilli"],"Bottle Gourd":["Bottle gourd"],"Bitter Gourd":["Bitter gourd"],
"Pumpkin":["Pumpkin"],"Peas":["Peas","Green Peas"],"Banana":["Banana"],"Mango":["Mango"],
"Apple":["Apple"],"Grapes":["Grapes"],"Orange":["Orange"],"Pomegranate":["Pomegranate"],
"Papaya":["Papaya"],"Watermelon":["Watermelon"],"Guava":["Guava"],"Pineapple":["Pineapple"]}
def num(v):
    try:
        n=float(str(v).replace(",","").strip())
        return n if n>0 else None
    except (TypeError,ValueError): return None
def fetch(state,aliases):
    out=[]
    for alias in aliases:
        try:
            r=requests.get(API_URL,params={"api-key":API_KEY,"format":"json","limit":1000,
              "filters[state]":state,"filters[commodity]":alias},timeout=20)
            r.raise_for_status(); records=r.json().get("records",[])
        except (requests.RequestException,ValueError): continue
        for x in records:
            st=str(x.get("state","")).strip(); com=str(x.get("commodity","")).strip()
            market=str(x.get("market","")).strip(); modal=num(x.get("modal_price"))
            if st.lower()!=state.lower() or alias.lower() not in com.lower() or not market or modal is None: continue
            out.append({"state":st,"district":str(x.get("district","")).strip(),"market":market,
              "commodity":com,"variety":str(x.get("variety","")).strip(),"date":str(x.get("arrival_date","")).strip(),
              "minimum":num(x.get("min_price")),"maximum":num(x.get("max_price")),"modal":modal,
              "source":"data.gov.in / Agmarknet"})
    unique={}
    for x in out:
        k=(x["state"].lower(),x["district"].lower(),x["market"].lower(),x["commodity"].lower(),x["date"],x["variety"].lower())
        unique[k]=x
    return list(unique.values())
@app.get("/")
def home(): return send_from_directory(".","index.html")
@app.get("/api/markets")
def markets():
    if not API_KEY: return jsonify({"error":"API key missing. Set DATA_GOV_IN_API_KEY and restart AgroSmart.","records":[]}),503
    crop=request.args.get("crop","").strip()
    states=request.args.getlist("state") or STATES
    if crop not in CROPS: return jsonify({"error":"Unsupported crop.","records":[]}),400
    states=[s for s in states if s in STATES]
    if not states: return jsonify({"error":"Select at least one supported state.","records":[]}),400
    rows=[]; missing=[]
    for s in states:
        found=fetch(s,CROPS[crop])
        if found: rows.extend(found)
        else: missing.append(s)
    rows.sort(key=lambda x:x.get("date",""),reverse=True)
    return jsonify({"crop":crop,"source":"Government of India data.gov.in / Agmarknet",
      "retrieved_at":datetime.now().astimezone().isoformat(),
      "latest_reported_date":max((x.get("date","") for x in rows),default=None),
      "states_without_results":missing,"count":len(rows),"records":rows,
      "notice":"Reported prices may be delayed; check each record date."})
if __name__=="__main__": app.run(host="127.0.0.1",port=5000,debug=False)
