class_name ZonePlayer
extends CharacterBody3D

const BASE_SPEED = 5.2 * 1.14
const RUN_SPEED = 8.5 * 1.14
const JUMP_SPEED = 7.5
var game: Node
var human = true
var alive = true
var actor_id = 0
var hp = 200.0
var max_hp = 200.0
var medkits = 2
var armor = 60.0
var helmet = 40.0
var ice = 4
var weapon = "rifle"
var ammo = {"rifle":30,"pistol":12,"shotgun":6}
var reserves = {"rifle":150,"pistol":60,"shotgun":30}
var reload_time = 0.0
var fire_time = 0.0
var healing = 0.0
var healing_left = 0.0
var crouching = false
var crouch_toggle = false
var jump_buffer = 0.0
var coyote = 0.0
var step_distance = 0.0
var ice_time = 0.0
var pitch = -0.08
var yaw = 0.0
var aiming = false
var free_look = false
var free_yaw = 0.0
var visual: Node3D
var pivot: Node3D
var arm: SpringArm3D
var camera: Camera3D
var body_shape: CollisionShape3D

func _ready():
	collision_layer = 2
	collision_mask = 1 | 2
	floor_snap_length = 0.4
	floor_max_angle = deg_to_rad(49)
	floor_stop_on_slope = true
	floor_constant_speed = true
	body_shape = CollisionShape3D.new()
	var capsule = CapsuleShape3D.new()
	capsule.radius = 0.32
	capsule.height = 1.8
	body_shape.shape = capsule
	body_shape.position.y = 0.9
	add_child(body_shape)
	visual = load("res://scripts/actor_visual.gd").new()
	add_child(visual)
	pivot = Node3D.new()
	pivot.position.y = 1.55
	add_child(pivot)
	arm = SpringArm3D.new()
	arm.spring_length = 3.8
	arm.margin = 0.18
	arm.collision_mask = 1
	var probe = SphereShape3D.new()
	probe.radius = 0.17
	arm.shape = probe
	pivot.add_child(arm)
	camera = Camera3D.new()
	camera.fov = 70
	camera.near = 0.15
	camera.far = 700
	camera.current = true
	arm.add_child(camera)
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED

func _unhandled_input(event):
	if not alive or game.paused_match:
		return
	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		if free_look:
			free_yaw = clampf(free_yaw-event.relative.x*0.00175,-2.5,2.5)
		else:
			yaw -= event.relative.x * 0.00175 * (0.65 if aiming else 1.0)
			pitch = clampf(pitch-event.relative.y*0.00175*(0.65 if aiming else 1.0),-0.95,1.0)
	if event.is_action_pressed("jump"):
		jump_buffer = 0.14
		crouch_toggle = false
	if event.is_action_pressed("crouch_toggle"):
		crouch_toggle = not crouch_toggle
	if event.is_action_pressed("reload"):
		reload_weapon()
	if event.is_action_pressed("kit"):
		use_kit()
	if event.is_action_pressed("ice") and ice_time <= 0:
		if game.place_ice(self):
			ice_time = 0.45
	if event.is_action_pressed("loot"):
		game.claim_loot(self)
	for i in range(3):
		if event.is_action_pressed("weapon_"+str(i+1)):
			weapon = ["rifle","shotgun","pistol"][i]
			reload_time = 0
	if event.is_action_pressed("vault"):
		try_vault()

