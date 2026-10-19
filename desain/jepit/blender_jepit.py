# BeefFresh Jepit di Blender: bahan, poros engsel, render, katalog komponen, berkas .blend.
# Jalankan dari folder desain/jepit:
#   blender -b -P blender_jepit.py -- 48          (angka = jumlah sampel Cycles; 8 untuk uji cepat)
# Di .blend: putar objek kosong "Poros engsel" pada sumbu Y untuk membuka kepala (0 sampai 1,6 rad).
import bpy, json, math, os, sys
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

HERE = os.path.dirname(os.path.abspath(bpy.context.space_data.text.filepath)) if bpy.context.space_data else os.getcwd()
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAMPLES = int(args[0]) if args else 48
MODEL, OUT = os.path.join(HERE, "model"), os.path.join(HERE, "render")
os.makedirs(OUT, exist_ok=True)
INFO = json.load(open(os.path.join(MODEL, "bagian.json")))
KAT = json.load(open(os.path.join(MODEL, "katalog.json")))

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.name = "Rakitan"

# ------------------------------------------------------------------ bahan
def warna(h): return tuple(int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
def lin(c): return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)
BAHAN = {  # nama: (warna dasar sRGB, kasar, logam, tambahan)
    "pvc": ("#d8d1c5", 0.62, 0, {}), "pvc_hitam": ("#1b1c1f", 0.75, 0, {}), "busa": ("#2c3036", 1.0, 0, {}),
    "daging": ("#9c2f27", 0.42, 0, {"Subsurface Weight": 0.25, "Subsurface Radius": (0.9, 0.25, 0.15), "Subsurface Scale": 0.002}),
    "plastik_hitam": ("#141416", 0.45, 0, {}), "beludru": ("#030304", 1.0, 0, {"Sheen Weight": 0.12}),
    "pcb_ungu": ("#5a2380", 0.35, 0, {}), "chip": ("#b9a46a", 0.3, 0, {}), "led": ("#fff3c8", 0.2, 0, {"Emission Color": (1, 0.93, 0.8), "Emission Strength": 3.0}),
    "smd": ("#2a2a2a", 0.4, 0, {}), "emas": ("#e3b85a", 0.25, 1, {}), "baja_hitam": ("#202022", 0.35, 0.9, {}), "logam": ("#b9bcc1", 0.28, 1, {}),
    "pcb_hijau": ("#17603a", 0.35, 0, {}), "pcb_biru": ("#1b4b98", 0.35, 0, {}), "kaca": ("#05070c", 0.05, 0, {"Coat Weight": 1.0}),
    "kertas_putih": ("#f4f4ef", 0.9, 0, {}), "kabel": (None, 0.45, 0, {}),
}
MAT = {}
def bahan(nama, hexwarna=None):
    kunci = nama if nama != "kabel" else "kabel" + hexwarna
    if kunci in MAT: return MAT[kunci]
    base, r, met, extra = BAHAN[nama]
    m = bpy.data.materials.new(kunci); m.use_nodes = True; pb = m.node_tree.nodes["Principled BSDF"]
    pb.inputs["Base Color"].default_value = (*lin(warna(base or hexwarna)), 1); pb.inputs["Roughness"].default_value = r; pb.inputs["Metallic"].default_value = met
    for k, v in extra.items():
        if k in pb.inputs: pb.inputs[k].default_value = v if not isinstance(v, tuple) or len(v) != 3 or k != "Emission Color" else (*v, 1)
    MAT[kunci] = m; return m

GRUP_KOL = {"bawah": "Baki bawah", "atas": "Kepala (berengsel)", "aksesori": "Aksesori kalibrasi"}
def kumpulan(nama, induk=None):
    c = bpy.data.collections.get(nama) or bpy.data.collections.new(nama)
    if c.name not in [x.name for x in (induk or sc.collection).children]: (induk or sc.collection).children.link(c)
    return c

def pasang_bahan(o, b):
    o.data.materials.clear(); o.data.materials.append(bahan(b["bahan"], b["warna"]))
    for p in o.data.polygons: p.use_smooth = False

