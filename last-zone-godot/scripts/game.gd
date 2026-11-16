class_name MatchGame
extends Node3D

var world: Node3D
var actors: Array[Node3D] = []
var loot: Array[Node3D] = []
var player: Node3D
var covers: Array[Node3D] = []
var zone_center = Vector3.ZERO
var zone_radius = 345.0
var zone_target_radius = 240.0
var zone_shrinking = false
var time_elapsed = 0.0
var paused_match = true
var started = false
var finished = false
var zone_phase = 0
var zone_clock = 0.0
var zone_from = 345.0
var zone_material: ShaderMaterial
var zone_mesh: MeshInstance3D
var canvas: CanvasLayer
var ui: Control
var menu: PanelContainer
var hud: Control
var status: Label
var health: Label
var inventory: Label
var events: Label
var notice: Label
var damage_layer: Control
var music: AudioStreamPlayer
var voices = 0
var sounds = {}
var kills = 0
var rng = RandomNumberGenerator.new()
var menu_camera: Camera3D
var notice_time = 0.0
var quality = 1
var cross: Label
var binding_panel: PanelContainer
var listening_action = ""
var binding_buttons = {}
var loot_cells = {}

func _ready():
	process_mode=Node.PROCESS_MODE_ALWAYS
	rng.seed=20261116
	_setup_inputs()
	_load_bindings()
	_load_audio()
	world=load("res://scripts/world_builder.gd").new()
	add_child(world)
	world.build()
	_build_zone()
	_build_ui()
	menu_camera=Camera3D.new()
	add_child(menu_camera)
	menu_camera.position=Vector3(75,48,86)
	menu_camera.look_at(Vector3(0,2,0))
	menu_camera.far=750
	menu_camera.current=true
	if "--smoke-test" in OS.get_cmdline_user_args():
		start_match()

func _setup_inputs():
	var keys={"forward":KEY_W,"back":KEY_S,"left":KEY_A,"right":KEY_D,"sprint":KEY_SHIFT,"jump":KEY_SPACE,"crouch_toggle":KEY_CTRL,"crouch_hold":KEY_C,"reload":KEY_R,"kit":KEY_H,"ice":KEY_T,"loot":KEY_E,"free_look":KEY_F,"vault":KEY_V,"weapon_1":KEY_1,"weapon_2":KEY_2,"weapon_3":KEY_3,"pause_match":KEY_ESCAPE}
	for action in keys:
		if not InputMap.has_action(action):
			InputMap.add_action(action)
		var event=InputEventKey.new()
		event.physical_keycode=keys[action]
		InputMap.action_add_event(action,event)
	for action in ["fire","aim"]:
		InputMap.add_action(action)
		var event=InputEventMouseButton.new()
		event.button_index=MOUSE_BUTTON_LEFT if action=="fire" else MOUSE_BUTTON_RIGHT
		InputMap.action_add_event(action,event)

func _load_audio():
	for name in ["shot","step","wood","land","reload","jump","impact"]:
		sounds[name]=load("res://assets/audio/"+name+".ogg")
	music=AudioStreamPlayer.new()
	var stream=load("res://assets/audio/music.ogg")
	if stream:
		stream.loop=true
		music.stream=stream
	music.volume_db=-17
	add_child(music)
	music.play()

func play_one_shot(kind:String,where:Vector3,volume:float=-5.0,pitch_scale:float=1.0):
	if not sounds.has(kind) or voices>=24:
		return
	if is_instance_valid(player) and where.distance_to(player.global_position)>150:
		return
	var audio=AudioStreamPlayer3D.new()
	audio.stream=sounds[kind]
	audio.volume_db=volume
	audio.pitch_scale=pitch_scale
	audio.max_distance=140 if kind=="shot" else 42
	audio.unit_size=8 if kind=="shot" else 5
	add_child(audio)
	audio.global_position=where+Vector3.UP*0.5
	voices+=1
	audio.finished.connect(_finish_voice.bind(audio))
	audio.play()

func play_step(where:Vector3,running:bool):
	if is_instance_valid(player) and where.distance_to(player.global_position)>40:
		return
	play_one_shot("step",where,-5 if running else -9,rng.randf_range(0.94,1.08))

