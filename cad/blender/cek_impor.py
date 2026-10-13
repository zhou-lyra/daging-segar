# Memeriksa GLB seperti yang akan dilihat pengguna Blender: orientasi, satuan, nama objek.
# Jalankan:  blender -b -P cek_impor.py -- ../model-3d/beeffresh_rakitan.glb
import bpy, sys
glb = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
import mathutils
mn = mathutils.Vector((1e9,)*3); mx = mathutils.Vector((-1e9,)*3)
for o in bpy.context.scene.objects:
    if o.type != "MESH": continue
    for c in o.bound_box:
        w = o.matrix_world @ mathutils.Vector(c)
        for i in range(3): mn[i] = min(mn[i], w[i]); mx[i] = max(mx[i], w[i])
    print("OBJEK:", o.name)
d = mx - mn
print(f"UKURAN_MM: x={d.x*1000:.1f} y={d.y*1000:.1f} z={d.z*1000:.1f}  | z_min_mm={mn.z*1000:.1f}")
