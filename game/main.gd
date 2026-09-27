extends Node2D
## Two squads fight across the generated map. Right-click moves the blue squad.
## Art is loaded straight from PNGs at runtime so the project needs no import step.

const ART := "res://art/"
const STATS := {
	"rifle":  {"hp": 40.0,  "speed": 22.0, "range": 72.0,  "cd": 0.9, "dmg": 6.0,  "frames": 4},
	"rocket": {"hp": 40.0,  "speed": 19.0, "range": 100.0, "cd": 2.6, "dmg": 26.0, "frames": 4},
	"hero":   {"hp": 120.0, "speed": 24.0, "range": 84.0,  "cd": 0.55, "dmg": 9.0, "frames": 4},
	"tank":   {"hp": 240.0, "speed": 24.0, "range": 125.0, "cd": 2.3, "dmg": 34.0, "frames": 3},
}
const SIGHT := 160.0

var tex := {}
var units: Array = []
var tracers: Array = []
var rockets: Array = []
var puffs: Array = []
var layers := {}


func _ready() -> void:
	seed(4)  # same battle every run, so recordings are reproducible
	for name in ["ground", "decals", "under", "shadows", "units", "canopy", "fx", "over"]:
		var n := Node2D.new()
		add_child(n)
		layers[name] = n
	layers.under.draw.connect(_draw_under)
	layers.over.draw.connect(_draw_over)

	var g := Sprite2D.new()
	g.texture = _tex("ground")
	g.centered = false
	layers.ground.add_child(g)

	for p in [Vector2(360, 150), Vector2(354, 111), Vector2(368, 186)]:
		_prop("sandbags", p, 0.0, layers.decals, true)
	var trees := [Vector2(40, 40), Vector2(130, 70), Vector2(205, 30), Vector2(300, 60), Vector2(440, 40),
		Vector2(90, 230), Vector2(250, 240), Vector2(330, 225), Vector2(455, 245), Vector2(180, 215)]
	for i in trees.size():
		_prop("tree_a" if i % 2 == 0 else "tree_b", trees[i], i * 1.3, layers.canopy, true)

	for spec in [["hero", -8, 0], ["rifle", 0, -14], ["rifle", 0, 14], ["rifle", -14, -26], ["rocket", -14, 26], ["tank", -40, 0]]:
		var x: float = 90.0 + spec[1]
		_spawn(spec[0], "blue", Vector2(x, _road_y(x) + spec[2]), Vector2(470, _road_y(470)))
	for spec in [["rifle", 385, 146], ["rifle", 379, 108], ["rifle", 392, 184], ["rocket", 400, 128], ["tank", 440, 160]]:
		var p := Vector2(spec[1], spec[2])
		_spawn(spec[0], "red", p, p)


func _road_y(x: float) -> float:
	return 150.0 + 34.0 * sin(x / 95.0) + 12.0 * sin(x / 31.0)


func _tex(name: String) -> Texture2D:
	if not tex.has(name):
		var img := Image.load_from_file(ProjectSettings.globalize_path(ART + name + ".png"))
		tex[name] = ImageTexture.create_from_image(img)
	return tex[name]


func _sprite(name: String, frames := 1) -> Sprite2D:
	var s := Sprite2D.new()
	s.texture = _tex(name)
	s.hframes = frames
	return s


func _shadow_of(src: Sprite2D, offset: Vector2) -> Sprite2D:
	var s := Sprite2D.new()
	s.texture = src.texture
	s.hframes = src.hframes
	s.modulate = Color(0, 0, 0, 0.33)
	s.set_meta("offset", offset)
	layers.shadows.add_child(s)
	return s


func _prop(name: String, pos: Vector2, rot: float, layer: Node2D, shadow: bool) -> void:
	var s := _sprite(name)
	s.position = pos
	s.rotation = rot
	layer.add_child(s)
	if shadow:
		var sh := _shadow_of(s, Vector2(3, 3))
		sh.position = pos + Vector2(3, 3)
		sh.rotation = rot


func _spawn(kind: String, team: String, pos: Vector2, goal: Vector2) -> void:
	var st: Dictionary = STATS[kind]
	var u := {
		"kind": kind, "team": team, "pos": pos, "goal": goal, "heading": 0.0 if team == "blue" else PI,
		"hp": st.hp, "cd": randf() * st.cd, "anim": randf(), "fire_t": 0.0, "alive": true, "ordered": false,
	}
	if kind == "tank":
		u.body = _sprite("tank_%s_hull" % team, 3)
		u.turret = _sprite("tank_%s_turret" % team, 2)
		u.turret_rot = u.heading
		layers.units.add_child(u.body)
		layers.units.add_child(u.turret)
		u.turret_shadow = _shadow_of(u.turret, Vector2(2, 2))
	else:
		u.body = _sprite("%s_%s_walk" % [kind, team], 4)
		u.walk_tex = u.body.texture
		u.fire_tex = _tex("%s_%s_fire" % [kind, team])
		layers.units.add_child(u.body)
	u.shadow = _shadow_of(u.body, Vector2(2, 2))
	units.append(u)


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_RIGHT:
		var target := get_global_mouse_position()
		var squad := units.filter(func(u): return u.alive and u.team == "blue")
		for i in squad.size():
			var ring := Vector2.from_angle(i * TAU / squad.size()) * (0.0 if i == 0 else 16.0)
			squad[i].goal = target + ring
			squad[i].ordered = true


