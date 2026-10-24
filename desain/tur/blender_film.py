# Film scroll BeefFresh: urutan gambar per model (latar transparan, digabung ke latar halaman saat dikonversi).
# Jalankan dari folder desain/tur:
#   blender -b -P blender_film.py -- jepit   [sampel] [mulai] [akhir] [persen] [GPU|CPU]
#   blender -b -P blender_film.py -- genggam ...
#   blender -b -P blender_film.py -- banding ...
#   blender -b -P blender_film.py -- jepitbb ...   (Model 2B, breadboard; model dari jepit/model_bb)
import bpy, json, math, os, sys
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
MODEL = args[0]; SAMPLES = int(args[1]) if len(args) > 1 else 24
F0 = int(args[2]) if len(args) > 2 else 0; F1 = int(args[3]) if len(args) > 3 else 10 ** 6
PCT = int(args[4]) if len(args) > 4 else 100; DEV = args[5] if len(args) > 5 else "GPU"
DES = os.path.abspath(os.path.join(os.getcwd(), ".."))
OUT = os.path.join(os.getcwd(), "frame_mentah", MODEL); os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

# ------------------------------------------------------------------ bahan (sama dengan render biasa)
def warna(h): return tuple(int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
def lin(c): return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)
BAHAN = {"pvc": ("#cfc8bc", 0.5, 0), "pvc_hitam": ("#1b1c1f", 0.7, 0), "busa": ("#2c3036", 1.0, 0), "daging": ("#9c2f27", 0.38, 0),
         "plastik_hitam": ("#141416", 0.45, 0), "beludru": ("#030304", 1.0, 0), "pcb_ungu": ("#5a2380", 0.35, 0), "chip": ("#b9a46a", 0.3, 0),
         "led": ("#fff3c8", 0.2, 0), "smd": ("#2a2a2a", 0.4, 0), "emas": ("#e3b85a", 0.25, 1), "baja_hitam": ("#202022", 0.35, 0.9),
         "logam": ("#b9bcc1", 0.28, 1), "pcb_hijau": ("#17603a", 0.35, 0), "pcb_hitam": ("#1a1c20", 0.35, 0), "pcb_biru": ("#1b4b98", 0.35, 0), "kaca": ("#05070c", 0.05, 0),
         "kertas_putih": ("#f4f4ef", 0.9, 0), "kabel": (None, 0.45, 0), "cat_merah": ("#b3262e", 0.5, 0), "plastik": ("#141416", 0.45, 0)}
MAT = {}
def bahan(nama, hx):
    kunci = nama if nama != "kabel" else "kabel" + hx
    if kunci in MAT: return MAT[kunci]
    base, r, met = BAHAN.get(nama, ("#888888", 0.5, 0))
    m = bpy.data.materials.new(kunci); m.use_nodes = True; pb = m.node_tree.nodes["Principled BSDF"]
    pb.inputs["Base Color"].default_value = (*lin(warna(base or hx)), 1); pb.inputs["Roughness"].default_value = r; pb.inputs["Metallic"].default_value = met
    if nama == "daging": pb.inputs["Subsurface Weight"].default_value = 0.25; pb.inputs["Subsurface Scale"].default_value = 0.002
    if nama == "led": pb.inputs["Emission Color"].default_value = (1, 0.93, 0.8, 1); pb.inputs["Emission Strength"].default_value = 0.0
    if nama == "kaca": pb.inputs["Coat Weight"].default_value = 1.0
    MAT[kunci] = m; return m

def impor(folder, glb, geser=(0, 0, 0), sub="model"):
    info = json.load(open(os.path.join(DES, folder, sub, "bagian.json")))
    sebelum = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(DES, folder, sub, glb))
    obj = {}
    for o in [o for o in bpy.data.objects if o not in sebelum]:
        if o.type != "MESH": bpy.data.objects.remove(o); continue
        k = o.name.split(".")[0]
        if k not in info["bagian"] or info["bagian"][k]["grup"] == "aksesori": bpy.data.objects.remove(o); continue
        b = info["bagian"][k]; o.data.materials.clear(); o.data.materials.append(bahan(b["bahan"], b["warna"]))
        o.location = Vector(o.location) + Vector(geser); obj[k] = o
    return info, obj

