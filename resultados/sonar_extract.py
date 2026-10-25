import json, requests
S="http://localhost:9000"; A=("admin","admin"); out="evidencia/sonar/"
def ok(x): return any(i["softwareQuality"] in ("SECURITY","RELIABILITY") for i in x.get("impacts",[]))
for p in ["backend","frontend"]:
    k=f"cuidarteplus-{p}"
    iss=requests.get(S+"/api/issues/search",auth=A,params={"componentKeys":k,"impactSoftwareQualities":"SECURITY,RELIABILITY","ps":500,"statuses":"OPEN,CONFIRMED,REOPENED"}).json()["issues"]
    iss=[x for x in iss if ok(x)]
    hs=requests.get(S+"/api/hotspots/search",auth=A,params={"project":k,"ps":500}).json().get("hotspots",[])
    ms=requests.get(S+"/api/measures/component",auth=A,params={"component":k,"metricKeys":"ncloc,files,vulnerabilities,bugs,security_hotspots,security_rating,reliability_rating"}).json()["component"]["measures"]
    json.dump({"project":k,"measures":ms,"issues":iss,"hotspots":hs},open(out+f"{p}.json","w"),ensure_ascii=False,indent=1)
    L=[f"== {k}: {len(iss)} issues (seguridad/fiabilidad), {len(hs)} security hotspots", "medidas: "+", ".join(f"{m['metric']}={m['value']}" for m in ms)]
    for x in sorted(iss,key=lambda x:(x["component"],x.get("line",0))):
        L.append(f"  [issue] {x['component'].split(':',1)[-1]}:{x.get('line','-')} {x['rule']} sev={x['severity']} impactos={[(i['softwareQuality'],i['severity']) for i in x['impacts']]} :: {x['message']}")
    for x in hs: L.append(f"  [hotspot] {x['component'].split(':',1)[-1]}:{x.get('line','-')} {x['ruleKey']} prob={x['vulnerabilityProbability']} :: {x['message']}")
    open(out+f"resumen_{p}.txt","w",encoding="utf8").write("\n".join(L)); print("\n".join(L))
