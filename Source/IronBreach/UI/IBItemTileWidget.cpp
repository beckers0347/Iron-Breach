#include "UI/IBItemTileWidget.h"
#include "Items/IBItemDefinition.h"
#include "UI/IBUISettings.h"
#include "UI/IBStyleKit.h"
#include "UI/IBPaintKit.h"
#include "Components/Image.h"
#include "Components/TextBlock.h"
#include "Components/Border.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Components/SizeBox.h"
#include "Blueprint/WidgetTree.h"
#include "Engine/Texture2D.h"

void UIBItemGlyphWidget::NativeOnInitialized()
{
	Super::NativeOnInitialized();
	WidgetTree->RootWidget = WidgetTree->ConstructWidget<UOverlay>();
	SetVisibility(ESlateVisibility::HitTestInvisible);
}

void UIBItemGlyphWidget::SetGlyph(EIBItemCategory InCategory, EIBEquipSlot InSlot)
{
	Category = InCategory; EquipSlot = InSlot; InvalidateLayoutAndVolatility();
}

void UIBItemGlyphWidget::SetTint(FLinearColor InTint)
{
	Tint = InTint; InvalidateLayoutAndVolatility();
}

int32 UIBItemGlyphWidget::NativePaint(const FPaintArgs& Args, const FGeometry& Geo, const FSlateRect& Cull,
	FSlateWindowElementList& Out, int32 Layer, const FWidgetStyle& Style, bool Enabled) const
{
	const int32 Base = Super::NativePaint(Args, Geo, Cull, Out, Layer, Style, Enabled) + 1;
	const FVector2f Size(Geo.GetLocalSize());
	const FVector2f Center = Size * .5f;
	const float Scale = FMath::Min(Size.X, Size.Y) / 32.f;
	const FLinearColor Color = Tint * Style.GetColorAndOpacityTint();
	auto Stroke = [&](std::initializer_list<FVector2f> Points)
	{
		TArray<FVector2f> Path;
		for (const FVector2f P : Points) { Path.Add(Center + P * Scale); }
		IBPaint::Line(Out, Base, Geo, Path, Color, FMath::Max(1.f, Scale * 1.2f));
	};
	if (EquipSlot == EIBEquipSlot::ArmorHead)
	{
		Stroke({{-8,-8},{-5,-12},{5,-12},{8,-8},{9,4},{5,10},{-5,10},{-9,4},{-8,-8}});
		Stroke({{-7,-3},{-2,0},{2,0},{7,-3}}); Stroke({{0,1},{0,7}});
	}
	else if (EquipSlot == EIBEquipSlot::ArmorArms)
	{
		Stroke({{-7,-11},{5,-9},{8,-3},{4,1},{5,9},{0,12},{-6,8},{-7,-11}});
		Stroke({{-6,-3},{5,-1}}); Stroke({{-5,5},{4,6}});
	}
	else if (EquipSlot == EIBEquipSlot::ArmorLegs)
	{
		Stroke({{-10,-11},{-1,-10},{-2,5},{-1,11},{-11,11},{-10,6},{-10,-11}});
		Stroke({{1,-10},{10,-11},{10,6},{11,11},{1,11},{2,5},{1,-10}});
		Stroke({{-9,1},{-3,1}}); Stroke({{3,1},{9,1}});
	}
	else if (EquipSlot == EIBEquipSlot::ArmorChest || Category == EIBItemCategory::Armor)
	{
		Stroke({{-5,-11},{0,-8},{5,-11},{12,-7},{10,0},{7,-1},{6,11},{-6,11},{-7,-1},{-10,0},{-12,-7},{-5,-11}});
		Stroke({{-5,-2},{0,1},{5,-2}}); Stroke({{0,1},{0,9}});
	}
	else if (EquipSlot == EIBEquipSlot::GearAntiKaiju || Category == EIBItemCategory::Consumable)
	{
		Stroke({{-4,-12},{4,-12},{4,-8},{7,-5},{7,9},{4,12},{-4,12},{-7,9},{-7,-5},{-4,-8},{-4,-12}});
		Stroke({{-5,-4},{5,-4}}); Stroke({{-5,7},{5,7}}); Stroke({{-3,1},{3,1}}); Stroke({{0,-2},{0,4}});
	}
	else if (Category == EIBItemCategory::Weapon || EquipSlot == EIBEquipSlot::WeaponPrimary || EquipSlot == EIBEquipSlot::WeaponSpecial || EquipSlot == EIBEquipSlot::WeaponHeavy)
	{
		Stroke({{-13,-2},{-9,-2},{-9,-5},{6,-5},{9,-2},{14,-2},{14,1},{5,1},{2,4},{-3,4},{-5,10},{-9,9},{-7,2},{-13,5},{-13,-2}});
		Stroke({{-4,-5},{-4,-8},{3,-8},{3,-5}}); Stroke({{-1,4},{2,10},{5,9},{3,3}});
	}
	else if (Category == EIBItemCategory::KaijuMaterial)
	{
		Stroke({{-11,-5},{-5,-11},{2,-8},{4,0},{-2,6},{-10,3},{-11,-5}});
		Stroke({{-5,-11},{-3,-2},{4,0}}); Stroke({{-3,-2},{-10,3}});
		Stroke({{4,-5},{10,-2},{12,7},{5,12},{-1,8}}); Stroke({{4,2},{6,7},{12,7}});
	}
	else if (Category == EIBItemCategory::Splice)
	{
		Stroke({{0,-12},{10,-6},{10,6},{0,12},{-10,6},{-10,-6},{0,-12}});
		IBPaint::Ring(Out, Base, Geo, Center, 4 * Scale, Color, FMath::Max(1.f, Scale));
	}
	else if (Category == EIBItemCategory::Doctrine)
	{
		Stroke({{0,-13},{11,0},{0,13},{-11,0},{0,-13}}); Stroke({{-4,3},{0,-5},{4,3},{-4,3}});
	}
	else if (Category == EIBItemCategory::Collectible)
	{
		Stroke({{-8,-12},{4,-12},{9,-7},{9,12},{-8,12},{-8,-12}}); Stroke({{4,-12},{4,-7},{9,-7}});
		Stroke({{-4,-3},{5,-3}}); Stroke({{-4,2},{5,2}}); Stroke({{-4,7},{2,7}});
	}
	else if (Category == EIBItemCategory::Cosmetic)
	{
		Stroke({{-5,-11},{5,-11},{11,11},{4,9},{0,12},{-4,9},{-11,11},{-5,-11}}); Stroke({{-2,-7},{-4,6}}); Stroke({{2,-7},{4,6}});
	}
	else
	{
		for (const FVector2f P : {FVector2f(-10,-10), FVector2f(2,-10), FVector2f(-10,2), FVector2f(2,2)})
		{ Stroke({P,P+FVector2f(8,0),P+FVector2f(8,8),P+FVector2f(0,8),P}); }
	}
	return Base;
}