# ------------------------------------------------------------------ rakitan
bpy.ops.import_scene.gltf(filepath=os.path.join(MODEL, "jepit.glb"))
obj = {}
for o in list(sc.objects):
    if o.type != "MESH": continue
    k = o.name.split(".")[0]
    if k not in INFO["bagian"]: continue
    b = INFO["bagian"][k]; pasang_bahan(o, b); o.name = b["nama"]; o["kunci"] = k
    for c in o.users_collection: c.objects.unlink(o)
    kumpulan(GRUP_KOL[b["grup"]]).objects.link(o); obj[k] = o
for o in list(sc.objects):
    if o.type == "EMPTY": bpy.data.objects.remove(o)

ax, az = INFO["sumbu_engsel"]
bpy.ops.object.empty_add(type="ARROWS", location=(ax / 1000, 0.043, az / 1000)); poros = bpy.context.object; poros.name = "Poros engsel"
poros.empty_display_size = 0.02
for c in poros.users_collection: c.objects.unlink(poros)
kumpulan(GRUP_KOL["atas"]).objects.link(poros)
for k, o in obj.items():
    if INFO["bagian"][k]["grup"] == "atas":
        mw = o.matrix_world.copy(); o.parent = poros; o.matrix_parent_inverse = poros.matrix_world.inverted(); o.matrix_world = mw

# ------------------------------------------------------------------ studio terang (cocok dengan halaman web)
w = bpy.data.worlds.new("Studio"); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes["Background"]; bg.inputs[0].default_value = (*lin(warna("#f1ece4")), 1); bg.inputs[1].default_value = 0.35
bpy.ops.mesh.primitive_plane_add(size=3.0, location=(0.05, 0.05, -0.0381)); lantai = bpy.context.object; lantai.name = "Meja"
ml = bpy.data.materials.new("meja"); ml.use_nodes = True; p_ = ml.node_tree.nodes["Principled BSDF"]
p_.inputs["Base Color"].default_value = (*lin(warna("#e9e2d7")), 1); p_.inputs["Roughness"].default_value = 0.8; lantai.data.materials.append(ml)
lantai.is_shadow_catcher = False
bpy.ops.object.light_add(type="AREA", location=(-0.25, -0.35, 0.45)); kunci_ = bpy.context.object; kunci_.name = "Lampu utama"; kunci_.data.energy = 22; kunci_.data.size = 0.5
bpy.ops.object.light_add(type="AREA", location=(0.35, 0.25, 0.3)); isi_ = bpy.context.object; isi_.name = "Lampu pengisi"; isi_.data.energy = 7; isi_.data.size = 0.6
bpy.ops.object.empty_add(location=(0.043, 0.043, 0.015)); sasaran = bpy.context.object; sasaran.name = "Sasaran kamera"
for L in (kunci_, isi_):
    t_ = L.constraints.new("TRACK_TO"); t_.target = sasaran; t_.track_axis = "TRACK_NEGATIVE_Z"; t_.up_axis = "UP_Y"
bpy.ops.object.camera_add(); cam = bpy.context.object; cam.name = "Kamera"; sc.camera = cam
cam.data.lens = 60; cam.data.clip_start = 0.003; cam.data.clip_end = 10
t_ = cam.constraints.new("TRACK_TO"); t_.target = sasaran; t_.track_axis = "TRACK_NEGATIVE_Z"; t_.up_axis = "UP_Y"

sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = SAMPLES; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1600, 1100
sc.view_settings.view_transform = "AgX"; sc.view_settings.exposure = -0.4
PCT = 40 if SAMPLES <= 8 else 100; sc.render.resolution_percentage = PCT
sc.render.image_settings.file_format = "JPEG"; sc.render.image_settings.quality = 90

