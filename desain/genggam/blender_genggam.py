# Render Blender desain A-PVC (genggam) + berkas .blend.
# Jalankan dari folder desain/genggam:  blender -b -P blender_genggam.py -- 32   (8 = uji cepat)
import bpy, json, math, os, sys
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

HERE = os.getcwd()
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAMPLES = int(args[0]) if args else 32
MODEL, OUT = os.path.join(HERE, "model"), os.path.join(HERE, "render"); os.makedirs(OUT, exist_ok=True)
INFO = json.load(open(os.path.join(MODEL, "bagian.json")))
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.name = "Genggam"

def warna(h): return tuple(int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
def lin(c): return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)
BAHAN = {"pvc": ("#d8d1c5", 0.62, 0, {}), "pvc_hitam": ("#1b1c1f", 0.75, 0, {}), "busa": ("#2c3036", 1.0, 0, {}),
         "daging": ("#9c2f27", 0.42, 0, {"Subsurface Weight": 0.25, "Subsurface Scale": 0.002}), "plastik_hitam": ("#141416", 0.45, 0, {}),
         "beludru": ("#030304", 1.0, 0, {}), "pcb_ungu": ("#5a2380", 0.35, 0, {}), "chip": ("#b9a46a", 0.3, 0, {}),
         "led": ("#fff3c8", 0.2, 0, {"Emission Strength": 3.0}), "smd": ("#2a2a2a", 0.4, 0, {}), "emas": ("#e3b85a", 0.25, 1, {}),
         "baja_hitam": ("#202022", 0.35, 0.9, {}), "logam": ("#b9bcc1", 0.28, 1, {}), "pcb_hijau": ("#17603a", 0.35, 0, {}),
         "pcb_biru": ("#1b4b98", 0.35, 0, {}), "kaca": ("#05070c", 0.05, 0, {"Coat Weight": 1.0}), "kabel": (None, 0.45, 0, {}), "cat_merah": ("#b3262e", 0.5, 0, {})}
MAT = {}
def bahan(nama, hx):
    kunci = nama if nama != "kabel" else "kabel" + hx
    if kunci in MAT: return MAT[kunci]
    base, r, met, extra = BAHAN.get(nama, ("#888888", 0.5, 0, {}))
    m = bpy.data.materials.new(kunci); m.use_nodes = True; pb = m.node_tree.nodes["Principled BSDF"]
    pb.inputs["Base Color"].default_value = (*lin(warna(base or hx)), 1); pb.inputs["Roughness"].default_value = r; pb.inputs["Metallic"].default_value = met
    for k, v in extra.items():
        if k in pb.inputs: pb.inputs[k].default_value = v
    if nama == "led": pb.inputs["Emission Color"].default_value = (1, 0.93, 0.8, 1)
    if nama == "pvc" and kunci == "pvc": pass
    MAT[kunci] = m; return m

bpy.ops.import_scene.gltf(filepath=os.path.join(MODEL, "genggam.glb"))
obj = {}
kol = {"alat": bpy.data.collections.new("Alat (A versi PVC)"), "daging": bpy.data.collections.new("Daging contoh")}
for c in kol.values(): sc.collection.children.link(c)
for o in list(sc.objects):
    if o.type == "EMPTY": bpy.data.objects.remove(o); continue
    if o.type != "MESH": continue
    k = o.name.split(".")[0]
    if k not in INFO["bagian"]: continue
    b = INFO["bagian"][k]; o.data.materials.clear(); o.data.materials.append(bahan(b["bahan"], b["warna"]))
    o.name = b["nama"]; o["kunci"] = k
    for c in o.users_collection: c.objects.unlink(o)
    kol[b["grup"]].objects.link(o); obj[k] = o
# tutup atas agak tembus pada render supaya isi terlihat (di .blend tetap padat)
w = bpy.data.worlds.new("Studio"); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes["Background"]; bg.inputs[0].default_value = (*lin(warna("#f1ece4")), 1); bg.inputs[1].default_value = 0.35
bpy.ops.mesh.primitive_plane_add(size=3.0, location=(0, 0, -0.0141)); meja = bpy.context.object; meja.name = "Meja"
ml = bpy.data.materials.new("meja"); ml.use_nodes = True; ml.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*lin(warna("#e9e2d7")), 1); meja.data.materials.append(ml)
bpy.ops.object.light_add(type="AREA", location=(-0.2, -0.3, 0.4)); L1 = bpy.context.object; L1.data.energy = 18; L1.data.size = 0.45
bpy.ops.object.light_add(type="AREA", location=(0.3, 0.25, 0.25)); L2 = bpy.context.object; L2.data.energy = 6; L2.data.size = 0.5
bpy.ops.object.empty_add(location=(0, 0, 0.02)); sas = bpy.context.object; sas.name = "Sasaran kamera"
for L in (L1, L2):
    c = L.constraints.new("TRACK_TO"); c.target = sas; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
