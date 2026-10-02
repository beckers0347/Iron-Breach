#include "UI/IBMenuScreen.h"
#include "UI/IBMenuSubsystem.h"
#include "UI/IBUISettings.h"
#include "UI/IBStyleKit.h"
#include "UI/IBMenuLayout.h"
#include "UI/IBMenuNavButton.h"
#include "UI/IBHangarStyle.h"
#include "UI/IBInventoryScreen.h"
#include "Items/IBPlayerState.h"
#include "Items/IBInventoryComponent.h"
#include "Player/IBCharacterTypes.h"
#include "Components/Image.h"
#include "Components/ProgressBar.h"
#include "Components/SizeBox.h"
#include "Components/ScaleBox.h"
#include "Engine/Texture2D.h"
#include "Engine/LocalPlayer.h"
#include "GameFramework/PlayerController.h"
#include "Components/Border.h"
#include "Components/TextBlock.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Blueprint/WidgetTree.h"

void UIBMenuScreen::NativeOnInitialized()
{
	Super::NativeOnInitialized();

	SetIsFocusable(true); // required for NativeOnKeyDown to receive anything

	if (CloseKeys.IsEmpty())
	{
		CloseKeys = { EKeys::Escape, EKeys::Gamepad_FaceButton_Right };
	}
	if (NextScreenKeys.IsEmpty())
	{
		NextScreenKeys = { EKeys::E, EKeys::Gamepad_RightShoulder };
	}
	if (PrevScreenKeys.IsEmpty())
	{
		PrevScreenKeys = { EKeys::Q, EKeys::Gamepad_LeftShoulder };
	}
}

EIBMenuGroup UIBMenuScreen::GetPresentationGroup() const
{
    const FName Id = ScreenId.IsNone() ? HangarDefaultTab : ScreenId;
    const EIBMenuGroup Group = bDirectorLayout ? EIBMenuGroup::Director : UIBUISettings::Get()->GetMenuGroup(Id);
    if (Group != EIBMenuGroup::Utility) { return Group; }
    const ULocalPlayer* LP = GetOwningLocalPlayer();
    const UIBMenuSubsystem* Menu = LP ? LP->GetSubsystem<UIBMenuSubsystem>() : nullptr;
    return Menu ? Menu->GetActiveMenuGroup() : EIBMenuGroup::Personal;
}

void UIBMenuScreen::EnsureTabBanner()
{
    const EIBMenuGroup Group = GetPresentationGroup();
    if (TabLabels.Num() > 0 && BuiltTabGroup == Group) { return; }
    if (!TabBannerBox)
    {
        UOverlay* Root = WidgetTree ? Cast<UOverlay>(WidgetTree->RootWidget) : nullptr;
        if (!Root) { return; }
        TabBannerBox = WidgetTree->ConstructWidget<UHorizontalBox>();
        UOverlaySlot* BannerSlot = Root->AddChildToOverlay(TabBannerBox);
        BannerSlot->SetHorizontalAlignment(HAlign_Center);
        BannerSlot->SetVerticalAlignment(VAlign_Top);
        BannerSlot->SetPadding(FMargin(0,24,0,0));
    }
    TabBannerBox->ClearChildren(); TabLabels.Reset(); TabIds.Reset(); TabUnderlines.Reset();
    BuiltTabGroup = Group;
    ULocalPlayer* LP = GetOwningLocalPlayer();
    UIBMenuSubsystem* Menu = LP ? LP->GetSubsystem<UIBMenuSubsystem>() : nullptr;
    for (FName Id : UIBUISettings::Get()->GetMenuTabs(Group))
    {
        FText Text;
        if (Id == TEXT("Character")) { Text = NSLOCTEXT("IBMenu","Character","CHARACTER"); }
        else if (Id == TEXT("Backpack")) { Text = NSLOCTEXT("IBMenu","Backpack","INVENTORY"); }
        else if (const FIBMenuScreenDef* Def = UIBUISettings::Get()->FindScreen(Id)) { Text = Def->TabLabel.ToUpper(); }
        UIBMenuNavButton* Button = WidgetTree->ConstructWidget<UIBMenuNavButton>();
        Button->Init(Menu, Id);
        // The label is the button's direct content: the opt-in checks find tabs by that text.
        UTextBlock* Label = IBMenuLayout::Text(WidgetTree,Text,13,IBStyle::TextLo(),120);
        Button->SetContent(Label);
        UVerticalBox* Tab = WidgetTree->ConstructWidget<UVerticalBox>();
        Tab->AddChildToVerticalBox(Button);
        UIBMenuGlyph* Underline = IBHangar::Glyph(WidgetTree,EIBMenuGlyph::Notch,IBHangar::Cyan(),8.f);
        Underline->SetGlyphSize(FVector2D(24,8)); Underline->SetWeight(1.5f);
        Underline->SetVisibility(ESlateVisibility::HitTestInvisible);
        Tab->AddChildToVerticalBox(Underline)->SetHorizontalAlignment(HAlign_Fill);
        TabBannerBox->AddChildToHorizontalBox(Tab)->SetPadding(FMargin(2,0));
        TabIds.Add(Id); TabLabels.Add(Label); TabUnderlines.Add(Underline);
    }
}

