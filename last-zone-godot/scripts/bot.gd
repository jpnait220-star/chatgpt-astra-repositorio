class_name ZoneBot
extends CharacterBody3D

var game: Node
var hp: float = 200.0
var alive: bool = true
var human: bool = false
var actor_id: int = 1
var team: int = -1
var medkits: int = 1
var weapon: String = "rifle"
var visual: Node3D

var _rng := RandomNumberGenerator.new()
var _enemy: Node3D
var _last_seen := Vector3.ZERO
var _lost_time: float = 0.0
var _reaction: float = 0.35
var _scan: float = 0.0
var _shot: float = 0.0
var _burst: int = 0
var _strafe: float = 1.0
var _strafe_time: float = 0.0
var _home := Vector3.ZERO
var _goal := Vector3.ZERO
var _wander: float = 0.0
var _cover := Vector3.ZERO
var _cover_valid: bool = false
var _cover_time: float = 0.0
var _heal_time: float = 0.0
var _jump_delay: float = 0.0
var _step_distance: float = 0.0
var _stuck: float = 0.0
var _previous_position := Vector3.ZERO
var _loot: Node3D
var _crouching: bool = false

func _ready() -> void:
	if game == null:
		game = get_parent()
	_rng.seed = 12487 + actor_id * 3571
	_scan = _rng.randf_range(0.0, 0.35)
	_home = global_position
	_goal = _home
	_previous_position = global_position
	_strafe = -1.0 if actor_id % 2 else 1.0
	collision_layer = 2
	collision_mask = 1
	floor_snap_length = 0.45
	floor_max_angle = deg_to_rad(48.0)
	floor_stop_on_slope = true
	var shape := CapsuleShape3D.new()
	shape.radius = 0.35
	shape.height = 1.8
	var collision := CollisionShape3D.new()
	collision.shape = shape
	collision.position.y = 0.9
	add_child(collision)
	visual = ActorVisual.new()
	add_child(visual)
	add_to_group("actors")

func _physics_process(delta: float) -> void:
	if not alive or game == null:
		return
	_scan -= delta
	_shot = maxf(0.0, _shot - delta)
	_reaction = maxf(0.0, _reaction - delta)
	_wander -= delta
	_cover_time -= delta
	_strafe_time -= delta
	_jump_delay = maxf(0.0, _jump_delay - delta)
	if not _valid_enemy(_enemy):
		_enemy = null
	if _scan <= 0.0:
		_scan = 0.28 + float(actor_id % 5) * 0.025
		_scan_enemies()
	var sees_enemy := _valid_enemy(_enemy) and _visible(_enemy)
	if sees_enemy:
		_last_seen = _enemy.global_position
		_lost_time = 0.0
	else:
		_lost_time += delta
		if _lost_time > 1.5:
			_enemy = null
	var urgent := _needs_zone()
	_crouching = false
	if _heal_time > 0.0:
		_heal_time -= delta
		_crouching = true
		if _heal_time <= 0.0 and medkits > 0:
			medkits -= 1
			hp = minf(200.0, hp + 100.0)
		_move_toward(global_position, delta, false)
	elif hp < 140.0 and medkits > 0 and not urgent and (not sees_enemy or global_position.distance_to(_enemy.global_position) > 30.0):
		_heal_time = 3.0
		_move_toward(global_position, delta, false)
	elif urgent:
		_goal = _zone_goal()
		_move_toward(_goal, delta, true)
	elif sees_enemy:
		_combat_move(delta)
	else:
		_loot_or_patrol(delta)
	if sees_enemy and _heal_time <= 0.0:
		_aim_and_shoot(delta)
	elif velocity.length_squared() > 0.2:
		var direction := Vector3(velocity.x, 0.0, velocity.z)
		rotation.y = lerp_angle(rotation.y, atan2(-direction.x, -direction.z), 1.0 - exp(-delta * 7.0))
	if not is_on_floor():
		velocity.y -= 19.5 * delta
	elif velocity.y < 0.0:
		velocity.y = -0.6
	var before := global_position
	move_and_slide()
	var travelled := Vector2(global_position.x - before.x, global_position.z - before.z).length()
	if is_on_floor() and travelled > 0.001:
		_step_distance += travelled
		var running := Vector2(velocity.x, velocity.z).length() > 6.0
		if _step_distance >= (2.0 if running else 1.35):
			_step_distance = 0.0
			game.play_step(global_position, running)
	if visual != null:
		visual.animate(velocity, is_on_floor(), _crouching, delta, sees_enemy)
	_previous_position = before
	game.claim_loot(self)

