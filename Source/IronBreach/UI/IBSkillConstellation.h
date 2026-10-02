#pragma once
#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Skills/IBSkillTypes.h"
#include "IBSkillConstellation.generated.h"

DECLARE_MULTICAST_DELEGATE_OneParam(FIBSkillPicked,FName);
UCLASS()
class IRONBREACH_API UIBSkillConstellation : public UUserWidget
{
    GENERATED_BODY()
public:
    FIBSkillState State;
    EIBOperativeClass Class = EIBOperativeClass::Breaker;
    FName Selected;
    FIBSkillPicked OnPicked;
    void Navigate(FVector2D Direction);
protected:
    virtual void NativeOnInitialized() override;
    virtual int32 NativePaint(const FPaintArgs&,const FGeometry&,const FSlateRect&,FSlateWindowElementList&,int32,const FWidgetStyle&,bool) const override;
    virtual FReply NativeOnMouseMove(const FGeometry&,const FPointerEvent&) override;
    virtual FReply NativeOnMouseButtonDown(const FGeometry&,const FPointerEvent&) override;
private:
    FName HitNode(const FGeometry& Geo,FVector2D ScreenPosition) const;
};
