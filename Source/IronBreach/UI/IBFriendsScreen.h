#pragma once

#include "CoreMinimal.h"
#include "UI/IBMenuScreen.h"
#include "IBFriendsScreen.generated.h"

class UHorizontalBox;
class UTextBlock;
class UButton;
class UScrollBox;
class UIBPlayerBannerWidget;
class UIBFriendsSubsystem;

/**
 * The SQUAD tab — friends and party inside the in-game menu system (cycles
 * with Q/E next to Character/Ledger/Map, hotkey F). Top: the Apex banner row
 * for everyone in your session. Below: the Steam friends list with the
 * presence dots and INVITE / JOIN actions.
 *
 * Also the lobby's invite surface: the main-menu strip's FRIENDS chip opens
 * this same screen through the menu subsystem, so pre-deploy and mid-mission
 * inviting are one implementation.
 *
 * Pure C++ like the Settings screen (registry WidgetClass points straight at
 * this class); Shane can child it in a WBP later.
 */
UCLASS()
class IRONBREACH_API UIBFriendsScreen : public UIBMenuScreen
{
	GENERATED_BODY()

protected:
	virtual void NativeOnInitialized() override;
	virtual void NativeScreenOpened() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

	UFUNCTION() void HandleRefreshClicked();
	UFUNCTION() void HandleFriendsUpdated();
	UFUNCTION() void HandleRowAction(const FString& NetIdStr, bool bJoin);

private:
	void BuildLayout();
	void RefreshBanners(bool bForce = false);
	void RebuildFriendRows();
	UIBFriendsSubsystem* GetFriendsSubsystem() const;

	UPROPERTY(Transient) TObjectPtr<UHorizontalBox> BannerRow;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> CountText;
	UPROPERTY(Transient) TObjectPtr<UScrollBox> FriendsList;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> FriendsEmptyText;

	UPROPERTY(Transient)
	TArray<TObjectPtr<UIBPlayerBannerWidget>> Banners;

	TArray<int32> LastRoster;
	float RefreshAccumulator = 0.0f;
	bool bFriendsBound = false;
};
