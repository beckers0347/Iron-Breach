#pragma once
#include "CoreMinimal.h"
#include "UI/IBMenuScreen.h"
#include "Components/Border.h"
#include "IBMissionsScreen.generated.h"

/** A directional shade keeps mission text readable over its real recon image. */
UCLASS()
class IRONBREACH_API UIBMissionImageShade : public UBorder
{
    GENERATED_BODY()
protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;
};

/** Mission briefings use the same destination registry as the Watch. No second travel path. */
UCLASS()
class IRONBREACH_API UIBMissionsScreen : public UIBMenuScreen
{
    GENERATED_BODY()
public:
    void SelectDestination(FName Id);
    FName GetSelectedDestination() const { return SelectedId; }
protected:
    virtual void NativeOnInitialized() override;
    virtual void NativeScreenOpened() override;
    virtual void NativeTick(const FGeometry& Geometry, float DeltaTime) override;
private:
    void RebuildList();
    void RefreshDetails();
    void RefreshObjective();
    UFUNCTION() void ViewOnWatch();
    FName SelectedId;
    int32 FilterIndex = 0;
    float RefreshElapsed = 0.f;
    UPROPERTY(Transient) TObjectPtr<class UVerticalBox> MissionList;
    UPROPERTY(Transient) TObjectPtr<class UTextBlock> MissionName;
    UPROPERTY(Transient) TObjectPtr<class UTextBlock> MissionType;
    UPROPERTY(Transient) TObjectPtr<class UTextBlock> Brief;
    UPROPERTY(Transient) TObjectPtr<class UTextBlock> Objective;
    UPROPERTY(Transient) TObjectPtr<class UTextBlock> Intel;
    UPROPERTY(Transient) TObjectPtr<class UTextBlock> Status;
    UPROPERTY(Transient) TObjectPtr<class UTextBlock> ReconCaption;
    UPROPERTY(Transient) TObjectPtr<class UTextBlock> ReconFallback;
    UPROPERTY(Transient) TObjectPtr<class UTextBlock> ObjectiveSource;
    UPROPERTY(Transient) TObjectPtr<class UTextBlock> MissionCount;
    /** Live log strip above the briefings: the replicated director's objective for the map you stand in. */
    UPROPERTY(Transient) TObjectPtr<class UWidget> ActiveStrip;
    UPROPERTY(Transient) TObjectPtr<class UTextBlock> ActiveLocation;
    UPROPERTY(Transient) TObjectPtr<class UTextBlock> ActiveObjective;
    FText LastActiveObjective;
    UPROPERTY(Transient) TObjectPtr<class UImage> Recon;
    UPROPERTY(Transient) TObjectPtr<class UButton> WatchButton;
    UPROPERTY(Transient) TArray<TObjectPtr<class UButton>> Filters;
};
