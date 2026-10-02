#include "Skills/IBSkillTypes.h"

namespace IBSkills
{
const TArray<FIBSkillNode>& Catalog()
{
    static const TArray<FIBSkillNode> Nodes = []
    {
        TArray<FIBSkillNode> Result;
        auto Add = [&](EIBOperativeClass Class, const TCHAR* Id, const TCHAR* Name, const TCHAR* Description,
            EIBSkillKind Kind, EIBSkillIcon Icon, EIBKitEffect Effect, FVector2D Position, int32 Cost=0, int32 Level=1) -> FIBSkillNode&
        {
            FIBSkillNode& Node = Result.AddDefaulted_GetRef();
            Node.Class=Class; Node.Id=Id; Node.Name=FText::FromString(Name); Node.Description=FText::FromString(Description);
            Node.Kind=Kind; Node.Icon=Icon; Node.Cost=Cost; Node.Level=Level; Node.Position=Position;
            Node.Spec.DisplayName=Node.Name; Node.Spec.Description=Node.Description; Node.Spec.Effect=Effect;
            return Node;
        };
        auto Variant = [&](const TCHAR* Parent, const TCHAR* Id, const TCHAR* Name, const TCHAR* Description,
            FVector2D Offset, int32 Cost, int32 Level) -> FIBSkillNode&
        {
            const FIBSkillNode* Base=Result.FindByPredicate([&](const FIBSkillNode& N) { return N.Id==Parent; });
            check(Base);
            FIBSkillNode Copy=*Base; Copy.Parent=Parent; Copy.Id=Id; Copy.Name=FText::FromString(Name);
            Copy.Description=FText::FromString(Description); Copy.Position+=Offset; Copy.Cost=Cost; Copy.Level=Level;
            Copy.Spec.DisplayName=Copy.Name; Copy.Spec.Description=Copy.Description;
            return Result.Add_GetRef(Copy);
        };
        // Serialized Bellringer identities become Saber; Picket becomes Sentinel; Breaker becomes Guardian.
        const auto Saber=EIBOperativeClass::Bellringer, Sentinel=EIBOperativeClass::Picket, Guardian=EIBOperativeClass::Breaker;
        auto& Dash=Add(Saber,TEXT("saber.vector"),TEXT("VECTOR DASH"),TEXT("Burst in your movement direction. Use it to cross exposed ground or leave an incoming strike. Clean Vector is the standard dash."),EIBSkillKind::Signature,EIBSkillIcon::Dash,EIBKitEffect::Dash,{.15,.74});
        Dash.Spec.Cooldown=6; Dash.Spec.Strength=1600; Dash.Spec.Duration=.2f;
        auto& Charge=Add(Saber,TEXT("saber.breach"),TEXT("BREACH CHARGE"),TEXT("Lunge forward, then release a concussive strike into enemies ahead. Aim at exposed armor seams; the normal kaiju armor rules still apply."),EIBSkillKind::Tactical,EIBSkillIcon::Charge,EIBKitEffect::ConeStrike,{.36,.58});
        Charge.Spec.Cooldown=12; Charge.Spec.Duration=.2f; Charge.Spec.Strength=1300; Charge.Spec.Range=420; Charge.Spec.Radius=230; Charge.Spec.Damage=65;
        auto& Sweep=Add(Saber,TEXT("saber.sweep"),TEXT("KINETIC SWEEP"),TEXT("Release a circular shockwave around you. Push nearby enemies away and make room to move. Does not damage your fireteam."),EIBSkillKind::Tactical,EIBSkillIcon::Sweep,EIBKitEffect::RadialStrike,{.56,.44});
        Sweep.Spec.Cooldown=14; Sweep.Spec.Strength=650; Sweep.Spec.Radius=450; Sweep.Spec.Damage=45;
        auto& Line=Add(Saber,TEXT("saber.line"),TEXT("IMPULSE LINE"),TEXT("Fire a movement tether at a surface and launch toward it. Trades a tactical slot for rapid repositioning; requires an anchor within reach."),EIBSkillKind::Tactical,EIBSkillIcon::Grapple,EIBKitEffect::Grapple,{.74,.3},3,7);
        Line.Spec.Cooldown=8; Line.Spec.Range=2800; Line.Spec.Strength=2200;
        auto& Redline=Add(Saber,TEXT("saber.redline"),TEXT("REDLINE"),TEXT("Break an encirclement with a powerful kinetic pulse and a short damage-reduction window. Commit when the surrounding enemies are close."),EIBSkillKind::Overdrive,EIBSkillIcon::Overdrive,EIBKitEffect::RadialStrike,{.9,.16},4,8);
        Redline.Spec.Cooldown=70; Redline.Spec.Radius=850; Redline.Spec.Damage=130; Redline.Spec.Strength=1200; Redline.Spec.Duration=6; Redline.Spec.DamageTakenScale=.65f;
        auto& Long=Variant(TEXT("saber.vector"),TEXT("saber.long"),TEXT("LONG VECTOR"),TEXT("A longer, faster dash with a longer recovery. Covers wider danger zones, but commits you farther from cover."),{-.08,-.24},2,3); Long.Spec.Strength=2300; Long.Spec.Cooldown=9;
        auto& Return=Variant(TEXT("saber.vector"),TEXT("saber.return"),TEXT("RETURN VECTOR"),TEXT("Leave an anchor when you dash. Press the signature key again within three seconds to return, provided the path is clear. Recovery begins on the first dash."),{.12,.16},2,5); Return.Spec.Effect=EIBKitEffect::ReturnDash; Return.Spec.Cooldown=10;
        auto& BreachWide=Variant(TEXT("saber.breach"),TEXT("saber.fan"),TEXT("BREACH FAN"),TEXT("Widen the impact to catch a group, at the cost of damage to each target."),{-.06,-.24},3,10); BreachWide.Spec.Radius=430; BreachWide.Spec.Damage=45;
        auto& BreachFocus=Variant(TEXT("saber.breach"),TEXT("saber.lance"),TEXT("BREACH LANCE"),TEXT("Focus the charge into a narrower strike with longer reach. Rewards careful alignment with a priority target."),{.13,.18},3,12); BreachFocus.Spec.Radius=140; BreachFocus.Spec.Range=700; BreachFocus.Spec.Damage=85;
        auto& Ring=Variant(TEXT("saber.sweep"),TEXT("saber.ring"),TEXT("SHOCK RING"),TEXT("Expand the sweep's radius and push, trading some damage for room to escape."),{-.06,-.24},3,14); Ring.Spec.Radius=700; Ring.Spec.Damage=30; Ring.Spec.Strength=1000;
        auto& Focus=Variant(TEXT("saber.sweep"),TEXT("saber.focus"),TEXT("FOCUSED SWEEP"),TEXT("Concentrate the wave into a forward arc. Higher damage, but no protection from enemies behind you."),{.13,.18},3,16); Focus.Spec.Effect=EIBKitEffect::ConeStrike; Focus.Spec.Strength=0; Focus.Spec.Duration=.05f; Focus.Spec.Range=500; Focus.Spec.Radius=300; Focus.Spec.Damage=80;
        auto& FastLine=Variant(TEXT("saber.line"),TEXT("saber.quickline"),TEXT("QUICK LINE"),TEXT("A short tether with faster recovery. Best for moving between nearby cover."),{.13,.16},3,18); FastLine.Spec.Range=1600; FastLine.Spec.Cooldown=5;
        auto& HighLine=Variant(TEXT("saber.line"),TEXT("saber.longline"),TEXT("LONG LINE"),TEXT("Reach distant anchor points. The longer cooldown makes a missed anchor more costly."),{-.08,-.2},4,22); HighLine.Spec.Range=4200; HighLine.Spec.Cooldown=12;
        auto& WideRed=Variant(TEXT("saber.redline"),TEXT("saber.breakout"),TEXT("BREAKOUT"),TEXT("A wider Redline pulse pushes a larger group away. Gives up its defensive window for immediate space."),{-.09,-.08},5,30); WideRed.Spec.Radius=1300; WideRed.Spec.DamageTakenScale=1;
        auto& HoldRed=Variant(TEXT("saber.redline"),TEXT("saber.afterburn"),TEXT("AFTERBURN"),TEXT("Trade pulse damage for a longer defensive window. Use the opening to cross a sustained line of fire."),{.07,.18},5,35); HoldRed.Spec.Damage=80; HoldRed.Spec.Duration=12;

        auto& Veil=Add(Sentinel,TEXT("sentinel.veil"),TEXT("VEIL SHIFT"),TEXT("Briefly camouflage your body and break ordinary enemies' visual tracking. Attacking ends the veil. Area attacks and kaiju strikes can still hit you."),EIBSkillKind::Signature,EIBSkillIcon::Veil,EIBKitEffect::Cloak,{.11,.5});
        Veil.Spec.Cooldown=14; Veil.Spec.Duration=3; Veil.Spec.Strength=0;
        auto& Dart=Add(Sentinel,TEXT("sentinel.dart"),TEXT("TARGETING DART"),TEXT("Place a sensor at your aim point. Nearby hostiles receive tracking markers for the fireteam while the sensor lasts; use it to track a priority target."),EIBSkillKind::Tactical,EIBSkillIcon::Dart,EIBKitEffect::DeployZone,{.36,.28});
        Dart.Spec.Cooldown=14; Dart.Spec.Duration=8; Dart.Spec.Range=3000; Dart.Spec.Radius=400; Dart.Spec.bMarksTargets=true; Dart.Spec.bPlaceAtAim=true;
        auto& Decoy=Add(Sentinel,TEXT("sentinel.decoy"),TEXT("ECHO DECOY"),TEXT("Project a false operative ahead of you. Ordinary enemies that can see it switch their attention to the echo until it is destroyed or expires. Kaiju are not forced to change targets."),EIBSkillKind::Tactical,EIBSkillIcon::Decoy,EIBKitEffect::Decoy,{.36,.72});
        Decoy.Spec.Cooldown=20; Decoy.Spec.Duration=6; Decoy.Spec.Range=500; Decoy.Spec.Radius=1800; Decoy.Spec.Damage=0;
        auto& SLine=Add(Sentinel,TEXT("sentinel.line"),TEXT("LINE BOLT"),TEXT("Tether to a visible surface to take a new firing position. Occupies one tactical slot in place of a sensor or decoy."),EIBSkillKind::Tactical,EIBSkillIcon::Grapple,EIBKitEffect::Grapple,{.6,.5},3,7);
        SLine.Spec.Cooldown=8; SLine.Spec.Range=3000; SLine.Spec.Strength=2100;
        auto& Blackout=Add(Sentinel,TEXT("sentinel.blackout"),TEXT("BLACKOUT"),TEXT("Camouflage yourself while a wide sensor field marks and slows hostiles around the activation point. Attacking ends your camouflage, while the field remains."),EIBSkillKind::Overdrive,EIBSkillIcon::Overdrive,EIBKitEffect::Cloak,{.88,.5},4,8);
        Blackout.Spec.Cooldown=75; Blackout.Spec.Duration=8; Blackout.Spec.Strength=0; Blackout.Spec.Radius=1100; Blackout.Spec.bMarksTargets=true; Blackout.Spec.SlowFactor=.65f;
        auto& Ghost=Variant(TEXT("sentinel.veil"),TEXT("sentinel.ghost"),TEXT("GHOST STEP"),TEXT("Add a short directional dash when entering the veil. Camouflage ends sooner, so choose your landing position before activating."),{.07,-.26},2,3); Ghost.Spec.Strength=1100; Ghost.Spec.Duration=2;
        auto& Silent=Variant(TEXT("sentinel.veil"),TEXT("sentinel.silent"),TEXT("SILENT VEIL"),TEXT("Stay camouflaged longer, with a longer cooldown. Attacking still ends the effect."),{.07,.28},2,5); Silent.Spec.Duration=6; Silent.Spec.Cooldown=22;
        auto& Spread=Variant(TEXT("sentinel.dart"),TEXT("sentinel.spread"),TEXT("SENSOR SPREAD"),TEXT("Cover a wider area for less time. Useful for locating a dispersed group before advancing."),{-.06,-.19},3,10); Spread.Spec.Radius=950; Spread.Spec.Duration=5;
        auto& Pin=Variant(TEXT("sentinel.dart"),TEXT("sentinel.pin"),TEXT("PINNING DART"),TEXT("A small sensor field also slows targets inside it. Precise placement matters more than coverage."),{.14,-.14},3,12); Pin.Spec.Radius=250; Pin.Spec.SlowFactor=.45f;
        auto& EchoLong=Variant(TEXT("sentinel.decoy"),TEXT("sentinel.echo"),TEXT("PERSISTENT ECHO"),TEXT("The decoy lasts longer, but takes longer to recharge. Use it to hold attention while you reposition."),{-.06,.2},3,14); EchoLong.Spec.Duration=10; EchoLong.Spec.Cooldown=28;
        auto& EchoBurst=Variant(TEXT("sentinel.decoy"),TEXT("sentinel.echo_burst"),TEXT("DISRUPTION ECHO"),TEXT("A shorter-lived decoy emits a slowing sensor field when it ends. The pulse works on nearby hostiles even when they ignore the decoy."),{.14,.15},3,16); EchoBurst.Spec.Duration=4; EchoBurst.Spec.bMarksTargets=true; EchoBurst.Spec.SlowFactor=.5f;
        auto& Short=Variant(TEXT("sentinel.line"),TEXT("sentinel.shortline"),TEXT("SHORT LINE"),TEXT("Shorten tether reach to gain a faster recharge for nearby position changes."),{.1,-.19},3,18); Short.Spec.Range=1700; Short.Spec.Cooldown=5;
        auto& Reach=Variant(TEXT("sentinel.line"),TEXT("sentinel.skyline"),TEXT("SKYLINE"),TEXT("A longer tether reaches remote overlooks. The extra reach comes with a slower recharge."),{.1,.19},4,22); Reach.Spec.Range=4400; Reach.Spec.Cooldown=12;
        auto& Web=Variant(TEXT("sentinel.blackout"),TEXT("sentinel.web"),TEXT("BLACKOUT WEB"),TEXT("Expand the sensor field and strengthen its slow, trading away your personal camouflage."),{.06,-.25},5,30); Web.Spec.Effect=EIBKitEffect::DeployZone; Web.Spec.Radius=1500; Web.Spec.SlowFactor=.4f;
        auto& Escape=Variant(TEXT("sentinel.blackout"),TEXT("sentinel.escape"),TEXT("GHOST NETWORK"),TEXT("Trade the slowing field for longer camouflage and a wide tracking pulse. Attacking still breaks concealment."),{.06,.25},5,35); Escape.Spec.Duration=12; Escape.Spec.SlowFactor=1;

        auto& Guard=Add(Guardian,TEXT("guardian.guard"),TEXT("TIMED GUARD"),TEXT("Brace for a brief window that absorbs most incoming damage. Absorbed damage charges your next Impact Discharge, up to its storage cap."),EIBSkillKind::Signature,EIBSkillIcon::Guard,EIBKitEffect::Guard,{.5,.15});
        Guard.Spec.Cooldown=6; Guard.Spec.Duration=1; Guard.Spec.DamageTakenScale=.2f; Guard.Spec.Strength=0;
        auto& Impact=Add(Guardian,TEXT("guardian.impact"),TEXT("IMPACT DISCHARGE"),TEXT("Release a close-range shockwave. Adds stored guard energy to the hit, then consumes it. You can still discharge without stored energy."),EIBSkillKind::Tactical,EIBSkillIcon::Impact,EIBKitEffect::RadialStrike,{.24,.4});
        Impact.Spec.Cooldown=12; Impact.Spec.Radius=500; Impact.Spec.Strength=900; Impact.Spec.Damage=40; Impact.Spec.bUsesGuardEnergy=true;
        auto& Ward=Add(Guardian,TEXT("guardian.surge"),TEXT("PROTECTIVE SURGE"),TEXT("Place a protective field at your feet. You and nearby infantry teammates take less damage while inside it. Leaving the field ends the protection shortly afterward."),EIBSkillKind::Tactical,EIBSkillIcon::Ward,EIBKitEffect::DeployZone,{.76,.4});
        Ward.Spec.Cooldown=22; Ward.Spec.Duration=6; Ward.Spec.Radius=650; Ward.Spec.DamageTakenScale=.65f;
        auto& Advance=Add(Guardian,TEXT("guardian.advance"),TEXT("BULWARK ADVANCE"),TEXT("Dash into position with a short protective window. Trades a tactical slot for movement under fire."),EIBSkillKind::Tactical,EIBSkillIcon::Dash,EIBKitEffect::Dash,{.5,.85},3,7);
        Advance.Spec.Cooldown=10; Advance.Spec.Strength=1450; Advance.Spec.Duration=1; Advance.Spec.DamageTakenScale=.45f;
        auto& Citadel=Add(Guardian,TEXT("guardian.citadel"),TEXT("CITADEL"),TEXT("Create a broad defensive field that protects your fireteam and slows hostiles inside it. Establish a position for a dangerous engagement."),EIBSkillKind::Overdrive,EIBSkillIcon::Overdrive,EIBKitEffect::DeployZone,{.5,.5},4,8);
        Citadel.Spec.Cooldown=80; Citadel.Spec.Duration=12; Citadel.Spec.Radius=1000; Citadel.Spec.DamageTakenScale=.4f; Citadel.Spec.SlowFactor=.7f;
        auto& Parry=Variant(TEXT("guardian.guard"),TEXT("guardian.parry"),TEXT("PERFECT GUARD"),TEXT("A shorter guard absorbs more damage. Precise timing feeds more energy into your next discharge."),{-.17,-.04},2,3); Parry.Spec.Duration=.5f; Parry.Spec.DamageTakenScale=.05f;
        auto& Brace=Variant(TEXT("guardian.guard"),TEXT("guardian.brace"),TEXT("EXTENDED BRACE"),TEXT("Brace for longer, absorbing less of each hit. Better for sustained fire than a single heavy impact."),{.17,-.04},2,5); Brace.Spec.Duration=2.5f; Brace.Spec.DamageTakenScale=.5f; Brace.Spec.Cooldown=10;
        auto& Lance=Variant(TEXT("guardian.impact"),TEXT("guardian.lance"),TEXT("IMPACT LANCE"),TEXT("Direct stored energy into a forward strike with greater reach. Gives up coverage behind you."),{-.16,-.13},3,10); Lance.Spec.Effect=EIBKitEffect::ConeStrike; Lance.Spec.Strength=0; Lance.Spec.Duration=.05f; Lance.Spec.Range=850; Lance.Spec.Radius=250; Lance.Spec.Damage=65;
        auto& Pulse=Variant(TEXT("guardian.impact"),TEXT("guardian.pulse"),TEXT("REPULSOR PULSE"),TEXT("Widen the discharge and increase its push, trading base damage for control. Stored energy still contributes damage."),{-.14,.18},3,12); Pulse.Spec.Radius=850; Pulse.Spec.Strength=1400; Pulse.Spec.Damage=25;
        auto& WideWard=Variant(TEXT("guardian.surge"),TEXT("guardian.wide"),TEXT("WIDE SURGE"),TEXT("Protect a wider group with weaker damage reduction. Useful when teammates must spread out."),{.16,-.13},3,14); WideWard.Spec.Radius=1000; WideWard.Spec.DamageTakenScale=.8f;
        auto& DeepWard=Variant(TEXT("guardian.surge"),TEXT("guardian.deep"),TEXT("HARDPOINT"),TEXT("A smaller field provides stronger protection. Gather around a position you intend to hold."),{.14,.18},3,16); DeepWard.Spec.Radius=400; DeepWard.Spec.DamageTakenScale=.45f;
        auto& Rush=Variant(TEXT("guardian.advance"),TEXT("guardian.rush"),TEXT("SHIELD RUSH"),TEXT("Add a frontal impact to the advance, trading some protection for offensive pressure."),{-.17,.06},3,18); Rush.Spec.Effect=EIBKitEffect::ConeStrike; Rush.Spec.Duration=.2f; Rush.Spec.Range=400; Rush.Spec.Radius=250; Rush.Spec.Damage=50; Rush.Spec.DamageTakenScale=.7f;
        auto& Rescue=Variant(TEXT("guardian.advance"),TEXT("guardian.rescue"),TEXT("RESCUE ADVANCE"),TEXT("A shorter dash leaves a protective field at your landing position. Use it to reach an exposed teammate."),{.17,.06},4,22); Rescue.Spec.Strength=1100; Rescue.Spec.bLeaveWard=true; Rescue.Spec.Radius=450; Rescue.Spec.Cooldown=16;
        auto& Siege=Variant(TEXT("guardian.citadel"),TEXT("guardian.siege"),TEXT("SIEGE LINE"),TEXT("A longer-lasting Citadel covers less ground. Helps a compact fireteam sustain a firing position."),{.13,.16},5,30); Siege.Spec.Duration=18; Siege.Spec.Radius=700;
        auto& Refuge=Variant(TEXT("guardian.citadel"),TEXT("guardian.refuge"),TEXT("REFUGE"),TEXT("Expand the Citadel to cover a retreat. Loses its slowing effect and provides lighter protection."),{-.13,.16},5,35); Refuge.Spec.Radius=1500; Refuge.Spec.SlowFactor=1; Refuge.Spec.DamageTakenScale=.6f;
        return Result;
    }();
    return Nodes;
}

const FIBSkillNode* Find(FName Id) { return Catalog().FindByPredicate([Id](const FIBSkillNode& N) { return N.Id==Id; }); }
FName RootAbility(FName Id) { const FIBSkillNode* N=Find(Id); return N ? (N->Parent.IsNone() ? N->Id : N->Parent) : NAME_None; }
bool IsUnlocked(const FIBSkillState& State, FName Id) { return State.Unlocked.Contains(Id); }
FIBSkillState StarterState(EIBOperativeClass Class)
{
    FIBSkillState State; State.Equipped.SetNum(4); int32 Tactical=1;
    for (const FIBSkillNode& N : Catalog()) if (N.Class==Class && N.Cost==0)
    {
        State.Unlocked.Add(N.Id);
        State.Equipped[N.Kind==EIBSkillKind::Signature ? 0 : Tactical++] = N.Id;
    }
    return State;
}
int32 PointsAvailable(const FIBSkillState& State, int32 Level)
{
    int32 Spent=0; TSet<FName> Seen;
    for (FName Id: State.Unlocked) if (!Seen.Contains(Id)) { Seen.Add(Id); if (const FIBSkillNode* N=Find(Id)) { Spent+=N->Cost; } }
    return FMath::Max(0,FMath::Clamp(Level,1,50)-1-Spent);
}
bool CanEquip(const FIBSkillNode& N, EIBSkillSlot Slot)
{
    return (Slot==EIBSkillSlot::Signature && N.Kind==EIBSkillKind::Signature)
        || ((Slot==EIBSkillSlot::TacticalOne || Slot==EIBSkillSlot::TacticalTwo) && N.Kind==EIBSkillKind::Tactical)
        || (Slot==EIBSkillSlot::Overdrive && N.Kind==EIBSkillKind::Overdrive);
}
bool Unlock(FIBSkillState& State,EIBOperativeClass Class,int32 Level,FName Id,FText& Error)
{
    const FIBSkillNode* N=Find(Id);
    if (!N || N->Class!=Class) { Error=NSLOCTEXT("IBSkills","WrongClass","This skill belongs to another class."); return false; }
    if (IsUnlocked(State,Id)) { Error=NSLOCTEXT("IBSkills","Owned","Already unlocked."); return false; }
    if (Level<N->Level) { Error=FText::Format(NSLOCTEXT("IBSkills","Level","Requires level {0}."),N->Level); return false; }
    if (!N->Parent.IsNone() && !IsUnlocked(State,N->Parent)) { Error=NSLOCTEXT("IBSkills","Parent","Unlock the parent ability first."); return false; }
    if (PointsAvailable(State,Level)<N->Cost) { Error=NSLOCTEXT("IBSkills","Points","Not enough skill points."); return false; }
    State.Unlocked.Add(Id); Error=FText::GetEmpty(); return true;
}
bool Equip(FIBSkillState& State,EIBOperativeClass Class,FName Id,EIBSkillSlot Slot,FText& Error)
{
    const FIBSkillNode* N=Find(Id); const int32 Index=static_cast<int32>(Slot);
    if (!N || N->Class!=Class || !CanEquip(*N,Slot) || !IsUnlocked(State,Id) || Index<0 || Index>=4)
    { Error=NSLOCTEXT("IBSkills","InvalidEquip","Unlock a compatible skill before equipping it."); return false; }
    State.Equipped.SetNum(4);
    for (int32 I=0; I<4; ++I) if (I!=Index && !State.Equipped[I].IsNone() && RootAbility(State.Equipped[I])==RootAbility(Id))
    { Error=NSLOCTEXT("IBSkills","Duplicate","This ability is already equipped in another slot."); return false; }
    if (State.Equipped[Index]==Id) { Error=NSLOCTEXT("IBSkills","Equipped","Already equipped."); return false; }
    State.Equipped[Index]=Id; Error=FText::GetEmpty(); return true;
}
FIBSkillState Sanitize(const FIBSkillState& State,EIBOperativeClass Class,int32 Level)
{
    FIBSkillState Clean=StarterState(Class); FText Error;
    // Parents before variants, regardless of file ordering. Recheck budget and class on disk too.
    for (int32 Pass=0; Pass<2; ++Pass) for (FName Id:State.Unlocked)
        if (const FIBSkillNode* N=Find(Id); N && (Pass==0)==N->Parent.IsNone()) { Unlock(Clean,Class,Level,Id,Error); }
    Clean.Equipped.Init(NAME_None,4);
    TSet<FName> Used;
    for (int32 I=0; I<FMath::Min(4,State.Equipped.Num()); ++I)
    {
        const FName Id=State.Equipped[I]; const FIBSkillNode* N=Find(Id);
        if (!N || N->Class!=Class || !CanEquip(*N,static_cast<EIBSkillSlot>(I)) || !IsUnlocked(Clean,Id)) { continue; }
        if (Used.Contains(RootAbility(Id))) { continue; }
        Clean.Equipped[I]=Id;
        Used.Add(RootAbility(Id));
    }
    // Repair invalid/duplicated saved slots without overwriting valid tactical swaps.
    for (int32 I=0; I<3; ++I) if (Clean.Equipped[I].IsNone())
    {
        for (const FIBSkillNode& N:Catalog())
            if (N.Class==Class && N.Cost==0 && CanEquip(N,static_cast<EIBSkillSlot>(I)) && !Used.Contains(N.Id))
            { Clean.Equipped[I]=N.Id; Used.Add(N.Id); break; }
    }
    return Clean;
}
FText SlotName(EIBSkillSlot Slot)
{
    switch(Slot) {
    case EIBSkillSlot::Signature: return NSLOCTEXT("IBSkills","Signature","SIGNATURE");
    case EIBSkillSlot::TacticalOne: return NSLOCTEXT("IBSkills","Tactical1","TACTICAL 1");
    case EIBSkillSlot::TacticalTwo: return NSLOCTEXT("IBSkills","Tactical2","TACTICAL 2");
    default: return NSLOCTEXT("IBSkills","Overdrive","OVERDRIVE"); }
}
}