void UIBItemTileWidget::NativeOnInitialized()
{
	Super::NativeOnInitialized();

	// Bare WBP (or raw C++ tile): build the square ourselves — rarity frame,
	// icon fill, name label for icon-less early content, stack count corner.
	if (!RarityBorder && !IconImage && WidgetTree)
	{
		USizeBox* Size = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
		Size->SetWidthOverride(112.f);
		Size->SetHeightOverride(96.f);
		WidgetTree->RootWidget = Size;

		UBorder* Frame = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
		Frame->SetBrush(IBStyle::RoundedBrush(FLinearColor::Transparent, 0.f));
		Frame->SetPadding(FMargin(2.f));
		Size->AddChild(Frame);

		UBorder* Inner = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
		Inner->SetBrush(IBStyle::RoundedBrush(FLinearColor::Transparent, 0.f));
		Inner->SetPadding(FMargin(0.f));
		Frame->SetContent(Inner);

		UOverlay* Stack = WidgetTree->ConstructWidget<UOverlay>(UOverlay::StaticClass());
		Inner->SetContent(Stack);
		FallbackGlyph = CreateWidget<UIBItemGlyphWidget>(this);
		USizeBox* GlyphSize = WidgetTree->ConstructWidget<USizeBox>();
		GlyphSize->SetWidthOverride(42.f); GlyphSize->SetHeightOverride(42.f); GlyphSize->SetContent(FallbackGlyph);
		UOverlaySlot* GlyphSlot = Stack->AddChildToOverlay(GlyphSize);
		GlyphSlot->SetHorizontalAlignment(HAlign_Center); GlyphSlot->SetVerticalAlignment(VAlign_Center);
		GlyphSlot->SetPadding(FMargin(0,0,0,10));

		UImage* Icon = WidgetTree->ConstructWidget<UImage>(UImage::StaticClass());
		if (UOverlaySlot* IconSlot = Stack->AddChildToOverlay(Icon))
		{
			IconSlot->SetHorizontalAlignment(HAlign_Fill);
			IconSlot->SetVerticalAlignment(VAlign_Fill);
			IconSlot->SetPadding(FMargin(5.f));
		}

		UTextBlock* Name = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
		FSlateFontInfo NameFont = Name->GetFont();
		NameFont.Size = 10;
		Name->SetFont(NameFont);
		Name->SetJustification(ETextJustify::Center);
		Name->SetAutoWrapText(true);
		Name->SetColorAndOpacity(FSlateColor(FLinearColor(0.85f, 0.9f, 1.f)));
		if (UOverlaySlot* NameSlot = Stack->AddChildToOverlay(Name))
		{
			NameSlot->SetHorizontalAlignment(HAlign_Center);
			NameSlot->SetVerticalAlignment(VAlign_Bottom);
			NameSlot->SetPadding(FMargin(6.f,0.f,6.f,7.f));
		}

		UTextBlock* Count = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
		FSlateFontInfo CountFont = Count->GetFont();
		CountFont.Size = 11;
		Count->SetFont(CountFont);
		Count->SetColorAndOpacity(FSlateColor(FLinearColor::White));
		Count->SetShadowOffset(FVector2D(1.f, 1.f));
		if (UOverlaySlot* CountSlot = Stack->AddChildToOverlay(Count))
		{
			CountSlot->SetHorizontalAlignment(HAlign_Right);
			CountSlot->SetVerticalAlignment(VAlign_Bottom);
			CountSlot->SetPadding(FMargin(0.f, 0.f, 5.f, 3.f));
		}

		TileSurface = Inner;
		RarityBorder = Frame;
		IconImage = Icon;
		NameText = Name;
		StackText = Count;
	}

	RefreshVisuals();
}