void UIBMenuScreen::RefreshTabBanner()
{
    EnsureTabBanner();
    const APlayerController* PC = GetOwningPlayer();
    const AIBPlayerState* PS = PC ? PC->GetPlayerState<AIBPlayerState>() : nullptr;
    // Real identity only: callsign, level, class, clearance and XP all come from the
    // replicated player state, so every machine draws the same numbers — the XP mirror
    // (total plus the current level's bounds) replicates alongside the level. Nothing here
    // is computed from a local guess, and nothing is drawn without a real value.
    if (HangarCallsign) { HangarCallsign->SetText(PS && PS->HasOperative() ? FText::FromString(PS->GetDisplayCallsign().ToUpper()) : NSLOCTEXT("IBMenu","Operative","OPERATIVE")); }
    if (HangarRank)
    {
        HangarRank->SetText(PS && PS->HasOperative()
            ? FText::Format(NSLOCTEXT("IBMenu","Rank","LV {0}   {1}"),PS->GetOperativeLevel(),IBCharacter::ClassName(PS->GetOperativeClass()).ToUpper())
            : NSLOCTEXT("IBMenu","NoOperative","NO OPERATIVE ON STATION"));
        HangarRank->SetColorAndOpacity(PS && PS->HasOperative() ? IBCharacter::ClassColor(PS->GetOperativeClass()) : IBStyle::TextLo());
    }
    if (HangarClearance) { HangarClearance->SetText(FText::Format(NSLOCTEXT("IBMenu","Rating","CLEARANCE  {0}"),PS && PS->GetInventory() ? PS->GetInventory()->GetTotalClearanceRating() : 0)); }
    if (HangarAccount)
    {
        // The platform name (Steam persona / machine name) only when it adds information.
        const FString Account = PS ? PS->GetPlayerName() : FString();
        const bool bShowAccount = PS && PS->HasOperative() && !Account.IsEmpty() && !Account.Equals(PS->GetDisplayCallsign(), ESearchCase::IgnoreCase);
        HangarAccount->SetText(FText::FromString(Account));
        HangarAccount->SetVisibility(bShowAccount ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
    }
    if (HangarXPRow && HangarXPBar && HangarXPText)
    {
        // Replicated ledger mirror: progress through the level when a ladder is tuned, else the raw total.
        const bool bHasOperative = PS && PS->HasOperative();
        if (bHasOperative && PS->HasNextLevel())
        {
            HangarXPBar->SetPercent(PS->GetOperativeLevelProgress());
            HangarXPText->SetText(FText::Format(NSLOCTEXT("IBMenu","XPProgress","{0} / {1} XP"),
                FText::AsNumber(PS->GetOperativeXP() - PS->GetOperativeLevelFloorXP()), FText::AsNumber(PS->GetOperativeNextLevelXP() - PS->GetOperativeLevelFloorXP())));
        }
        else if (bHasOperative && PS->GetOperativeLevel() > 1)
        {
            HangarXPBar->SetPercent(1.f);
            HangarXPText->SetText(FText::Format(NSLOCTEXT("IBMenu","XPTop","{0} XP  ·  TOP OF LADDER"),FText::AsNumber(PS->GetOperativeXP())));
        }
        else if (bHasOperative)
        {
            HangarXPBar->SetPercent(0.f);
            HangarXPText->SetText(FText::Format(NSLOCTEXT("IBMenu","XPTotal","{0} XP"),FText::AsNumber(PS->GetOperativeXP())));
        }
        HangarXPRow->SetVisibility(bHasOperative ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
    }
    if (TabBannerBox) { TabBannerBox->SetVisibility(ESlateVisibility::SelfHitTestInvisible); }
    const bool bDirector = GetPresentationGroup() == EIBMenuGroup::Director;
    if (GroupLink && GroupLinkLabel)
    {
        ULocalPlayer* LP = GetOwningLocalPlayer();
        GroupLink->Init(LP ? LP->GetSubsystem<UIBMenuSubsystem>() : nullptr,bDirector ? TEXT("Character") : TEXT("Watch"));
        GroupLinkLabel->SetText(bDirector ? NSLOCTEXT("IBMenu","ToCharacter","CHARACTER  [I]") : NSLOCTEXT("IBMenu","ToDirector","DIRECTOR  [B]"));
    }
    const UIBInventoryScreen* Inventory = Cast<UIBInventoryScreen>(this);
    const FName ActiveId = Inventory ? FName(Inventory->IsBackpackTab() ? TEXT("Backpack") : TEXT("Character")) : (ScreenId.IsNone() ? HangarDefaultTab : ScreenId);
    for (int32 i=0; i<TabLabels.Num(); ++i)
    {
        UTextBlock* Label = TabLabels[i];
        const bool bActive = TabIds[i] == ActiveId;
        if (UIBMenuNavButton* Button = Cast<UIBMenuNavButton>(Label->GetParent()))
        {
            FButtonStyle Style = Button->GetStyle();
            Style.Normal = IBStyle::RoundedBrush(FLinearColor::Transparent,0);
            Style.Hovered = IBStyle::RoundedBrush(FLinearColor(.2f,.65f,.75f,.09f),0);
            Style.Pressed = IBStyle::RoundedBrush(FLinearColor(.2f,.65f,.75f,.16f),0);
            Style.NormalPadding = FMargin(14,11); Style.PressedPadding = Style.NormalPadding;
            Button->SetStyle(Style);
        }
        Label->SetColorAndOpacity(bActive ? IBStyle::TextHi() : IBStyle::TextLo());
        // Visibility, not opacity: RoundedBox outline alpha ignores RenderOpacity.
        TabUnderlines[i]->SetVisibility(bActive ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Hidden);
    }
}
void UIBMenuScreen::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);

	// Focus is the menu's oxygen: every in-menu key (close, cycle, hotkeys)
	// routes through this widget, and a stray click on a non-focusable child
	// (the dim border, the map canvas) silently drops keyboard focus to the
	// viewport — where UI-only mode eats it. Reassert every frame while open;
	// it's a cheap check and it makes Escape unkillable.
	if (OwnerSubsystem && IsVisible() && !HasKeyboardFocus() && !HasFocusedDescendants())
	{
		SetKeyboardFocus();
	}

	// The owning player state can be replaced under an open screen (seamless travel, a
	// reconnect). Keep the subscription pointed at the live one and redraw once when it
	// moves; BindOperativeEvents is a pointer compare on every other frame.
	if (OwnerSubsystem && BindOperativeEvents())
	{
		RefreshTabBanner();
	}

	// Panel transition: the sheet settles up into place over 160 ms after opening.
	if (OpenSettle < 1.f)
	{
		OpenSettle = FMath::Min(1.f, OpenSettle + InDeltaTime / 0.16f);
		const float Ease = 1.f - FMath::Pow(1.f - OpenSettle, 3.f);
		SetRenderTranslation(FVector2D(0.0, (1.f - Ease) * 12.f));
	}
}

