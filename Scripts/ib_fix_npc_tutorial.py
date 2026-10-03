"""
IBPY: ib_fix_npc_tutorial.py

Sets up the M1 opening in CarrowGateGarrison_BoulderShore3 (or the open level):

  * Everything starts INSIDE the Barracks: PlayerStart in the room facing the rear wall; Static is already there
    (Act I opens on him), Rhodes enters at "Lt. Rhodes enters the watch room." and Bricks at the stand-to order.
  * NPCs use SK_Idris_Own + animations retargeted from the Infantry skeleton (run ib_build_npc_retarget.py once
    first): idle while standing, walk while the guide route moves them. This removes the twisted feet and the
    hands clipping into the thighs that the shared-skeleton mesh produced.
  * Guide route: Rhodes leads. He goes out of the Barracks' nose door, around the building, then to the muster;
    Bricks and Static follow. Starts when Act I completes.
  * Act chain: Act I plays (its start delay was 10,000,000 s), Acts II-V chain off the act before them.

Run in the editor (not PIE) then File > Save All.  py "X:/IronBreach/Scripts/ib_fix_npc_tutorial.py"
"""
import math
import unreal

RHODES, BRICKS, STATIC = "NPC_Rhodes_PLACEHOLDER", "NPC_Okafor_Bricks_PLACEHOLDER", "NPC_Yun_Static_PLACEHOLDER"
MESH_FORWARD_YAW = 90.0     # NPC meshes face +Y like the UE mannequin they are retargeted from
IDLE_STANCE_YAW = 23.0      # MM_Idle stands with the body turned 23 degrees; undone when placing NPCs
OWN_MESH = "/Game/Characters/NPCs/MsIdris/SK_Idris_Own"
RET = "/Game/Characters/NPCs/MsIdris/Retargeted/"
BARRACKS_LABEL = "Barracks"
# Barracks frame, cm from its centre: +x toward the rear wall, the nose door is at -x, +y to the right of +x.
PLAYER_LOCAL = (-900.0, 0.0)
STAGE_LOCAL = {STATIC: (200.0, -300.0), RHODES: (-1350.0, 0.0), BRICKS: (150.0, 500.0)}


def log(m):
    unreal.log("IBPY: " + m)


def by_label():
    return {a.get_actor_label(): a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()}


def face_yaw(dx, dy):
    """Actor yaw so a +Y-facing mesh looks along (dx, dy)."""
    return math.degrees(math.atan2(dy, dx)) - MESH_FORWARD_YAW - IDLE_STANCE_YAW


def barracks_frame(actors):
    b = actors.get(BARRACKS_LABEL)
    if not b:
        return None
    o, e = b.get_actor_bounds(False)
    yaw = b.get_actor_rotation().yaw
    f = (math.cos(math.radians(yaw)), math.sin(math.radians(yaw)))
    r = (-f[1], f[0])
    floor = b.get_actor_location().z + 5.0

    def world(lx, ly):
        return o.x + f[0] * lx + r[0] * ly, o.y + f[1] * lx + r[1] * ly
    return world, floor, f, e


def stage(actors, fr):
    world, floor, f, e = fr
    px, py = world(*PLAYER_LOCAL)
    ps = next((a for a in actors.values() if a.get_class().get_name() == "PlayerStart"), None)
    if ps:
        look = math.degrees(math.atan2(f[1], f[0]))
        ps.set_actor_location(unreal.Vector(px, py, floor + 110.0), False, True)
        ps.set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=look), False)
        log("  PlayerStart -> inside the Barracks (%.0f, %.0f, %.0f) yaw %.0f" % (px, py, floor + 110.0, look))
    for label, (lx, ly) in STAGE_LOCAL.items():
        a = actors.get(label)
        if not a:
            log("  missing " + label)
            continue
        x, y = world(lx, ly)
        a.set_actor_location(unreal.Vector(x, y, floor), False, True)
        a.set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=face_yaw(px - x, py - y)), False)
        log("  %s placed at (%.0f, %.0f, %.0f)" % (label, x, y, floor))


CHAR_OF = {"NPC_Idris": "Idris", "NPC_Rhodes_PLACEHOLDER": "Rhodes", "NPC_Rhodes_ACT5": "Rhodes",
           "NPC_Okafor_Bricks_PLACEHOLDER": "Bricks", "NPC_Okafor_Bricks_ACT5": "Bricks",
           "NPC_Yun_Static_PLACEHOLDER": "Static", "NPC_Yun_Static_ACT5": "Static"}


def retarget_setup(actors):
    """Each NPC gets its OWN character mesh + its own retargeted idle (animations are per skeleton)."""
    anims = {}
    for label, ch in CHAR_OF.items():
        a = actors.get(label)
        mesh = unreal.load_asset("/Game/Characters/NPCs/%s/SKN_%s" % (ch, ch))
        idle = unreal.load_asset("/Game/Characters/NPCs/%s/Retargeted/Loco_Idle_%s" % (ch, ch))
        walk = unreal.load_asset("/Game/Characters/NPCs/%s/Retargeted/Loco_Walking_%s" % (ch, ch))
        if not a or not (mesh and idle and walk):
            log("  skip %s (actor or assets missing)" % label)
            continue
        c = a.skeletal_mesh_component
        c.set_skinned_asset_and_update(mesh)
        c.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
        d = c.get_editor_property("animation_data")
        d.set_editor_property("anim_to_play", idle)
        d.set_editor_property("saved_looping", True)
        d.set_editor_property("saved_playing", True)
        c.set_editor_property("animation_data", d)
        anims[label] = (a, idle, walk)
        log("  %s: SK_%s + retargeted idle" % (label, ch))
    return anims


