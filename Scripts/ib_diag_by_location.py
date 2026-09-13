import unreal
def log(msg):
    unreal.log(f"IBPY: {msg}")

es = unreal.EditorActorSubsystem()
actors = es.get_all_level_actors()

# (name, center xy, radius)
TARGETS = [
    ("06_Mess Hall", unreal.Vector(3000.0, 7806.5, 500.0), 1500.0),
    ("07_Armory", unreal.Vector(9424.264069, -2575.735931, 300.0), 1500.0),
    ("08_Command & Comms", unreal.Vector(3306.5, -1500.0, 700.0), 1500.0),
]

for name, center, radius in TARGETS:
    near = []
    for a in actors:
        loc = a.get_actor_location()
        d = ((loc.x-center.x)**2 + (loc.y-center.y)**2)**0.5
        if d <= radius:
            near.append((d, a))
    near.sort(key=lambda t: t[0])
    log(f"=== {name}: {len(near)} actors within {radius}cm ===")
    for d, a in near:
        label = a.get_actor_label()
        cls = a.get_class().get_name()
        log(f"  d={d:.0f} {label} ({cls})")
log("=== all done ===")