void UIBMenuScreen::NotifyScreenOpened(UIBMenuSubsystem* InOwner, FName InScreenId)
{
	OwnerSubsystem = InOwner;
	ScreenId = InScreenId;
	OpenSettle = 0.f;
	SetRenderTranslation(FVector2D(0.0, 12.0));
	SetKeyboardFocus();
	EnsureTabBanner();
	BindOperativeEvents();
	RefreshTabBanner();
	NativeScreenOpened();
	BP_OnScreenOpened();
}

void UIBMenuScreen::NotifyScreenClosed()
{
	UnbindOperativeEvents();
	NativeScreenClosed();
	BP_OnScreenClosed();
}

void UIBMenuScreen::NativeDestruct()
{
	// Closing removes the screen from the viewport (UIBMenuSubsystem), and a world teardown
	// destructs it without a close at all — both paths have to drop the binding.
	UnbindOperativeEvents();
	Super::NativeDestruct();
}

bool UIBMenuScreen::BindOperativeEvents()
{
	const APlayerController* PC = GetOwningPlayer();
	AIBPlayerState* PS = PC ? PC->GetPlayerState<AIBPlayerState>() : nullptr;
	if (PS == BoundOperativeState.Get()) { return false; }
	UnbindOperativeEvents();
	if (!PS) { return false; }
	// Both events, bound and unbound together so the pair can never drift apart. XP alone is
	// not enough: an award broadcasts before the level-up does, so the header would redraw
	// with the previous LV still on screen (see the declaration for the full ordering).
	// AddUnique: screens are cached and reopened many times over a session, and a duplicated
	// dynamic binding would refresh the header once per open, forever.
	PS->OnOperativeXPChanged.AddUniqueDynamic(this, &UIBMenuScreen::HandleOperativeStateChanged);
	PS->OnOperativeIdentityChanged.AddUniqueDynamic(this, &UIBMenuScreen::HandleOperativeStateChanged);
	BoundOperativeState = PS;
	return true;
}

