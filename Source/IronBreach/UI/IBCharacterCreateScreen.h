#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Player/IBCharacterTypes.h"
#include "IBCharacterCreateScreen.generated.h"

class UButton;
class UTextBlock;
class UEditableText;
class UImage;
class USizeBox;
class UUniformGridPanel;
class AIBOperativePreviewStage;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnIBOperativeCreated, const FIBCharacterRecord&, Character);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnIBCreateCancelled);

/**
 * Character creation — the Graft Program intake form. The body you're
 * building stands on the left (live: gender swaps the mannequin, the chosen
 * trade lights the rim); the form sits on the right: callsign, the four
 * combat trades (Corpsman locked, per Phase-1 scope), gender, ENLIST.
 *
 * Owned by UIBCharacterSelectScreen, which lends it the preview stage. When
 * the roster is empty there is no BACK — the Breakwater does not take "no
 * operative" for an answer.
 */
UCLASS()
class IRONBREACH_API UIBCharacterCreateScreen : public UUserWidget
{
	GENERATED_BODY()

public:
	/** Call before AddChild. Stage may be null (no preview, form still works). */
	void InitCreate(bool bInAllowCancel, AIBOperativePreviewStage* InStage)
	{
		bAllowCancel = bInAllowCancel;
		Stage = InStage;
	}

	UPROPERTY(BlueprintAssignable, Category = "Character")
	FOnIBOperativeCreated OnOperativeCreated;

	UPROPERTY(BlueprintAssignable, Category = "Character")
	FOnIBCreateCancelled OnCreateCancelled;

protected:
	virtual void NativeOnInitialized() override;
	virtual void NativeConstruct() override;
	virtual void NativeDestruct() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;
	virtual FReply NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent) override;
	virtual FReply NativeOnPreviewKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent) override;

private:
	void BuildLayout();
	UButton* BuildClassCard(EIBOperativeClass Class);
	void RefreshSelectionStyles();
	void RefreshPreview();
	void SetStatus(const FText& Message, bool bError);
	bool HandleDismissKey();

	UFUNCTION() void HandleClassBreaker();
	UFUNCTION() void HandleClassPicket();
	UFUNCTION() void HandleClassBellringer();
	UFUNCTION() void HandleGenderMale();
	UFUNCTION() void HandleGenderFemale();
	UFUNCTION() void HandleEnlist();
	UFUNCTION() void HandleBack();
	UFUNCTION() void HandleCallsignChanged(const FText& Text);
	UFUNCTION() void HandleCallsignCommitted(const FText& Text, ETextCommit::Type CommitMethod);

	void PickClass(EIBOperativeClass Class);
	void PickGender(EIBOperativeGender Gender);
	class UIBCharacterSubsystem* GetCharacters() const;

	bool bAllowCancel = true;

	bool bClassChosen = false;
	EIBOperativeClass SelectedClass = EIBOperativeClass::Breaker;
	bool bGenderChosen = false;
	EIBOperativeGender SelectedGender = EIBOperativeGender::Male;

	/** Escape / B handled ahead of focus routing (the callsign field would eat it). */
	TSharedPtr<class FIBSheetDismissProcessor> DismissProcessor;

	UPROPERTY(Transient) TObjectPtr<AIBOperativePreviewStage> Stage;
	UPROPERTY(Transient) TObjectPtr<UImage> PreviewImage;
	UPROPERTY(Transient) TObjectPtr<UEditableText> Ed_Callsign;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> Txt_Status;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> PlateName;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> PlateRole;
	UPROPERTY(Transient) TObjectPtr<UButton> Btn_Enlist;
	UPROPERTY(Transient) TObjectPtr<UButton> Btn_Back;
	UPROPERTY(Transient) TObjectPtr<USizeBox> BackSize;
	UPROPERTY(Transient) TObjectPtr<UButton> Btn_Male;
	UPROPERTY(Transient) TObjectPtr<UButton> Btn_Female;

	/** Indexed by EIBOperativeClass value. */
	UPROPERTY(Transient) TArray<TObjectPtr<UButton>> ClassButtons;
};
