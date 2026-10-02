#pragma once
#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "IBSkillMarkerWidget.generated.h"
/** Screen-space sensor marks remain useful behind cover and in either pawn type. */
UCLASS()
class IRONBREACH_API UIBSkillMarkerWidget : public UUserWidget
{
    GENERATED_BODY()
protected:
    virtual void NativeOnInitialized() override;
    virtual int32 NativePaint(const FPaintArgs&,const FGeometry&,const FSlateRect&,FSlateWindowElementList&,int32,const FWidgetStyle&,bool) const override;
};