void UIBMenuScreen::UnbindOperativeEvents()
{
	if (AIBPlayerState* Bound = BoundOperativeState.Get())
	{
		Bound->OnOperativeXPChanged.RemoveDynamic(this, &UIBMenuScreen::HandleOperativeStateChanged);
		Bound->OnOperativeIdentityChanged.RemoveDynamic(this, &UIBMenuScreen::HandleOperativeStateChanged);
	}
	BoundOperativeState = nullptr;
}

void UIBMenuScreen::HandleOperativeStateChanged()
{
	// Either event redraws the whole header from the player state, so whichever of the two
	// lands second corrects whatever the first one drew early. A change that arrives between
	// the broadcast and the unbind must not rebuild a screen that is no longer on the viewport.
	if (IsInViewport())
	{
		RefreshTabBanner();
	}
}

FReply UIBMenuScreen::NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent)
{
	const FKey Key = InKeyEvent.GetKey();
	ULocalPlayer* LP = GetOwningLocalPlayer();
	UIBMenuSubsystem* Menu = OwnerSubsystem ? OwnerSubsystem.Get() : (LP ? LP->GetSubsystem<UIBMenuSubsystem>() : nullptr);

	if (Menu)
	{
		if (CloseKeys.Contains(Key))
		{
			Menu->CloseMenu();
			return FReply::Handled();
		}
		if (NextScreenKeys.Contains(Key) || PrevScreenKeys.Contains(Key))
		{
			const int32 Direction = NextScreenKeys.Contains(Key) ? 1 : -1;
			if (OwnerSubsystem) { Menu->CycleScreen(Direction); }
			else
			{
				const TArray<FName> Tabs = UIBUISettings::Get()->GetMenuTabs(GetPresentationGroup());
				const int32 Index = Tabs.IndexOfByKey(HangarDefaultTab);
				if (Index != INDEX_NONE) { Menu->OpenScreen(Tabs[(Index + Direction + Tabs.Num()) % Tabs.Num()]); }
			}
			return FReply::Handled();
		}

		// Screen hotkeys from settings: same key toggles closed, another
		// screen's key jumps sideways — mirrors the in-game bindings so the
		// menu keys feel like one system inside and out.
		for (const FIBMenuScreenDef& Def : UIBUISettings::Get()->Screens)
		{
			if (Def.Hotkeys.Contains(Key))
			{
				Menu->ToggleScreen(Def.ScreenId == TEXT("Inventory") ? FName(TEXT("Character")) : Def.ScreenId);
				return FReply::Handled();
			}
		}
	}

	return Super::NativeOnKeyDown(InGeometry, InKeyEvent);
}

