class_name IslandWorld
extends Node3D

const MAP_RADIUS := 350.0
const WIDTH := 720.0
const CELLS := 180
const STEP := WIDTH / CELLS
const WALL_HEIGHT := 3.2
var spawn_points: Array[Vector3] = []
var loot_points: Array[Vector3] = []
var _built := false
var _rng := RandomNumberGenerator.new()
var _heights := PackedFloat32Array()
var _roads: Array[Dictionary] = []
var _houses: Array[Dictionary] = []
var _tree_points: Array[Vector3] = []
var _box_visuals: Array[MeshInstance3D] = []
var _sites: Array[Vector2] = [Vector2.ZERO, Vector2(245, 0), Vector2(-245, 0), Vector2(0, 245), Vector2(0, -245), Vector2(180, 180), Vector2(-180, 180), Vector2(180, -180), Vector2(-180, -180)]
var _bark: Material
var _leaf: Material
var _surface_shader: Shader
var _terrain_shader: Shader

func _ready() -> void:
	build()

func build() -> void:
	if _built:
		return
	_built = true
	_rng.seed = 640718
	_define_layout()
	_build_environment()
	_build_terrain()
	_build_roads()
	_build_houses()
	_build_street_details()
	_batch_boxes()
	_make_spawn_points()
	_build_forest()
	_build_details()

func _material(color: Color, roughness: float = 0.92) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.albedo_color = color
	material.roughness = roughness
	material.metallic_specular = 0.12
	return material

func _surface_material(color: Color, kind: int) -> ShaderMaterial:
	if _surface_shader == null:
		_surface_shader = Shader.new()
		_surface_shader.code = """shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;
uniform vec4 base_color : source_color = vec4(0.7,0.7,0.6,1.0);
uniform int surface_kind = 0;
varying vec3 world_position;
varying vec3 world_normal;
float grain(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
float noise(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.0-2.0*f);return mix(mix(grain(i),grain(i+vec2(1.0,0.0)),f.x),mix(grain(i+vec2(0.0,1.0)),grain(i+vec2(1.0)),f.x),f.y);}
void vertex(){world_position=(MODEL_MATRIX*vec4(VERTEX,1.0)).xyz;world_normal=normalize(MODEL_NORMAL_MATRIX*NORMAL);}
void fragment(){vec3 normal_axis=abs(normalize(world_normal));vec2 uvw=normal_axis.y>0.65?world_position.xz:(normal_axis.x>0.65?world_position.zy:world_position.xy);float fine=grain(floor(uvw*90.0));float broad=noise(uvw*1.7);vec3 color=base_color.rgb*(0.86+fine*0.11+broad*0.08);
if(surface_kind==1){float damp=(1.0-smoothstep(0.0,0.8,world_position.y))*0.22;color*=1.0-damp;float stipple=noise(uvw*14.0);color*=0.94+stipple*0.08;}
if(surface_kind==2){vec2 tiles=uvw*vec2(2.2,3.8);tiles.x+=mod(floor(tiles.y),2.0)*0.5;vec2 edge=fract(tiles);float grout=1.0-smoothstep(0.025,0.065,min(edge.x,edge.y));color*=1.0-grout*0.32;color*=0.91+grain(floor(tiles))*0.17;}
if(surface_kind==3){color*=0.83+noise(uvw*24.0)*0.16;float cracks=smoothstep(0.986,1.0,noise(uvw*1.3));color*=1.0-cracks*0.18;}
if(surface_kind==4){float stones=grain(floor(uvw*9.0));color*=0.80+stones*0.26;}
if(surface_kind==5){float bark=abs(sin(uvw.x*28.0+noise(uvw*3.0)*5.0));color*=0.70+bark*0.30;}
ALBEDO=color;ROUGHNESS=0.94;SPECULAR=0.10;
}"""
	var material := ShaderMaterial.new()
	material.shader = _surface_shader
	material.set_shader_parameter("base_color", color)
	material.set_shader_parameter("surface_kind", kind)
	return material

