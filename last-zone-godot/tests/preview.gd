extends SceneTree

func _initialize():
	run.call_deferred()

func run():
	var game=load("res://scenes/main.tscn").instantiate()
	root.add_child(game)
	current_scene=game
	await process_frame
	await game._render_preview()
	game.music.stop()
	game.queue_free()
	await process_frame
	await process_frame
	print("GODOT PREVIEWS SAVED")
	quit()