UWidget* UIBMenuScreen::BuildMenuHeader(bool bCompact)
{
    // One slim band: insignia + identity on the left, the tab ring in the
    // middle, clearance / group link / settings on the right. Every label the
    // opt-in checks click stays a button's direct text content.
    UHorizontalBox* Header = WidgetTree->ConstructWidget<UHorizontalBox>();
    UHorizontalBox* Identity = WidgetTree->ConstructWidget<UHorizontalBox>();
    UIBMenuGlyph* Crest = IBHangar::Glyph(WidgetTree,EIBMenuGlyph::Insignia,IBHangar::Cyan(),bCompact ? 24.f : 30.f);
    Crest->SetWeight(1.4f);
    UHorizontalBoxSlot* CrestSlot = Identity->AddChildToHorizontalBox(IBHangar::Chip(WidgetTree,Crest,FMargin(5)));
    CrestSlot->SetPadding(FMargin(0,0,12,0)); CrestSlot->SetVerticalAlignment(VAlign_Center);
    if (bCompact)
    {
        UVerticalBox* Copy = WidgetTree->ConstructWidget<UVerticalBox>();
        Copy->AddChildToVerticalBox(IBHangar::Label(WidgetTree,TEXT("DIRECTOR"),15,IBStyle::TextHi()));
        Copy->AddChildToVerticalBox(IBMenuLayout::Text(WidgetTree,NSLOCTEXT("IBMenu","DirectorSub","BREAKWATER COMMAND"),9,IBHangar::Cyan(),160))->SetPadding(FMargin(0,2,0,0));
        Identity->AddChildToHorizontalBox(Copy)->SetVerticalAlignment(VAlign_Center);
    }
    else
    {
        UVerticalBox* Copy = WidgetTree->ConstructWidget<UVerticalBox>();
        UHorizontalBox* NameRow = WidgetTree->ConstructWidget<UHorizontalBox>();
        HangarCallsign = IBMenuLayout::Heading(WidgetTree,FText::GetEmpty(),18);
        HangarCallsign->SetTextOverflowPolicy(ETextOverflowPolicy::Ellipsis);
        HangarCallsign->SetClipping(EWidgetClipping::ClipToBounds);
        NameRow->AddChildToHorizontalBox(HangarCallsign)->SetVerticalAlignment(VAlign_Bottom);
        HangarAccount = IBMenuLayout::Text(WidgetTree,FText::GetEmpty(),9,IBStyle::TextLo(),60);
        HangarAccount->SetTextOverflowPolicy(ETextOverflowPolicy::Ellipsis);
        UHorizontalBoxSlot* AccountSlot = NameRow->AddChildToHorizontalBox(HangarAccount);
        AccountSlot->SetPadding(FMargin(10,0,0,2)); AccountSlot->SetVerticalAlignment(VAlign_Bottom);
        Copy->AddChildToVerticalBox(NameRow);
        HangarRank = IBMenuLayout::Text(WidgetTree,FText::GetEmpty(),10,IBHangar::Cyan(),120);
        Copy->AddChildToVerticalBox(HangarRank)->SetPadding(FMargin(0,2,0,0));
        // XP: a 3 px bar through the current level and the real numbers beside it.
        UHorizontalBox* XPRow = WidgetTree->ConstructWidget<UHorizontalBox>();
        HangarXPBar = WidgetTree->ConstructWidget<UProgressBar>();
        FProgressBarStyle XPStyle;
        XPStyle.SetBackgroundImage(IBStyle::RoundedBrush(FLinearColor(.06f,.11f,.14f,.9f),0));
        XPStyle.SetFillImage(IBStyle::RoundedBrush(FLinearColor::White,0));
        HangarXPBar->SetWidgetStyle(XPStyle); HangarXPBar->SetFillColorAndOpacity(IBHangar::Cyan()); HangarXPBar->SetPercent(0.f);
        USizeBox* XPSize = IBMenuLayout::Width(WidgetTree,HangarXPBar,132); XPSize->SetHeightOverride(3);
        UHorizontalBoxSlot* BarSlot = XPRow->AddChildToHorizontalBox(XPSize); BarSlot->SetVerticalAlignment(VAlign_Center);
        HangarXPText = IBMenuLayout::Text(WidgetTree,FText::GetEmpty(),8,IBStyle::TextLo(),60);
        UHorizontalBoxSlot* XPTextSlot = XPRow->AddChildToHorizontalBox(HangarXPText); XPTextSlot->SetPadding(FMargin(8,0,0,0)); XPTextSlot->SetVerticalAlignment(VAlign_Center);
        HangarXPRow = XPRow;
        Copy->AddChildToVerticalBox(XPRow)->SetPadding(FMargin(0,5,0,0));
        Identity->AddChildToHorizontalBox(Copy)->SetVerticalAlignment(VAlign_Center);
    }
    Header->AddChildToHorizontalBox(IBMenuLayout::Width(WidgetTree,Identity,bCompact ? 236 : 312))->SetVerticalAlignment(VAlign_Center);

    TabBannerBox = WidgetTree->ConstructWidget<UHorizontalBox>();
    UHorizontalBoxSlot* NavSlot = Header->AddChildToHorizontalBox(TabBannerBox);
    NavSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); NavSlot->SetVerticalAlignment(VAlign_Center); NavSlot->SetHorizontalAlignment(HAlign_Center);

    if (!bCompact)
    {
        // Clearance chip: the one number the hangar tracks (real inventory total).
        UHorizontalBox* Rating = WidgetTree->ConstructWidget<UHorizontalBox>();
        UHorizontalBoxSlot* MarkSlot = Rating->AddChildToHorizontalBox(IBHangar::Glyph(WidgetTree,EIBMenuGlyph::Diamond,IBHangar::Cyan(),14.f));
        MarkSlot->SetPadding(FMargin(0,0,8,0)); MarkSlot->SetVerticalAlignment(VAlign_Center);
        HangarClearance = IBMenuLayout::Text(WidgetTree,FText::GetEmpty(),11,IBStyle::TextHi(),100);
        Rating->AddChildToHorizontalBox(HangarClearance)->SetVerticalAlignment(VAlign_Center);
        UHorizontalBoxSlot* RatingSlot = Header->AddChildToHorizontalBox(IBHangar::Chip(WidgetTree,Rating,FMargin(12,7)));
        RatingSlot->SetPadding(FMargin(8,0,14,0)); RatingSlot->SetVerticalAlignment(VAlign_Center);
    }
    ULocalPlayer* LP = GetOwningLocalPlayer();
    UIBMenuSubsystem* Menu = LP ? LP->GetSubsystem<UIBMenuSubsystem>() : nullptr;
    GroupLink = WidgetTree->ConstructWidget<UIBMenuNavButton>();
    GroupLink->Init(Menu,bCompact ? TEXT("Character") : TEXT("Watch"));
    GroupLinkLabel = IBMenuLayout::Text(WidgetTree,bCompact ? NSLOCTEXT("IBMenu","ToCharacter","CHARACTER  [I]") : NSLOCTEXT("IBMenu","ToDirector","DIRECTOR  [B]"),11,IBHangar::Cyan(),120);
    GroupLink->SetContent(GroupLinkLabel);
    FButtonStyle LinkStyle = GroupLink->GetStyle();
    LinkStyle.Normal = IBStyle::RoundedBrush(FLinearColor(.004f,.014f,.022f,.6f),0,IBHangar::Fade(IBHangar::Cyan(),.35f),1.f);
    LinkStyle.Hovered = IBStyle::RoundedBrush(FLinearColor(.2f,.65f,.75f,.14f),0,IBHangar::Cyan(),1.f);
    LinkStyle.Pressed = IBStyle::RoundedBrush(FLinearColor(.2f,.65f,.75f,.22f),0,IBHangar::Cyan(),1.f);
    LinkStyle.NormalPadding = FMargin(14,9); LinkStyle.PressedPadding = LinkStyle.NormalPadding;
    GroupLink->SetStyle(LinkStyle);
    Header->AddChildToHorizontalBox(GroupLink)->SetVerticalAlignment(VAlign_Center);
    UIBMenuNavButton* Settings = WidgetTree->ConstructWidget<UIBMenuNavButton>();
    Settings->Init(Menu,TEXT("Settings"));
    Settings->SetContent(IBHangar::Glyph(WidgetTree,EIBMenuGlyph::Cog,IBStyle::TextLo(),18.f));
    FButtonStyle CogStyle = LinkStyle;
    CogStyle.Normal = IBStyle::RoundedBrush(FLinearColor::Transparent,0);
    CogStyle.NormalPadding = FMargin(10,8); CogStyle.PressedPadding = CogStyle.NormalPadding;
    Settings->SetStyle(CogStyle);
    UHorizontalBoxSlot* CogSlot = Header->AddChildToHorizontalBox(Settings);
    CogSlot->SetPadding(FMargin(10,0,0,0)); CogSlot->SetVerticalAlignment(VAlign_Center);

    UBorder* Band = IBHangar::Glass(WidgetTree,Header,bCompact ? FMargin(28,6) : FMargin(28,7),FIBGlassStyle::Band(),FLinearColor(.003f,.011f,.018f,.90f));
    return Band;
}