func _grass_material() -> ShaderMaterial:
	_terrain_shader = Shader.new()
	_terrain_shader.code = """shader_type spatial;
render_mode diffuse_burley, specular_disabled;
varying vec3 land_position;
varying vec4 vertex_tint;
float hash_grass(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
float smooth_grass(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.0-2.0*f);return mix(mix(hash_grass(i),hash_grass(i+vec2(1.0,0.0)),f.x),mix(hash_grass(i+vec2(0.0,1.0)),hash_grass(i+vec2(1.0)),f.x),f.y);}
void vertex(){land_position=(MODEL_MATRIX*vec4(VERTEX,1.0)).xyz;vertex_tint=COLOR;}
void fragment(){vec2 p=land_position.xz;float patch=smooth_grass(p*0.055);float blades=smooth_grass(p*11.0);float detail=hash_grass(floor(p*95.0));vec3 grass=pow(max(vertex_tint.rgb,vec3(0.001)),vec3(2.2));vec3 earth=vec3(0.105,0.082,0.047);float dry=smoothstep(0.67,0.93,smooth_grass(p*0.11));grass=mix(grass,earth,dry*0.26);grass*=0.82+patch*0.16+blades*0.14+detail*0.055;ALBEDO=grass;ROUGHNESS=0.99;}
"""
	var material := ShaderMaterial.new()
	material.shader = _terrain_shader
	return material

func _define_layout() -> void:
	_roads.append({"center": Vector2.ZERO, "size": Vector2(620, 10)})
	_roads.append({"center": Vector2.ZERO, "size": Vector2(10, 620)})
	for site in _sites:
		if absf(site.x) > 100 and absf(site.y) > 100:
			_roads.append({"center": Vector2(site.x, site.y * 0.5), "size": Vector2(7, absf(site.y) + 8)})
		_roads.append({"center": site, "size": Vector2(62, 6)})
		_roads.append({"center": site, "size": Vector2(6, 58)})
		for ix in [-1, 1]:
			for iz in [-1, 1]:
				_houses.append({"center": site + Vector2(ix * 17, iz * 16), "width": 10.0, "depth": 9.0, "stories": 2 if _houses.size() % 7 == 0 else 1})

func _raw_height(x: float, z: float) -> float:
	var radius := Vector2(x, z).length()
	var edge := smoothstep(315.0, 357.0, radius)
	var hills := (sin(x * 0.019 + cos(z * 0.014)) * cos(z * 0.018) + 1.0) * 1.1
	hills += (sin(x * 0.033 - z * 0.017) + 1.0) * 0.32
	var blend := 1.0
	for road in _roads:
		var local := Vector2(x, z) - Vector2(road.center)
		var size: Vector2 = road.size
		var distance := maxf(absf(local.x) - size.x * 0.5, absf(local.y) - size.y * 0.5)
		if distance < 6.0:
			return lerpf(0.0, -3.0, edge)
		blend = minf(blend, smoothstep(6.0, 17.0, distance))
	for house in _houses:
		var local := Vector2(x, z) - Vector2(house.center)
		var distance := maxf(absf(local.x) - float(house.width) * 0.5, absf(local.y) - float(house.depth) * 0.5)
		blend = minf(blend, smoothstep(7.0, 17.0, distance))
	return lerpf(hills * blend, -3.0, edge)

func get_height(x: float, z: float) -> float:
	if _heights.is_empty():
		return _raw_height(x, z)
	var gx := clampf((x + WIDTH * 0.5) / STEP, 0.0, CELLS - 0.0001)
	var gz := clampf((z + WIDTH * 0.5) / STEP, 0.0, CELLS - 0.0001)
	var ix := int(floor(gx))
	var iz := int(floor(gz))
	var u := gx - ix
	var v := gz - iz
	var index := iz * (CELLS + 1) + ix
	var a := _heights[index]
	var b := _heights[index + CELLS + 1]
	var c := _heights[index + CELLS + 2]
	var d := _heights[index + 1]
	var ground := a + u * (d - a) + v * (b - a) if u + v <= 1.0 else c + (1.0 - u) * (b - c) + (1.0 - v) * (d - c)
	for road in _roads:
		var local := Vector2(x, z) - Vector2(road.center)
		var size: Vector2 = road.size
		if absf(local.x) < size.x * 0.5 and absf(local.y) < size.y * 0.5:
			return maxf(ground, 0.045)
	return ground