func _build_zone():
	zone_mesh=MeshInstance3D.new()
	var shape=CylinderMesh.new()
	shape.top_radius=1
	shape.bottom_radius=1
	shape.height=70
	shape.radial_segments=160
	shape.cap_top=false
	shape.cap_bottom=false
	zone_mesh.mesh=shape
	var shader=Shader.new()
	shader.code="shader_type spatial; render_mode unshaded,cull_disabled,depth_draw_never; void fragment(){ float line=pow(0.5+0.5*sin(UV.x*1000.0+sin(UV.y*30.0-TIME)*0.8),18.0); float pulse=pow(0.5+0.5*sin(UV.y*180.0-TIME),18.0); ALBEDO=vec3(0.48,0.31,0.9); EMISSION=vec3(0.12,0.06,0.3); ALPHA=(0.055+line*0.18+pulse*0.10)*(1.0-smoothstep(0.35,1.0,UV.y)); }"
	zone_material=ShaderMaterial.new()
	zone_material.shader=shader
	zone_mesh.material_override=zone_material
	zone_mesh.position.y=30
	zone_mesh.scale=Vector3(zone_radius,1,zone_radius)
	add_child(zone_mesh)

func _style_panel(panel:PanelContainer,color:Color):
	var style=StyleBoxFlat.new()
	style.bg_color=color
	style.corner_radius_top_left=12
	style.corner_radius_top_right=12
	style.corner_radius_bottom_left=12
	style.corner_radius_bottom_right=12
	style.content_margin_left=24
	style.content_margin_right=24
	style.content_margin_top=20
	style.content_margin_bottom=20
	panel.add_theme_stylebox_override("panel",style)

func _label(parent:Node,text:String,size:int=20)->Label:
	var label=Label.new()
	label.text=text
	label.add_theme_font_size_override("font_size",size)
	label.add_theme_color_override("font_color",Color("ecf1df"))
	label.add_theme_color_override("font_shadow_color",Color("142b30"))
	label.add_theme_constant_override("shadow_offset_x",1)
	label.add_theme_constant_override("shadow_offset_y",2)
	parent.add_child(label)
	return label

func _build_ui():
	canvas=CanvasLayer.new()
	add_child(canvas)
	ui=Control.new()
	ui.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	canvas.add_child(ui)
	menu=PanelContainer.new()
	menu.position=Vector2(40,95)
	menu.custom_minimum_size=Vector2(500,0)
	_style_panel(menu,Color(0.04,0.10,0.12,0.94))
	ui.add_child(menu)
	var box=VBoxContainer.new()
	box.add_theme_constant_override("separation",14)
	menu.add_child(box)
	_label(box,"LAST ZONE",48)
	_label(box,"GODOT 4 · PROTÓTIPO NATIVO",17)
	_label(box,"Ilha verde • 200 HP • 48 participantes\nFísica nativa, armas e áudio espacial",20)
	var play=Button.new()
	play.text="ENTRAR NA PARTIDA"
	play.custom_minimum_size.y=55
	box.add_child(play)
	play.pressed.connect(start_match)
	var quality_button=Button.new()
	quality_button.text="QUALIDADE: MÉDIA"
	box.add_child(quality_button)
	quality_button.pressed.connect(func():
		quality=(quality+1)%3
		quality_button.text="QUALIDADE: "+["LEVE","MÉDIA","ALTA"][quality]
		get_viewport().msaa_3d=[Viewport.MSAA_DISABLED,Viewport.MSAA_2X,Viewport.MSAA_4X][quality]
		var sun=world.get_node_or_null("Sunlight")
		if sun:
			sun.shadow_enabled=quality>0)
	_label(box,"WASD mover · Shift correr · Espaço pular\nCtrl alterna agachar · C segura agachar\nMouse atira/mira · 1/2/3 arma · R recarrega\nE coleta · H kit · T gelo (também no ar)\nF olhar livre · V transpor · Esc pausa",16)
	var volume=HSlider.new()
	volume.min_value=0
	volume.max_value=100
	volume.value=65
	box.add_child(volume)
	_label(box,"Volume da música",14)
	volume.value_changed.connect(func(value):music.volume_db=linear_to_db(maxf(0.001,value/100.0*0.24)))
	_label(box,"Versão solo inicial. Multiplayer e paraquedas\nainda não foram migrados do HTML.",14)
	hud=Control.new()
	hud.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	hud.mouse_filter=Control.MOUSE_FILTER_IGNORE
	ui.add_child(hud)
	hud.visible=false
	status=_label(hud,"",19)
	status.position=Vector2(28,22)
	health=_label(hud,"",25)
	health.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_LEFT)
	health.position=Vector2(28,-110)
	inventory=_label(hud,"",20)
	inventory.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_RIGHT)
	inventory.position=Vector2(-370,-145)
	events=_label(hud,"",15)
	events.position=Vector2(28,112)
	notice=_label(hud,"",18)
	notice.set_anchors_and_offsets_preset(Control.PRESET_CENTER_TOP)
	notice.position=Vector2(-220,65)
	cross=_label(hud,"+",27)
	cross.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	cross.position=Vector2(-9,-18)
	damage_layer=Control.new()
	damage_layer.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	damage_layer.mouse_filter=Control.MOUSE_FILTER_IGNORE
	hud.add_child(damage_layer)
	_build_bindings(box)
	_layout_ui()
	get_viewport().size_changed.connect(_layout_ui)

