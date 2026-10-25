import os, zlib, struct
from PIL import Image
d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datos")
def pdf(path, text, size=None):
    body = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET"
    objs = ["<</Type/Catalog/Pages 2 0 R>>","<</Type/Pages/Kids[3 0 R]/Count 1>>",
     "<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>",
     f"<</Length {len(body)}>>\nstream\n{body}\nendstream","<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>"]
    out = b"%PDF-1.4\n"; offs=[]
    for i,o in enumerate(objs,1):
        offs.append(len(out)); out += f"{i} 0 obj\n{o}\nendobj\n".encode()
    x=len(out); out += f"xref\n0 {len(objs)+1}\n0000000000 65535 f \n".encode()
    for o in offs: out += f"{o:010d} 00000 n \n".encode()
    out += f"trailer\n<</Size {len(objs)+1}/Root 1 0 R>>\nstartxref\n{x}\n%%EOF\n".encode()
    if size:  # relleno como comentario PDF hasta alcanzar el tamaño
        out += b"%" + b"A"*(size-len(out)-2) + b"\n"
    open(os.path.join(d,path),"wb").write(out)
pdf("resultado_examen.pdf","Resultado examen QA - Hemograma",2097152)
pdf("resultado_examen_v1.pdf","Resultado examen QA - Glicemia version 1")
pdf("resultado_examen_v2.pdf","Resultado examen QA - Glicemia version 2")
pdf("resultado_eliminar.pdf","Resultado QA a eliminar 1")
pdf("resultado_eliminar2.pdf","Resultado QA a eliminar 2")
pdf("resultado_grande.pdf","Resultado QA grande",11534336)
im = Image.new("RGB",(64,64),(200,60,60)); im.save(os.path.join(d,"radiografia.jpg"),"JPEG")
im.save(os.path.join(d,"imagen.png"),"PNG")
open(os.path.join(d,"script_malicioso.exe"),"wb").write(b"MZ"+b"\x90\x00"*64)
open(os.path.join(d,"resultado_falso.pdf"),"wb").write(b"MZ"+b"\x90\x00"*64)
open(os.path.join(d,"foto_falsa.jpg"),"w").write("<html><script>alert(1)</script></html>")
