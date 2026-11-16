class_name ActorVisual
extends Node3D

var torso: Node3D
var head: Node3D
var hips: Array[Node3D] = []
var knees: Array[Node3D] = []
var feet: Array[Node3D] = []
var shoulders: Array[Node3D] = []
var elbows: Array[Node3D] = []
var gun: Node3D
var phase = 0.0
var blend = 0.0
var crouch = 0.0
var pitch = 0.0
var shirt: StandardMaterial3D
var skin: StandardMaterial3D
var dark: StandardMaterial3D
var silver: StandardMaterial3D
var violet: StandardMaterial3D

func material(color:Color,roughness:float=0.85)->StandardMaterial3D:
	var m=StandardMaterial3D.new()
	m.albedo_color=color
	m.roughness=roughness
	return m

func mesh(parent:Node3D,geometry:Mesh,mat:Material,where:Vector3)->MeshInstance3D:
	var m=MeshInstance3D.new()
	m.mesh=geometry
	m.material_override=mat
	m.position=where
	parent.add_child(m)
	return m

func box(parent:Node3D,size:Vector3,where:Vector3,mat:Material)->MeshInstance3D:
	var geometry=BoxMesh.new()
	geometry.size=size
	return mesh(parent,geometry,mat,where)

func ball(parent:Node3D,radius:float,where:Vector3,mat:Material,scale_by:Vector3=Vector3.ONE)->MeshInstance3D:
	var geometry=SphereMesh.new()
	geometry.radius=radius
	geometry.height=radius*2
	geometry.radial_segments=16
	geometry.rings=8
	var m=mesh(parent,geometry,mat,where)
	m.scale=scale_by
	return m

func capsule(parent:Node3D,radius:float,height:float,where:Vector3,mat:Material)->MeshInstance3D:
	var geometry=CapsuleMesh.new()
	geometry.radius=radius
	geometry.height=height
	geometry.radial_segments=12
	geometry.rings=4
	return mesh(parent,geometry,mat,where)