func start_match():
	if started:
		if finished:
			get_tree().reload_current_scene()
		else:
			_toggle_pause(false)
		return
	started=true
	paused_match=false
	menu.hide()
	hud.show()
	player=load("res://scripts/player.gd").new()
	player.game=self
	player.position=world.spawn_points[0]+Vector3.UP*0.15
	player.process_mode=Node.PROCESS_MODE_PAUSABLE
	add_child(player)
	actors.append(player)
	for i in range(1,48):
		var bot=load("res://scripts/bot.gd").new()
		bot.game=self
		bot.actor_id=i
		bot.position=world.spawn_points[i]+Vector3.UP*0.15
		bot.process_mode=Node.PROCESS_MODE_PAUSABLE
		add_child(bot)
		bot.visual.configure(true,i)
		actors.append(bot)
	for i in range(world.loot_points.size()):
		var kind="kit" if i%2==0 else ["ammo","armor","helmet","ice","shotgun"][i%5]
		spawn_loot(world.loot_points[i],kind)
	Input.mouse_mode=Input.MOUSE_MODE_CAPTURED
	notify("48 participantes · 108 kits distribuídos pela ilha")

func _unhandled_input(event):
	if event.is_action_pressed("pause_match") and started and not finished:
		_toggle_pause(not paused_match)
	if event is InputEventMouseButton and event.pressed and started and not paused_match and Input.mouse_mode!=Input.MOUSE_MODE_CAPTURED:
		Input.mouse_mode=Input.MOUSE_MODE_CAPTURED

func _toggle_pause(value:bool):
	paused_match=value
	get_tree().paused=value
	menu.visible=value
	Input.mouse_mode=Input.MOUSE_MODE_VISIBLE if value else Input.MOUSE_MODE_CAPTURED

func _process(delta):
	if not started or paused_match or finished:
		return
	time_elapsed+=delta
	zone_clock+=delta
	notice_time=maxf(0,notice_time-delta)
	if notice_time==0:
		notice.text=""
	var duration=38.0 if zone_shrinking else (35.0 if zone_phase==0 else 22.0)
	if zone_shrinking:
		zone_radius=lerpf(zone_from,zone_target_radius,minf(1,zone_clock/duration))
	if zone_clock>=duration:
		zone_clock=0
		zone_shrinking=not zone_shrinking
		if zone_shrinking:
			zone_from=zone_radius
			notify("A zona está fechando. Entre na área segura!")
		else:
			zone_phase+=1
			zone_target_radius=maxf(12,zone_radius*0.67)
	zone_mesh.scale=Vector3(zone_radius,1,zone_radius)
	var alive_count=0
	for actor in actors:
		if is_instance_valid(actor) and actor.alive:
			alive_count+=1
			if actor!=player and is_instance_valid(player):actor.visual.visible=actor.position.distance_to(player.position)<140
			if not actor.human and Vector2(actor.position.x,actor.position.z).length()>zone_radius:
				actor.take_damage(delta*(3+zone_phase),false,null)
	status.text="VIVOS %d / 48     ELIMINAÇÕES %d\nSAFE %s · %ds · %dm"%[alive_count,kills,"FECHANDO" if zone_shrinking else "AGUARDE",ceili(duration-zone_clock),int(zone_radius)]
	if is_instance_valid(player):
		health.text="%d / 200 HP\nColete %d · Capacete %d"%[ceili(player.hp),int(player.armor),int(player.helmet)]
		inventory.text="%s · %d / %d\nR recarregar · H kit ×%d\nT gelo ×%d · E coletar"%[player.weapon.to_upper(),player.ammo[player.weapon],player.reserves[player.weapon],player.medkits,player.ice]
		if player.reload_time>0:
			inventory.text+="\nRECARREGANDO %.1fs"%player.reload_time
		var near=choose_loot(player.position)
		if near and near.position.distance_to(player.position)<2.5:
			notice.text="E · COLETAR "+str(near.get_meta("kind")).to_upper()
	if alive_count==1 and player.alive:
		finish(true)