# ------------------------------------------------------------------ studio gelap
w = bpy.data.worlds.new("Studio gelap"); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes["Background"]; bg.inputs[0].default_value = (*lin(warna("#15171a")), 1); bg.inputs[1].default_value = 0.25
sc.render.film_transparent = True
def lampu(nama, loc, energi, ukuran, warna_="#ffffff"):
    bpy.ops.object.light_add(type="AREA", location=loc); L = bpy.context.object; L.name = nama
    L.data.energy = energi; L.data.size = ukuran; L.data.color = lin(warna(warna_)); return L
L_kunci = lampu("Kunci", (-0.36, -0.12, 0.30), 11, 0.30, "#fff4e8")
L_isi = lampu("Isi", (0.32, -0.12, 0.16), 2.0, 0.5, "#dfe8ff")
L_tepi = lampu("Tepi", (0.08, 0.36, 0.30), 16, 0.25, "#cfe0ff")
bpy.ops.object.empty_add(); sas = bpy.context.object; sas.name = "Sasaran"
for L in (L_kunci, L_isi, L_tepi):
    c = L.constraints.new("TRACK_TO"); c.target = sas; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
bpy.ops.object.camera_add(); cam = bpy.context.object; sc.camera = cam; cam.data.lens = 55; cam.data.clip_start = 0.003
c = cam.constraints.new("TRACK_TO"); c.target = sas; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"

sc.render.engine = "CYCLES"; sc.cycles.samples = SAMPLES; sc.cycles.use_denoising = True
sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.03
if DEV == "GPU":
    pr = bpy.context.preferences.addons["cycles"].preferences
    try:
        pr.compute_device_type = "OPTIX"; pr.get_devices()
        for d in pr.devices: d.use = d.type == "OPTIX"
        sc.cycles.device = "GPU"; sc.cycles.denoiser = "OPTIX"
    except Exception as e: print("GPU gagal:", e); sc.cycles.device = "CPU"
else: sc.cycles.device = "CPU"
sc.render.resolution_x, sc.render.resolution_y = 1280, 960; sc.render.resolution_percentage = PCT
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"; sc.view_settings.exposure = -0.5
sc.render.image_settings.file_format = "PNG"; sc.render.image_settings.color_mode = "RGBA"; sc.render.image_settings.compression = 30
sc.cycles.max_bounces = 6

def kamera(az, el, d, t):
    a, e = math.radians(az), math.radians(el)
    cam.location = (t[0] + d * math.cos(e) * math.sin(a), t[1] - d * math.cos(e) * math.cos(a), t[2] + d * math.sin(e)); sas.location = t

def mulus(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def kunci_ke(F, keys):
    """keys: list (frame, dict). Interpolasi mulus antar kunci."""
    for (fa, a), (fb, b) in zip(keys[:-1], keys[1:]):
        if fa <= F <= fb:
            s = mulus((F - fa) / max(fb - fa, 1)); out = {}
            for k in a:
                va, vb = a[k], b[k]
                out[k] = [x + (y - x) * s for x, y in zip(va, vb)] if isinstance(va, (list, tuple)) else va + (vb - va) * s
            return out
    return dict(keys[-1][1])

# ------------------------------------------------------------------ sinar LED (kerucut bercahaya) + lampu titik kecil
def sinar(led, pusat, r_ujung, nama="Sinar LED"):
    led, pusat = Vector(led) / 1000, Vector(pusat) / 1000; arah = pusat - led; L = arah.length   # masukan dalam mm
    bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=r_ujung, radius2=0.0006, depth=L, end_fill_type="NOTHING")
    k = bpy.context.object; k.name = nama
    k.location = (led + pusat) / 2; k.rotation_mode = "QUATERNION"; k.rotation_quaternion = arah.to_track_quat("-Z", "Y")
    m = bpy.data.materials.new("sinar"); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial"); mix = nt.nodes.new("ShaderNodeMixShader"); tr = nt.nodes.new("ShaderNodeBsdfTransparent"); em = nt.nodes.new("ShaderNodeEmission")
    em.inputs[0].default_value = (1.0, 0.9, 0.72, 1); em.inputs[1].default_value = 0.0
    lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs[0].default_value = 0.2
    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = 0.28
    nt.links.new(lw.outputs["Facing"], mul.inputs[0]); nt.links.new(mul.outputs[0], mix.inputs[0]); nt.links.new(tr.outputs[0], mix.inputs[1]); nt.links.new(em.outputs[0], mix.inputs[2]); nt.links.new(mix.outputs[0], o.inputs[0])
    k.data.materials.append(m); k.visible_shadow = False
    bpy.ops.object.light_add(type="POINT", location=led + arah.normalized() * 0.0012); p = bpy.context.object; p.data.shadow_soft_size = 0.001; p.data.energy = 0.0
    p.data.color = (1.0, 0.92, 0.78)
    return em, p

