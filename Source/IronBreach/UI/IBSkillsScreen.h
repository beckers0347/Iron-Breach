#pragma once
#include "CoreMinimal.h"
#include "UI/IBMenuScreen.h"
#include "Skills/IBSkillTypes.h"
#include "IBSkillsScreen.generated.h"
class UIBSkillComponent;
class UIBSkillConstellation;
class AIBOperativePreviewStage;
class UMaterialInstanceDynamic;
class UTextBlock;
class UButton;
class UImage;

UCLASS()
class IRONBREACH_API UIBSkillsScreen : public UIBMenuScreen
{
    GENERATED_BODY()
public:
    void SelectNode(FName Id);
    FName GetSelectedNode() const { return Selected; }
protected:
    virtual void NativeOnInitialized() override;
    virtual void NativeScreenOpened() override;
    virtual void NativeScreenClosed() override;
    virtual void NativeDestruct() override;
    virtual void NativeTick(const FGeometry&,float) override;
    virtual FReply NativeOnKeyDown(const FGeometry&,const FKeyEvent&) override;
private:
    UIBSkillComponent* Skills() const;
    void Refresh();
    void ReleasePortrait();
    void Equip(EIBSkillSlot SkillSlot);
    void SelectEquipped(int32 SkillSlot);
    UFUNCTION() void Unlock();
    UFUNCTION() void Refund();
    UFUNCTION() void EquipSignature() { Equip(EIBSkillSlot::Signature); }
    UFUNCTION() void EquipTacticalOne() { Equip(EIBSkillSlot::TacticalOne); }
    UFUNCTION() void EquipTacticalTwo() { Equip(EIBSkillSlot::TacticalTwo); }
    UFUNCTION() void EquipOverdrive() { Equip(EIBSkillSlot::Overdrive); }
    UFUNCTION() void PickSignature() { SelectEquipped(0); }
    UFUNCTION() void PickTacticalOne() { SelectEquipped(1); }
    UFUNCTION() void PickTacticalTwo() { SelectEquipped(2); }
    UFUNCTION() void PickOverdrive() { SelectEquipped(3); }
    UPROPERTY() TObjectPtr<UIBSkillConstellation> Constellation;
    UPROPERTY() TObjectPtr<UTextBlock> ClassTitle;
    UPROPERTY() TObjectPtr<UTextBlock> Points;
    UPROPERTY() TObjectPtr<UTextBlock> DetailName;
    UPROPERTY() TObjectPtr<UTextBlock> DetailKind;
    UPROPERTY() TObjectPtr<UTextBlock> DetailDescription;
    UPROPERTY() TObjectPtr<UTextBlock> DetailStats;
    UPROPERTY() TObjectPtr<UTextBlock> DetailState;
    UPROPERTY() TObjectPtr<UTextBlock> Status;
    UPROPERTY() TObjectPtr<UButton> UnlockButton;
    UPROPERTY() TObjectPtr<UTextBlock> UnlockLabel;
    UPROPERTY() TObjectPtr<UButton> RefundButton;
    UPROPERTY() TObjectPtr<UTextBlock> RefundLabel;
    UPROPERTY() TArray<TObjectPtr<UButton>> EquipButtons;
    UPROPERTY() TArray<TObjectPtr<UButton>> StripButtons;
    UPROPERTY() TArray<TObjectPtr<UTextBlock>> StripNames;
    UPROPERTY() TObjectPtr<UImage> Portrait;
    UPROPERTY() TObjectPtr<AIBOperativePreviewStage> Stage;
    UPROPERTY() TObjectPtr<UMaterialInstanceDynamic> PortraitMaterial;
    FName Selected;
    bool bRefundArmed=false;
    bool bOpen=false;
    float RefreshClock=0;
};