func _build_environment() -> void:
	var sky_material := ProceduralSkyMaterial.new()
	sky_material.sky_top_color = Color(0.20, 0.43, 0.70)
	sky_material.sky_horizon_color = Color(0.70, 0.82, 0.88)
	sky_material.ground_horizon_color = Color(0.67, 0.78, 0.79)
	sky_material.ground_bottom_color = Color(0.18, 0.23, 0.19)
	sky_material.sun_angle_max = 18.0
	var sky := Sky.new()
	sky.sky_material = sky_material
	var environment := Environment.new()
	environment.background_mode = Environment.BG_SKY
	environment.sky = sky
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	environment.ambient_light_energy = 0.48
	environment.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	environment.fog_enabled = true
	environment.fog_light_color = Color(0.66, 0.79, 0.83)
	environment.fog_density = 0.0010
	environment.fog_sky_affect = 0.18
	var world_environment := WorldEnvironment.new()
	world_environment.environment = environment
	add_child(world_environment)
	var sunlight := DirectionalLight3D.new()
	sunlight.name = "Sunlight"
	sunlight.rotation_degrees = Vector3(-52, -32, 0)
	sunlight.light_color = Color(1.0, 0.96, 0.88)
	sunlight.light_energy = 1.0
	sunlight.shadow_enabled = true
	sunlight.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
	sunlight.directional_shadow_max_distance = 155.0
	sunlight.shadow_bias = 0.02
	sunlight.shadow_normal_bias = 0.25
	add_child(sunlight)

func _build_terrain() -> void:
	_heights.resize((CELLS + 1) * (CELLS + 1))
	var vertices := PackedVector3Array()
	var colors := PackedColorArray()
	var uvs := PackedVector2Array()
	var indices := PackedInt32Array()
	for iz in range(CELLS + 1):
		for ix in range(CELLS + 1):
			var x := -WIDTH * 0.5 + ix * STEP
			var z := -WIDTH * 0.5 + iz * STEP
			var height := _raw_height(x, z)
			_heights[iz * (CELLS + 1) + ix] = height
			vertices.append(Vector3(x, height, z))
			uvs.append(Vector2(float(ix) / CELLS * 110, float(iz) / CELLS * 110))
			var shade := sin(x * 0.065) * cos(z * 0.05) * 0.035
			var color := Color(0.29 + shade, 0.46 + shade, 0.20 + shade * 0.5)
			color = color.lerp(Color(0.64, 0.59, 0.40), smoothstep(329.0, 345.0, Vector2(x, z).length()))
			colors.append(color)
	for iz in range(CELLS):
		for ix in range(CELLS):
			var a := iz * (CELLS + 1) + ix
			var b := a + CELLS + 1
			var c := b + 1
			var d := a + 1
			indices.append_array(PackedInt32Array([a, d, b, b, d, c]))
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = vertices
	arrays[Mesh.ARRAY_COLOR] = colors
	arrays[Mesh.ARRAY_TEX_UV] = uvs
	arrays[Mesh.ARRAY_INDEX] = indices
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	var tool := SurfaceTool.new()
	tool.create_from(mesh, 0)
	tool.generate_normals()
	mesh = tool.commit()
	var material := _grass_material()
	var instance := MeshInstance3D.new()
	instance.mesh = mesh
	instance.material_override = material
	add_child(instance)
	var terrain_body := StaticBody3D.new()
	terrain_body.name = "TerrainCollision"
	terrain_body.collision_layer = 1
	terrain_body.collision_mask = 0
	var collision := CollisionShape3D.new()
	collision.shape = mesh.create_trimesh_shape()
	terrain_body.add_child(collision)
	add_child(terrain_body)
	var water := MeshInstance3D.new()
	var water_mesh := PlaneMesh.new()
	water_mesh.size = Vector2(2200, 2200)
	water.mesh = water_mesh
	water.position.y = -2.6
	var water_shader := Shader.new()
	water_shader.code = """shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;
varying vec2 sea_position;
void vertex(){sea_position=(MODEL_MATRIX*vec4(VERTEX,1.0)).xz;}
void fragment(){float wave=sin(sea_position.x*0.11+TIME*0.6)*cos(sea_position.y*0.08-TIME*0.45);ALBEDO=vec3(0.045,0.14,0.17)+wave*0.008;ROUGHNESS=0.29;METALLIC=0.08;SPECULAR=0.38;NORMAL_MAP=vec3(0.5+sin(sea_position.x*0.15+TIME*0.6)*0.045,0.5+cos(sea_position.y*0.12-TIME*0.4)*0.045,1.0);}"""
	var water_material := ShaderMaterial.new()
	water_material.shader = water_shader
	water.material_override = water_material
	add_child(water)

