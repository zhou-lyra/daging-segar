# Render Blender untuk rumah alat BeefFresh + simpan berkas .blend.
# Jalankan:  blender -b -P render.py -- ../model-3d/beeffresh_rakitan.glb ../gambar 48
#   argumen: GLB, folder keluaran, jumlah sampel (default 48)
import bpy, math, os, sys
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

args = sys.argv[sys.argv.index("--") + 1:]
GLB, OUT = os.path.abspath(args[0]), os.path.abspath(args[1])
SAMPLES = int(args[2]) if len(args) > 2 else 48
BLEND = os.path.join(os.path.dirname(GLB), "beeffresh_rakitan.blend")
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
sc = bpy.context.scene
meshes = {o.name: o for o in sc.objects if o.type == "MESH"}
print("OBJEK:", sorted(meshes))

# ---- ukuran & pusat
mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3)
for o in meshes.values():
    for c in o.bound_box:
        w = o.matrix_world @ Vector(c)
        for i in range(3): mn[i] = min(mn[i], w[i]); mx[i] = max(mx[i], w[i])
ctr = (mn + mx) / 2; size = max(mx - mn)

# ---- dunia + lantai
w = bpy.data.worlds.new("dunia"); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.02, 0.024, 0.06, 1); bg.inputs[1].default_value = 0.5
bpy.ops.mesh.primitive_plane_add(size=1.0, location=(ctr.x, ctr.y, mn.z - 0.00005))
lantai = bpy.context.object; lantai.name = "Lantai"
m = bpy.data.materials.new("lantai"); m.use_nodes = True
pb = m.node_tree.nodes["Principled BSDF"]; pb.inputs["Base Color"].default_value = (0.012, 0.014, 0.03, 1); pb.inputs["Roughness"].default_value = 0.45
lantai.data.materials.append(m)

# ---- lampu
bpy.ops.object.light_add(type="SUN", location=(0, 0, 1)); sun = bpy.context.object; sun.name = "Matahari"
sun.data.energy = 1.5; sun.data.angle = math.radians(10); sun.rotation_euler = (math.radians(50), 0, math.radians(35))
bpy.ops.object.light_add(type="AREA", location=(ctr.x - 0.12, ctr.y - 0.15, ctr.z + 0.12)); fill = bpy.context.object; fill.name = "Pengisi"
fill.data.energy = 2.5; fill.data.size = 0.15
bpy.ops.object.empty_add(location=tuple(ctr)); sasaran = bpy.context.object; sasaran.name = "Sasaran"
tc = fill.constraints.new("TRACK_TO"); tc.target = sasaran; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"

# ---- kamera
bpy.ops.object.camera_add(); cam = bpy.context.object; cam.name = "Kamera"; sc.camera = cam
cam.data.lens = 65; cam.data.clip_start = 0.005; cam.data.clip_end = 5
tc = cam.constraints.new("TRACK_TO"); tc.target = sasaran; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
def kamera(az, el, jarak):
    a, e = math.radians(az), math.radians(el); d = jarak * size
    cam.location = (ctr.x + d * math.cos(e) * math.sin(a), ctr.y - d * math.cos(e) * math.cos(a), ctr.z + d * math.sin(e))

# ---- pengepasan bingkai: ukur proyeksi kotak-batas semua objek yang tampil, besarkan jarak sampai muat dengan margin
def bingkai():
    bpy.context.view_layer.update(); xs, ys = [], []
    for o in meshes.values():
        if o.hide_render: continue
        for c in o.bound_box:
            v = world_to_camera_view(sc, cam, o.matrix_world @ Vector(c)); xs.append(v.x); ys.append(v.y)
    return min(xs), max(xs), min(ys), max(ys)
def fit(nama, az, el, jarak, margin=0.08):
    for _ in range(40):
        kamera(az, el, jarak); x0, x1, y0, y1 = bingkai()
        if x0 >= margin and x1 <= 1 - margin and y0 >= margin and y1 <= 1 - margin: break
        jarak *= 1.05
    print(f"BINGKAI {nama}: x {x0:.2f}-{x1:.2f}  y {y0:.2f}-{y1:.2f}  jarak {jarak:.2f}x")

# ---- render
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1600, 1000
sc.view_settings.view_transform = "AgX"; sc.view_settings.exposure = -0.3
def render(nama):
    sc.render.filepath = os.path.join(OUT, nama); bpy.ops.render.render(write_still=True); print("RENDER:", nama)

# ---- pemotong (Boolean) untuk tampilan potongan
bpy.ops.mesh.primitive_cube_add(location=(ctr.x, ctr.y + size * 0.5, ctr.z), scale=(size, size * 0.5, size)); cutter = bpy.context.object
cutter.name = "Pemotong"; cutter.display_type = "WIRE"; cutter.hide_render = True
mods = []
for o in meshes.values():
    md = o.modifiers.new("Potong", "BOOLEAN"); md.operation = "DIFFERENCE"; md.object = cutter; md.solver = "EXACT"; md.show_viewport = False; md.show_render = False
    mods.append(md)
cutter.hide_viewport = True

EXPL = {"Badan bawah": 0, "Tabung gelap": -0.20, "ESP32 (tiruan)": 0.22, "OLED (tiruan)": 0.30, "Sensor TCS34725 (tiruan)": 0.12, "Tutup": 0.50}
tutup = meshes["Tutup"]

# 1. utuh
fit('utuh', 35, 28, 2.4); render("1_rakitan_utuh.png")
# 2. terbuka dari atas (tutup disembunyikan)
tutup.hide_render = True; fit('terbuka', 10, 62, 2.2); render("2_terbuka_dari_atas.png"); tutup.hide_render = False
# 3. potongan samping
for md in mods: md.show_render = True
sasaran.location = ctr; fit('potongan', 0, 12, 2.1); render("3_potongan_samping.png")
for md in mods: md.show_render = False
# 4. urai (exploded)
for n, o in meshes.items(): o.location.z += EXPL[n] * size
sasaran.location = (ctr.x, ctr.y, ctr.z + size * 0.1); fit('urai', 35, 22, 3.0); render("4_urai.png")
for n, o in meshes.items(): o.location.z -= EXPL[n] * size
sasaran.location = ctr
# 5. tampak bawah (lantai disembunyikan)
lantai.hide_render = True; fit('bawah', 35, -40, 2.4); render("5_tampak_bawah_tabung.png"); lantai.hide_render = False

# ---- simpan .blend (keadaan awal: utuh, kamera isometrik; pemotong dimatikan)
fit('blend', 35, 28, 2.4)
bpy.ops.wm.save_as_mainfile(filepath=BLEND, compress=True); print("BLEND:", BLEND)