def path_check(route_pts):
    """Report anywhere along the route with no floor under it (that is how the route 'walked off the edge')."""
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    bad = []
    for (x0, y0), (x1, y1) in zip(route_pts, route_pts[1:]):
        n = max(2, int(math.hypot(x1 - x0, y1 - y0) / 150.0))
        for k in range(n + 1):
            x, y = x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n
            hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, 700), unreal.Vector(x, y, 100),
                                                         unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [], unreal.DrawDebugTrace.NONE, True)
            if not hit:
                bad.append((round(x), round(y)))
    log("  route floor check: %s" % ("every sample has floor" if not bad else "NO FLOOR at %s" % bad[:8]))
    return bad


def wire(actors, fr, anims):
    route = next((a for a in actors.values() if a.get_class().get_name() == "IBGuideRoute"), None)
    act1 = next((a for a in actors.values() if a.get_class().get_name() == "Act1BarracksDirector"), None)
    if route:
        route.set_editor_property("guide_actor", actors.get(RHODES))
        route.set_editor_property("followers", [actors.get(BRICKS), actors.get(STATIC)])
        route.set_editor_property("facing_yaw_offset", -MESH_FORWARD_YAW)
        route.set_editor_property("debug_draw", False)
        route.set_editor_property("auto_start", False)
        if act1:
            route.set_editor_property("start_after_act1", act1)
        entries = []
        for label, (a, idle, walk) in anims.items():
            e = unreal.IBGuideNPCAnims()
            e.set_editor_property("actor", a)
            e.set_editor_property("idle", idle)
            e.set_editor_property("walk", walk)
            entries.append(e)
        route.set_editor_property("npc_animations", entries)
        if fr:
            world, floor, f, e = fr
            old = list(route.get_editor_property("waypoints"))
            muster = old[-1] if old else None
            # out of the nose door, then clear of the building's corner, then the long leg to the muster
            corners = [world(-e.x - 400.0, 0.0), world(-e.x - 400.0, e.y + 900.0)]
            new = []
            for (x, y) in corners:
                w = unreal.IBGuideWaypoint()
                w.set_editor_property("location", unreal.Vector(x, y, floor))
                w.set_editor_property("wait_for_player_radius", 700.0)
                new.append(w)
            if muster:
                new.append(muster)
            route.set_editor_property("waypoints", new)
            pts = [world(*PLAYER_LOCAL)] + corners + [(muster.get_editor_property("location").x, muster.get_editor_property("location").y)] if muster else corners
            path_check(pts)
            log("  route: %d waypoints (door %s, corner %s, muster)" % (len(new), tuple(round(v) for v in corners[0]), tuple(round(v) for v in corners[1])))
        log("  route: guide=Rhodes, followers=[Bricks, Static], starts after Act I")
    else:
        log("  WARNING: no IBGuideRoute in this level")
    if act1:
        cues = []
        for label, ev in ((STATIC, None), (RHODES, "RhodesEnters"), (BRICKS, "StandToOrder")):
            c = unreal.Act1NPCCue()
            c.set_editor_property("actor", actors.get(label))
            c.set_editor_property("reveal_on_event", unreal.Name(ev) if ev else unreal.Name("None"))
            cues.append(c)
        act1.set_editor_property("npc_cues", cues)
        beats = list(act1.get_editor_property("beats"))
        for b in beats:
            if "Rhodes enters" in str(b.get_editor_property("text")):
                b.set_editor_property("scripted_event_tag", unreal.Name("RhodesEnters"))
        act1.set_editor_property("beats", beats)
        act1.set_editor_property("initial_delay", 1.0)
        act1.set_editor_property("auto_start", True)
        log("  Act I: Static from the start, Rhodes on RhodesEnters, Bricks on StandToOrder; start delay 1 s")
    chain = [("Act2EscalationDirector", "Act1BarracksDirector"), ("Act3ContactDirector", "Act2EscalationDirector"),
             ("Act4DeepWaterDirector", "Act3ContactDirector"), ("Act5RetreatDirector", "Act4DeepWaterDirector")]
    by_cls = {a.get_class().get_name(): a for a in actors.values()}
    for cls, prev in chain:
        if by_cls.get(cls) and by_cls.get(prev):
            by_cls[cls].set_editor_property("previous_act_director", by_cls[prev])


def main():
    log("=== ib_fix_npc_tutorial ===")
    actors = by_label()
    fr = barracks_frame(actors)
    if fr:
        stage(actors, fr)
    else:
        log("  WARNING: no 'Barracks' actor in this level")
    anims = retarget_setup(actors)
    wire(actors, fr, anims)
    log("=== done (save the level) ===")


main()
