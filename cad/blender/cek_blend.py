# Membuka .blend hasil render dan melaporkan isinya. Jalankan: blender -b ../model-3d/beeffresh_rakitan.blend -P cek_blend.py
import bpy
print("RENDER ENGINE:", bpy.context.scene.render.engine, "| kamera aktif:", bpy.context.scene.camera.name if bpy.context.scene.camera else None)
for o in sorted(bpy.data.objects, key=lambda x: x.name):
    mods = [f"{m.name}({'on' if m.show_viewport else 'off'})" for m in o.modifiers]
    d = o.dimensions * 1000 if o.type == "MESH" else None
    print(f"OBJ {o.type:7s} {o.name:28s}", f"{d.x:.1f}x{d.y:.1f}x{d.z:.1f} mm" if d else "", " ".join(mods))
print("SATUAN:", bpy.context.scene.unit_settings.system, "skala", bpy.context.scene.unit_settings.scale_length)