def tampil(): return [o for o in sc.objects if o.type == "MESH" and not o.hide_render and o is not lantai]
def bingkai(objs):
    bpy.context.view_layer.update(); xs, ys = [], []
    for o in objs:
        for c in o.bound_box:
            v = world_to_camera_view(sc, cam, o.matrix_world @ Vector(c)); xs.append(v.x); ys.append(v.y)
    return min(xs), max(xs), min(ys), max(ys)
def kamera(az_, el, d, t):
    a, e = math.radians(az_), math.radians(el)
    cam.location = (t[0] + d * math.cos(e) * math.sin(a), t[1] - d * math.cos(e) * math.cos(a), t[2] + d * math.sin(e))
def pas(az_, el, objs=None, margin=0.07, t=None):
    objs = objs or tampil(); bpy.context.view_layer.update()
    mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3)
    for o in objs:
        for c in o.bound_box:
            p = o.matrix_world @ Vector(c)
            for i in range(3): mn[i] = min(mn[i], p[i]); mx[i] = max(mx[i], p[i])
    t = t or (mn + mx) / 2; sasaran.location = t; d = max(mx - mn) * 1.2
    for _ in range(60):
        kamera(az_, el, d, t); x0, x1, y0, y1 = bingkai(objs)
        if x0 >= margin and x1 <= 1 - margin and y0 >= margin and y1 <= 1 - margin: break
        d *= 1.05
    for _ in range(30):
        kamera(az_, el, d / 1.03, t); x0, x1, y0, y1 = bingkai(objs)
        if not (x0 >= margin and x1 <= 1 - margin and y0 >= margin and y1 <= 1 - margin): kamera(az_, el, d, t); break
        d /= 1.03
def render(nama):
    sc.render.filepath = os.path.join(OUT, nama); bpy.ops.render.render(write_still=True); print("RENDER:", nama, flush=True)

# pemotong untuk tampilan potongan (bidang Y = 43 mm, sisi kanan dibuang)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0.05, 0.043 + 0.25, 0.02)); pot = bpy.context.object; pot.name = "Pemotong (Boolean)"
pot.scale = (0.5, 0.5, 0.5); pot.display_type = "WIRE"; pot.hide_render = True
for o in obj.values():
    md = o.modifiers.new("Potong", "BOOLEAN"); md.operation = "DIFFERENCE"; md.object = pot; md.solver = "EXACT"
    md.show_viewport = False; md.show_render = False
pot.hide_viewport = True

aks = [obj[k] for k in ("kal_putih", "kal_hitam")]
def buka(sudut): poros.rotation_euler = (0, math.radians(sudut), 0); bpy.context.view_layer.update()

# 1. tertutup
for o in aks: o.hide_render = True
buka(0); pas(-38, 24); render("1_tertutup.jpg")
# 2. terbuka 90 derajat, daging di atas busa
buka(90); pas(-30, 30); render("2_terbuka.jpg")
# 3. potongan (tertutup)
buka(0)
for o in obj.values(): o.modifiers["Potong"].show_render = True
pas(180, 10); render("3_potongan.jpg")
# 4. detail ruang ukur (potongan, dekat)
dekat = [obj[k] for k in ("tutup_cat", "sensor_pcb", "dudukan_pelat", "dudukan_pipi", "daging")]
pas(180, 6, objs=dekat, margin=0.04); render("4_ruang_ukur.jpg")
for o in obj.values(): o.modifiers["Potong"].show_render = False
# 5. urai
URAI = {"busa_1": 6, "busa_2": 14, "busa_3": 22, "daging": 45, "tutup_cat": 75, "beludru": 75, "dudukan_pelat": 100, "dudukan_pipi": 100,
        "kepala_lantai": 120, "esp_": 145, "kepala_depan": 135, "kepala_belakang": 135, "kepala_kiri": 135, "kepala_kanan": 135,
        "oled_": 180, "kepala_tutup": 200, "kepala_bibir": 200, "engsel_atas": 135, "kait_atas": 135}
def urai_mm(k):
    for p, v in URAI.items():
        if k == p or (p.endswith("_") and k.startswith(p)): return v
    return 92 if k.startswith("sensor_") else 0