func _ready():
	shirt=material(Color("d9e3e0"))
	skin=material(Color("bf977b"))
	dark=material(Color("152536"))
	silver=material(Color("dce2e8"),0.65)
	violet=material(Color("645078"))
	torso=Node3D.new()
	add_child(torso)
	# A shaped continuous torso, with rounded shoulders and an overlapping neck.
	var tool=SurfaceTool.new()
	tool.begin(Mesh.PRIMITIVE_TRIANGLES)
	var rings=[Vector3(0.16,0.82,0.105),Vector3(0.19,1.03,0.125),Vector3(0.255,1.30,0.135),Vector3(0.19,1.43,0.105)]
	for r in range(rings.size()-1):
		for i in range(20):
			var a=TAU*i/20.0
			var b=TAU*(i+1)/20.0
			var vertices=[Vector3(cos(a)*rings[r].x,rings[r].y,sin(a)*rings[r].z),Vector3(cos(b)*rings[r].x,rings[r].y,sin(b)*rings[r].z),Vector3(cos(a)*rings[r+1].x,rings[r+1].y,sin(a)*rings[r+1].z),Vector3(cos(b)*rings[r+1].x,rings[r+1].y,sin(b)*rings[r+1].z)]
			for j in [0,2,1,1,2,3]:
				tool.add_vertex(vertices[j])
	tool.generate_normals()
	mesh(torso,tool.commit(),shirt,Vector3.ZERO)
	capsule(torso,0.085,0.20,Vector3(0,1.48,0),skin)
	ball(torso,0.115,Vector3(-0.22,1.31,0),shirt)
	ball(torso,0.115,Vector3(0.22,1.31,0),shirt)
	capsule(torso,0.105,0.28,Vector3(0,0.86,0),dark).rotation.z=PI/2
	box(torso,Vector3(0.35,0.055,0.23),Vector3(0,0.94,0),material(Color("554839")))
	box(torso,Vector3(0.055,0.05,0.015),Vector3(0,0.94,-0.125),material(Color("b39b60"),0.4))
	for side in [-1.0,1.0]:
		var hip=Node3D.new()
		hip.position=Vector3(side*0.12,0.85,0)
		torso.add_child(hip)
		hips.append(hip)
		capsule(hip,0.10,0.43,Vector3(0,-0.20,0),dark)
		var knee=Node3D.new()
		knee.position.y=-0.40
		hip.add_child(knee)
		knees.append(knee)
		ball(knee,0.085,Vector3.ZERO,dark)
		capsule(knee,0.078,0.39,Vector3(0,-0.18,0),dark)
		# Pale feather details on the requested dark trousers.
		for i in range(5):
			var feather=capsule(hip,0.011,0.095,Vector3(side*0.058,-0.11-i*0.038,-0.082),silver)
			feather.rotation.z=side*(0.7-i*0.07)
		var foot=Node3D.new()
		foot.position=Vector3(0,-0.38,0)
		knee.add_child(foot)
		feet.append(foot)
		ball(foot,0.1,Vector3(0,0.005,-0.045),material(Color("342b29")),Vector3(0.85,0.66,1.5))
		box(foot,Vector3(0.17,0.035,0.28),Vector3(0,-0.043,-0.045),material(Color("182324")))
		var shoulder=Node3D.new()
		shoulder.position=Vector3(side*0.265,1.32,0)
		torso.add_child(shoulder)
		shoulders.append(shoulder)
		capsule(shoulder,0.078,0.31,Vector3(0,-0.145,0),shirt)
		var elbow=Node3D.new()
		elbow.position.y=-0.29
		shoulder.add_child(elbow)
		elbows.append(elbow)
		ball(elbow,0.065,Vector3.ZERO,skin)
		capsule(elbow,0.060,0.28,Vector3(0,-0.13,0),skin)
		ball(elbow,0.063,Vector3(0,-0.26,0),skin,Vector3(0.8,1.12,0.8))
	head=Node3D.new()
	head.position=Vector3(0,1.67,0)
	head.scale=Vector3(0.81,0.84,0.86)
	torso.add_child(head)
	ball(head,0.205,Vector3.ZERO,skin,Vector3(0.91,1.07,0.88))
	ball(head,0.16,Vector3(0,-0.085,-0.01),skin,Vector3(0.9,0.6,0.9))
	for side in [-1.0,1.0]:
		ball(head,0.041,Vector3(side*0.18,-0.01,0),skin,Vector3(0.45,1,0.65))
		ball(head,0.026,Vector3(side*0.068,0.025,-0.167),material(Color("f0eee5")),Vector3(1,0.58,0.4))
		ball(head,0.011,Vector3(side*0.068,0.025,-0.178),material(Color("263431")),Vector3(1,1,0.4))
		box(head,Vector3(0.061,0.012,0.012),Vector3(side*0.068,0.065,-0.17),violet)
	ball(head,0.025,Vector3(0,-0.015,-0.185),skin,Vector3(0.65,1.2,1.1))
	box(head,Vector3(0.055,0.009,0.008),Vector3(0,-0.085,-0.164),material(Color("815f51")))
	ball(head,0.205,Vector3(0,0.125,0),violet,Vector3(0.98,0.23,0.91))
	ball(head,0.212,Vector3(0,0.18,0),silver,Vector3(1,0.44,0.93))
	for i in range(20):
		var angle=i*2.39996
		var cone=CylinderMesh.new()
		cone.top_radius=0
		cone.bottom_radius=0.055
		cone.height=0.18+(i%3)*0.018
		cone.radial_segments=6
		var tuft=mesh(head,cone,silver,Vector3(cos(angle)*0.13,0.22+0.025*sin(i),sin(angle)*0.12))
		tuft.rotation=Vector3(sin(angle)*0.25,angle,-cos(angle)*0.35)
	# Compact rounded backpack, straps and a multi-part rifle.
	var pack_mat=material(Color("263a41"))
	box(torso,Vector3(0.25,0.31,0.10),Vector3(0,1.17,0.20),pack_mat)
	for side in [-1.0,1.0]:
		capsule(torso,0.052,0.33,Vector3(side*0.12,1.17,0.20),pack_mat)
		box(torso,Vector3(0.035,0.32,0.025),Vector3(side*0.145,1.24,-0.133),pack_mat)
	gun=Node3D.new()
	gun.position=Vector3(0.10,1.13,-0.37)
	torso.add_child(gun)
	var metal=material(Color("36444c"),0.4)
	metal.metallic=0.65
	var wood=material(Color("655043"))
	box(gun,Vector3(0.08,0.13,0.37),Vector3(0,0,-0.08),metal)
	box(gun,Vector3(0.065,0.11,0.23),Vector3(0,0,0.20),wood)
	box(gun,Vector3(0.05,0.13,0.07),Vector3(0,-0.12,-0.02),metal)
	box(gun,Vector3(0.07,0.06,0.22),Vector3(0,0,-0.34),wood)
	var barrel=CylinderMesh.new()
	barrel.top_radius=0.018
	barrel.bottom_radius=0.021
	barrel.height=0.30
	var barrel_mesh=mesh(gun,barrel,metal,Vector3(0,0.025,-0.57))
	barrel_mesh.rotation.x=PI/2
	box(gun,Vector3(0.025,0.05,0.025),Vector3(0,0.065,-0.50),metal)
	for node in find_children("*","MeshInstance3D",true,false):
		node.visibility_range_end=145.0
	animate(Vector3.ZERO,true,false,0.016)