func _box(body: Node3D, center: Vector3, size: Vector3, material: Material, collidable: bool = true) -> MeshInstance3D:
	var mesh_instance := MeshInstance3D.new()
	var mesh := BoxMesh.new()
	mesh.size = size
	mesh_instance.mesh = mesh
	mesh_instance.position = center
	mesh_instance.material_override = material
	body.add_child(mesh_instance)
	_box_visuals.append(mesh_instance)
	if collidable:
		var collider := CollisionShape3D.new()
		var shape := BoxShape3D.new()
		shape.size = size
		collider.shape = shape
		collider.position = center
		body.add_child(collider)
	return mesh_instance

func _batch_boxes() -> void:
	# Thousands of walls and window trims share unit-box draws; physics shapes remain native.
	var groups: Dictionary = {}
	for instance in _box_visuals:
		var material: Material = instance.material_override
		if not groups.has(material):
			groups[material] = []
		groups[material].append(instance)
	var unit_box := BoxMesh.new()
	unit_box.size = Vector3.ONE
	for material in groups:
		var transforms: Array[Transform3D] = []
		for instance: MeshInstance3D in groups[material]:
			var transform_value: Transform3D = global_transform.affine_inverse() * instance.global_transform
			transform_value.basis = transform_value.basis * Basis.from_scale((instance.mesh as BoxMesh).size)
			transforms.append(transform_value)
			instance.queue_free()
		_multimesh(unit_box, material, transforms)
	_box_visuals.clear()

func _static_body(label: String) -> StaticBody3D:
	var body := StaticBody3D.new()
	body.name = label
	body.collision_layer = 1
	body.collision_mask = 0
	add_child(body)
	return body

func _build_roads() -> void:
	var asphalt := _surface_material(Color(0.35, 0.37, 0.36), 3)
	var paint := _material(Color(0.85, 0.85, 0.72))
	for road in _roads:
		var center: Vector2 = road.center
		var size: Vector2 = road.size
		var body := _static_body("Road")
		_box(body, Vector3(center.x, 0.015, center.y), Vector3(size.x, 0.06, size.y), asphalt)
		var horizontal := size.x > size.y
		var length := maxf(size.x, size.y)
		for n in range(int(length / 12)):
			var shift := -length * 0.5 + n * 12 + 6
			var stripe_center := Vector3(center.x + (shift if horizontal else 0), 0.048, center.y + (0 if horizontal else shift))
			_box(body, stripe_center, Vector3(3.0 if horizontal else 0.14, 0.006, 0.14 if horizontal else 3.0), paint, false)

func _window_wall(body: StaticBody3D, center: Vector3, length: float, horizontal: bool, material: Material, frame: Material) -> void:
	var axis := Vector3.RIGHT if horizontal else Vector3.BACK
	var thickness := Vector3(length, 0.85, 0.22) if horizontal else Vector3(0.22, 0.85, length)
	_box(body, center + Vector3(0, 0.425, 0), thickness, material)
	_box(body, center + Vector3(0, 2.70, 0), Vector3(length, 1.0, 0.22) if horizontal else Vector3(0.22, 1.0, length), material)
	var count := maxi(1, int(length / 4.2))
	var bay := length / count
	for i in range(count):
		var x := -length * 0.5 + bay * (i + 0.5)
		var pillar_width := (bay - 1.5) * 0.5
		for sign_value in [-1, 1]:
			var pillar_position: Vector3 = center + axis * (x + sign_value * (0.75 + pillar_width * 0.5)) + Vector3(0, 1.525, 0)
			_box(body, pillar_position, Vector3(pillar_width, 1.35, 0.22) if horizontal else Vector3(0.22, 1.35, pillar_width), material)
			_box(body, center + axis * (x + sign_value * 0.785) + Vector3(0, 1.525, 0), Vector3(0.07, 1.44, 0.27) if horizontal else Vector3(0.27, 1.44, 0.07), frame, false)
			_box(body, center + axis * x + Vector3(0, 1.525 + sign_value * 0.71, 0), Vector3(1.64, 0.07, 0.27) if horizontal else Vector3(0.27, 0.07, 1.64), frame, false)