UOverlay* UIBMenuScreen::BuildDirectorPage(const FText& Hint)
{
    bDirectorLayout = true;
    bHangarLayout = true;
    UOverlay* Root = WidgetTree->ConstructWidget<UOverlay>(); WidgetTree->RootWidget = Root;
    UOverlay* Scene = WidgetTree->ConstructWidget<UOverlay>(UOverlay::StaticClass(),TEXT("DirectorScene"));
    UOverlaySlot* SceneSlot = Root->AddChildToOverlay(Scene);
    SceneSlot->SetHorizontalAlignment(HAlign_Fill); SceneSlot->SetVerticalAlignment(VAlign_Fill);
    UOverlaySlot* HeaderSlot = Root->AddChildToOverlay(BuildMenuHeader(true));
    HeaderSlot->SetHorizontalAlignment(HAlign_Fill); HeaderSlot->SetVerticalAlignment(VAlign_Top);
    UTextBlock* Hints = IBMenuLayout::Text(WidgetTree,Hint,11,FLinearColor(.62f,.74f,.79f),60);
    Hints->SetVisibility(ESlateVisibility::HitTestInvisible);
    UOverlaySlot* FooterSlot = Root->AddChildToOverlay(Hints);
    FooterSlot->SetHorizontalAlignment(HAlign_Left); FooterSlot->SetVerticalAlignment(VAlign_Bottom);
    FooterSlot->SetPadding(FMargin(32,0,32,18));
    return Scene;
}
UVerticalBox* UIBMenuScreen::BuildHangarPage(const FText& Hint)
{
	bHangarLayout = true;
	UOverlay* Root = WidgetTree->ConstructWidget<UOverlay>(); WidgetTree->RootWidget = Root;
	UImage* Background = WidgetTree->ConstructWidget<UImage>();
	Background->SetBrushFromTexture(LoadObject<UTexture2D>(nullptr, TEXT("/Game/IronBreach/UI/Hangar/T_MenuHangar.T_MenuHangar")));
	Background->SetVisibility(ESlateVisibility::HitTestInvisible);
	UOverlaySlot* BackgroundSlot = Root->AddChildToOverlay(Background);
	BackgroundSlot->SetHorizontalAlignment(HAlign_Fill); BackgroundSlot->SetVerticalAlignment(VAlign_Fill);
	UBorder* Shade = WidgetTree->ConstructWidget<UBorder>();
	Shade->SetBrushColor(FLinearColor(.002f,.009f,.018f,.28f)); // full-screen tint, never a framed card
	Shade->SetVisibility(ESlateVisibility::HitTestInvisible);
	UOverlaySlot* ShadeSlot = Root->AddChildToOverlay(Shade);
	ShadeSlot->SetHorizontalAlignment(HAlign_Fill); ShadeSlot->SetVerticalAlignment(VAlign_Fill);
	UVerticalBox* Sheet = WidgetTree->ConstructWidget<UVerticalBox>();
	Sheet->AddChildToVerticalBox(BuildMenuHeader(false));
	UVerticalBox* Body = WidgetTree->ConstructWidget<UVerticalBox>();
	UVerticalBoxSlot* BodySlot = Sheet->AddChildToVerticalBox(Body);
	BodySlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); BodySlot->SetPadding(FMargin(44,22,44,16));
	Sheet->AddChildToVerticalBox(IBMenuLayout::Text(WidgetTree, Hint, 10, FLinearColor(.52f,.64f,.70f),80))->SetPadding(FMargin(44,0,44,18));
	USizeBox* Design = IBMenuLayout::Width(WidgetTree, Sheet, 1600); Design->SetHeightOverride(900);
	UScaleBox* Fit = WidgetTree->ConstructWidget<UScaleBox>(); Fit->SetStretch(EStretch::ScaleToFit); Fit->SetContent(Design);
	UOverlaySlot* FitSlot = Root->AddChildToOverlay(Fit);
	FitSlot->SetHorizontalAlignment(HAlign_Fill); FitSlot->SetVerticalAlignment(VAlign_Fill);
	return Body;
}