func _physics_process(delta):
	if not alive or game.paused_match:
		return
	var was_floor = is_on_floor()
	coyote = 0.12 if was_floor else maxf(0,coyote-delta)
	jump_buffer = maxf(0,jump_buffer-delta)
	fire_time = maxf(0,fire_time-delta)
	ice_time = maxf(0,ice_time-delta)
	if reload_time > 0:
		reload_time = maxf(0,reload_time-delta)
		if reload_time == 0:
			var needed=mini({"rifle":30,"shotgun":6,"pistol":12}[weapon]-ammo[weapon],reserves[weapon])
			ammo[weapon]+=needed
			reserves[weapon]-=needed
	if healing > 0:
		var restored = minf(healing_left,25.0*delta)
		hp = minf(max_hp,hp+restored)
		healing_left -= restored
		healing = maxf(0,healing-delta)
	aiming = Input.is_action_pressed("aim")
	free_look = Input.is_action_pressed("free_look")
	if not free_look:
		free_yaw = lerpf(free_yaw,0,1-exp(-delta*12))
	var wants_crouch = crouch_toggle or Input.is_action_pressed("crouch_hold")
	# A shape query stops the capsule expanding through a ceiling.
	if crouching and not wants_crouch:
		var query = PhysicsShapeQueryParameters3D.new()
		var standing = CapsuleShape3D.new()
		standing.height = 1.8
		standing.radius = 0.31
		query.shape = standing
		query.transform = Transform3D(Basis.IDENTITY,global_position+Vector3.UP*0.91)
		query.collision_mask = 1
		wants_crouch = not get_world_3d().direct_space_state.intersect_shape(query,1).is_empty()
	crouching = wants_crouch
	body_shape.shape.height = 1.18 if crouching else 1.8
	body_shape.position.y = 0.59 if crouching else 0.9
	var input = Input.get_vector("left","right","forward","back")
	var direction = Basis(Vector3.UP,yaw)*Vector3(input.x,0,input.y)
	var speed = 2.6*1.14 if crouching else (3.2*1.14 if aiming else (RUN_SPEED if Input.is_action_pressed("sprint") and input.y<0 else BASE_SPEED))
	var acceleration = 34.0 if was_floor else 8.5
	if not was_floor and input.length()<0.01:
		acceleration = 0.8 # Keep jump momentum, with limited air steering.
	velocity.x = move_toward(velocity.x,direction.x*speed,acceleration*delta)
	velocity.z = move_toward(velocity.z,direction.z*speed,acceleration*delta)
	if jump_buffer > 0 and coyote > 0 and not crouching:
		velocity.y = JUMP_SPEED
		jump_buffer = 0
		coyote = 0
		floor_snap_length = 0
	else:
		floor_snap_length = 0.4 if velocity.y <= 0 else 0
		if not was_floor:
			velocity.y -= 22*delta
		elif velocity.y < 0:
			velocity.y = -0.5
	var before = global_position
	move_and_slide()
	if is_on_floor() and not was_floor:
		game.play_one_shot("land",global_position,-9)
	if is_on_floor() and velocity.length()>0.6:
		step_distance += Vector2(global_position.x-before.x,global_position.z-before.z).length()
		if step_distance > (1.9 if speed>8 else 1.4):
			step_distance = 0
			game.play_step(global_position,speed>8)
	visual.rotation.y = lerp_angle(visual.rotation.y,yaw,1-exp(-delta*16))
	if visual.has_method("animate"):
		visual.animate(velocity,is_on_floor(),crouching,delta,aiming)
	var shoulder=Basis(Vector3.UP,yaw)*Vector3(0.52,0,0)
	pivot.position.x=shoulder.x
	pivot.position.z=shoulder.z
	pivot.position.y = lerpf(pivot.position.y,1.05 if crouching else 1.55,1-exp(-delta*15))
	pivot.rotation = Vector3(pitch,yaw+free_yaw,0)
	arm.spring_length = lerpf(arm.spring_length,1.65 if aiming else 3.8,1-exp(-delta*12))
	camera.fov = lerpf(camera.fov,53.0 if aiming else 70.0,1-exp(-delta*12))
	if Input.is_action_pressed("fire") and not free_look and fire_time <= 0 and reload_time <= 0:
		shoot()
	if global_position.y < -10:
		take_damage(200,false,null)
	if Vector2(global_position.x-game.zone_center.x,global_position.z-game.zone_center.z).length()>game.zone_radius:
		take_damage(3*delta,false,null)

func shoot():
	if ammo[weapon] <= 0:
		reload_weapon()
		return
	healing = 0
	ammo[weapon] -= 1
	fire_time = {"rifle":0.12,"shotgun":0.85,"pistol":0.3}[weapon]
	var direction = -camera.global_basis.z
	# Modest magnetic assistance while firing, with real physics visibility checks.
	var nearest = 0.085
	var selected = null
	for actor in game.actors:
		if actor == self or not is_instance_valid(actor) or not actor.alive:
			continue
		var target = actor.global_position+Vector3.UP*1.3
		var offset = target-camera.global_position
		if offset.length()>85:
			continue
		var error = direction.angle_to(offset.normalized())
		if error<nearest and game.visible_between(camera.global_position,target,self):
			nearest=error
			selected=target
	if selected != null:
		direction = direction.slerp((selected-camera.global_position).normalized(),0.32)
		var target_yaw = atan2(-direction.x,-direction.z)
		yaw = lerp_angle(yaw,target_yaw,0.32)
	game.request_shot(self,camera.global_position,direction,weapon)

func reload_weapon():
	if reload_time <= 0 and reserves[weapon]>0 and ammo[weapon]<{"rifle":30,"shotgun":6,"pistol":12}[weapon]:
		reload_time = 2.2 if weapon=="rifle" else 2.6 if weapon=="shotgun" else 1.4
		game.play_one_shot("reload",global_position,-8)

func use_kit():
	if medkits>0 and hp<max_hp and healing<=0:
		medkits -= 1
		healing = 4.0
		healing_left = 100.0
		game.notify("Usando kit: +100 de vida")

func try_vault():
	if not is_on_floor():
		return
	var forward = -Basis(Vector3.UP,yaw).z
	var space = get_world_3d().direct_space_state
	var low = PhysicsRayQueryParameters3D.create(global_position+Vector3.UP*0.55,global_position+Vector3.UP*0.55+forward*1.5,1,[get_rid()])
	var high = PhysicsRayQueryParameters3D.create(global_position+Vector3.UP*1.75,global_position+Vector3.UP*1.75+forward*2.4,1,[get_rid()])
	if not space.intersect_ray(low).is_empty() and space.intersect_ray(high).is_empty():
		velocity += forward*5
		velocity.y = 7.8

func take_damage(amount:float,headshot:bool,killer):
	if not alive:
		return
	var slot = helmet if headshot else armor
	var absorbed = minf(slot,amount*(0.45 if headshot else 0.4))
	if headshot:
		helmet -= absorbed
	else:
		armor -= absorbed
	hp = maxf(0,hp-amount+absorbed)
	if hp<=0:
		alive=false
		game.on_actor_died(self,killer)
