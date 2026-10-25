from qa import *
from playwright.sync_api import sync_playwright
e = Ev("CP-12"); e.w("CP-12", time.strftime("%Y-%m-%d %H:%M"))
print(restore()) if False else None
TK={"ADM":login("admin"),"MED":login("qa_medico1"),"PAC":login("paciente")}
# Recursos descartables por rol/operación (se crean con ADM/MED al vuelo para no depender de cuáles quedaron tras CP-08)
def mk_user(n): 
    r=api("POST","/usuarios",token=TK["ADM"],body={"nombre_usuario":n,"correo":n+"@example.com","contrasena_hash":"Cuidarte#Aux2026"}); return r.json()["id"]
def mk_pac(rut,em): return api("POST","/pacientes",token=TK["ADM"],body={"rut":rut,"primer_nombre":"Mat","apellido_paterno":"Riz","fecha_nacimiento":"1990-01-01","sexo":"M","email":em}).json()["id"]
def mk_ex(): return api("POST","/examenes",token=TK["MED"],body={"tipo_examen_medico_id":1,"paciente_id":1,"diagnosis":"mat"}).json()["id"]
def mk_doc(ex): return api("POST","/documentos",token=TK["MED"],data={"examen_medico_id":ex,"paciente_id":1},files={"documento":("m.pdf",open(DAT+"/resultado_examen_v1.pdf","rb"),"application/pdf")}).json()["documento"]["id"]
M={ # operación: (esperado ADM,MED,PAC) ; función(rol)->respuesta
}
exp={1:("Sí","No","No"),2:("Sí","Sí","No"),3:("Sí","Sí","No"),4:("Sí","No","No"),5:("Sí","Sí","No"),6:("Sí","Sí","No"),7:("Sí","Sí","No"),8:("Sí","Sí","Sí"),9:("Sí","No","No")}
res={}
def rec(op,rol,r,allowed_expected):
    okcode = r.status_code<300; res[(op,rol)]=(r.status_code,okcode==allowed_expected)
    e.w(f"op{op} {rol}: HTTP {r.status_code} ({r.elapsed_s}s) esperado {'permitido' if allowed_expected else 'denegado (403)'} -> {'OK' if (okcode==allowed_expected) else 'NO CUMPLE'} | {r.text[:100]!r}")