IBMenuLayout::FPage UIBMenuScreen::BuildHangarSection(const FText& Title, const FText& Subtitle, const FText& Hint)
{
	IBMenuLayout::FPage Page;
	UVerticalBox* Sheet = BuildHangarPage(Hint);
	Page.Root = Cast<UOverlay>(WidgetTree->RootWidget);
	UHorizontalBox* Header = WidgetTree->ConstructWidget<UHorizontalBox>();
	UVerticalBox* TitleBox = WidgetTree->ConstructWidget<UVerticalBox>();
	TitleBox->AddChildToVerticalBox(IBHangar::Label(WidgetTree, Subtitle.ToString(), 11, IBHangar::Cyan()));
	TitleBox->AddChildToVerticalBox(IBMenuLayout::Heading(WidgetTree, Title, 36))->SetPadding(FMargin(0,4,0,0));
	Header->AddChildToHorizontalBox(TitleBox)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
	Page.HeaderRight = WidgetTree->ConstructWidget<UVerticalBox>();
	Header->AddChildToHorizontalBox(Page.HeaderRight)->SetVerticalAlignment(VAlign_Center);
	Sheet->AddChildToVerticalBox(Header)->SetPadding(FMargin(0,0,0,20));
	Page.Body = WidgetTree->ConstructWidget<UVerticalBox>();
	Sheet->AddChildToVerticalBox(Page.Body)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
	return Page;
}
