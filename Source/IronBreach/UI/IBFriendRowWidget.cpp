#include "UI/IBFriendRowWidget.h"
#include "UI/IBStyleKit.h"
#include "Components/SizeBox.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"

void UIBFriendRowWidget::NativeOnInitialized()
{
	Super::NativeOnInitialized();
	BuildLayout();
}

void UIBFriendRowWidget::BuildLayout()
{
	if (!WidgetTree || NameText) { return; }

	USizeBox* Frame = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
	Frame->SetHeightOverride(46.f);
	WidgetTree->RootWidget = Frame;

	// Surface carries the hover / focus fill for the whole line; the lane holds
	// a 3 px lead edge beside the original row, which is otherwise untouched.
	Surface = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
	Frame->AddChild(Surface);
	UHorizontalBox* Lane = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
	Surface->SetContent(Lane);

	LeadEdge = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
	USizeBox* EdgeBox = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
	EdgeBox->SetWidthOverride(3.f);
	EdgeBox->AddChild(LeadEdge);
	if (UHorizontalBoxSlot* EdgeSlot = Lane->AddChildToHorizontalBox(EdgeBox))
	{
		EdgeSlot->SetVerticalAlignment(VAlign_Fill);
	}

	UHorizontalBox* Row = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
	if (UHorizontalBoxSlot* RowSlot = Lane->AddChildToHorizontalBox(Row))
	{
		RowSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
		RowSlot->SetPadding(FMargin(9.f, 0.f, 4.f, 0.f));
	}

	// Presence dot.
	USizeBox* DotBox = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
	DotBox->SetWidthOverride(9.f);
	DotBox->SetHeightOverride(9.f);
	PresenceDot = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
	PresenceDot->SetBrush(IBStyle::RoundedBrush(IBStyle::TextLo(), 4.5f));
	DotBox->AddChild(PresenceDot);
	if (UHorizontalBoxSlot* DotSlot = Row->AddChildToHorizontalBox(DotBox))
	{
		DotSlot->SetVerticalAlignment(VAlign_Center);
		DotSlot->SetPadding(FMargin(2.f, 0.f, 10.f, 0.f));
	}

	// Name + presence subline.
	UVerticalBox* NameCol = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	NameText = IBStyle::MakeText(WidgetTree, FText::GetEmpty(), 13, IBStyle::TextHi(), 100);
	SubText = IBStyle::MakeText(WidgetTree, FText::GetEmpty(), 9, IBStyle::TextLo(), 300);
	NameCol->AddChildToVerticalBox(NameText);
	NameCol->AddChildToVerticalBox(SubText);
	if (UHorizontalBoxSlot* NameSlot = Row->AddChildToHorizontalBox(NameCol))
	{
		NameSlot->SetVerticalAlignment(VAlign_Center);
		NameSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
	}

	// Context action chip.
	UTextBlock* RawActionLabel = nullptr;
	ActionButton = IBStyle::MakeButton(WidgetTree, FText::GetEmpty(), 11, false, &RawActionLabel);
	ActionLabel = RawActionLabel;
	ActionButton->OnClicked.AddDynamic(this, &UIBFriendRowWidget::HandleActionClicked);
	if (UHorizontalBoxSlot* ActionSlot = Row->AddChildToHorizontalBox(ActionButton))
	{
		ActionSlot->SetVerticalAlignment(VAlign_Center);
	}

	ApplyStateVisuals();
}

void UIBFriendRowWidget::ApplyStateVisuals()
{
	if (!Surface) { return; }
	// Flat at rest — a list of outlined boxes is exactly what the panel should
	// not look like. Hover fills faintly; focus fills further and lights the
	// lead edge, which is the tell that survives when the pointer is elsewhere.
	const FLinearColor Fill = bFocused ? FLinearColor(.045f, .165f, .205f, .95f)
		: bHovered ? FLinearColor(.028f, .105f, .135f, .80f)
		: FLinearColor::Transparent;
	Surface->SetBrush(IBStyle::RoundedBrush(Fill, 0.f,
		bFocused ? IBStyle::Cyan() : FLinearColor::Transparent, bFocused ? 1.f : 0.f));
	if (LeadEdge)
	{
		LeadEdge->SetBrush(IBStyle::RoundedBrush(bFocused ? IBStyle::Cyan()
			: bHovered ? IBStyle::Line() : FLinearColor::Transparent, 0.f));
	}
}

void UIBFriendRowWidget::NativeOnMouseEnter(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent)
{
	Super::NativeOnMouseEnter(InGeometry, InMouseEvent);
	bHovered = true;
	ApplyStateVisuals();
}

void UIBFriendRowWidget::NativeOnMouseLeave(const FPointerEvent& InMouseEvent)
{
	Super::NativeOnMouseLeave(InMouseEvent);
	bHovered = false;
	ApplyStateVisuals();
}

void UIBFriendRowWidget::NativeOnAddedToFocusPath(const FFocusEvent& InFocusEvent)
{
	Super::NativeOnAddedToFocusPath(InFocusEvent);
	bFocused = true;
	ApplyStateVisuals();
}

void UIBFriendRowWidget::NativeOnRemovedFromFocusPath(const FFocusEvent& InFocusEvent)
{
	Super::NativeOnRemovedFromFocusPath(InFocusEvent);
	bFocused = false;
	ApplyStateVisuals();
}

void UIBFriendRowWidget::InitRow(const FIBFriendInfo& InInfo, bool bCanInvite)
{
	BuildLayout();
	Info = InInfo;

	const FLinearColor Dot = Info.bPlayingThisGame ? IBStyle::Cyan()
		: Info.bOnline ? FLinearColor(0.30f, 0.65f, 0.35f)
		: FLinearColor(0.25f, 0.29f, 0.36f);
	PresenceDot->SetBrush(IBStyle::RoundedBrush(Dot, 4.5f));

	NameText->SetText(FText::FromString(Info.DisplayName));
	NameText->SetColorAndOpacity(FSlateColor(Info.bOnline ? IBStyle::TextHi() : IBStyle::TextLo()));
	SubText->SetText(Info.bPlayingThisGame
		? NSLOCTEXT("IBFriends", "InGame", "IN IRON BREACH")
		: Info.bOnline ? NSLOCTEXT("IBFriends", "Online", "ONLINE")
		               : NSLOCTEXT("IBFriends", "Offline", "OFFLINE"));

	// Context action: chase them, or pull them in.
	bJoinAction = Info.bPlayingThisGame;
	const bool bShowAction = Info.bPlayingThisGame || (Info.bOnline && bCanInvite);
	ActionButton->SetVisibility(bShowAction ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
	if (bShowAction)
	{
		ActionLabel->SetText(bJoinAction
			? NSLOCTEXT("IBFriends", "Join", "JOIN")
			: NSLOCTEXT("IBFriends", "Invite", "INVITE"));
		IBStyle::StyleButton(ActionButton, /*bAccent=*/bJoinAction);
	}
}

void UIBFriendRowWidget::HandleActionClicked()
{
	OnAction.Broadcast(Info.NetIdStr, bJoinAction);
}