void UIBItemTileWidget::SetItem(const FIBItemInstance& InItem)
{
	Item = InItem;
	Definition = InItem.Definition;
	RepresentedSlot = Definition ? Definition->EquipSlot : EIBEquipSlot::None;
	bLocked = false;
	RefreshVisuals();
}

void UIBItemTileWidget::SetPresentationSize(FVector2D Size)
{
	// Only the native fallback owns a SizeBox; leave authored WBP trees alone.
	if (TileSurface && WidgetTree)
	{
		if (USizeBox* Frame = Cast<USizeBox>(WidgetTree->RootWidget))
		{
			Frame->SetWidthOverride(FMath::Max(48.f, Size.X));
			Frame->SetHeightOverride(FMath::Max(48.f, Size.Y));
		}
	}
}

void UIBItemTileWidget::SetSelected(bool bInSelected)
{
	if (bSelected == bInSelected) { return; }
	bSelected = bInSelected;
	RefreshVisuals();
}

void UIBItemTileWidget::SetLocked(const UIBItemDefinition* InDefinition)
{
	Item = FIBItemInstance();
	Definition = InDefinition;
	RepresentedSlot = EIBEquipSlot::None;
	bLocked = true;
	RefreshVisuals();
}

void UIBItemTileWidget::SetEmptySlot(EIBEquipSlot InSlot)
{
	Item = FIBItemInstance();
	Definition = nullptr;
	RepresentedSlot = InSlot;
	bLocked = false;
	RefreshVisuals();
}

