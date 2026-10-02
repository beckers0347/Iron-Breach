#include "UI/IBSkillMarkerWidget.h"
#include "UI/IBPaintKit.h"
#include "UI/IBStyleKit.h"
#include "Classes/IBKitZone.h"
#include "Combat/HealthComponent.h"
#include "Blueprint/WidgetTree.h"
#include "Blueprint/WidgetLayoutLibrary.h"
#include "Components/Overlay.h"
#include "GameFramework/Character.h"
#include "GameFramework/PlayerController.h"
#include "EngineUtils.h"
void UIBSkillMarkerWidget::NativeOnInitialized()
{
    Super::NativeOnInitialized(); WidgetTree->RootWidget=WidgetTree->ConstructWidget<UOverlay>();
    SetVisibility(ESlateVisibility::HitTestInvisible); ForceVolatile(true);
}
int32 UIBSkillMarkerWidget::NativePaint(const FPaintArgs& Args,const FGeometry& Geo,const FSlateRect& Cull,FSlateWindowElementList& Out,int32 Layer,const FWidgetStyle& Style,bool Enabled) const
{
    const int32 Base=Super::NativePaint(Args,Geo,Cull,Out,Layer,Style,Enabled);
    APlayerController* PC=GetOwningPlayer(); if (!PC || !PC->GetPawn() || !GetWorld()) { return Base; }
    TSet<ACharacter*> Targets;
    for (TActorIterator<AIBKitZone> It(GetWorld()); It; ++It)
        for (const auto Weak:It->GetMarkedTargets()) if (ACharacter* Target=Weak.Get()) { Targets.Add(Target); }
    for (ACharacter* Target:Targets)
    {
        const UHealthComponent* Health=Target->FindComponentByClass<UHealthComponent>(); if (Health && Health->IsDepleted()) { continue; }
        FVector2D Screen;
        if (!UWidgetLayoutLibrary::ProjectWorldLocationToWidgetPosition(PC,Target->GetActorLocation()+FVector(0,0,Target->GetSimpleCollisionHalfHeight()+35),Screen,true)) { continue; }
        const FVector2D Size=Geo.GetLocalSize(); if (Screen.X<20 || Screen.Y<20 || Screen.X>Size.X-20 || Screen.Y>Size.Y-25) { continue; }
        const FVector2f At(Screen); const FLinearColor Cyan=IBStyle::Cyan();
        IBPaint::DiamondFill(Out,Base+1,Geo,At,10,FLinearColor(.003,.015,.025,.8f));
        IBPaint::Diamond(Out,Base+2,Geo,At,8,Cyan,1.5f);
        IBPaint::LabelAt(Out,Base+2,Geo,At+FVector2f(0,13),.5f,FString::Printf(TEXT("%.0f m"),FVector::Dist(PC->GetPawn()->GetActorLocation(),Target->GetActorLocation())/100),IBPaint::Font(TEXT("Regular"),10),Cyan);
    }
    return Base+2;
}
