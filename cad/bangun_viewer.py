#!/usr/bin/env python3
"""Membuat penampil 3D mandiri (satu berkas HTML, tanpa pustaka luar) dari model OpenSCAD.
Pakai:  ../.venv-cad/bin/python bangun_viewer.py   -> gambar/viewer_3d.html
Seret = putar, roda = zoom, Shift+seret = geser. Centang bagian untuk menampilkan/menyembunyikan; 'Potong' memotong di tengah lebar."""
import base64, os, subprocess, sys
import numpy as np, trimesh

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "gambar"); os.makedirs(OUT, exist_ok=True)
SCAD = os.path.join(HERE, "beeffresh_rumah.scad")
# (kunci, label, part openscad, warna, alpha, tampil awal)
BAGIAN = [("base", "Badan bawah", "base", "#7c8099", 1.0, True), ("tabung", "Tabung gelap", "tube_asm", "#3b3b46", 1.0, True),
          ("esp", "ESP32 (tiruan)", "ghost_esp", "#2e9e4f", 1.0, True), ("oled", "OLED (tiruan)", "ghost_oled", "#4a7bd0", 1.0, True),
          ("tcs", "Sensor TCS34725 (tiruan)", "ghost_tcs", "#c9974a", 1.0, True), ("tutup", "Tutup", "lid_asm", "#b8bdd6", 0.45, True)]

def stl_biner(part):
    path = os.path.join(HERE, "stl", part + ".stl")
    r = subprocess.run(["openscad", "-o", path, "-D", f'part="{part}"', SCAD], capture_output=True, text=True)
    if r.returncode != 0 or "ERROR" in r.stderr: sys.exit(f"gagal render {part}: {r.stderr[-300:]}")
    m = trimesh.load(path)
    tri = m.triangles.astype("<f4"); n = m.face_normals.astype("<f4")
    buf = bytearray(80) + np.uint32(len(tri)).tobytes()
    rec = np.zeros(len(tri), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    rec["n"], rec["v"] = n, tri
    return bytes(buf) + rec.tobytes()

data = {k: base64.b64encode(stl_biner(p)).decode() for k, _, p, _, _, _ in BAGIAN}
# berkas untuk Blender (glTF/GLB): tiap bagian = satu objek bernama, berwarna
scene = trimesh.Scene()
for k, l, p, c, a, _ in BAGIAN:
    m = trimesh.load(os.path.join(HERE, 'stl', p + '.stl')); rgba = [int(c[i:i+2], 16)/255 for i in (1, 3, 5)] + [a]
    # glTF: satuan METER dan sumbu atas Y. Modelku: milimeter, sumbu atas Z. Konversi: (x,y,z)->(x,z,-y), lalu x0,001.
    m.apply_transform(trimesh.transformations.rotation_matrix(-np.pi/2, [1, 0, 0])); m.apply_scale(0.001)
    m.visual = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(name=l, baseColorFactor=rgba, metallicFactor=0.0, roughnessFactor=0.8, alphaMode='BLEND' if a < 1 else 'OPAQUE'))
    scene.add_geometry(m, node_name=l, geom_name=l)