func _build_houses() -> void:
	var colors := [Color(0.63, 0.66, 0.58), Color(0.70, 0.61, 0.47), Color(0.48, 0.61, 0.60), Color(0.73, 0.71, 0.61)]
	var roof_material := _surface_material(Color(0.53, 0.34, 0.23), 2)
	var frame_material := _material(Color(0.19, 0.26, 0.23))
	var floor_material := _surface_material(Color(0.57, 0.52, 0.42), 4)
	for index in range(_houses.size()):
		var house: Dictionary = _houses[index]
		var center: Vector2 = house.center
		var width: float = house.width
		var depth: float = house.depth
		var stories: int = house.stories
		var body := _static_body("House_%02d" % index)
		var wall_material := _surface_material(colors[index % colors.size()], 1)
		_box(body, Vector3(center.x, -0.06, center.y), Vector3(width, 0.16, depth), floor_material)
		for story in range(stories):
			var y := story * WALL_HEIGHT
			_window_wall(body, Vector3(center.x, y, center.y - depth * 0.5), width, true, wall_material, frame_material)
			_window_wall(body, Vector3(center.x - width * 0.5, y, center.y), depth, false, wall_material, frame_material)
			_window_wall(body, Vector3(center.x + width * 0.5, y, center.y), depth, false, wall_material, frame_material)
			if story == 0:
				var side_width := (width - 2.2) * 0.5
				for sign_value in [-1, 1]:
					_window_wall(body, Vector3(center.x + sign_value * (1.1 + side_width * 0.5), y, center.y + depth * 0.5), side_width, true, wall_material, frame_material)
				_box(body, Vector3(center.x, y + 2.7, center.y + depth * 0.5), Vector3(2.2, 1.0, 0.22), wall_material)
			else:
				_window_wall(body, Vector3(center.x, y, center.y + depth * 0.5), width, true, wall_material, frame_material)
		if stories == 2:
			_box(body, Vector3(center.x, WALL_HEIGHT - 0.08, center.y - depth * 0.25), Vector3(width, 0.16, depth * 0.5), floor_material)
			var run := depth * 0.5 - 0.4
			var angle := atan2(WALL_HEIGHT, run)
			var ramp_position := Vector3(center.x - width * 0.5 + 1.35, WALL_HEIGHT * 0.5 - 0.08 / cos(angle), center.y + run * 0.5)
			var ramp_size := Vector3(1.8, 0.16, sqrt(run * run + WALL_HEIGHT * WALL_HEIGHT))
			var ramp_mesh := _box(body, ramp_position, ramp_size, floor_material, false)
			ramp_mesh.rotation.x = angle
			var ramp_collision := CollisionShape3D.new()
			var shape := BoxShape3D.new()
			shape.size = ramp_size
			ramp_collision.shape = shape
			ramp_collision.position = ramp_position
			ramp_collision.rotation.x = angle
			body.add_child(ramp_collision)
		var roof_y := stories * WALL_HEIGHT
		var half_width := width * 0.5 + 0.4
		var rise := 1.3
		var roof_tool := SurfaceTool.new()
		roof_tool.begin(Mesh.PRIMITIVE_TRIANGLES)
		var points := [Vector3(center.x - half_width, roof_y, center.y - depth * 0.5 - 0.4), Vector3(center.x - half_width, roof_y, center.y + depth * 0.5 + 0.4), Vector3(center.x, roof_y + rise, center.y - depth * 0.5 - 0.4), Vector3(center.x, roof_y + rise, center.y + depth * 0.5 + 0.4), Vector3(center.x + half_width, roof_y, center.y - depth * 0.5 - 0.4), Vector3(center.x + half_width, roof_y, center.y + depth * 0.5 + 0.4)]
		for triangle in [[0, 1, 2], [1, 3, 2], [2, 3, 4], [3, 5, 4], [0, 2, 4], [1, 5, 3]]:
			for vertex_index in [triangle[0], triangle[2], triangle[1]]:
				roof_tool.add_vertex(points[vertex_index])
		roof_tool.generate_normals()
		var roof_mesh := roof_tool.commit()
		var roof_instance := MeshInstance3D.new()
		roof_instance.mesh = roof_mesh
		roof_instance.material_override = roof_material
		body.add_child(roof_instance)
		var roof_collision := CollisionShape3D.new()
		roof_collision.shape = roof_mesh.create_trimesh_shape()
		body.add_child(roof_collision)
		_box(body, Vector3(center.x + width * 0.28, 0.40, center.y - depth * 0.22), Vector3(1.1, 0.8, 1.1), _material(Color(0.42, 0.32, 0.20)))
		for offset in [Vector2(-2, -2), Vector2(2, -2), Vector2(-2, 2), Vector2(2, 2)]:
			loot_points.append(Vector3(center.x + offset.x, 0.12, center.y + offset.y))
		for sign_value in [-1, 1]:
			loot_points.append(Vector3(center.x + sign_value * (width * 0.5 + 2), 0.12, center.y))

