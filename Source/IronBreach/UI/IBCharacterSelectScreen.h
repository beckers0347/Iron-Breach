#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Player/IBCharacterTypes.h"
#include "IBCharacterSelectScreen.generated.h"

class UButton;
class UTextBlock;
class UImage;
class UVerticalBox;
class UOverlay;
class UIBCharacterCreateScreen;
class AIBOperativePreviewStage;

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnIBOperativeFlowFinished);

/**
 * Operative select — the screen after PRESS ANY BUTTON. Destiny law: the body
 * on the left, the roster on the right. Click a billet to put that operative
 * on the stage (live mannequin, trade-colored rim light), DEPLOY to take them
 * out, two-step DECOMMISSION to retire them. Empty billets enlist new
 * operatives; an empty roster routes straight into creation (no way around
 * making your first character). Owns the creation sheet and the preview
 * stage; fires OnFlowFinished when an operative is on station (or the sheet
 * is dismissed, where allowed).
 *
 * Pure C++ (LobbyStrip pattern) — reskin by parenting a WBP later.
 */
UCLASS()
class IRONBREACH_API UIBCharacterSelectScreen : public UUserWidget
{
	GENERATED_BODY()

public:
	/** Dismissible = a character is already on station (reopened from the menu). */
	void InitSelect(bool bInDismissible) { bDismissible = bInDismissible; }

	UPROPERTY(BlueprintAssignable, Category = "Character")
	FOnIBOperativeFlowFinished OnFlowFinished;

	/** Lock the sheet and narrate: the operative is on station and the world is
	 *  being stood up. The sheet stays on screen until the travel lands. */
	void SetDeploying(const FText& Status);

	bool IsDeploying() const { return bDeploying; }

protected:
	virtual void NativeOnInitialized() override;
	virtual void NativeConstruct() override;
	virtual void NativeDestruct() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;
	virtual FReply NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent) override;
	virtual FReply NativeOnPreviewKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent) override;

private:
	void BuildLayout();
	void RefreshCards();
	UButton* BuildRosterCard(int32 Index, const FIBCharacterRecord& Record, bool bLastOnStation);
	void BuildEmptyCard();
	void SelectByIndex(int32 Index);
	void RefreshSelection();
	void EnsureStage();
	void OpenCreate();
	void CloseCreate();
	void SetStatus(const FText& Message, bool bError);
	class UIBCharacterSubsystem* GetCharacters() const;
	const FIBCharacterRecord* FindSelected() const;
	bool HandleDismissKey();

	UFUNCTION() void HandleRosterChanged();
	UFUNCTION() void HandleOperativeCreated(const FIBCharacterRecord& Character);
	UFUNCTION() void HandleCreateCancelled();
	UFUNCTION() void HandleBack();
	UFUNCTION() void HandleQuit();
	UFUNCTION() void HandleNewOperative();
	UFUNCTION() void HandleDeploy();
	UFUNCTION() void HandleDecommission();

	// Three billets, three fixed click handlers (UButton clicks carry no payload).
	UFUNCTION() void HandleSelect0();
	UFUNCTION() void HandleSelect1();
	UFUNCTION() void HandleSelect2();

	bool bDismissible = false;
	bool bDeploying = false;

	/** Who is on the stage / would deploy. */
	FGuid SelectedId;

	/** Two-step decommission: first click arms, second confirms. */
	FGuid PendingDeleteId;

	bool bLoggedFocusSteal = false;

	/** Escape / B handled ahead of focus routing (see IBSheetDismissProcessor). */
	TSharedPtr<class FIBSheetDismissProcessor> DismissProcessor;

	UPROPERTY(Transient) TObjectPtr<UOverlay> RootOverlay;
	UPROPERTY(Transient) TObjectPtr<UImage> PreviewImage;
	UPROPERTY(Transient) TObjectPtr<UVerticalBox> CardsColumn;
	UPROPERTY(Transient) TObjectPtr<UVerticalBox> ActionPanel;
	UPROPERTY(Transient) TObjectPtr<UVerticalBox> Nameplate;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> NameplateName;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> NameplateRole;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> NameplateMeta;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> Txt_Status;
	UPROPERTY(Transient) TObjectPtr<UButton> Btn_Back;
	UPROPERTY(Transient) TObjectPtr<UButton> Btn_Deploy;
	UPROPERTY(Transient) TObjectPtr<UButton> Btn_Decom;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> DecomLabel;
	UPROPERTY(Transient) TObjectPtr<UIBCharacterCreateScreen> CreateScreen;
	UPROPERTY(Transient) TObjectPtr<AIBOperativePreviewStage> Stage;

	/** Roster cards in roster order (empty billets are not in here). */
	UPROPERTY(Transient) TArray<TObjectPtr<UButton>> CardButtons;
};
