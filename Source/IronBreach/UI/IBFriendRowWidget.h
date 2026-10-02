#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Online/IBFriendsSubsystem.h" // FIBFriendInfo by value
#include "IBFriendRowWidget.generated.h"

class UTextBlock;
class UButton;
class UBorder;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnIBFriendRowAction, const FString&, NetIdStr, bool, bJoin);

/**
 * One friends-panel row: presence dot, name, and a single context action —
 * JOIN when the friend is in Iron Breach, INVITE when they're merely online.
 * Code-drawn via the style kit; broadcasts OnAction, panel does the calling.
 *
 * The row carries the hover and focus reads for the whole entry so the target
 * is the line you are pointing at, not just the chip at the end of it.
 */
UCLASS()
class IRONBREACH_API UIBFriendRowWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	/** bCanInvite: we have a live session to invite INTO (host lobby up). */
	void InitRow(const FIBFriendInfo& InInfo, bool bCanInvite);

	UPROPERTY(BlueprintAssignable, Category = "Friends")
	FOnIBFriendRowAction OnAction;

protected:
	virtual void NativeOnInitialized() override;
	virtual void NativeOnMouseEnter(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent) override;
	virtual void NativeOnMouseLeave(const FPointerEvent& InMouseEvent) override;
	/** Focus-PATH, so the row lights when its own action chip takes focus and
	 *  the row itself never becomes a second focus stop in the list. */
	virtual void NativeOnAddedToFocusPath(const FFocusEvent& InFocusEvent) override;
	virtual void NativeOnRemovedFromFocusPath(const FFocusEvent& InFocusEvent) override;

	UFUNCTION() void HandleActionClicked();

private:
	void BuildLayout();
	/** Single place the row surface and its lead edge are painted. */
	void ApplyStateVisuals();

	FIBFriendInfo Info;
	bool bJoinAction = false;
	bool bHovered = false;
	bool bFocused = false;

	UPROPERTY(Transient) TObjectPtr<UBorder> Surface;
	/** 3 px lead edge: invisible at rest, the row's focus tell when lit. */
	UPROPERTY(Transient) TObjectPtr<UBorder> LeadEdge;
	UPROPERTY(Transient) TObjectPtr<UBorder> PresenceDot;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> NameText;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> SubText;
	UPROPERTY(Transient) TObjectPtr<UButton> ActionButton;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> ActionLabel;
};