func _process(dt: float) -> void:
	for u in units:
		if u.alive:
			_think(u, dt)
		_sync(u)
	_separate()
	_update_rockets(dt)
	for t in tracers:
		t.life -= dt
	tracers = tracers.filter(func(t): return t.life > 0)
	for p in puffs:
		p.life -= dt
		p.pos += p.vel * dt
	puffs = puffs.filter(func(p): return p.life > 0)
	for u in units:  # burning wrecks keep smoking
		if not u.alive and u.kind == "tank" and randf() < dt * 6:
			puffs.append({"pos": u.pos + Vector2(randf_range(-4, 4), randf_range(-4, 4)), "vel": Vector2(6, -10), "life": 1.6, "max": 1.6, "r": 3.0})
	layers.under.queue_redraw()
	layers.over.queue_redraw()


func _nearest_enemy(u: Dictionary):
	var best = null
	var best_d := SIGHT
	for o in units:
		if o.alive and o.team != u.team:
			var d: float = u.pos.distance_to(o.pos)
			if d < best_d:
				best_d = d
				best = o
	return best


func _think(u: Dictionary, dt: float) -> void:
	var st: Dictionary = STATS[u.kind]
	u.fire_t = max(0.0, u.fire_t - dt)
	u.cd -= dt
	var target = _nearest_enemy(u)
	if u.ordered and u.pos.distance_to(u.goal) < 6:
		u.ordered = false
	var in_range: bool = target != null and u.pos.distance_to(target.pos) <= st.range
	if in_range and not u.ordered:
		var aim: float = (target.pos - u.pos).angle()
		if u.kind == "tank":
			u.turret_rot = rotate_toward(u.turret_rot, aim, dt * 2.0)
			if u.cd <= 0 and absf(angle_difference(u.turret_rot, aim)) < 0.08:
				_fire(u, target)
		else:
			u.heading = rotate_toward(u.heading, aim, dt * 8.0)
			if u.cd <= 0 and absf(angle_difference(u.heading, aim)) < 0.2:
				_fire(u, target)
		return
	var dest: Vector2 = u.goal
	if target != null and not u.ordered:
		dest = target.pos
	if u.pos.distance_to(dest) < 4:
		return
	var want: float = (dest - u.pos).angle()
	var turn := 1.8 if u.kind == "tank" else 9.0
	u.heading = rotate_toward(u.heading, want, dt * turn)
	if absf(angle_difference(u.heading, want)) < 0.6:
		u.pos += Vector2.from_angle(u.heading) * st.speed * dt
		u.anim += dt
	if u.kind == "tank":
		u.turret_rot = rotate_toward(u.turret_rot, u.heading if target == null else (target.pos - u.pos).angle(), dt * 2.0)


func _muzzle(u: Dictionary) -> Vector2:
	if u.kind == "tank":
		return u.pos + Vector2.from_angle(u.turret_rot) * 15.0
	return u.pos + Vector2.from_angle(u.heading) * 7.0 + Vector2.from_angle(u.heading + PI / 2) * 2.0


func _fire(u: Dictionary, target: Dictionary) -> void:
	var st: Dictionary = STATS[u.kind]
	u.cd = st.cd * randf_range(0.85, 1.15)
	u.fire_t = 0.12
	var m := _muzzle(u)
	_flash(m, u.turret_rot if u.kind == "tank" else u.heading, 1.6 if u.kind == "tank" else 1.0)
	if u.kind == "rocket":
		rockets.append({"pos": m, "target": target, "dmg": st.dmg, "team": u.team})
		return
	var miss := Vector2(randf_range(-5, 5), randf_range(-5, 5))
	tracers.append({"a": m, "b": target.pos + miss, "life": 0.12 if u.kind == "tank" else 0.07,
		"w": 2.0 if u.kind == "tank" else 1.0})
	if u.kind == "tank":
		_boom(target.pos + miss * 0.4, 0.55)
	_hit(target, st.dmg * (0.25 if target.kind == "tank" and u.kind != "tank" else 1.0))


func _update_rockets(dt: float) -> void:
	for r in rockets:
		var to: Vector2 = r.target.pos - r.pos
		r.pos += to.normalized() * min(to.length(), 150.0 * dt)
		puffs.append({"pos": r.pos, "vel": Vector2(randf_range(-4, 4), randf_range(-4, 4)), "life": 0.6, "max": 0.6, "r": 1.6})
		if to.length() < 3:
			_boom(r.pos, 0.8)
			if r.target.alive:
				_hit(r.target, r.dmg * (1.6 if r.target.kind == "tank" else 1.0))
			r.done = true
	rockets = rockets.filter(func(r): return not r.get("done", false))