bpy.ops.object.camera_add(); cam = bpy.context.object; cam.name = "Kamera"; sc.camera = cam; cam.data.lens = 60; cam.data.clip_start = 0.003
c = cam.constraints.new("TRACK_TO"); c.target = sas; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = SAMPLES; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1600, 1100; sc.render.resolution_percentage = 40 if SAMPLES <= 8 else 100
sc.view_settings.view_transform = "AgX"; sc.view_settings.exposure = -0.4
sc.render.image_settings.file_format = "JPEG"; sc.render.image_settings.quality = 90

def tampil(): return [o for o in sc.objects if o.type == "MESH" and not o.hide_render and o is not meja]
def pas(az, el, objs=None, margin=0.07):
    objs = objs or tampil(); bpy.context.view_layer.update()
    mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3)
    for o in objs:
        for cc in o.bound_box:
            p = o.matrix_world @ Vector(cc)
            for i in range(3): mn[i] = min(mn[i], p[i]); mx[i] = max(mx[i], p[i])
    t = (mn + mx) / 2; sas.location = t; d = max(mx - mn) * 1.2; a, e = math.radians(az), math.radians(el)
    def taruh(dd): cam.location = (t[0] + dd * math.cos(e) * math.sin(a), t[1] - dd * math.cos(e) * math.cos(a), t[2] + dd * math.sin(e))
    def muat():
        bpy.context.view_layer.update(); xs, ys = [], []
        for o in objs:
            for cc in o.bound_box:
                v = world_to_camera_view(sc, cam, o.matrix_world @ Vector(cc)); xs.append(v.x); ys.append(v.y)
        return min(xs) >= margin and max(xs) <= 1 - margin and min(ys) >= margin and max(ys) <= 1 - margin
    for _ in range(60):
        taruh(d)
        if muat(): break
        d *= 1.05
    for _ in range(30):
        taruh(d / 1.03)
        if not muat(): taruh(d); break
        d /= 1.03
def render(nama): sc.render.filepath = os.path.join(OUT, nama); bpy.ops.render.render(write_still=True); print("RENDER:", nama, flush=True)

tutup = [obj[k] for k in ("tutup_atas", "bibir", "tanda_tekan")]
# 1. utuh di atas daging
pas(-35, 26); render("1_utuh.jpg")
# 2. tutup dilepas, dilihat dari atas serong
for o in tutup: o.hide_render = True
pas(-20, 55); render("2_isi.jpg")
for o in tutup: o.hide_render = False
# 3. potongan tengah (pemotong membuang sisi -y, kamera di sisi itu)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.25, 0.02)); pot = bpy.context.object; pot.name = "Pemotong (Boolean)"; pot.scale = (0.5, 0.5, 0.5)
pot.display_type = "WIRE"; pot.hide_render = True
for o in obj.values():
    md = o.modifiers.new("Potong", "BOOLEAN"); md.operation = "DIFFERENCE"; md.object = pot; md.solver = "EXACT"; md.show_viewport = False; md.show_render = True
pas(0, 8); render("3_potongan.jpg")
dekat = [obj[k] for k in ("tabung", "pelat_muka", "sensor_pcb", "dudukan_cakram")]
pas(0, 6, objs=dekat, margin=0.05); render("4_ruang_ukur.jpg")
for o in obj.values(): o.modifiers["Potong"].show_render = False
pot.hide_viewport = True
# 5. urai
U = {}
for k, o in obj.items():
    dz = (-20 if k == "daging" else 75 if k in ("tutup_atas", "bibir", "tanda_tekan") else 62 if k.startswith("oled_") else 32 if k.startswith("esp_") else 22 if k.startswith(("sensor_", "dudukan_")) else 12 if k in ("tabung", "beludru") else 0) / 1000
    if k.startswith("kabel"): o.hide_render = True
    U[k] = dz; o.location.z += dz
pas(-35, 20); render("5_urai.jpg")
for k, o in obj.items(): o.location.z -= U[k]; o.hide_render = False
# 6. tampak bawah: pelat muka dan lubang (daging dan meja disembunyikan)
obj["daging"].hide_render = True; meja.hide_render = True
pas(-30, -40); render("6_bawah.jpg")
obj["daging"].hide_render = False; meja.hide_render = False
pas(-35, 26)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(MODEL, "genggam.blend"), compress=True); print("BLEND:", os.path.join(MODEL, "genggam.blend"))