e.step(1,"9 operaciones x 3 roles por API")
for rol in ["ADM","MED","PAC"]:
    t=TK[rol]; E=lambda op: exp[op][["ADM","MED","PAC"].index(rol)]=="Sí"
    # 1 gestionar usuarios: listar, crear, editar, eliminar (se evalúan las 4; la celda cumple si todas se comportan como se espera)
    sub=[]
    r=api("GET","/usuarios",token=t); sub.append(("listar",r.status_code))
    r2=api("POST","/usuarios",token=t,body={"nombre_usuario":f"qa_m12_{rol}","correo":f"qa_m12_{rol}@example.com","contrasena_hash":"Cuidarte#Aux2026"}); sub.append(("crear",r2.status_code)); uid=r2.json().get("id") if r2.status_code<300 else mk_user(f"qa_m12_t_{rol}")
    r3=api("PUT",f"/usuarios/{uid}",token=t,body={"correo":f"qa_m12_e_{rol}@example.com"}); sub.append(("editar",r3.status_code))
    r4=api("DELETE",f"/usuarios/{uid}",token=t); sub.append(("eliminar",r4.status_code))
    allok=all((c<300)==E(1) for _,c in sub); res[(1,rol)]=(sub,allok); e.w(f"op1 {rol}: {sub} esperado {'permitido' if E(1) else 'denegado'} -> {'OK' if allok else 'NO CUMPLE'}")
    r=api("GET","/pacientes",token=t); rec(2,rol,r,E(2)); r=api("GET","/pacientes/2",token=t); e.w("   (ficha ajena GET /pacientes/2:",r.status_code,")")
    r=api("POST","/pacientes",token=t,body={"rut":f"2{ '0' if rol=='ADM' else '1' if rol=='MED' else '2'}.000.000-0","primer_nombre":"X","apellido_paterno":"Y","fecha_nacimiento":"1990-01-01","sexo":"M","email":f"x_{rol}@example.com"}); 
    p3=r; e.w(f"op3a crear paciente {rol}: HTTP {r.status_code} ({r.elapsed_s}s)")
    r=api("PUT","/pacientes/2",token=t,body={"observaciones_medicas_generales":f"cp12 {rol}"}); rec(3,rol,r,E(3))
    pid=mk_pac(f"7.{ {'ADM':'111','MED':'222','PAC':'333'}[rol]}.000-0",f"mat_{rol}@example.com") 
    r=api("DELETE",f"/pacientes/{pid}",token=t); rec(4,rol,r,E(4))
    r=api("POST","/examenes",token=t,body={"tipo_examen_medico_id":1,"paciente_id":1,"diagnosis":"cp12"}); rec(5,rol,r,E(5))
    ex=mk_ex(); r=api("DELETE",f"/examenes/{ex}",token=t); rec(6,rol,r,E(6))
    ex2=mk_ex(); d=mk_doc(ex2); r=api("DELETE",f"/documentos/{d}",token=t); e.w(f"   op6b eliminar documento {rol}: HTTP {r.status_code}")
    r=api("POST","/documentos",token=t,data={"examen_medico_id":IDS["EX_A3"],"paciente_id":1},files={"documento":("m.pdf",open(DAT+"/resultado_examen_v1.pdf","rb"),"application/pdf")}); rec(7,rol,r,E(7))
    r=api("GET",f"/examenes/{IDS['EX_A1']}",token=t); r2=api("GET",f"/documentos/{IDS['DOC_A1']}",token=t); r3=api("GET",f"/examenes/{IDS['EX_B1']}",token=t); r4=api("GET",f"/documentos/{IDS['DOC_B1']}",token=t)
    ok8 = r.status_code==200 and r2.status_code==200 and ((r3.status_code==200 and r4.status_code==200) if rol!="PAC" else (r3.status_code!=200 and r4.status_code!=200))
    res[(8,rol)]=([r.status_code,r2.status_code,r3.status_code,r4.status_code],ok8); e.w(f"op8 {rol}: propio ex/doc {r.status_code}/{r2.status_code}, ajeno ex/doc {r3.status_code}/{r4.status_code} -> {'OK' if ok8 else 'NO CUMPLE'}")
    r=api("GET","/auditoria",token=t); rec(9,rol,r,E(9))
# conteo de celdas
e.step(5,"conteo de celdas")
def cell_ok(op,rol):
    v=res[(op,rol)]; return v[1]
tot=0; okc=0
for op in range(1,10):
    for rol in ["ADM","MED","PAC"]:
        c=cell_ok(op,rol); tot+=1; okc+= 1 if c else 0
        if not c: e.w(f"  celda no cumple: op{op} {rol} -> {res[(op,rol)][0]}")
e.w(f"celdas que se comportan como se espera: {okc} de {tot}")
json.dump({f"{k[0]}-{k[1]}":v[1] for k,v in res.items()},open("evidencia/CP-12_celdas.json","w"))
e.step(3,"UI como PAC_A")
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(); pg.set_viewport_size({"width":1500,"height":1100})
    pg.goto(WEB+"/login"); pg.get_by_label("Nombre de usuario").fill("paciente"); pg.get_by_label("Contraseña").fill(PW["paciente"]); pg.get_by_role("button",name="Entrar").click(); pg.wait_for_url("**/home",timeout=15000)
    for ru in ["/pacientes","/pacientes/nuevo","/examenes","/usuarios"]:
        pg.goto(WEB+ru); pg.wait_for_timeout(7000); e.w(ru,"->",pg.url,"|",pg.inner_text("body")[:170].replace("\n"," | ")); pg.screenshot(path=os.path.join(EVD,f"CP-12_paso3{ru.replace('/','_')}.png"))
    pg.evaluate("""()=>{const u=JSON.parse(localStorage.user);u.rolNombre='admin';localStorage.user=JSON.stringify(u)}"""); pg.goto(WEB+"/usuarios"); pg.wait_for_timeout(5000)
    e.w("tras user.rolNombre='admin':",pg.url,"|",pg.inner_text("body")[:200].replace("\n"," | ")); pg.screenshot(path=os.path.join(EVD,"CP-12_paso3_rol_manipulado.png"))
    e.w("API con T_PAC_A sigue respondiendo:",short(api("GET","/usuarios",token=TK["PAC"]),100)); b.close()