func _build_street_details() -> void:
	var curb_material := _surface_material(Color(0.58, 0.58, 0.51), 4)
	var path_material := _surface_material(Color(0.53, 0.46, 0.32), 4)
	var street_body := _static_body("StreetDetails")
	# Low stone shoulders are visual accents below the actual asphalt walk surface.
	for road_index in range(_roads.size()):
		var road: Dictionary = _roads[road_index]
		var center: Vector2 = road.center
		var size: Vector2 = road.size
		var horizontal := size.x > size.y
		var length := maxf(size.x, size.y)
		var width := minf(size.x, size.y)
		for segment in range(int(length / 8)):
			var shift := -length * 0.5 + segment * 8 + 4
			for sign_value in [-1, 1]:
				var point := center + Vector2(shift if horizontal else sign_value * (width * 0.5 + 0.14), sign_value * (width * 0.5 + 0.14) if horizontal else shift)
				var intersection := false
				for other_index in range(_roads.size()):
					if other_index == road_index:
						continue
					var other: Dictionary = _roads[other_index]
					var local := point - Vector2(other.center)
					var other_size: Vector2 = other.size
					if absf(local.x) < other_size.x * 0.5 + (4 if horizontal else 0.5) and absf(local.y) < other_size.y * 0.5 + (0.5 if horizontal else 4):
						intersection = true
						break
				if not intersection:
					_box(street_body, Vector3(point.x, 0.012, point.y), Vector3(7.8 if horizontal else 0.22, 0.044, 0.22 if horizontal else 7.8), curb_material, false)
	for house in _houses:
		var center: Vector2 = house.center
		var site := _sites[0]
		for candidate in _sites:
			if candidate.distance_squared_to(center) < site.distance_squared_to(center):
				site = candidate
		var front := Vector2(center.x, center.y + float(house.depth) * 0.5 + 0.18)
		if center.y < site.y:
			var end := Vector2(front.x, site.y - 3.1)
			_box(street_body, Vector3(front.x, 0.006, (front.y + end.y) * 0.5), Vector3(1.65, 0.012, absf(end.y-front.y)), path_material, false)
		else:
			var side := center.x + (float(house.width) * 0.5 + 2.5) * (1 if center.x > site.x else -1)
			_box(street_body, Vector3((front.x+side)*0.5,0.006,front.y),Vector3(absf(side-front.x),0.012,1.65),path_material,false)
			_box(street_body, Vector3(side,0.006,(front.y+site.y+3.1)*0.5),Vector3(1.65,0.012,absf(front.y-site.y-3.1)),path_material,false)
	var poles: Array[Transform3D] = []
	var pole_material := _material(Color(0.24, 0.27, 0.25), 0.75)
	var lamp_material := _material(Color(0.85, 0.79, 0.61), 0.65)
	lamp_material.emission_enabled = true
	lamp_material.emission = Color(0.30, 0.24, 0.12)
	for site in _sites:
		for sign_x in [-1,1]:
			for sign_z in [-1,1]:
				var point: Vector3 = Vector3(site.x+sign_x*6.5, 2.3, site.y+sign_z*6.5)
				poles.append(Transform3D(Basis.IDENTITY,point))
				_box(street_body, point+Vector3(0,2.25,0),Vector3(0.52,0.12,0.38),lamp_material,false)
				var collider := CollisionShape3D.new()
				var shape := CylinderShape3D.new()
				shape.radius = 0.13
				shape.height = 4.6
				collider.shape=shape
				collider.position=point
				street_body.add_child(collider)
	var pole_mesh := CylinderMesh.new()
	pole_mesh.height=4.6
	pole_mesh.top_radius=0.07
	pole_mesh.bottom_radius=0.11
	pole_mesh.radial_segments=8
	_multimesh(pole_mesh,pole_material,poles)

