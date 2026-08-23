#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "IBLobbyStripWidget.generated.h"

class UHorizontalBox;
class UVerticalBox;
class UTextBlock;
class UButton;
class UBorder;
class UScrollBox;
class UIBPlayerBannerWidget;
class UIBFriendsSubsystem;

/**
 * The Valorant moment: your squad standing in the main menu as a row of
 * banner cards, empty seats dealt face-down, count ticking up as friends
 * link in. Also owns the FRIENDS flyout (Steam list, invite/join).
 *
 * Full-viewport overlay widget — the main menu creates one and adds it to
 * the viewport; everything anchors itself. PlayerArray is re-scanned twice a
 * second; the strip only rebuilds when membership actually changes.
 */
UCLASS()
class IRONBREACH_API UIBLobbyStripWidget : public UUserWidget
{
	GENERATED_BODY()

protected:
	virtual void NativeOnInitialized() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

	UFUNCTION() void HandleFriendsToggle();
	UFUNCTION() void HandleFriendsRefresh();
	UFUNCTION() void HandleFriendsUpdated();
	UFUNCTION() void HandleRowAction(const FString& NetIdStr, bool bJoin);

private:
	void BuildLayout();
	void RefreshBanners(bool bForce = false);
	void RebuildFriendRows();
	UIBFriendsSubsystem* GetFriendsSubsystem() const;

	UPROPERTY(Transient) TObjectPtr<UHorizontalBox> BannerRow;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> CountText;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> LobbyTitleText;
	UPROPERTY(Transient) TObjectPtr<UBorder> FriendsPanel;
	UPROPERTY(Transient) TObjectPtr<class USizeBox> FriendsPanelFrame;
	UPROPERTY(Transient) TObjectPtr<UScrollBox> FriendsList;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> FriendsEmptyText;
	UPROPERTY(Transient) TObjectPtr<UButton> FriendsButton;

	UPROPERTY(Transient)
	TArray<TObjectPtr<UIBPlayerBannerWidget>> Banners;

	/** Membership fingerprint from the last rebuild (PlayerState ids). */
	TArray<int32> LastRoster;

	float RefreshAccumulator = 0.0f;
	bool bFriendsOpen = false;
	bool bFriendsBound = false;
};