void UIBItemTileWidget::RefreshVisuals()
{
	UTexture2D* IconTexture = Definition ? Definition->Icon.LoadSynchronous() : nullptr;
	if (IconImage)
	{
		if (IconTexture)
		{
			IconImage->SetBrushFromTexture(IconTexture);
		}
		IconImage->SetVisibility(IconTexture ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Hidden);
		// Silhouette: black out the icon, keep the shape — the classic
		// "you haven't found this yet" read.
		IconImage->SetColorAndOpacity(bLocked ? LockedTint : FLinearColor::White);
	}
	if (FallbackGlyph)
	{
		FallbackGlyph->SetGlyph(Definition ? Definition->Category : EIBItemCategory::None, RepresentedSlot);
		FallbackGlyph->SetTint(Definition ? IBStyle::TextHi() : FLinearColor(.26f,.47f,.56f,.65f));
		FallbackGlyph->SetVisibility(IconTexture ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible);
	}

	if (StackText)
	{
		const bool bShowStack = !bLocked && Item.IsValid() && Item.StackCount > 1;
		StackText->SetText(FText::AsNumber(Item.StackCount));
		StackText->SetVisibility(bShowStack ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
	}

	if (NameText)
	{
		// Icon-less content (most of it, this early) reads as a labeled chip;
		// once real icons land the label collapses automatically.
		const bool bHasIcon = IconTexture != nullptr;
		if (bLocked)
		{
			NameText->SetText(NSLOCTEXT("IBTile", "Sealed", "DATA\nSEALED"));
		}
		else if (Definition)
		{
			NameText->SetText(Definition->DisplayName);
		}
		else
		{
			NameText->SetText(NSLOCTEXT("IBTile", "Empty", "UNASSIGNED"));
		}
		NameText->SetColorAndOpacity(Definition && !bLocked ? IBStyle::TextHi() : IBStyle::TextLo());
		NameText->SetVisibility((!bHasIcon)
			? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
	}

	if (RarityBorder)
	{
		FLinearColor Frame = FLinearColor(0.1f, 0.1f, 0.1f, 0.6f); // empty-well default
		if (Definition)
		{
			Frame = UIBUISettings::Get()->GetRarityColor(Definition->Rarity);
			if (bLocked)
			{
				Frame *= 0.35f; // dimmed frame still whispers the rarity
				Frame.A = 1.0f;
			}
		}
		RarityBorder->SetBrushColor(TileSurface ? FLinearColor::Transparent : (bSelected ? FLinearColor(.3f,.85f,1.f) : Frame));
	}

	BP_OnTileUpdated();
}

int32 UIBItemTileWidget::NativePaint(const FPaintArgs& Args, const FGeometry& Geo, const FSlateRect& Cull,
	FSlateWindowElementList& Out, int32 Layer, const FWidgetStyle& Style, bool Enabled) const
{
	if (!TileSurface) { return Super::NativePaint(Args, Geo, Cull, Out, Layer, Style, Enabled); }
	const FVector2f Size(Geo.GetLocalSize());
	const FLinearColor Tint = Style.GetColorAndOpacityTint();
	const FLinearColor Rarity = Definition ? UIBUISettings::Get()->GetRarityColor(Definition->Rarity) : FLinearColor(.13f,.29f,.34f);
	const float Strength = bLocked ? .12f : (Definition ? .26f : .07f);
	IBPaint::Gradient(Out, Layer, Geo, FVector2f::ZeroVector, Size,
		FLinearColor(.003f,.009f,.015f,.9f) * Tint,
		FLinearColor(Rarity.R*Strength, Rarity.G*Strength, Rarity.B*Strength,.86f) * Tint);
	IBPaint::Line(Out, Layer+1, Geo, {{1,1},{Size.X-1,1},{Size.X-1,Size.Y-1},{1,Size.Y-1},{1,1}},
		IBPaint::Alpha(Rarity, bLocked ? .3f : .95f) * Tint, 1.f);
	const int32 Base = Super::NativePaint(Args, Geo, Cull, Out, Layer+2, Style, Enabled);
	if (Definition && !bLocked)
	{
		IBPaint::Diamond(Out, Base+1, Geo, FVector2f(9,Size.Y-9), 3.f, Rarity * Tint, 1.f);
		IBPaint::Seg(Out, Base+1, Geo, FVector2f(1,1), FVector2f(Size.X*.42f,1), IBPaint::Alpha(Rarity,.8f) * Tint, 2.f);
	}
	if (bSelected || bHovered)
	{
		const FLinearColor Accent = (bSelected ? FLinearColor(.7f,.95f,1.f) : FLinearColor(.4f,.72f,.83f)) * Tint;
		IBPaint::Line(Out, Base+2, Geo, {{0,14},{0,0},{14,0}}, Accent, 2.f);
		IBPaint::Line(Out, Base+2, Geo, {{Size.X-14,Size.Y},{Size.X,Size.Y},{Size.X,Size.Y-14}}, Accent, 2.f);
	}
	return Base+2;
}

FReply UIBItemTileWidget::NativeOnMouseButtonDown(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent)
{
	if (InMouseEvent.GetEffectingButton() == EKeys::LeftMouseButton)
	{
		OnTileClicked.Broadcast(this);
		return FReply::Handled();
	}
	return Super::NativeOnMouseButtonDown(InGeometry, InMouseEvent);
}

void UIBItemTileWidget::NativeOnMouseEnter(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent)
{
	Super::NativeOnMouseEnter(InGeometry, InMouseEvent);
	bHovered = true; InvalidateLayoutAndVolatility();
	OnTileHoverChanged.Broadcast(this, true);
}

void UIBItemTileWidget::NativeOnMouseLeave(const FPointerEvent& InMouseEvent)
{
	Super::NativeOnMouseLeave(InMouseEvent);
	bHovered = false; InvalidateLayoutAndVolatility();
	OnTileHoverChanged.Broadcast(this, false);
}