os.makedirs(os.path.join(HERE, 'model-3d'), exist_ok=True)
scene.export(os.path.join(HERE, 'model-3d', 'beeffresh_rakitan.glb')); print('ditulis model-3d/beeffresh_rakitan.glb')
meta = [{"k": k, "label": l, "color": c, "alpha": a, "on": on} for k, l, _, c, a, on in BAGIAN]
import json
HTML = r'''<!doctype html><meta charset="utf-8">
<style>
 body{margin:0;font:13px var(--font,system-ui);color:var(--foreground,#f6efe2)}
 #w{position:relative;width:100%;max-width:980px}
 canvas{width:100%;height:480px;display:block;background:#0d1024;border:1px solid var(--border,#262c5a);border-radius:6px;cursor:grab;touch-action:none}
 #ui{display:flex;flex-wrap:wrap;gap:6px 16px;margin:8px 0;align-items:center}
 label{cursor:pointer;display:flex;align-items:center;gap:6px} i{width:10px;height:10px;border-radius:2px;display:inline-block}
 #h{color:var(--muted-foreground,#8f8aa6);font-size:12px} #err{color:#d9594c}
</style>
<div id="w"><canvas id="c"></canvas><div id="ui"></div><div id="h">Seret = putar &nbsp;·&nbsp; roda = zoom &nbsp;·&nbsp; Shift+seret = geser. <b>Potong</b> memilih sumbu lalu geser untuk melihat isi; <b>Urai</b> memisahkan bagian ke atas. Komponen hijau/biru/emas adalah benda tiruan berukuran standar.</div><div id="err"></div></div>
<script>
const META=__META__, DATA=__DATA__;
const cv=document.getElementById('c'), gl=cv.getContext('webgl',{antialias:true});
if(!gl){document.getElementById('err').textContent='WebGL tidak tersedia di tampilan ini.';}
const VS=`attribute vec3 p;attribute vec3 n;uniform mat4 M;uniform mat4 V;uniform mat4 P;varying vec3 vn;varying vec3 wp;
void main(){vec4 w=M*vec4(p,1.0);wp=w.xyz;vn=n;gl_Position=P*V*w;}`;
const FS=`precision mediump float;varying vec3 vn;varying vec3 wp;uniform vec3 col;uniform float alpha;uniform float cut;uniform float ax;uniform float flip;uniform vec3 L;
void main(){ if(ax>-0.5){float v=ax<0.5?wp.x:(ax<1.5?wp.y:wp.z); if(flip<0.5?(v>cut):(v<cut)) discard;}
 vec3 N=normalize(vn); if(!gl_FrontFacing) N=-N; float d=max(dot(N,normalize(L)),0.0); float r=pow(1.0-abs(N.z)*0.0,1.0);
 vec3 c=col*(0.35+0.75*d)+vec3(0.10)*pow(max(dot(N,normalize(L+vec3(0,0,1))),0.0),12.0);
 gl_FragColor=vec4(c,alpha);}`;
function sh(t,s){const o=gl.createShader(t);gl.shaderSource(o,s);gl.compileShader(o);if(!gl.getShaderParameter(o,gl.COMPILE_STATUS))document.getElementById('err').textContent+=gl.getShaderInfoLog(o);return o}
const pr=gl.createProgram();gl.attachShader(pr,sh(gl.VERTEX_SHADER,VS));gl.attachShader(pr,sh(gl.FRAGMENT_SHADER,FS));gl.linkProgram(pr);gl.useProgram(pr);
const loc=n=>gl.getUniformLocation(pr,n), aP=gl.getAttribLocation(pr,'p'), aN=gl.getAttribLocation(pr,'n');
function b64(s){const b=atob(s),u=new Uint8Array(b.length);for(let i=0;i<b.length;i++)u[i]=b.charCodeAt(i);return u.buffer}
const parts={}; let mn=[1e9,1e9,1e9], mx=[-1e9,-1e9,-1e9];
for(const m of META){const buf=b64(DATA[m.k]),dv=new DataView(buf),nt=dv.getUint32(80,true),pos=new Float32Array(nt*9),nor=new Float32Array(nt*9);
 for(let t=0;t<nt;t++){const o=84+t*50;for(let v=0;v<3;v++)for(let a=0;a<3;a++){const x=dv.getFloat32(o+12+v*12+a*4,true);pos[t*9+v*3+a]=x;nor[t*9+v*3+a]=dv.getFloat32(o+a*4,true);if(x<mn[a])mn[a]=x;if(x>mx[a])mx[a]=x}}
 const bp=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,bp);gl.bufferData(gl.ARRAY_BUFFER,pos,gl.STATIC_DRAW);
 const bn=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,bn);gl.bufferData(gl.ARRAY_BUFFER,nor,gl.STATIC_DRAW);
 parts[m.k]={bp,bn,n:nt*3,on:m.on,alpha:m.alpha,col:[parseInt(m.color.slice(1,3),16)/255,parseInt(m.color.slice(3,5),16)/255,parseInt(m.color.slice(5,7),16)/255]}}
const ctr=[0,1,2].map(i=>(mn[i]+mx[i])/2), size=Math.max(mx[0]-mn[0],mx[1]-mn[1],mx[2]-mn[2]);
let yaw=-0.7,pit=0.55,dist=size*1.9,pan=[0,0,0],cutAx=-1,cutPos=0,cutFlip=0,expl=0;
const EXPL={base:0,tabung:-0.20,esp:0.22,oled:0.30,tcs:0.12,tutup:0.50};
const ui=document.getElementById('ui');
for(const m of META){const l=document.createElement('label');l.innerHTML='<input type="checkbox" '+(m.on?'checked':'')+'><i style="background:'+m.color+'"></i>'+m.label;l.firstChild.onchange=e=>{parts[m.k].on=e.target.checked;draw()};ui.appendChild(l)}
function ctl(html){const d=document.createElement('label');d.innerHTML=html;ui.appendChild(d);return d}
const tt=ctl('<input type="checkbox" checked> Tutup transparan');tt.firstChild.onchange=e=>{parts.tutup.alpha=e.target.checked?0.45:1.0;draw()};
const cs=ctl('Potong: <select><option value="-1">mati</option><option value="0">sumbu X (panjang)</option><option value="1">sumbu Y (lebar)</option><option value="2">sumbu Z (tinggi)</option></select> <input type="range" min="0" max="1000" value="500" style="width:130px"> <input type="checkbox"> balik');
const sel=cs.querySelector('select'),sl=cs.querySelector('input[type=range]'),fl=cs.querySelector('input[type=checkbox]');
function setCut(){cutAx=+sel.value;if(cutAx>=0)cutPos=mn[cutAx]+(mx[cutAx]-mn[cutAx])*(sl.value/1000);cutFlip=fl.checked?1:0;draw()}
sel.onchange=()=>{sl.value=500;setCut()};sl.oninput=setCut;fl.onchange=setCut;
const ex=ctl('Urai: <input type="range" min="0" max="100" value="0" style="width:130px">');ex.querySelector('input').oninput=e=>{expl=e.target.value/100;draw()};
const lr=document.createElement('label');lr.innerHTML='<span style="cursor:pointer;text-decoration:underline">Atur ulang</span>';lr.onclick=()=>{yaw=-0.7;pit=0.55;dist=size*1.9;pan=[0,0,0];sel.value=-1;sl.value=500;fl.checked=false;ex.querySelector('input').value=0;expl=0;setCut()};ui.appendChild(lr);
function mul(a,b){const o=new Float32Array(16);for(let i=0;i<4;i++)for(let j=0;j<4;j++){let s=0;for(let k=0;k<4;k++)s+=a[k*4+j]*b[i*4+k];o[i*4+j]=s}return o}
function persp(f,a,n,fa){const t=1/Math.tan(f/2),o=new Float32Array(16);o[0]=t/a;o[5]=t;o[10]=(fa+n)/(n-fa);o[11]=-1;o[14]=2*fa*n/(n-fa);return o}
function look(e,c,u){let z=[e[0]-c[0],e[1]-c[1],e[2]-c[2]],l=Math.hypot(...z);z=z.map(v=>v/l);let x=[u[1]*z[2]-u[2]*z[1],u[2]*z[0]-u[0]*z[2],u[0]*z[1]-u[1]*z[0]];l=Math.hypot(...x);x=x.map(v=>v/l);const y=[z[1]*x[2]-z[2]*x[1],z[2]*x[0]-z[0]*x[2],z[0]*x[1]-z[1]*x[0]];
 return new Float32Array([x[0],y[0],z[0],0,x[1],y[1],z[1],0,x[2],y[2],z[2],0,-(x[0]*e[0]+x[1]*e[1]+x[2]*e[2]),-(y[0]*e[0]+y[1]*e[1]+y[2]*e[2]),-(z[0]*e[0]+z[1]*e[1]+z[2]*e[2]),1])}
function draw(){const dpr=window.devicePixelRatio||1,w=cv.clientWidth,h=cv.clientHeight;if(cv.width!=w*dpr||cv.height!=h*dpr){cv.width=w*dpr;cv.height=h*dpr}
 gl.viewport(0,0,cv.width,cv.height);gl.clearColor(0.051,0.063,0.141,1);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);gl.enable(gl.DEPTH_TEST);
 const t=[ctr[0]+pan[0],ctr[1]+pan[1],ctr[2]+pan[2]],e=[t[0]+dist*Math.cos(pit)*Math.sin(yaw),t[1]-dist*Math.cos(pit)*Math.cos(yaw),t[2]+dist*Math.sin(pit)];
 const V=look(e,t,[0,0,1]),P=persp(0.8,cv.width/cv.height,size*0.05,size*20),I=new Float32Array([1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]);
 gl.uniformMatrix4fv(loc('V'),false,V);gl.uniformMatrix4fv(loc('P'),false,P);gl.uniformMatrix4fv(loc('M'),false,I);gl.uniform3f(loc('L'),0.4,-0.6,0.9);gl.uniform1f(loc('cut'),cutPos);gl.uniform1f(loc('ax'),cutAx);gl.uniform1f(loc('flip'),cutFlip);
 const order=META.map(m=>m.k).sort((a,b)=>(parts[a].alpha<1)-(parts[b].alpha<1));
 for(const k of order){const p=parts[k];if(!p.on)continue;gl.uniform3fv(loc('col'),p.col);gl.uniform1f(loc('alpha'),p.alpha);gl.uniformMatrix4fv(loc('M'),false,new Float32Array([1,0,0,0,0,1,0,0,0,0,1,0,0,0,EXPL[k]*expl*size,1]));
  if(p.alpha<1){gl.enable(gl.BLEND);gl.blendFunc(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA);gl.depthMask(false)}else{gl.disable(gl.BLEND);gl.depthMask(true)}
  gl.bindBuffer(gl.ARRAY_BUFFER,p.bp);gl.enableVertexAttribArray(aP);gl.vertexAttribPointer(aP,3,gl.FLOAT,false,0,0);
  gl.bindBuffer(gl.ARRAY_BUFFER,p.bn);gl.enableVertexAttribArray(aN);gl.vertexAttribPointer(aN,3,gl.FLOAT,false,0,0);gl.drawArrays(gl.TRIANGLES,0,p.n)}
 gl.depthMask(true)}
let drag=null;cv.onpointerdown=e=>{drag={x:e.clientX,y:e.clientY,s:e.shiftKey};cv.setPointerCapture(e.pointerId);cv.style.cursor='grabbing'};
cv.onpointerup=()=>{drag=null;cv.style.cursor='grab'};
cv.onpointermove=e=>{if(!drag)return;const dx=e.clientX-drag.x,dy=e.clientY-drag.y;drag.x=e.clientX;drag.y=e.clientY;
 if(drag.s){const k=dist*0.0016;pan[0]-=dx*k*Math.cos(yaw);pan[1]-=dx*k*Math.sin(yaw);pan[2]+=dy*k}else{yaw-=dx*0.008;pit=Math.max(-1.5,Math.min(1.5,pit+dy*0.008))}draw()};
cv.onwheel=e=>{e.preventDefault();dist*=Math.exp(e.deltaY*0.0012);draw()};
window.addEventListener('resize',draw);draw();window.__siap=true;
</script>'''
html = HTML.replace("__META__", json.dumps(meta)).replace("__DATA__", json.dumps(data))
out = os.path.join(OUT, "viewer_3d.html"); open(out, "w").write(html)
print(f"ditulis {out} ({len(html)//1024} KB)")
