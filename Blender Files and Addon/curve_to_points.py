bl_info = {
    "name": "Multi-Curve to Three.js Points Exporter",
    "author": "Gemini",
    "version": (1, 5, 0),
    "blender": (3, 0, 0), # Keep this at 3.0.0 for broad compatibility
    "location": "File > Export > Curve to Three.js Points",
    "description": "Export curve points with editable startIndex in output",
    "warning": "",
    "category": "Import-Export",
}

import bpy
import bmesh
from bpy.props import StringProperty, IntProperty, EnumProperty
from bpy_extras.io_utils import ExportHelper
from mathutils import Vector
import os

class ExportCurveToThreeJS(bpy.types.Operator, ExportHelper):
    """Export curve points for Three.js CatmullRomCurve3"""
    bl_idname = "export_curve.threejs_points"
    bl_label = "Export Curve(s) to Three.js"
    
    filename_ext = ".js"
    filter_glob: StringProperty(default="*.js;*.json", options={'HIDDEN'}, maxlen=255)
    
    sample_count: IntProperty(name="Sample Count", default=50, min=3, max=1000)
    point_source: EnumProperty(
        name="Point Source",
        items=[('CONTROL', "Control Points", ""), ('SAMPLED', "Sampled Points", "")],
        default='CONTROL',
    )

    def execute(self, context):
        selected_curves = [obj for obj in context.selected_objects if obj.type == 'CURVE']
        
        if not selected_curves:
            self.report({'ERROR'}, "No curves selected")
            return {'CANCELLED'}
        
        all_curves_data = []
        for obj in selected_curves:
            curve_data = self.extract_curve_data(context, obj)
            if curve_data:
                all_curves_data.append(curve_data)
        
        self.export_javascript(all_curves_data)
        self.report({'INFO'}, f"Successfully exported {len(all_curves_data)} curves.")
        return {'FINISHED'}

    def extract_curve_data(self, context, obj):
        curve = obj.data
        points = []
        
        if self.point_source == 'CONTROL':
            for spline in curve.splines:
                pts_list = spline.bezier_points if spline.type == 'BEZIER' else spline.points
                for p in pts_list:
                    co = p.co if spline.type == 'BEZIER' else Vector((p.co[0], p.co[1], p.co[2]))
                    world_pos = obj.matrix_world @ co
                    points.append([world_pos.x, world_pos.z, -world_pos.y])
        else:
            depsgraph = context.evaluated_depsgraph_get()
            eval_obj = obj.evaluated_get(depsgraph)
            mesh = eval_obj.to_mesh()
            bm = bmesh.new()
            bm.from_mesh(mesh)
            for i in range(self.sample_count):
                t = i / (self.sample_count - 1)
                v_idx = int(t * (len(bm.verts) - 1))
                world_pos = obj.matrix_world @ bm.verts[v_idx].co
                points.append([world_pos.x, world_pos.z, -world_pos.y])
            bm.free()
            eval_obj.to_mesh_clear()

        return {
            "name": obj.name,
            "points": points,
            "closed": getattr(curve.splines[0], "use_cyclic_u", False) if curve.splines else False
        }

    def export_javascript(self, curves_list):
        with open(self.filepath, 'w') as f:
            f.write("import * as THREE from 'three';\n\n")
            f.write("export const exportedCurves = [\n")
            
            for curve in curves_list:
                f.write("  {\n")
                f.write(f"    name: \"{curve['name']}\",\n")
                f.write(f"    closed: {'true' if curve['closed'] else 'false'},\n")
                f.write("    startIndex: 0, // <-- Manually edit this index to shift the start point\n")
                f.write("    points: [\n")
                for p in curve["points"]:
                    f.write(f"      new THREE.Vector3({p[0]:.6f}, {p[1]:.6f}, {p[2]:.6f}),\n")
                f.write("    ],\n")
                f.write("  },\n")
            f.write("];\n\n")
            
            f.write("export const createCurves = () => {\n")
            f.write("  const curves = {};\n")
            f.write("  exportedCurves.forEach(data => {\n")
            f.write("    let pts = [...data.points];\n")
            f.write("    const idx = data.startIndex || 0;\n\n")
            f.write("    if (idx > 0 && idx < pts.length) {\n")
            f.write("      pts = [...pts.slice(idx), ...pts.slice(0, idx)];\n")
            f.write("    }\n\n")
            f.write("    const curve = new THREE.CatmullRomCurve3(pts);\n")
            f.write("    curve.closed = data.closed;\n")
            f.write("    curves[data.name] = curve;\n")
            f.write("  });\n")
            f.write("  return curves;\n")
            f.write("};\n")

def menu_func_export(self, context):
    self.layout.operator(ExportCurveToThreeJS.bl_idname, text="Curve to Three.js Points")

def register():
    print("Registering Three.js Exporter...") # Check System Console for this!
    bpy.utils.register_class(ExportCurveToThreeJS)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    print("Unregistering Three.js Exporter...")
    bpy.utils.unregister_class(ExportCurveToThreeJS)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register()