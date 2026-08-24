#pragma once

#include "CoreMinimal.h"
#include "UI/IBMenuScreen.h"
#include "IBFriendsScreen.generated.h"

class UHorizontalBox;
class UTextBlock;
class UButton;
class UScrollBox;
class USizeBox;
class UBorder;
class UIBPlayerBannerWidget;
class UIBFriendsSubsystem;

/**
 * FIRETEAM — the Squad tab, styled after the concept sheet: your hero banner
 * center with squadmates beside it, empty seats as clickable INVITE PLAYER
 * cards, a SOCIAL chip (online count) that slides the friends list in from
 * the right, LEAVE FIRETEAM + privacy line along the bottom, and a CURRENT
 * LOCATION card bottom-left.
 *
 * Cycles with Q/E, hotkey F; also opened by the main-menu strip's FRIENDS
 * chip — one social surface in-lobby and mid-mission.
 */
UCLASS()
class IRONBREACH_API UIBFriendsScreen : public UIBMenuScreen
{
	GENERATED_BODY()

protected:
	virtual void NativeOnInitialized() override;
	virtual void NativeScreenOpened() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

	UFUNCTION() void HandleSocialToggle();
	UFUNCTION() void HandleRefreshClicked();
	UFUNCTION() void HandleFriendsUpdated();
	UFUNCTION() void HandleRowAction(const FString& NetIdStr, bool bJoin);
	UFUNCTION() void HandleInviteSlotClicked(UIBPlayerBannerWidget* Banner);
	UFUNCTION() void HandleLeaveClicked();

private:
	void BuildLayout();
	void RefreshBanners(bool bForce = false);
	void RebuildFriendRows();
	void RefreshLocationCard();
	void SetFlyoutOpen(bool bOpen);
	UIBFriendsSubsystem* GetFriendsSubsystem() const;

	UPROPERTY(Transient) TObjectPtr<UHorizontalBox> BannerRow;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> SocialCountText;
	UPROPERTY(Transient) TObjectPtr<UScrollBox> FriendsList;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> FriendsEmptyText;
	UPROPERTY(Transient) TObjectPtr<USizeBox> FlyoutFrame;
	UPROPERTY(Transient) TObjectPtr<UButton> LeaveButton;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> LocationMapText;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> LocationZoneText;

	UPROPERTY(Transient)
	TArray<TObjectPtr<UIBPlayerBannerWidget>> Banners;

	TArray<int32> LastRoster;
	float RefreshAccumulator = 0.0f;
	bool bFriendsBound = false;
	bool bFlyoutOpen = false;

	/** The local player's banner always sits here (the featured hero card). */
	static constexpr int32 LocalSlotIndex = 1;
};
