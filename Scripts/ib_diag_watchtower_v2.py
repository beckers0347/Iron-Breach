import unreal
def log(msg):
    unreal.log(f"IBPY: {msg}")

es = unreal.EditorActorSubsystem()
actors = es.get_all_level_actors()

# Watch Tower door frame is at approx (13494, -2312, 78) -- search a generous radius
center = unreal.Vector(13494.0, -2312.5, 400.0)
radius = 1500.0

near = []
for a in actors:
    loc = a.get_actor_location()
    d = ((loc.x-center.x)**2 + (loc.y-center.y)**2)**0.5
    if d <= radius:
        near.append((d, a))

near.sort(key=lambda t: t[0])
log(f"=== {len(near)} actors within {radius}cm of Watch Tower center ===")
for d, a in near:
    label = a.get_actor_label()
    cls = a.get_class().get_name()
    log(f"  d={d:.0f} {label} ({cls})")
log("=== done ===")