func _valid_enemy(actor: Node3D) -> bool:
	return is_instance_valid(actor) and actor != self and bool(actor.get("alive")) and (team < 0 or actor.get("team") == null or int(actor.get("team")) != team)

func _scan_enemies() -> void:
	var best: Node3D = null
	var best_distance := 70.0 if weapon == "rifle" else 48.0
	for actor in game.actors:
		if not _valid_enemy(actor):
			continue
		var offset: Vector3 = actor.global_position - global_position
		var distance := offset.length()
		if distance >= best_distance:
			continue
		var forward := -global_transform.basis.z
		if distance > 17.0 and forward.dot(offset.normalized()) < -0.5 and actor != _enemy:
			continue
		if _visible(actor):
			best = actor
			best_distance = distance
	if best != _enemy and best != null:
		_reaction = 0.25 + float(actor_id % 5) * 0.035
		_burst = 0
	if best != null:
		_enemy = best

func _ray(from: Vector3, to: Vector3, mask: int = 1) -> Dictionary:
	var query := PhysicsRayQueryParameters3D.create(from, to, mask, [get_rid()])
	return get_world_3d().direct_space_state.intersect_ray(query)

func _visible(actor: Node3D) -> bool:
	if not _valid_enemy(actor):
		return false
	var from := global_position + Vector3.UP * 1.45
	var to := actor.global_position + Vector3.UP * 1.2
	var hit := _ray(from, to, 3)
	return hit.is_empty() or hit.get("collider") == actor

func _needs_zone() -> bool:
	var distance := Vector2(global_position.x - game.zone_center.x, global_position.z - game.zone_center.z).length()
	var boundary: float = game.zone_target_radius if game.zone_shrinking else game.zone_radius
	return distance > boundary - 16.0

func _zone_goal() -> Vector3:
	var toward: Vector3 = global_position - game.zone_center
	toward.y = 0.0
	if toward.length_squared() < 0.01:
		toward = Vector3.RIGHT.rotated(Vector3.UP, float(actor_id) * 2.399)
	var radius: float = maxf(0.0, float(game.zone_target_radius if game.zone_shrinking else game.zone_radius) - 21.0)
	var result: Vector3 = game.zone_center + toward.normalized() * radius * (0.72 + float(actor_id % 6) * 0.025)
	result.y = game.world.get_height(result.x, result.z)
	return result

func _combat_move(delta: float) -> void:
	var distance := global_position.distance_to(_enemy.global_position)
	if hp < 75.0 and _cover_time <= 0.0:
		_cover_time = 2.2
		_find_cover()
	if hp < 75.0 and _cover_valid and global_position.distance_to(_cover) > 1.1:
		_move_toward(_cover, delta, true)
		return
	if _strafe_time <= 0.0:
		_strafe_time = _rng.randf_range(1.0, 1.8)
		_strafe = -_strafe
	var toward := _enemy.global_position - global_position
	toward.y = 0.0
	toward = toward.normalized()
	var sideways := toward.cross(Vector3.UP) * _strafe
	var range_goal := 9.0 if weapon == "shotgun" else 23.0
	var movement := sideways * 2.0
	if distance > range_goal + 8.0:
		movement += toward * 4.0
	elif distance < 7.0:
		movement -= toward * 3.5
	_move_toward(global_position + movement, delta, false)

func _aim_and_shoot(delta: float) -> void:
	if not _valid_enemy(_enemy):
		return
	var from := global_position + Vector3.UP * (1.0 if _crouching else 1.45)
	var point := _enemy.global_position + Vector3.UP * 1.25
	var direction := point - from
	var distance := direction.length()
	var desired_yaw := atan2(-direction.x, -direction.z)
	var turn := wrapf(desired_yaw - rotation.y, -PI, PI)
	rotation.y += clampf(turn * (1.0 - exp(-delta * 10.0)), -delta * 3.2, delta * 3.2)
	if visual != null and visual.has_method("set_aim_pitch"):
		visual.set_aim_pitch(atan2(direction.y, Vector2(direction.x, direction.z).length()))
	if _reaction > 0.0 or _shot > 0.0 or absf(wrapf(desired_yaw - rotation.y, -PI, PI)) > 0.10:
		return
	if weapon == "shotgun" and distance > 18.0:
		return
	# Hitscan bullets aim at the current visible torso; movement can outpace the finite turn.
	var error := 0.0030 + minf(70.0, distance) * 0.000035
	direction = direction.normalized()
	direction.x += _rng.randf_range(-error, error)
	direction.y += _rng.randf_range(-error * 0.8, error * 0.8)
	game.request_shot(self, from, direction.normalized(), weapon)
	_shot = 0.16 if weapon == "rifle" else (0.95 if weapon == "shotgun" else 0.34)
	_burst += 1
	if weapon == "rifle" and _burst >= 4 + actor_id % 3:
		_burst = 0
		_shot += 0.22 + float(actor_id % 3) * 0.035