func visible_between(from:Vector3,to:Vector3,actor:CollisionObject3D)->bool:
	var query=PhysicsRayQueryParameters3D.create(from,to,1,[actor.get_rid()])
	return get_world_3d().direct_space_state.intersect_ray(query).is_empty()

func request_shot(shooter:Node3D,origin:Vector3,direction:Vector3,weapon:String):
	var query=PhysicsRayQueryParameters3D.create(origin,origin+direction.normalized()*190,3,[shooter.get_rid()])
	var hit=get_world_3d().direct_space_state.intersect_ray(query)
	var end=origin+direction*160
	if not hit.is_empty():
		end=hit.position
		var target=hit.collider
		if target.has_method("take_damage") and target!=shooter and target.alive:
			var distance=origin.distance_to(end)
			var maximum=48.0 if weapon=="shotgun" else 18.0 if weapon=="pistol" else 21.0
			var minimum=6.0 if weapon=="shotgun" else 8.0 if weapon=="pistol" else 13.0
			var far_distance=35.0 if weapon=="shotgun" else 75.0 if weapon=="pistol" else 115.0
			var amount=lerpf(maximum,minimum,clampf((distance-7)/(far_distance-7),0,1))
			var headshot=end.y-target.global_position.y>1.43
			if headshot:
				amount*=1.85
			var before=target.hp
			target.take_damage(amount,headshot,shooter)
			if shooter.human:
				float_damage(end,before-target.hp,headshot)
		elif target.has_meta("ice_wall"):
			target.set_meta("hp",float(target.get_meta("hp"))-24)
			if target.get_meta("hp")<=0:
				covers.erase(target)
				target.queue_free()
	play_one_shot("shot",shooter.global_position,-7,0.80 if weapon=="shotgun" else 1.20 if weapon=="pistol" else 1.0)
	var beam=MeshInstance3D.new()
	var line=ImmediateMesh.new()
	var material=StandardMaterial3D.new()
	material.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
	material.albedo_color=Color(0.98,0.83,0.43)
	line.surface_begin(Mesh.PRIMITIVE_LINES,material)
	line.surface_add_vertex(origin)
	line.surface_add_vertex(end)
	line.surface_end()
	beam.mesh=line
	add_child(beam)
	var lifetime=Timer.new()
	lifetime.wait_time=0.045
	lifetime.one_shot=true
	beam.add_child(lifetime)
	lifetime.timeout.connect(beam.queue_free)
	lifetime.start()

func float_damage(where:Vector3,amount:float,headshot:bool):
	var label=_label(damage_layer,str(roundi(amount))+("!" if headshot else ""),25)
	var screen=player.camera.unproject_position(where)
	label.position=screen
	label.add_theme_color_override("font_color",Color("ffe189") if headshot else Color.WHITE)
	var tween=create_tween()
	tween.set_parallel(true)
	tween.tween_property(label,"position:y",screen.y-40,0.7)
	tween.tween_property(label,"modulate:a",0.0,0.7)
	tween.chain().tween_callback(label.queue_free)