def pemotong(y_bidang):
    bpy.ops.mesh.primitive_cube_add(size=1); pot = bpy.context.object; pot.name = "Pemotong"; pot.scale = (0.6, 0.5, 0.6)
    pot.hide_render = True; pot.display_type = "WIRE"; return pot

def pasang_potong(objs, pot):
    for o in objs:
        md = o.modifiers.new("Potong", "BOOLEAN"); md.operation = "DIFFERENCE"; md.object = pot; md.solver = "EXACT"; md.show_render = False

def atur_potong(objs, pot, y_bidang, s):
    """s 0..1: pemotong masuk dari sisi kamera (-y) sampai bidang tengah."""
    on = s > 0.002
    pot.location = (0.0, y_bidang - 0.25 - (1 - s) * 0.12, 0.02)
    for o in objs: o.modifiers["Potong"].show_render = on

def render(F):
    if not (F0 <= F <= F1): return False
    sc.render.filepath = os.path.join(OUT, f"{F:04d}.png"); bpy.ops.render.render(write_still=True); print("FRAME", MODEL, F, flush=True); return True

# ------------------------------------------------------------------ adegan
if MODEL == "jepit":
    info, obj = impor("jepit", "jepit.glb")
    ax, az = info["sumbu_engsel"]; W = info["P"]["W"] / 1000; XC = YC = W / 2
    bpy.ops.object.empty_add(location=(ax / 1000, YC, az / 1000)); poros = bpy.context.object
    atas_ = [k for k, o in obj.items() if info["bagian"][k]["grup"] == "atas"]
    for k in atas_:
        o = obj[k]; mw = o.matrix_world.copy(); o.parent = poros; o.matrix_parent_inverse = poros.matrix_world.inverted(); o.matrix_world = mw
    URAI = {"busa_1": 6, "busa_2": 14, "busa_3": 22, "daging": 45, "tutup_cat": 75, "beludru": 75, "dudukan_pelat": 100, "dudukan_pipi": 100, "kepala_lantai": 120,
            "kepala_depan": 135, "kepala_belakang": 135, "kepala_kiri": 135, "kepala_kanan": 135, "engsel_atas": 135, "kait_atas": 135, "kepala_tutup": 200, "kepala_bibir": 200}
    def urai(k): return URAI.get(k, 92 if k.startswith("sensor_") else 145 if k.startswith("esp_") else 180 if k.startswith("oled_") else 0)
    asal = {k: o.location.copy() for k, o in obj.items()}
    em, pl = sinar(info["led"], (XC * 1000, YC * 1000, 0.0), 0.0072)
    pot = pemotong(YC); pasang_potong(obj.values(), pot)
    T0 = (XC, YC, 0.03); TC = (XC + 0.008, YC, 0.012)
    KEYS = [(0, dict(az=-62, el=24, d=0.42, t=T0, h=0, x=0, c=0, b=0)), (34, dict(az=-8, el=18, d=0.38, t=T0, h=0, x=0, c=0, b=0)),
            (40, dict(az=-8, el=18, d=0.38, t=T0, h=0, x=0, c=0, b=0)), (64, dict(az=-28, el=30, d=0.42, t=T0, h=95, x=0, c=0, b=0)),
            (70, dict(az=-28, el=30, d=0.42, t=T0, h=95, x=0, c=0, b=0)), (82, dict(az=-35, el=20, d=0.45, t=T0, h=0, x=0, c=0, b=0)),
            (104, dict(az=-35, el=16, d=0.62, t=(XC, YC, 0.09), h=0, x=1, c=0, b=0)), (110, dict(az=-35, el=16, d=0.62, t=(XC, YC, 0.09), h=0, x=1, c=0, b=0)),
            (120, dict(az=-20, el=12, d=0.40, t=T0, h=0, x=0, c=0, b=0)), (134, dict(az=0, el=6, d=0.30, t=TC, h=0, x=0, c=1, b=0)),
            (144, dict(az=0, el=4, d=0.17, t=TC, h=0, x=0, c=1, b=1)), (155, dict(az=6, el=6, d=0.17, t=TC, h=0, x=0, c=1, b=1))]
    def terapkan(st):
        poros.rotation_euler = (0, math.radians(st["h"]), 0)
        for k, o in obj.items(): o.location = asal[k] + Vector((0, 0, urai(k) / 1000 * st["x"]))
        for k in obj:
            if k.startswith("kabel"): obj[k].hide_render = st["x"] > 0.02
        atur_potong(obj.values(), pot, YC, st["c"])
        em.inputs[1].default_value = 2.2 * st["b"]; pl.data.energy = 0.05 * st["b"]
    N = KEYS[-1][0] + 1