func _clear_space(x: float, z: float, padding: float = 3.0) -> bool:
	if Vector2(x, z).length() > 325:
		return false
	for road in _roads:
		var local := Vector2(x, z) - Vector2(road.center)
		var size: Vector2 = road.size
		if absf(local.x) < size.x * 0.5 + padding and absf(local.y) < size.y * 0.5 + padding:
			return false
	for house in _houses:
		var local := Vector2(x, z) - Vector2(house.center)
		if absf(local.x) < float(house.width) * 0.5 + padding and absf(local.y) < float(house.depth) * 0.5 + padding:
			return false
	return true

func _make_spawn_points() -> void:
	for index in range(64):
		var site := _sites[index % _sites.size()]
		var angle := index * 2.399963
		var radius := 34.0 + int(index / _sites.size()) * 3.5
		var point := site + Vector2(cos(angle), sin(angle)) * radius
		if point.length() > 320:
			point = point.normalized() * 318
		for attempt in range(15):
			if _clear_space(point.x, point.y, 1.8):
				break
			point = site + Vector2(cos(angle + attempt * 0.4), sin(angle + attempt * 0.4)) * (radius + 3)
		spawn_points.append(Vector3(point.x, get_height(point.x, point.y) + 0.2, point.y))

func _multimesh(mesh: Mesh, material: Material, transforms: Array[Transform3D], colors: Array[Color] = []) -> MultiMeshInstance3D:
	var multi := MultiMesh.new()
	multi.transform_format = MultiMesh.TRANSFORM_3D
	multi.use_colors = not colors.is_empty()
	multi.mesh = mesh
	multi.instance_count = transforms.size()
	for index in range(transforms.size()):
		multi.set_instance_transform(index, transforms[index])
		if not colors.is_empty():
			multi.set_instance_color(index, colors[index])
	var instance := MultiMeshInstance3D.new()
	instance.multimesh = multi
	instance.material_override = material
	add_child(instance)
	return instance