func spawn_loot(where:Vector3,kind:String):
	var item=Node3D.new()
	item.position=where
	item.set_meta("kind",kind)
	var mesh=MeshInstance3D.new()
	var shape=BoxMesh.new()
	shape.size=Vector3(0.40,0.22,0.31) if kind=="kit" else Vector3(0.26,0.18,0.34)
	mesh.mesh=shape
	var material=StandardMaterial3D.new()
	material.albedo_color={"kit":Color("e9e8d7"),"ammo":Color("c1a364"),"ice":Color("7bdde8"),"armor":Color("586f80"),"helmet":Color("638b73"),"shotgun":Color("7a5840")}.get(kind,Color.WHITE)
	mesh.material_override=material
	mesh.position.y=0.22
	item.add_child(mesh)
	if kind=="helmet":
		var helmet_mesh=SphereMesh.new()
		helmet_mesh.radius=0.22
		helmet_mesh.height=0.25
		helmet_mesh.is_hemisphere=true
		mesh.mesh=helmet_mesh
	elif kind=="armor":
		shape.size=Vector3(0.38,0.44,0.13)
		for side in [-1,1]:
			var strap=MeshInstance3D.new()
			var strip=BoxMesh.new()
			strip.size=Vector3(0.065,0.20,0.13)
			strap.mesh=strip
			strap.material_override=material
			strap.position=Vector3(side*0.145,0.47,0)
			item.add_child(strap)
	elif kind=="ammo":
		shape.size=Vector3(0.24,0.10,0.21)
		for i in range(3):
			var bullet=MeshInstance3D.new()
			var cylinder=CylinderMesh.new()
			cylinder.top_radius=0.018
			cylinder.bottom_radius=0.03
			cylinder.height=0.17
			bullet.mesh=cylinder
			bullet.material_override=material
			bullet.position=Vector3((i-1)*0.07,0.33,0)
			item.add_child(bullet)
	elif kind=="ice":
		var crystal=PrismMesh.new()
		crystal.size=Vector3(0.35,0.46,0.28)
		mesh.mesh=crystal
	elif kind=="shotgun":
		shape.size=Vector3(0.085,0.10,0.65)
		var barrel=MeshInstance3D.new()
		var barrel_mesh=CylinderMesh.new()
		barrel_mesh.top_radius=0.025
		barrel_mesh.bottom_radius=0.025
		barrel_mesh.height=0.50
		barrel.mesh=barrel_mesh
		barrel.material_override=material
		barrel.rotation.x=PI/2
		barrel.position=Vector3(0,0.23,-0.44)
		item.add_child(barrel)
	if kind=="kit":
		var cross_mat=StandardMaterial3D.new()
		cross_mat.albedo_color=Color("ce504a")
		for size in [Vector3(0.23,0.008,0.055),Vector3(0.055,0.008,0.20)]:
			var cross=MeshInstance3D.new()
			var cross_shape=BoxMesh.new()
			cross_shape.size=size
			cross.mesh=cross_shape
			cross.material_override=cross_mat
			cross.position.y=0.335
			item.add_child(cross)
	add_child(item)
	loot.append(item)
	var key=Vector2i(floori(where.x/8),floori(where.z/8))
	if not loot_cells.has(key):loot_cells[key]=[]
	loot_cells[key].append(item)

func choose_loot(where:Vector3)->Node3D:
	var best:Node3D=null
	var distance=50.0
	for item in loot:
		if not is_instance_valid(item):
			continue
		var d=where.distance_to(item.position)
		if d<distance:
			distance=d
			best=item
	return best

func claim_loot(actor:Node3D):
	var item=_nearby_loot(actor.position)
	if not item or item.position.distance_to(actor.position)>2.3:
		return
	var kind=item.get_meta("kind")
	if kind=="kit":
		if actor.medkits>=6:
			return
		actor.medkits+=1
	elif actor.human:
		if kind=="armor":actor.armor=100
		if kind=="helmet":actor.helmet=100
		if kind=="ice":actor.ice+=2
		if kind=="ammo":actor.reserves[actor.weapon]+=40
		if kind=="shotgun":actor.ammo.shotgun=6
	else:
		actor.weapon="shotgun" if kind=="shotgun" else "rifle"
	loot.erase(item)
	var cell=Vector2i(floori(item.position.x/8),floori(item.position.z/8))
	loot_cells[cell].erase(item)
	item.queue_free()
	if actor.human:
		play_one_shot("reload",actor.position,-12,1.5)
		notify("Coletado: "+str(kind))