for k, o in obj.items():
    if k.startswith("kabel"): o.hide_render = True
    o.location.z += urai_mm(k) / 1000
pas(-38, 20); render("5_urai.jpg")
for k, o in obj.items():
    o.location.z -= urai_mm(k) / 1000; o.hide_render = False

# ------------------------------------------------------------------ katalog komponen (scene terpisah)
sc_kat = bpy.data.scenes.new("Katalog komponen")
sc_kat.render.engine = "CYCLES"; sc_kat.cycles.samples = SAMPLES; sc_kat.cycles.use_denoising = True; sc_kat.cycles.device = "CPU"
sc_kat.render.resolution_x, sc_kat.render.resolution_y = 1800, 1500; sc_kat.view_settings.exposure = -0.4; sc_kat.render.image_settings.file_format = "JPEG"; sc_kat.render.image_settings.quality = 90; sc_kat.render.resolution_percentage = PCT; sc_kat.view_settings.view_transform = "AgX"; sc_kat.world = w
prev = set(bpy.data.objects)
with bpy.context.temp_override(scene=sc_kat):
    bpy.ops.import_scene.gltf(filepath=os.path.join(MODEL, "katalog.glb"))
baru = [o for o in bpy.data.objects if o not in prev]
for o in baru:
    if o.type == "MESH":
        k = o.name.split("__", 1)[1].split(".")[0]; pasang_bahan(o, INFO["bagian"][k])
    elif o.type == "EMPTY": bpy.data.objects.remove(o)
kmesh = [o for o in sc_kat.objects if o.type == "MESH"]
# label: angka dan nama di depan tiap komponen
mt = bpy.data.materials.new("teks"); mt.use_nodes = True; mt.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*lin(warna("#2a2226")), 1)
for kk in KAT:
    cu = bpy.data.curves.new(f"label {kk['no']}", "FONT"); cu.body = f"{kk['no']}. {kk['judul']}"; cu.size = 0.011; cu.align_x = "CENTER"; cu.extrude = 0.0002
    to = bpy.data.objects.new(f"Label {kk['no']}", cu); to.data.materials.append(mt)
    to.location = (kk["pusat"][0] / 1000, kk["pusat"][1] / 1000 - 0.068, 0.0002); sc_kat.collection.objects.link(to)
bpy.ops.mesh.primitive_plane_add(size=1)
m2 = bpy.context.object
for c in m2.users_collection: c.objects.unlink(m2)
sc_kat.collection.objects.link(m2); m2.name = "Meja katalog"; m2.scale = (0.8, 0.8, 1); m2.location = (0.19, -0.165, 0); m2.data.materials.append(ml)
for L in (kunci_, isi_): sc_kat.collection.objects.link(L.copy())
cam2 = cam.copy(); cam2.data = cam.data.copy(); sc_kat.collection.objects.link(cam2); sc_kat.camera = cam2
sas2 = sasaran.copy(); sc_kat.collection.objects.link(sas2); cam2.constraints[0].target = sas2
for o in sc_kat.objects:
    if o.type == "LIGHT": o.constraints[0].target = sas2; o.location = (o.location.x + 0.19, o.location.y - 0.19, o.location.z + 0.25)
sas2.location = (0.1875, -0.175, 0.0); cam2.data.lens = 50
d = 0.80; a_, e_ = math.radians(0), math.radians(62)
cam2.location = (0.1875, -0.175 - d * math.cos(e_), d * math.sin(e_))
sc_kat.render.filepath = os.path.join(OUT, "6_katalog_komponen.jpg")
with bpy.context.temp_override(scene=sc_kat):
    bpy.context.view_layer.update()
bpy.ops.render.render(write_still=True, scene=sc_kat.name); print("RENDER: 6_katalog_komponen.jpg", flush=True)

# ------------------------------------------------------------------ simpan
buka(0); pas(-38, 24)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(MODEL, "jepit.blend"), compress=True); print("BLEND:", os.path.join(MODEL, "jepit.blend"))