elif MODEL == "genggam":
    info, obj = impor("genggam", "genggam.glb")
    asal = {k: o.location.copy() for k, o in obj.items()}
    def urai(k):
        if k == "daging": return -20
        if k in ("tutup_atas", "bibir", "tanda_tekan"): return 75
        if k.startswith("oled_"): return 62
        if k.startswith("esp_"): return 32
        if k.startswith(("sensor_", "dudukan_")): return 22
        if k in ("tabung", "beludru"): return 12
        return 0
    em, pl = sinar(info["led"], (0.0, 0.0, 0.0), 0.0062)
    pot = pemotong(0.0); pasang_potong(obj.values(), pot)
    T0 = (-0.022, 0, 0.022); TC = (0.009, 0, 0.009)
    KEYS = [(0, dict(az=-55, el=26, d=0.34, t=T0, x=0, c=0, b=0)), (36, dict(az=20, el=22, d=0.32, t=T0, x=0, c=0, b=0)),
            (42, dict(az=20, el=22, d=0.32, t=T0, x=0, c=0, b=0)), (70, dict(az=-30, el=18, d=0.46, t=(-0.022, 0, 0.06), x=1, c=0, b=0)),
            (76, dict(az=-30, el=18, d=0.46, t=(-0.022, 0, 0.06), x=1, c=0, b=0)), (92, dict(az=-15, el=10, d=0.32, t=T0, x=0, c=0, b=0)),
            (106, dict(az=0, el=6, d=0.26, t=TC, x=0, c=1, b=0)), (118, dict(az=0, el=4, d=0.15, t=TC, x=0, c=1, b=1)), (129, dict(az=6, el=6, d=0.15, t=TC, x=0, c=1, b=1))]
    def terapkan(st):
        for k, o in obj.items(): o.location = asal[k] + Vector((0, 0, urai(k) / 1000 * st["x"]))
        for k in obj:
            if k.startswith("kabel"): obj[k].hide_render = st["x"] > 0.02
        atur_potong(obj.values(), pot, 0.0, st["c"])
        em.inputs[1].default_value = 2.2 * st["b"]; pl.data.energy = 0.05 * st["b"]
    N = KEYS[-1][0] + 1