func _loot_or_patrol(delta: float) -> void:
	if medkits < 2 and (not is_instance_valid(_loot) or _wander <= 0.0):
		_loot = game.choose_loot(global_position)
	if is_instance_valid(_loot):
		_move_toward(_loot.global_position, delta, hp < 130.0)
		if global_position.distance_to(_loot.global_position) < 1.6:
			game.claim_loot(self)
			_loot = null
		return
	if _wander <= 0.0 or global_position.distance_to(_goal) < 2.5:
		_wander = _rng.randf_range(4.0, 8.0)
		var angle := _rng.randf_range(0.0, TAU)
		var radius := _rng.randf_range(8.0, 38.0)
		_goal = _home + Vector3(cos(angle) * radius, 0.0, sin(angle) * radius)
		var from_center: Vector3 = _goal - game.zone_center
		from_center.y = 0.0
		if from_center.length() > float(game.zone_radius) - 20.0:
			_goal = _zone_goal()
		_goal.y = game.world.get_height(_goal.x, _goal.z)
	_move_toward(_goal, delta, false)

func _move_toward(destination: Vector3, delta: float, running: bool) -> void:
	var direction := destination - global_position
	direction.y = 0.0
	var desired := Vector3.ZERO
	if direction.length() > 0.65:
		direction = direction.normalized()
		var origin := global_position + Vector3.UP * 0.85
		if not _ray(origin, origin + direction * 1.2).is_empty():
			var found := false
			for angle in [0.7 * _strafe, -0.7 * _strafe, 1.2 * _strafe, -1.2 * _strafe, 1.7]:
				var alternative := direction.rotated(Vector3.UP, angle)
				if _ray(origin, origin + alternative * 1.35).is_empty():
					direction = alternative
					found = true
					break
			if not found and is_on_floor() and _jump_delay <= 0.0 and _ray(global_position + Vector3.UP * 1.65, global_position + Vector3.UP * 1.65 + direction * 1.3).is_empty():
				velocity.y = 6.2
				_jump_delay = 1.0
		var ahead := global_position + direction * 1.0
		var rise: float = game.world.get_height(ahead.x, ahead.z) - global_position.y
		if rise > 0.38 and rise < 0.95 and is_on_floor() and _jump_delay <= 0.0:
			velocity.y = 6.2
			_jump_delay = 1.0
		desired = direction * (7.4 if running else (2.2 if _crouching else 4.7))
	var acceleration := 24.0 if is_on_floor() else 8.0
	velocity.x = move_toward(velocity.x, desired.x, acceleration * delta)
	velocity.z = move_toward(velocity.z, desired.z, acceleration * delta)
	if desired.length_squared() > 1.0 and global_position.distance_to(_previous_position) < 0.025:
		_stuck += delta
	else:
		_stuck = 0.0
	if _stuck > 1.0:
		_strafe = -_strafe
		_wander = 0.0
		_stuck = 0.0
		if is_on_floor() and _jump_delay <= 0.0:
			velocity.y = 6.2
			_jump_delay = 1.0

func _find_cover() -> void:
	_cover_valid = false
	var score := INF
	if not _valid_enemy(_enemy):
		return
	for i in range(12):
		var angle := float(i) * TAU / 12.0
		var candidate := global_position + Vector3(cos(angle), 0.0, sin(angle)) * (5.0 if i % 2 else 8.0)
		candidate.y = game.world.get_height(candidate.x, candidate.z)
		var point := PhysicsPointQueryParameters3D.new()
		point.position = candidate + Vector3.UP
		point.collision_mask = 1
		if not get_world_3d().direct_space_state.intersect_point(point, 1).is_empty():
			continue
		var line := _ray(candidate + Vector3.UP * 1.2, _enemy.global_position + Vector3.UP * 1.2)
		if line.is_empty():
			continue
		var distance := candidate.distance_to(global_position)
		if distance < score:
			score = distance
			_cover = candidate
			_cover_valid = true

func take_damage(amount: float, _headshot: bool = false, killer: Node3D = null) -> void:
	if not alive or amount <= 0.0:
		return
	hp = maxf(0.0, hp - amount)
	_heal_time = 0.0
	if _valid_enemy(killer):
		_enemy = killer
		_reaction = minf(_reaction, 0.28)
	if hp <= 0.0:
		alive = false
		velocity = Vector3.ZERO
		collision_layer = 0
		collision_mask = 0
		if visual != null:
			visual.rotation.z = PI * 0.5
		game.on_actor_died(self, killer)
