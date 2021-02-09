import bpy
import re
 
bl_info = {
    "name": "Keymesh Alpha",
    "author": "Pablo Dobarro (Developer), Daniel Martinez Lara (Animation and Testing)",
    "version": (0, 1, 0),
    "blender": (2, 91, 0),
    "location": "Sidebar > KeyMesh",
    "warning": "Experimental",
    "category": "Object",
    "doc_url": "https://www.youtube.com/watch?v=vlNsvL30TmE&feature=youtu.be",
}



def next_available_keymesh_object_id():
    max_id = 0
    for ob in bpy.data.objects:
        if ob.get('km_id') is None:
            continue
        object_keymesh_id = ob['km_id']
        if object_keymesh_id > max_id:
            max_id = object_keymesh_id
    return max_id + 1


def object_next_available_keyframe_index(ob):
    if ob.get('km_id') is None:
        return 0
    
    object_keymesh_id = ob["km_id"]
    
    max_index = 0
    object_name_full = ob.name_full
    for mesh in bpy.data.meshes:
        if mesh.get('km_id') is None:
            continue    
        mesh_km_id = mesh["km_id"]
        mesh_km_datablock = mesh["km_datablock"]
        
        if mesh_km_id != object_keymesh_id:
            continue
    
        keyframe_index = mesh_km_datablock
        if keyframe_index > max_index:
            max_index = keyframe_index
    return max_index + 1
    
def keymesh_insert_keyframe_ex(object, keymesh_frame_index):
    if object.get('km_id') is None:
        object["km_id"] = next_available_keymesh_object_id()
    object_keymesh_id = object["km_id"]
    
    new_mesh = bpy.data.meshes.new_from_object(object)
    ob_name_full = object.name_full
    new_mesh_name = ob_name_full + "_km" + str(keymesh_frame_index)
    new_mesh.name = new_mesh_name
    new_mesh["km_id"] = object_keymesh_id
    new_mesh["km_datablock"] = keymesh_frame_index
    object.data = new_mesh
    object.data.use_fake_user = True
    current_frame = bpy.context.scene.frame_current
    object["km_datablock"] = keymesh_frame_index
    object.keyframe_insert(data_path = '["km_datablock"]', frame = current_frame)
    
    
def keymesh_insert_keyframe(object):        
    new_keyframe_index = object_next_available_keyframe_index(object)
    keymesh_insert_keyframe_ex(object, new_keyframe_index)
    
    fcurves = object.animation_data.action.fcurves
    for fcurve in fcurves:
        if fcurve.data_path != '["km_datablock"]':
            continue
        for kf in fcurve.keyframe_points:
            kf.interpolation = 'CONSTANT'

    bpy.app.handlers.frame_change_pre.clear()
    bpy.app.handlers.frame_change_pre.append(updateKeymesh)
 
class KeyframeMesh(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.keyframe_mesh"
    bl_label = "Keyframe Mesh"
 
    @classmethod
    def poll(cls, context):
        return context.active_object is not None
 
    def execute(self, context):
        ob = context.active_object
        keymesh_insert_keyframe(ob)
        return {'FINISHED'}
    
    
def updateKeymesh(scene):
    for object in scene.objects:
        if object.get('km_datablock') is None:
            continue
        
        object_km_id = object["km_id"]
        object_km_datablock = object["km_datablock"]
        
        final_mesh = None
        for mesh in bpy.data.meshes:
            
            # No Keymesh Datablock
            if mesh.get('km_id') is None:
                continue    
            mesh_km_id = mesh["km_id"]
            mesh_km_datablock = mesh["km_datablock"]
           
            # No keymesh datat for this object
            if mesh_km_id != object_km_id:
                continue
            
            # No keymesh data for this frame
            if mesh_km_datablock != object_km_datablock:
                continue
            
            final_mesh = mesh
            
        if not final_mesh:
            continue
        
        object.data = final_mesh
        
        
class PurgeKeymeshData(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.purge_keymesh_data"
    bl_label = "Purge Keymesh Data"
 
    @classmethod
    def poll(cls, context):
        return True
 
    def execute(self, context):
        used_km_mesh = {}
        
        for ob in bpy.data.objects:
            if ob.get('km_id') is None:
                continue
            
            km_id = ob.get('km_id')
            used_km_mesh[km_id] = []
            
            fcurves = ob.animation_data.action.fcurves
            for fcurve in fcurves:
                if fcurve.data_path != '["km_datablock"]':
                    continue
                
                keyframePoints = fcurve.keyframe_points
                for keyframe in keyframePoints:
                    used_km_mesh[km_id].append(keyframe.co.y)
        
        delete_mesh = []
        
        for mesh in bpy.data.meshes:
            if mesh.get('km_id') is None:
                continue    
            
            mesh_km_id = mesh.get('km_id')
            
            if mesh_km_id not in used_km_mesh:
                delete_mesh.append(mesh)
                continue
            
            mesh_km_datablock = mesh.get('km_datablock')
            
            if mesh_km_datablock not in used_km_mesh[mesh_km_id]:
                delete_mesh.append(mesh)
                continue
            
        print("purged")
        for mesh in delete_mesh:
            print(mesh.name)
            mesh.use_fake_user = False
            
        updateKeymesh(bpy.context.scene)                   

        for mesh in delete_mesh:
            if mesh.users == 0:
                bpy.data.meshes.remove(mesh)     
                
        return {'FINISHED'}




class KeymeshPanel(bpy.types.Panel):
    bl_idname = "panel.keymesh_panel"
    bl_label = "Keymesh"
    bl_category = "Keymesh"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
 
    def draw(self, context):
        self.layout.operator("object.keyframe_mesh", text="Keyframe Mesh")
        self.layout.operator("object.purge_keymesh_data", text="Purge Keymesh Data")
                
           
def register():
    bpy.utils.register_class(KeyframeMesh)
    bpy.utils.register_class(PurgeKeymeshData)
    bpy.utils.register_class(KeymeshPanel)
    bpy.app.handlers.frame_change_pre.clear()
    bpy.app.handlers.frame_change_pre.append(updateKeymesh)
    
 
 
def unregister():
    bpy.utils.unregister_class(KeyframeMesh)
    bpy.utils.unregister_class(PurgeKeymeshData)
    bpy.utils.unregister_class(KeymeshPanel)
    bpy.app.handlers.frame_change_pre.clear()
    

##if __name__ == "__main__":
##    register() 