func apply_color(color:Color):
	if shirt:
		shirt.albedo_color=color

func configure(bot:bool,index:int):
	if bot:
		var colors=[Color("839b8a"),Color("8096a7"),Color("ad9b7b"),Color("9687a1"),Color("748962")]
		apply_color(colors[index%colors.size()])

func set_aim_pitch(value:float):
	pitch=value

func aim_arm(index:int,target:Vector3):
	var start=shoulders[index].position
	var delta=target-start
	var length=clampf(delta.length(),0.04,0.54)
	var direction=delta.normalized()
	var along=(0.29*0.29+length*length-0.26*0.26)/(2*length)
	var offset=sqrt(maxf(0,0.29*0.29-along*along))
	var side=-1.0 if index==0 else 1.0
	var pole=Vector3(side*0.8,-0.4,0.25)
	pole=(pole-direction*pole.dot(direction)).normalized()
	var joint=start+direction*along+pole*offset
	shoulders[index].quaternion=Quaternion(Vector3.DOWN,(joint-start).normalized())
	var lower=shoulders[index].basis.inverse()*(start+direction*length-joint)
	elbows[index].quaternion=Quaternion(Vector3.DOWN,lower.normalized())

func animate(velocity:Vector3,on_floor:bool,crouching:bool,delta:float,aiming:bool=false):
	if not is_instance_valid(torso):
		return
	var speed=Vector2(velocity.x,velocity.z).length()
	blend=lerpf(blend,minf(1,speed/4.5),1-exp(-delta*12))
	crouch=lerpf(crouch,1.0 if crouching else 0.0,1-exp(-delta*12))
	phase+=delta*(8.5+speed*1.2)
	torso.position.y=-0.42*crouch+(sin(phase*2)*0.015*blend if on_floor else 0.0)
	torso.rotation.x=lerpf(torso.rotation.x,0.04*blend if on_floor else -0.05,1-exp(-delta*10))
	head.rotation.x=pitch*0.45
	for i in range(2):
		var stride=sin(phase+i*PI)*0.55*blend
		hips[i].rotation.x=lerpf(stride,-1.1,crouch)
		knees[i].rotation.x=lerpf(maxf(0,-sin(phase+i*PI))*0.8*blend,2.1,crouch)
		if not on_floor:
			hips[i].rotation.x=-0.25+(0.15 if i else -0.15)
			knees[i].rotation.x=0.45 if velocity.y>0 else 0.2
		feet[i].rotation.x=-hips[i].rotation.x-knees[i].rotation.x
	gun.position.y=1.13-(0.03 if aiming else 0.0)
	gun.rotation.x=pitch*0.6
	aim_arm(0,Vector3(-0.02,1.13,-0.62))
	aim_arm(1,Vector3(0.12,1.07,-0.35))