func place_ice(actor:Node3D)->bool:
	if actor.ice<=0 or not actor.alive:
		return false
	var yaw_angle=actor.yaw
	for distance in [3.4,4.3,2.7]:
		var forward=-Basis(Vector3.UP,yaw_angle).z
		var center=actor.position+forward*distance
		var y=world.get_height(center.x,center.z)
		# Anchor to real terrain, even when the player is in the air.
		if actor.position.y-y>4:
			continue
		center.y=y+1.25
		var shape=BoxShape3D.new()
		shape.size=Vector3(4,2.5,0.48)
		var query=PhysicsShapeQueryParameters3D.new()
		var probe=BoxShape3D.new()
		probe.size=Vector3(3.95,2.3,0.44)
		query.shape=probe
		query.transform=Transform3D(Basis(Vector3.UP,yaw_angle),center+Vector3.UP*0.12)
		query.collision_mask=1|2
		if not get_world_3d().direct_space_state.intersect_shape(query,1).is_empty():
			continue
		var center_query=PhysicsRayQueryParameters3D.create(actor.position+Vector3.UP,center,1,[actor.get_rid()])
		if not get_world_3d().direct_space_state.intersect_ray(center_query).is_empty():
			continue
		var wall=StaticBody3D.new()
		wall.position=center
		wall.rotation.y=yaw_angle
		wall.set_meta("ice_wall",true)
		wall.set_meta("hp",300.0)
		var collider=CollisionShape3D.new()
		collider.shape=shape
		wall.add_child(collider)
		var visual=MeshInstance3D.new()
		var block=BoxMesh.new()
		block.size=shape.size
		visual.mesh=block
		var material=StandardMaterial3D.new()
		material.albedo_color=Color("9cd7e2")
		material.roughness=0.28
		material.metallic=0.15
		visual.material_override=material
		wall.add_child(visual)
		add_child(wall)
		covers.append(wall)
		actor.ice-=1
		play_one_shot("impact",center,-12,1.4)
		var lifetime=Timer.new()
		lifetime.wait_time=30
		lifetime.one_shot=true
		wall.add_child(lifetime)
		lifetime.timeout.connect(_expire_ice.bind(wall))
		lifetime.start()
		return true
	notify("Sem espaço para gelo: tente mirar um pouco ao lado")
	return false

func on_actor_died(actor:Node3D,killer):
	if killer==player and actor!=player:
		kills+=1
	if actor!=player:
		spawn_loot(actor.position,"kit")
		events.text="%s foi eliminado"%("BOT "+str(actor.actor_id))
	if actor==player:
		finish(false)

func notify(text:String):
	if notice:
		notice.text=text
		notice_time=3.0

func finish(won:bool):
	finished=true
	paused_match=true
	get_tree().paused=true
	Input.mouse_mode=Input.MOUSE_MODE_VISIBLE
	menu.show()
	var first=menu.get_child(0).get_child(2)
	first.text="VITÓRIA!" if won else "DERROTA · tente outra rota"

func _render_preview():
	start_match()
	for actor in actors:
		actor.set_physics_process(false)
	player.position=Vector3(4,world.get_height(4,43),43)
	player.yaw=0
	player.pitch=-0.08
	player.visual.rotation.y=0
	player.visual.animate(Vector3.ZERO,true,false,0.016)
	player.pivot.position.x=0.52
	player.pivot.rotation=Vector3(player.pitch,0,0)
	for i in range(20):
		await get_tree().process_frame
	var image=get_viewport().get_texture().get_image()
	image.save_png("res://godot-town.png")
	menu_camera.current=true
	menu_camera.position=Vector3(115,65,112)
	menu_camera.look_at(Vector3.ZERO)
	for i in range(10):
		await get_tree().process_frame
	get_viewport().get_texture().get_image().save_png("res://godot-island.png")
	hud.hide()
	menu_camera.position=player.position+Vector3(1.8,1.35,-2.7)
	menu_camera.look_at(player.position+Vector3.UP*1.0)
	for i in range(10):
		await get_tree().process_frame
	get_viewport().get_texture().get_image().save_png("res://godot-character.png")

func _layout_ui():
	var size=get_viewport().get_visible_rect().size
	ui.set_anchors_preset(Control.PRESET_TOP_LEFT)
	hud.set_anchors_preset(Control.PRESET_TOP_LEFT)
	ui.size=size
	hud.size=size
	for control in [status,health,inventory,events,notice,cross,damage_layer]:
		control.set_anchors_preset(Control.PRESET_TOP_LEFT)
	status.position=Vector2(28,22)
	health.position=Vector2(28,size.y-100)
	inventory.position=Vector2(size.x-350,size.y-145)
	notice.position=Vector2(size.x*0.5-210,80)
	cross.position=size*0.5-Vector2(9,18)
	damage_layer.size=size