elif MODEL == "jepitbb":
    # Model 2B: ESP32 tegak di breadboard pada dinding belakang kepala, kabel dupont tanpa solder
    info, obj = impor("jepit", "jepit.glb", sub="model_bb")
    ax, az = info["sumbu_engsel"]; W = info["P"]["W"] / 1000; XC = YC = W / 2; Hc = info["P"]["Hc"] / 1000
    URAI = {"busa_1": 6, "busa_2": 14, "busa_3": 22, "daging": 45, "tutup_cat": 75, "beludru": 75, "dudukan_pelat": 100, "dudukan_pipi": 100, "kepala_lantai": 120,
            "kepala_depan": 135, "kepala_belakang": 135, "kepala_kiri": 135, "kepala_kanan": 135, "engsel_atas": 135, "kait_atas": 135, "kepala_tutup": 182, "kepala_bibir": 182}
    def urai(k): return URAI.get(k, 92 if k.startswith("sensor_") else 150 if (k.startswith("esp_") or k == "bb_papan") else 166 if k.startswith("oled_") else 0)
    asal = {k: o.location.copy() for k, o in obj.items()}
    BUKA = [k for k in obj if k in ("kepala_tutup", "kepala_bibir", "kepala_depan") or k.startswith("oled_") or k == "kait_atas"]
    em, pl = sinar(info["led"], (XC * 1000, YC * 1000, 0.0), 0.0072)
    bb = info["bagian"]["bb_papan"]["bounds"]; BB = ((bb[0][0] + bb[1][0]) / 2000 - 0.004, (bb[0][1] + bb[1][1]) / 2000, (bb[0][2] + bb[1][2]) / 2000)
    T0 = (XC, YC, 0.035); TI = (XC + 0.018, YC, Hc + 0.018)
    KEYS = [(0, dict(az=-62, el=24, d=0.46, t=T0, o=0, x=0)), (30, dict(az=-128, el=20, d=0.46, t=T0, o=0, x=0)),
            (36, dict(az=-128, el=20, d=0.46, t=T0, o=0, x=0)), (40, dict(az=-118, el=30, d=0.44, t=TI, o=1, x=0)),
            (58, dict(az=-100, el=34, d=0.40, t=TI, o=1, x=0)), (70, dict(az=-84, el=30, d=0.38, t=TI, o=1, x=0)),
            (84, dict(az=-104, el=16, d=0.27, t=BB, o=1, x=0)), (96, dict(az=-96, el=14, d=0.26, t=BB, o=1, x=0)),
            (100, dict(az=-70, el=20, d=0.42, t=T0, o=0, x=0)), (112, dict(az=-35, el=16, d=0.74, t=(XC, YC, 0.105), o=0, x=1)),
            (118, dict(az=-30, el=16, d=0.74, t=(XC, YC, 0.105), o=0, x=1))]
    def terapkan(st):
        for k, o in obj.items(): o.location = asal[k] + Vector((0, 0, urai(k) / 1000 * st["x"]))
        for k in obj:
            if k.startswith("kabel"): obj[k].hide_render = st["x"] > 0.02
            if k in BUKA: obj[k].hide_render = st["o"] > 0.5
    N = KEYS[-1][0] + 1
else:   # banding: kedua alat berdampingan
    infoE, objE = impor("jepit", "jepit.glb", geser=(-0.043 - 0.100, -0.043, 0))
    infoA, objA = impor("genggam", "genggam.glb", geser=(0.072, 0, -0.038))
    for k in ("daging",):
        if k in objA: objA[k].hide_render = True
    T0 = (-0.022, 0, 0.03)
    KEYS = [(0, dict(az=-18, el=18, d=0.66, t=T0)), (36, dict(az=8, el=14, d=0.60, t=T0))]
    def terapkan(st): pass
    N = KEYS[-1][0] + 1

# lantai penangkap bayangan
bpy.ops.mesh.primitive_plane_add(size=4, location=(0, 0, -0.0145 if MODEL == "genggam" else -0.0381)); lt = bpy.context.object; lt.is_shadow_catcher = True
if MODEL == "banding": lt.location.z = -0.0381

print("JUMLAH_FRAME", MODEL, N, flush=True)
for F in range(N):
    if not (F0 <= F <= F1): continue
    st = kunci_ke(F, KEYS); terapkan(st); kamera(st["az"], st["el"], st["d"], st["t"]); bpy.context.view_layer.update(); render(F)
