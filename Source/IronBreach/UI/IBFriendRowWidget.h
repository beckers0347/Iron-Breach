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

	UFUNCTION() void HandleActionClicked();

private:
	void BuildLayout();

	FIBFriendInfo Info;
	bool bJoinAction = false;

	UPROPERTY(Transient) TObjectPtr<UBorder> PresenceDot;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> NameText;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> SubText;
	UPROPERTY(Transient) TObjectPtr<UButton> ActionButton;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> ActionLabel;
};