func _nearby_loot(where:Vector3)->Node3D:
	var key=Vector2i(floori(where.x/8),floori(where.z/8))
	var best:Node3D=null
	var nearest=2.3
	for x in range(-1,2):
		for z in range(-1,2):
			for item in loot_cells.get(key+Vector2i(x,z),[]):
				if is_instance_valid(item) and item.position.distance_to(where)<nearest:
					best=item
					nearest=item.position.distance_to(where)
	return best

func _build_bindings(menu_box:VBoxContainer):
	var open=Button.new()
	open.text="AJUSTAR TECLAS"
	menu_box.add_child(open)
	binding_panel=PanelContainer.new()
	binding_panel.position=Vector2(560,45)
	binding_panel.custom_minimum_size=Vector2(480,610)
	_style_panel(binding_panel,Color(0.04,0.10,0.12,0.98))
	ui.add_child(binding_panel)
	binding_panel.hide()
	var scroll=ScrollContainer.new()
	scroll.custom_minimum_size=Vector2(430,570)
	binding_panel.add_child(scroll)
	var column=VBoxContainer.new()
	column.size_flags_horizontal=Control.SIZE_EXPAND_FILL
	scroll.add_child(column)
	_label(column,"TECLAS E BOTÕES",24)
	_label(column,"Clique na ação e pressione uma tecla.\nEsc cancela. Configuração salva neste PC.",14)
	for action in ["forward","back","left","right","sprint","jump","crouch_toggle","crouch_hold","fire","aim","reload","kit","ice","loot","free_look","vault","weapon_1","weapon_2","weapon_3"]:
		var button=Button.new()
		button.text=action+" · "+InputMap.action_get_events(action)[0].as_text()
		button.pressed.connect(func():
			listening_action=action
			button.text=action+" · pressione a tecla...")
		column.add_child(button)
		binding_buttons[action]=button
	var close=Button.new()
	close.text="FECHAR"
	column.add_child(close)
	close.pressed.connect(func():binding_panel.hide())
	open.pressed.connect(func():binding_panel.visible=not binding_panel.visible)

func _input(event):
	if listening_action=="":return
	if event is InputEventKey and event.pressed:
		if event.keycode==KEY_ESCAPE:
			listening_action=""
			get_viewport().set_input_as_handled()
			return
		var key=InputEventKey.new()
		key.physical_keycode=event.physical_keycode
		InputMap.action_erase_events(listening_action)
		InputMap.action_add_event(listening_action,key)
	elif event is InputEventMouseButton and event.pressed:
		var mouse=InputEventMouseButton.new()
		mouse.button_index=event.button_index
		InputMap.action_erase_events(listening_action)
		InputMap.action_add_event(listening_action,mouse)
	else:return
	binding_buttons[listening_action].text=listening_action+" · "+InputMap.action_get_events(listening_action)[0].as_text()
	listening_action=""
	var config=ConfigFile.new()
	for action in binding_buttons:
		var binding=InputMap.action_get_events(action)[0]
		config.set_value("keys",action,{"mouse":binding.button_index} if binding is InputEventMouseButton else {"key":binding.physical_keycode})
	config.save("user://controls.cfg")
	get_viewport().set_input_as_handled()

func _load_bindings():
	var config=ConfigFile.new()
	if config.load("user://controls.cfg")!=OK:return
	for action in config.get_section_keys("keys"):
		if not InputMap.has_action(action):continue
		var data=config.get_value("keys",action)
		var event:InputEvent
		if data.has("mouse"):
			event=InputEventMouseButton.new()
			event.button_index=data.mouse
		else:
			event=InputEventKey.new()
			event.physical_keycode=data.key
		InputMap.action_erase_events(action)
		InputMap.action_add_event(action,event)

func _expire_ice(wall:Node3D):
	if is_instance_valid(wall):
		covers.erase(wall)
		wall.queue_free()

func _finish_voice(audio:AudioStreamPlayer3D):
	voices=maxi(0,voices-1)
	if is_instance_valid(audio):audio.queue_free()