func _build_forest() -> void:
	_bark = _surface_material(Color(0.40, 0.30, 0.21), 5)
	_leaf = _material(Color.WHITE)
	(_leaf as StandardMaterial3D).vertex_color_use_as_albedo = true
	(_leaf as StandardMaterial3D).vertex_color_is_srgb = true
	var stems: Array[Transform3D] = []
	var crowns: Array[Transform3D] = []
	var pines: Array[Transform3D] = []
	var pine_colors: Array[Color] = []
	var colors: Array[Color] = []
	for attempt in range(5000):
		if stems.size() >= 300:
			break
		var angle := _rng.randf_range(0, TAU)
		var radius := sqrt(_rng.randf()) * 323
		var point := Vector2(cos(angle), sin(angle)) * radius
		if not _clear_space(point.x, point.y, 4):
			continue
		var close := false
		for tree in _tree_points:
			if Vector2(tree.x - point.x, tree.z - point.y).length_squared() < 36:
				close = true
				break
		for spawn in spawn_points:
			if Vector2(spawn.x - point.x, spawn.z - point.y).length_squared() < 9:
				close = true
		if close:
			continue
		var ground := get_height(point.x, point.y)
		var height := _rng.randf_range(3.4, 4.5)
		var tree_position := Vector3(point.x, ground, point.y)
		_tree_points.append(tree_position)
		stems.append(Transform3D(Basis.IDENTITY.scaled(Vector3(1, height / 3.4, 1)), tree_position + Vector3.UP * height * 0.5))
		for crown in range(5):
			if stems.size() % 4 == 0:
				if crown < 3:
					pines.append(Transform3D(Basis.IDENTITY.scaled(Vector3(1.7-crown*0.35,1.15,1.7-crown*0.35)),tree_position+Vector3.UP*(height+0.1+crown*0.95)))
					pine_colors.append(Color(0.20,0.34,0.22).lightened(crown*0.025))
				continue
			var crown_angle := crown * 2.4 + angle
			var spread := 0.0 if crown == 4 else 1.0
			var position := tree_position + Vector3(cos(crown_angle) * spread, height + 0.45 + (1.0 if crown == 4 else crown % 2 * 0.45), sin(crown_angle) * spread)
			crowns.append(Transform3D(Basis.IDENTITY.scaled(Vector3(1.3, 1.15, 1.25) * _rng.randf_range(0.85, 1.12)), position))
			colors.append(Color(0.22, 0.40, 0.17).lightened(_rng.randf_range(0.0, 0.12)))
		var trunk_body := _static_body("Tree")
		var collision := CollisionShape3D.new()
		var shape := CylinderShape3D.new()
		shape.radius = 0.34
		shape.height = height
		collision.shape = shape
		collision.position = tree_position + Vector3.UP * height * 0.5
		trunk_body.add_child(collision)
	var trunk_mesh := CylinderMesh.new()
	trunk_mesh.top_radius = 0.20
	trunk_mesh.bottom_radius = 0.34
	trunk_mesh.height = 3.4
	trunk_mesh.radial_segments = 8
	_multimesh(trunk_mesh, _bark, stems)
	var crown_mesh := SphereMesh.new()
	crown_mesh.radius = 1.0
	crown_mesh.height = 2.0
	crown_mesh.radial_segments = 12
	crown_mesh.rings = 6
	_multimesh(crown_mesh, _leaf, crowns, colors)
	var pine_mesh := CylinderMesh.new()
	pine_mesh.height=2.0
	pine_mesh.top_radius=0.05
	pine_mesh.bottom_radius=1.0
	pine_mesh.radial_segments=9
	_multimesh(pine_mesh,_leaf,pines,pine_colors)

func _build_details() -> void:
	var grass_mesh := PrismMesh.new()
	grass_mesh.size = Vector3(0.55, 0.45, 0.45)
	var grass_material := _material(Color(0.31, 0.45, 0.19))
	var grass_transforms: Array[Transform3D] = []
	for index in range(1800):
		var angle := _rng.randf_range(0, TAU)
		var point := Vector2(cos(angle), sin(angle)) * sqrt(_rng.randf()) * 320
		if not _clear_space(point.x, point.y, 0.9):
			continue
		var scale_value := _rng.randf_range(0.55, 1.25)
		grass_transforms.append(Transform3D(Basis(Vector3.UP, angle).scaled(Vector3.ONE * scale_value), Vector3(point.x, get_height(point.x, point.y) + 0.225 * scale_value, point.y)))
	_multimesh(grass_mesh, grass_material, grass_transforms)
	var rock_mesh := SphereMesh.new()
	rock_mesh.radial_segments = 7
	rock_mesh.rings = 4
	var rock_transforms: Array[Transform3D] = []
	for index in range(90):
		var angle := _rng.randf_range(0, TAU)
		var point := Vector2(cos(angle), sin(angle)) * _rng.randf_range(35, 310)
		if _clear_space(point.x, point.y, 2):
			rock_transforms.append(Transform3D(Basis(Vector3.UP, angle).scaled(Vector3(1.2, 0.65, 1.0)), Vector3(point.x, get_height(point.x, point.y) + 0.25, point.y)))
	_multimesh(rock_mesh, _material(Color(0.44, 0.47, 0.40)), rock_transforms)
	var bushes: Array[Transform3D] = []
	var bush_colors: Array[Color] = []
	for house in _houses:
		var center: Vector2 = house.center
		for side in [-1,1]:
			var point: Vector3 = Vector3(center.x+side*3.1,0,center.y-float(house.depth)*0.5-1.5)
			point.y=get_height(point.x,point.z)+0.52
			bushes.append(Transform3D(Basis.IDENTITY.scaled(Vector3(1.15,0.65,0.8)),point))
			bush_colors.append(Color(0.28,0.42,0.22))
	var bush_mesh:=SphereMesh.new()
	bush_mesh.radial_segments=10
	bush_mesh.rings=5
	bush_mesh.radius=1.0
	bush_mesh.height=2.0
	_multimesh(bush_mesh,_leaf,bushes,bush_colors)
