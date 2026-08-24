#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "IBLobbyStripWidget.generated.h"

class UHorizontalBox;
class UTextBlock;
class UButton;
class UIBPlayerBannerWidget;

/**
 * The Valorant moment: your squad standing in the main menu as a row of
 * banner cards, empty seats dealt face-down, count ticking up as friends
 * link in. The FRIENDS chip opens the SQUAD menu tab (UIBFriendsScreen via
 * the menu subsystem) — invites live there, in-game and in-lobby alike.
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

	UFUNCTION() void HandleFriendsClicked();

private:
	void BuildLayout();
	void RefreshBanners(bool bForce = false);

	UPROPERTY(Transient) TObjectPtr<UHorizontalBox> BannerRow;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> CountText;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> LobbyTitleText;
	UPROPERTY(Transient) TObjectPtr<UButton> FriendsButton;

	UPROPERTY(Transient)
	TArray<TObjectPtr<UIBPlayerBannerWidget>> Banners;

	/** Membership fingerprint from the last rebuild (PlayerState ids). */
	TArray<int32> LastRoster;

	float RefreshAccumulator = 0.0f;
};
