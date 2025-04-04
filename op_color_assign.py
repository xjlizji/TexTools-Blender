import bpy
import bmesh

from . import utilities_color
from . import utilities_ui
from .settings import tt_settings, prefs


gamma = 2.2


class op(bpy.types.Operator):
	bl_idname = "uv.textools_color_assign"
	bl_label = "Assign Color"
	bl_description = "Assign color to selected Objects or faces in Edit Mode"
	bl_options = {'UNDO'}

	index: bpy.props.IntProperty(description="Color Index", default=0)

	@classmethod
	def poll(cls, context):
		if bpy.context.area.ui_type != 'UV':
			return False
		if not bpy.context.active_object:
			return False
		if bpy.context.active_object not in bpy.context.selected_objects:
			return False
		if bpy.context.active_object.type != 'MESH':
			return False
		return True

	def execute(self, context):
		assign_color(self, context, self.index)
		return {'FINISHED'}


def assign_color(self, context, index):
	selected_obj = bpy.context.selected_objects.copy()

	previous_mode = 'OBJECT'
	if len(selected_obj) == 1:
		previous_mode = bpy.context.active_object.mode

	for obj in selected_obj:
		if obj.type != 'MESH':
			continue

		if tt_settings().color_assign_mode == 'MATERIALS':
			# Select object
			bpy.ops.object.mode_set(mode='OBJECT')
			bpy.ops.object.select_all(action='DESELECT')
			obj.select_set(True)
			bpy.context.view_layer.objects.active = obj

			# Enter Edit mode
			bpy.ops.object.mode_set(mode='EDIT')

			if previous_mode == 'OBJECT':
				bpy.ops.mesh.select_all(action='SELECT')

			# Verify material slots
			for _ in range(index+1):
				if index >= len(obj.material_slots):
					bpy.ops.object.material_slot_add()

			utilities_color.assign_slot(obj, index)

			# Assign to selection
			obj.active_material_index = index
			bpy.ops.object.material_slot_assign()

			# restore mode
			bpy.ops.object.mode_set(mode='OBJECT')
			bpy.ops.object.select_all(action='DESELECT')
			for obj in selected_obj:
				obj.select_set(True)
			bpy.ops.object.mode_set(mode=previous_mode)

		else:  # mode == VERTEXCOLORS
			color = utilities_color.get_color(index).copy()
			if prefs().bool_color_id_vertex_color_gamma:
				# Fix Gamma
				color[0] = pow(color[0], 1/gamma)
				color[1] = pow(color[1], 1/gamma)
				color[2] = pow(color[2], 1/gamma)

			mesh = obj.data

			bpy.ops.object.mode_set(mode='OBJECT')
			if not mesh.vertex_colors:
				mesh.vertex_colors.new(name="Col")
			color_layer = mesh.vertex_colors.active

			bpy.ops.object.mode_set(mode='EDIT')
			bm = bmesh.from_edit_mesh(mesh)

			# Ensure the bm loops have layer access
			color_layer_bmesh = bm.loops.layers.color.active

			# Assign red color to selected faces
			for face in bm.faces:
				if face.select:
					for loop in face.loops:
						loop[color_layer_bmesh] = (color[0], color[1], color[2], 1.0)

			# Update the mesh
			bmesh.update_edit_mesh(mesh)

	# Show Material or Data Tab
	utilities_color.update_properties_tab()

	# Change View mode
	utilities_color.update_view_mode()
