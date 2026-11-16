extends SceneTree

var failures: Array[String] = []

func check(condition:bool,message:String):
	if not condition:
		failures.append(message)
		push_error("TEST FAILED: "+message)

func _initialize():
	_run.call_deferred()

func frames(count:int):
	for i in range(count):
		await physics_frame

func _run():
	var game=load("res://scenes/main.tscn").instantiate()
	root.add_child(game)
	current_scene=game
	await process_frame
	game.start_match()
	await frames(4)
	check(game.actors.size()==48,"48 participants")
	check(game.loot.size()==216,"216 loot objects")
	var kits=0
	for item in game.loot:
		if item.get_meta("kind")=="kit":kits+=1
	check(kits==108,"108 health kits")
	check(game.actors.all(func(actor):return actor.hp==200),"all actors have 200 health")
	for actor in game.actors:
		if actor!=game.player:
			actor.set_physics_process(false)
	var player=game.player
	player.global_position=Vector3(0,0.4,55)
	player.velocity=Vector3.ZERO
	await frames(40)
	check(player.is_on_floor(),"native floor collision settles on road")
	Input.action_press("forward")
	await frames(50)
	check(absf(Vector2(player.velocity.x,player.velocity.z).length()-5.2*1.14)<0.03,"walking speed +14 percent")
	Input.action_press("sprint")
	await frames(45)
	check(absf(Vector2(player.velocity.x,player.velocity.z).length()-8.5*1.14)<0.03,"running speed +14 percent")
	Input.action_release("forward")
	Input.action_release("sprint")
	await frames(30)
	var jump=InputEventAction.new()
	jump.action="jump"
	jump.pressed=true
	player._unhandled_input(jump)
	await frames(3)
	check(player.velocity.y>0 and not player.is_on_floor(),"jump leaves native floor")
	Input.action_press("right")
	await frames(12)
	check(player.velocity.x>0.8 and not player.is_on_floor(),"limited air steering")
	Input.action_release("right")
	await frames(90)
	check(player.is_on_floor(),"jump lands without repeated falling")
	player.global_position=Vector3(0,1.0,60)
	player.velocity=Vector3(0,1,0)
	player.yaw=0
	await frames(1)
	var before=player.ice
	check(game.place_ice(player),"ice can be placed while airborne")
	check(player.ice==before-1 and game.covers.size()==1,"successful ice spends exactly one charge")
	check(absf(game.covers[0].position.y-game.world.get_height(0,56.6)-1.25)<0.05,"ice anchored to ground instead of flying feet")
	var wall=game.covers[0]
	check(not game.visible_between(Vector3(0,1,59),Vector3(0,1,54),player),"ice blocks line of sight")
	player.global_position=Vector3(80,game.world.get_height(80,80)+0.35,80)
	player.velocity=Vector3.ZERO
	await frames(40)
	var grounded=0
	Input.action_press("forward")
	for i in range(70):
		await frames(1)
		if player.is_on_floor():grounded+=1
	Input.action_release("forward")
	check(grounded>=60,"ground snap remains stable on real hill triangles")
	player._unhandled_input(jump)
	await frames(3)
	check(player.velocity.y>0,"jump works on sloped terrain")
	player.set_physics_process(false)
	player.hp=125
	player.medkits=1
	player.use_kit()
	check(player.healing>0 and player.medkits==0,"kit begins healing below 200 health")
	player.healing=0
	player.hp=200
	player.medkits=1
	player.use_kit()
	check(player.medkits==1,"kit retained at full health")
	# Terrain collision independently checked against its rendered triangle heights.
	for point in [Vector2(80,80),Vector2(-100,-55),Vector2(150,70),Vector2(0,50)]:
		var from=Vector3(point.x,25,point.y)
		var query=PhysicsRayQueryParameters3D.create(from,from-Vector3.UP*50,1)
		var hit=game.get_world_3d().direct_space_state.intersect_ray(query)
		check(not hit.is_empty(),"terrain ray hits")
		if not hit.is_empty():check(absf(hit.position.y-game.world.get_height(point.x,point.y))<0.12,"physics height equals terrain height")
	check(game.hud.size.x>=960 and game.health.position.y>400,"HUD positioned in viewport")
	print("GODOT TESTS: 48 actors, 108 kits, 200 HP, speed +14%, slope jump, air steering, airborne ice, LOS, terrain, health and HUD checked")
	game.music.stop()
	game.queue_free()
	await process_frame
	await process_frame
	if failures.is_empty():
		print("GODOT SMOKE PASS")
		quit(0)
	else:
		print("GODOT SMOKE FAIL: "+str(failures))
		quit(1)