func _hit(t: Dictionary, dmg: float) -> void:
	if not t.alive:
		return
	t.hp -= dmg
	if t.hp > 0:
		return
	t.alive = false
	if t.kind == "tank":
		_boom(t.pos, 1.4)
		_prop("crater", t.pos, randf() * TAU, layers.decals, false)
		for s in [t.body, t.turret]:
			s.modulate = Color(0.28, 0.25, 0.22)
			s.frame = 0
	else:
		var tw := create_tween()
		tw.tween_property(t.body, "modulate:a", 0.0, 1.5).set_delay(0.6)
		tw.parallel().tween_property(t.shadow, "modulate:a", 0.0, 1.5).set_delay(0.6)
		t.body.modulate = Color(0.55, 0.55, 0.55)


func _flash(pos: Vector2, rot: float, scale_k: float) -> void:
	var f := _sprite("flash", 2)
	f.position = pos
	f.rotation = rot
	f.scale = Vector2.ONE * scale_k
	layers.fx.add_child(f)
	var tw := create_tween()
	tw.tween_property(f, "frame", 1, 0.04)
	tw.tween_callback(f.queue_free).set_delay(0.04)


func _boom(pos: Vector2, scale_k: float) -> void:
	var e := _sprite("explosion", 8)
	e.position = pos
	e.scale = Vector2.ONE * scale_k
	e.rotation = randf() * TAU
	layers.fx.add_child(e)
	var tw := create_tween()
	tw.tween_property(e, "frame", 7, 0.6)
	tw.tween_callback(e.queue_free)


func _sync(u: Dictionary) -> void:
	var b: Sprite2D = u.body
	b.position = u.pos
	b.rotation = u.heading
	if u.alive:
		if u.kind == "tank":
			b.frame = int(u.anim * 12) % 3
			u.turret.frame = 1 if u.fire_t > 0.06 else 0
		elif u.fire_t > 0:
			b.texture = u.fire_tex
			b.hframes = 2
			b.frame = 1 if u.fire_t > 0.06 else 0
		else:
			b.texture = u.walk_tex
			b.hframes = 4
			b.frame = int(u.anim * 8) % 4
	var sh: Sprite2D = u.shadow
	sh.texture = b.texture
	sh.hframes = b.hframes
	sh.frame = b.frame
	sh.position = u.pos + sh.get_meta("offset")
	sh.rotation = b.rotation
	if u.kind == "tank":
		u.turret.position = u.pos - Vector2.from_angle(u.heading) * 2.0
		u.turret.rotation = u.turret_rot
		u.turret_shadow.frame = u.turret.frame
		u.turret_shadow.position = u.turret.position + Vector2(2, 2)
		u.turret_shadow.rotation = u.turret_rot


func _separate() -> void:
	var live := units.filter(func(u): return u.alive)
	for i in live.size():
		for j in range(i + 1, live.size()):
			var a: Dictionary = live[i]
			var b: Dictionary = live[j]
			var min_d := 22.0 if a.kind == "tank" or b.kind == "tank" else 9.0
			var d: Vector2 = b.pos - a.pos
			if d.length() < min_d and d.length() > 0.01:
				var push := d.normalized() * (min_d - d.length()) * 0.5
				a.pos -= push
				b.pos += push


func _draw_under() -> void:
	for u in units:
		if u.alive and u.team == "blue":
			var r := 13.0 if u.kind == "tank" else 7.0
			_ellipse(layers.under, u.pos + Vector2(0, 1), r, r * 0.8, Color(0.45, 1.0, 0.45, 0.8))


func _ellipse(n: Node2D, c: Vector2, rx: float, ry: float, col: Color) -> void:
	var pts := PackedVector2Array()
	for i in 21:
		var a := i * TAU / 20.0
		pts.append(c + Vector2(cos(a) * rx, sin(a) * ry))
	n.draw_polyline(pts, col, 1.0)


func _draw_over() -> void:
	var o: Node2D = layers.over
	for p in puffs:
		var k: float = p.life / p.max
		o.draw_circle(p.pos, p.r * (1.6 - k * 0.6), Color(0.55, 0.53, 0.5, 0.55 * k))
	for r in rockets:
		o.draw_circle(r.pos, 1.5, Color(1, 0.85, 0.4))
	for t in tracers:
		o.draw_line(t.a, t.b, Color(1, 0.9, 0.5, 0.9), t.w)
	for u in units:
		if not u.alive:
			continue
		var st: Dictionary = STATS[u.kind]
		var w := 20.0 if u.kind == "tank" else 10.0
		var top: Vector2 = u.pos + Vector2(-w / 2, -16 if u.kind == "tank" else -10)
		o.draw_rect(Rect2(top, Vector2(w, 2)), Color(0.08, 0.08, 0.08, 0.85))
		var frac: float = clamp(u.hp / st.hp, 0.0, 1.0)
		var col := Color(0.4, 0.95, 0.4) if frac > 0.5 else Color(0.95, 0.8, 0.3) if frac > 0.25 else Color(0.95, 0.3, 0.25)
		o.draw_rect(Rect2(top, Vector2(w * frac, 2)), col)
