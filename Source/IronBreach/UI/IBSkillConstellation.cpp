#include "UI/IBSkillConstellation.h"
#include "UI/IBPaintKit.h"
#include "Framework/Application/SlateApplication.h"
#include "UI/IBStyleKit.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"

namespace IBSkillArt
{
void Icon(FSlateWindowElementList& Out,int32 Layer,const FGeometry& Geo,FVector2f Center,float Scale,EIBSkillIcon Kind,FLinearColor Color)
{
    auto Stroke=[&](std::initializer_list<FVector2f> Points)
    { TArray<FVector2f> P; for (auto V:Points) { P.Add(Center+V*Scale); } IBPaint::Line(Out,Layer,Geo,P,Color,1.7f); };
    switch(Kind)
    {
    case EIBSkillIcon::Dash: Stroke({{-1,-.6f},{-.2f,0},{-1,.6f}}); Stroke({{0,-.6f},{.8f,0},{0,.6f}}); break;
    case EIBSkillIcon::Charge: Stroke({{-.8f,.8f},{.6f,-.6f},{.6f,.2f}}); Stroke({{-.2f,-.6f},{.6f,-.6f}}); Stroke({{-.9f,-.1f},{-.3f,.5f}}); break;
    case EIBSkillIcon::Sweep: IBPaint::Ring(Out,Layer,Geo,Center,Scale*.75f,Color,1.7f); Stroke({{-1,-.2f},{0,.5f},{1,-.2f}}); break;
    case EIBSkillIcon::Grapple: Stroke({{-.8f,.8f},{.5f,-.5f},{.8f,-.1f},{1,-.7f},{.4f,-1},{.5f,-.5f}}); break;
    case EIBSkillIcon::Overdrive: Stroke({{.2f,-1},{-.7f,.15f},{0,.15f},{-.2f,1},{.8f,-.2f},{.1f,-.2f},{.2f,-1}}); break;
    case EIBSkillIcon::Veil: Stroke({{-1,0},{-.5f,-.6f},{.5f,-.6f},{1,0},{.5f,.5f},{-.5f,.5f},{-1,0}}); Stroke({{-.8f,.8f},{.8f,-.8f}}); break;
    case EIBSkillIcon::Dart: IBPaint::Ring(Out,Layer,Geo,Center,Scale*.65f,Color,1.5f); Stroke({{-1,0},{1,0}}); Stroke({{0,-1},{0,1}}); break;
    case EIBSkillIcon::Decoy: IBPaint::Ring(Out,Layer,Geo,Center+FVector2f(-.2f,-.55f)*Scale,Scale*.25f,Color,1.5f); Stroke({{-.8f,.9f},{-.7f,.1f},{.3f,.1f},{.4f,.9f}}); Stroke({{.65f,-.6f},{.9f,.9f}}); break;
    case EIBSkillIcon::Guard: Stroke({{-.8f,-.7f},{0,-1},{.8f,-.7f},{.65f,.5f},{0,1},{-.65f,.5f},{-.8f,-.7f}}); Stroke({{0,-.5f},{0,.5f}}); break;
    case EIBSkillIcon::Impact: IBPaint::Diamond(Out,Layer,Geo,Center,Scale*.45f,Color); Stroke({{-1,-1},{-.6f,-.6f}}); Stroke({{1,-1},{.6f,-.6f}}); Stroke({{-1,1},{-.6f,.6f}}); Stroke({{1,1},{.6f,.6f}}); break;
    case EIBSkillIcon::Ward: Stroke({{-1,.7f},{-.85f,-.25f},{0,-.9f},{.85f,-.25f},{1,.7f}}); Stroke({{-.9f,.7f},{.9f,.7f}}); Stroke({{0,-.2f},{0,.4f}}); Stroke({{-.3f,.1f},{.3f,.1f}}); break;
    }
}
}
void UIBSkillConstellation::NativeOnInitialized()
{
    Super::NativeOnInitialized(); SetVisibility(ESlateVisibility::Visible);
    UBorder* Surface=WidgetTree->ConstructWidget<UBorder>(); Surface->SetBrushColor(FLinearColor::Transparent);
    WidgetTree->RootWidget=Surface;
    ForceVolatile(true); // the link pulse is time-driven; never let a cached paint freeze it
}
namespace IBSkillArt
{
/** Hexagon outline, flat top: the Breach's crystalline read for milestone and late-ladder nodes. */
void Hex(FSlateWindowElementList& Out,int32 Layer,const FGeometry& Geo,FVector2f C,float R,FLinearColor Color,float Thickness)
{
    TArray<FVector2f> Pts; Pts.Reserve(7);
    for (int32 I=0; I<=6; ++I) { const float A=PI/6.f+I*PI/3.f; Pts.Add(C+FVector2f(FMath::Cos(A),FMath::Sin(A))*R); }
    IBPaint::Line(Out,Layer,Geo,Pts,Color,Thickness);
}
/** A short bright run travelling A -> B; Phase 0..1 is its position along the link. */
void Pulse(FSlateWindowElementList& Out,int32 Layer,const FGeometry& Geo,FVector2f A,FVector2f B,float Phase,FLinearColor Color)
{
    const float T0=FMath::Clamp(Phase-.09f,0.f,1.f), T1=FMath::Clamp(Phase+.03f,0.f,1.f);
    if (T1-T0<.01f) { return; }
    IBPaint::Seg(Out,Layer,Geo,FMath::Lerp(A,B,T0),FMath::Lerp(A,B,T1),Color,2.f);
}
}
int32 UIBSkillConstellation::NativePaint(const FPaintArgs& Args,const FGeometry& Geo,const FSlateRect& Cull,FSlateWindowElementList& Out,int32 Layer,const FWidgetStyle& Style,bool Enabled) const
{
    const int32 Base=Super::NativePaint(Args,Geo,Cull,Out,Layer,Style,Enabled);
    const FVector2f Size(Geo.GetLocalSize());
    auto Point=[&](const FIBSkillNode& N) { return FVector2f(N.Position.X*Size.X,N.Position.Y*Size.Y); };
    const FLinearColor Cyan=IBStyle::Cyan(), Dim(.28,.43,.5,.85f);
    const float Now=static_cast<float>(FSlateApplication::Get().GetCurrentTime());
    const FIBSkillNode* Picked=IBSkills::Find(Selected);

    // Roots in catalog order: signature, tacticals, overdrive.
    TArray<const FIBSkillNode*> Roots; const FIBSkillNode* Signature=nullptr; const FIBSkillNode* Overdrive=nullptr;
    for (const FIBSkillNode& N:IBSkills::Catalog()) if (N.Class==Class && N.Parent.IsNone())
    {
        Roots.Add(&N);
        if (N.Kind==EIBSkillKind::Signature && !Signature) { Signature=&N; }
        if (N.Kind==EIBSkillKind::Overdrive) { Overdrive=&N; }
    }

    // The spine follows the trade, not a template. Saber: one rising slash. Sentinel:
    // a kite — the veil fans out to the sensors and everything converges on Blackout.
    // Guardian: a bastion ring with the Citadel as keystone. Other classes: a plain chain.
    TArray<TPair<FVector2f,FVector2f>> Spine;
    auto Link=[&](const FIBSkillNode* A,const FIBSkillNode* B) { if (A && B && A!=B) { Spine.Emplace(Point(*A),Point(*B)); } };
    if (Class==EIBOperativeClass::Picket && Signature && Overdrive)
    {
        for (const FIBSkillNode* R:Roots) if (R->Kind==EIBSkillKind::Tactical) { Link(Signature,R); Link(R,Overdrive); }
    }
    else if (Class==EIBOperativeClass::Breaker && Overdrive)
    {
        TArray<const FIBSkillNode*> Wall; for (const FIBSkillNode* R:Roots) if (R!=Overdrive) { Wall.Add(R); }
        // Ring order: top, left, bottom, right — the catalog lists guard, impact, surge, advance.
        if (Wall.Num()==4) { Link(Wall[0],Wall[1]); Link(Wall[1],Wall[3]); Link(Wall[3],Wall[2]); Link(Wall[2],Wall[0]); }
        else { for (int32 I=0; I<Wall.Num(); ++I) { Link(Wall[I],Wall[(I+1)%Wall.Num()]); } }
        for (const FIBSkillNode* R:Wall) { Link(Overdrive,R); }
    }
    else
    {
        for (int32 I=1; I<Roots.Num(); ++I) { Link(Roots[I-1],Roots[I]); }
    }
    for (const TPair<FVector2f,FVector2f>& S:Spine) { IBPaint::Seg(Out,Base+1,Geo,S.Key,S.Value,IBPaint::Alpha(Cyan,.12f)); }

    // Prerequisite links, then a pulse running out from the inspected node along its own links.
    for (const FIBSkillNode& N:IBSkills::Catalog()) if (N.Class==Class && !N.Parent.IsNone())
    {
        if (const FIBSkillNode* Parent=IBSkills::Find(N.Parent))
        {
            const bool Owned=IBSkills::IsUnlocked(State,N.Id);
            const FVector2f A=Point(*Parent), B=Point(N);
            IBPaint::Seg(Out,Base+1,Geo,A,B,Owned ? IBPaint::Alpha(Cyan,.75f) : Dim,Owned ? 1.5f : 1.f);
            if (Picked && (Picked==Parent || Picked==&N))
            {
                const float Phase=FMath::Fmod(Now*.55f+(N.Position.X*3.1f),1.f);
                IBSkillArt::Pulse(Out,Base+2,Geo,Picked==Parent ? A : B,Picked==Parent ? B : A,Phase,IBPaint::Alpha(Cyan,Owned ? .9f : .45f));
            }
        }
    }
    if (Picked && Picked->Parent.IsNone())
    {
        const FVector2f From=Point(*Picked);
        for (const TPair<FVector2f,FVector2f>& S:Spine)
        {
            if (!S.Key.Equals(From,.5f) && !S.Value.Equals(From,.5f)) { continue; }
            const FVector2f To=S.Key.Equals(From,.5f) ? S.Value : S.Key;
            IBSkillArt::Pulse(Out,Base+2,Geo,From,To,FMath::Fmod(Now*.4f+To.X*.002f,1.f),IBPaint::Alpha(Cyan,.35f));
        }
    }

    for (const FIBSkillNode& N:IBSkills::Catalog()) if (N.Class==Class)
    {
        const FVector2f C=Point(N); const bool Major=N.Parent.IsNone(), Owned=IBSkills::IsUnlocked(State,N.Id);
        const bool Milestone=N.Kind==EIBSkillKind::Overdrive && Major, Late=N.Level>=30;
        const bool Equipped=State.Equipped.Contains(N.Id), IsPicked=Selected==N.Id;
        const float R=Milestone ? 36.f : (Major ? 30.f : 21.f);
        const FLinearColor Color=IsPicked || Equipped ? Cyan : (Owned ? IBStyle::TextHi() : Dim);
        if (IsPicked) { IBPaint::Disc(Out,Base+2,Geo,C,R+12,IBPaint::Alpha(Cyan,.09f)); IBPaint::Ring(Out,Base+3,Geo,C,R+7,Cyan,1); }
        IBPaint::Disc(Out,Base+3,Geo,C,R,FLinearColor(.004,.017,.026,.94f));
        if (Milestone)
        {
            // The overdrive is the tree's keystone: a crystalline frame sits outside its ring.
            IBSkillArt::Hex(Out,Base+3,Geo,C,R+10,IBPaint::Alpha(Owned ? Cyan : Dim,Owned ? .55f : .35f),1.f);
            IBSkillArt::Hex(Out,Base+3,Geo,C,R+14,IBPaint::Alpha(Owned ? Cyan : Dim,.18f),1.f);
        }
        if (Late && !Major)
        {
            // Late-ladder variants take the Breach's facet instead of a plain ring.
            if (Owned) { IBSkillArt::Hex(Out,Base+4,Geo,C,R+1,Color,Equipped ? 2.f : 1.2f); }
            else { IBSkillArt::Hex(Out,Base+4,Geo,C,R+1,IBPaint::Alpha(Color,.6f),1.f); IBPaint::DashedRing(Out,Base+4,Geo,C,R-4,Color,1,12); }
        }
        else if (Owned) { IBPaint::Ring(Out,Base+4,Geo,C,R,Color,Equipped ? 2.f : 1.f); }
        else { IBPaint::DashedRing(Out,Base+4,Geo,C,R,Color,1,16); }
        IBSkillArt::Icon(Out,Base+5,Geo,C,Milestone ? 15.f : (Major ? 13.f : 9.f),N.Icon,Color);
        if (Equipped) { IBPaint::DiamondFill(Out,Base+6,Geo,C+FVector2f(0,R+1),4,Cyan); }
        if (!Owned) // a small lock badge supplements the muted/dashed state
        {
            const FVector2f Lock=C+FVector2f(R*.7f,R*.7f);
            IBPaint::Rect(Out,Base+6,Geo,Lock-FVector2f(4,1),FVector2f(8,6),Dim);
            IBPaint::Line(Out,Base+6,Geo,{Lock+FVector2f(-3,0),Lock+FVector2f(-3,-4),Lock+FVector2f(3,-4),Lock+FVector2f(3,0)},Dim,1);
        }
    }
    return Base+6;
}
FName UIBSkillConstellation::HitNode(const FGeometry& Geo,FVector2D Position) const
{
    const FVector2D Local=Geo.AbsoluteToLocal(Position), Size=Geo.GetLocalSize();
    for (const FIBSkillNode& N:IBSkills::Catalog()) if (N.Class==Class)
        if (FVector2D::Distance(Local,N.Position*Size)<(N.Parent.IsNone() ? 38 : 29)) { return N.Id; }
    return NAME_None;
}
FReply UIBSkillConstellation::NativeOnMouseMove(const FGeometry& Geo,const FPointerEvent& Event)
{
    const FName Id=HitNode(Geo,Event.GetScreenSpacePosition());
    if (!Id.IsNone() && Id!=Selected) { Selected=Id; OnPicked.Broadcast(Id); }
    return FReply::Unhandled();
}
FReply UIBSkillConstellation::NativeOnMouseButtonDown(const FGeometry& Geo,const FPointerEvent& Event)
{
    const FName Id=HitNode(Geo,Event.GetScreenSpacePosition());
    if (!Id.IsNone()) { Selected=Id; OnPicked.Broadcast(Id); return FReply::Handled(); }
    return FReply::Unhandled();
}
void UIBSkillConstellation::Navigate(FVector2D Direction)
{
    const FIBSkillNode* From=IBSkills::Find(Selected); if (!From) { return; }
    const FIBSkillNode* Best=nullptr; float Score=TNumericLimits<float>::Max();
    for (const FIBSkillNode& N:IBSkills::Catalog()) if (N.Class==Class && N.Id!=Selected)
    {
        const FVector2D Delta=N.Position-From->Position;
        const float Along=FVector2D::DotProduct(Delta.GetSafeNormal(),Direction);
        const float Candidate=Delta.Size()/FMath::Max(.01f,Along);
        if (Along>.25f && Candidate<Score) { Score=Candidate; Best=&N; }
    }
    if (Best) { Selected=Best->Id; OnPicked.Broadcast(Selected); }
}
