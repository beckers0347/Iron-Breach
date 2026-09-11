#include "UI/IBMapScreen.h"
#include "IronBreach.h"
#include "UI/IBMenuLayout.h"
#include "World/IBMapSubsystem.h"
#include "World/IBMapPOIComponent.h"
#include "UI/IBMapMarkerWidget.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/Image.h"
#include "Components/TextBlock.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Components/Border.h"
#include "Blueprint/WidgetTree.h"
#include "Engine/Texture2D.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"

void UIBMapScreen::NativeOnInitialized()
{
	Super::NativeOnInitialized();

	// An authored map keeps its pan/zoom tree. The bare-WBP view explains the
	// missing cartography without exposing asset names to the player.
	if (!MapCanvas && !MapImage && WidgetTree)
	{
		const auto Page = IBMenuLayout::Begin(WidgetTree,
			NSLOCTEXT("IBMap", "Title", "TACTICAL MAP"),
			NSLOCTEXT("IBMap", "Kicker", "BREAKWATER / LOCAL RECONNAISSANCE"),
			NSLOCTEXT("IBMap", "Controls", "B / THE WATCH     Q E / SWITCH MENU     ESC / RETURN"));
		if (!Page.Body) { return; }
		Page.HeaderRight->AddChildToVerticalBox(IBMenuLayout::Text(WidgetTree,
			NSLOCTEXT("IBMap", "Uplink", "LOCAL CARTOGRAPHY / UNAVAILABLE"), 12, IBStyle::Amber(), 80));
		UHorizontalBox* Columns = WidgetTree->ConstructWidget<UHorizontalBox>();
		Page.Body->AddChildToVerticalBox(Columns)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
		UOverlay* Chart = WidgetTree->ConstructWidget<UOverlay>();
		UVerticalBox* Message = WidgetTree->ConstructWidget<UVerticalBox>();
		UTextBlock* Symbol = IBMenuLayout::Heading(WidgetTree, NSLOCTEXT("IBMap", "Signal", "[  /  ]"), 64);
		Symbol->SetColorAndOpacity(FLinearColor(.17f, .34f, .36f));
		Message->AddChildToVerticalBox(Symbol)->SetHorizontalAlignment(HAlign_Center);
		ZoneNameText = IBMenuLayout::Heading(WidgetTree, FText::GetEmpty(), 28);
		ZoneNameText->SetJustification(ETextJustify::Center);
		Message->AddChildToVerticalBox(ZoneNameText)->SetPadding(FMargin(0, 18, 0, 12));
		UTextBlock* Hint = IBMenuLayout::Text(WidgetTree,
			NSLOCTEXT("IBMap", "MissingChart", "No local survey is available for this area."), 14);
		Hint->SetJustification(ETextJustify::Center);
		Message->AddChildToVerticalBox(Hint);
		UOverlaySlot* MessageSlot = Chart->AddChildToOverlay(Message);
		MessageSlot->SetHorizontalAlignment(HAlign_Center);
		MessageSlot->SetVerticalAlignment(VAlign_Center);
		UHorizontalBoxSlot* ChartSlot = Columns->AddChildToHorizontalBox(IBMenuLayout::Card(WidgetTree, Chart));
		ChartSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
		ChartSlot->SetPadding(FMargin(0, 0, 16, 0));
		UVerticalBox* Intel = WidgetTree->ConstructWidget<UVerticalBox>();
		IBMenuLayout::Section(WidgetTree, Intel, NSLOCTEXT("IBMap", "Brief", "RECON BRIEF"));
		Intel->AddChildToVerticalBox(IBMenuLayout::Heading(WidgetTree,
			NSLOCTEXT("IBMap", "Awaiting", "AWAITING\nSURVEY DATA"), 28))->SetPadding(FMargin(0, 12, 0, 22));
		UTextBlock* Brief = IBMenuLayout::Text(WidgetTree,
			NSLOCTEXT("IBMap", "BriefBody", "Terrain and points of interest will appear here when local cartography is available.\n\nFor destinations and deployment, open the Watch with B."), 14);
		Brief->SetAutoWrapText(true);
		Intel->AddChildToVerticalBox(Brief);
		Columns->AddChildToHorizontalBox(IBMenuLayout::Width(WidgetTree, IBMenuLayout::Card(WidgetTree, Intel), 350));
	}
}

void UIBMapScreen::NativeScreenOpened()
{
	if (UIBMapSubsystem* MapSubsystem = GetWorld() ? GetWorld()->GetSubsystem<UIBMapSubsystem>() : nullptr)
	{
		MapSubsystem->OnMapDataChanged.RemoveDynamic(this, &UIBMapScreen::HandleMapDataChanged);
		MapSubsystem->OnMapDataChanged.AddDynamic(this, &UIBMapScreen::HandleMapDataChanged);
	}
	RebuildMap();
}

void UIBMapScreen::NativeScreenClosed()
{
	if (UIBMapSubsystem* MapSubsystem = GetWorld() ? GetWorld()->GetSubsystem<UIBMapSubsystem>() : nullptr)
	{
		MapSubsystem->OnMapDataChanged.RemoveDynamic(this, &UIBMapScreen::HandleMapDataChanged);
	}
	bPanning = false;
}

void UIBMapScreen::HandleMapDataChanged()
{
	// Coalesce to one rebuild per frame — World Partition streaming can register
	// a burst of POIs in a single tick as cells load.
	bMapDirty = true;
}

void UIBMapScreen::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);

	if (bMapDirty)
	{
		bMapDirty = false;
		RebuildMarkers();
	}
	UpdatePlayerMarker();
}

void UIBMapScreen::RebuildMap()
{
	UIBMapSubsystem* MapSubsystem = GetWorld() ? GetWorld()->GetSubsystem<UIBMapSubsystem>() : nullptr;
	UIBMapZoneData* Zone = MapSubsystem ? MapSubsystem->GetZoneData() : nullptr;

	if (ZoneNameText)
	{
		ZoneNameText->SetText(Zone ? Zone->ZoneName : NSLOCTEXT("IBMap", "NoSurvey", "AREA NOT SURVEYED"));
	}

	if (MapImage)
	{
		UTexture2D* Texture = Zone ? Zone->MapTexture.LoadSynchronous() : nullptr;
		if (Texture)
		{
			MapImage->SetBrushFromTexture(Texture);
		}
		MapImage->SetVisibility(Texture ? ESlateVisibility::Visible : ESlateVisibility::Hidden);
	}

	if (!Zone)
	{
		UE_LOG(LogIronBreach, Warning,
			TEXT("[MapScreen] No zone data — place an IBMapZoneInfo in the level and assign a DA_Map asset (MENUS_UI_WIRING.md §7)."));
	}

	RebuildMarkers();
	ApplyViewTransform();
}

void UIBMapScreen::RebuildMarkers()
{
	if (!MapCanvas) { return; }

	for (UIBMapMarkerWidget* Marker : Markers)
	{
		if (Marker) { Marker->RemoveFromParent(); }
	}
	Markers.Reset();
	if (SelectedMarker) // don't spam Shane's info card on every open
	{
		SelectedMarker = nullptr;
		BP_OnPOIDeselected();
	}

	UIBMapSubsystem* MapSubsystem = GetWorld() ? GetWorld()->GetSubsystem<UIBMapSubsystem>() : nullptr;
	UIBMapZoneData* Zone = MapSubsystem ? MapSubsystem->GetZoneData() : nullptr;
	if (!MapSubsystem || !Zone || !MarkerClass) { return; }

	for (UIBMapPOIComponent* POI : MapSubsystem->GetVisiblePOIs())
	{
		UIBMapMarkerWidget* Marker = CreateWidget<UIBMapMarkerWidget>(this, MarkerClass);
		if (!Marker) { continue; }

		Marker->InitFromPOI(POI);
		Marker->OnMarkerClicked.AddDynamic(this, &UIBMapScreen::HandleMarkerClicked);

		MapCanvas->AddChildToCanvas(Marker);
		PositionOnCanvas(Marker, Zone->WorldToMapUV(POI->GetPOIWorldLocation()), FVector2D(48.0f, 48.0f));
		Markers.Add(Marker);
	}

	// Player pip renders above every pin.
	if (PlayerMarkerImage)
	{
		PlayerMarkerImage->RemoveFromParent();
		MapCanvas->AddChildToCanvas(PlayerMarkerImage);
	}
}

void UIBMapScreen::PositionOnCanvas(UWidget* Widget, const FVector2D& UV, const FVector2D& WidgetSize) const
{
	if (UCanvasPanelSlot* CanvasSlot = Cast<UCanvasPanelSlot>(Widget->Slot))
	{
		CanvasSlot->SetAnchors(FAnchors(0.0f, 0.0f));
		CanvasSlot->SetAlignment(FVector2D(0.5f, 0.5f)); // centered on the point
		CanvasSlot->SetSize(WidgetSize);
		CanvasSlot->SetPosition(UV * MapCanvasSize);
		CanvasSlot->SetZOrder(10);
	}
}

void UIBMapScreen::UpdatePlayerMarker()
{
	if (!PlayerMarkerImage) { return; }

	UIBMapSubsystem* MapSubsystem = GetWorld() ? GetWorld()->GetSubsystem<UIBMapSubsystem>() : nullptr;
	UIBMapZoneData* Zone = MapSubsystem ? MapSubsystem->GetZoneData() : nullptr;
	const APlayerController* PC = GetOwningPlayer();
	const APawn* Pawn = PC ? PC->GetPawn() : nullptr;

	// Pawn can be gone mid-respawn; just hide the pip until it's back.
	const bool bCanShow = Zone && Pawn;
	PlayerMarkerImage->SetVisibility(bCanShow ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Hidden);
	if (bCanShow)
	{
		PositionOnCanvas(PlayerMarkerImage, Zone->WorldToMapUV(Pawn->GetActorLocation()), FVector2D(24.0f, 24.0f));
	}
}

// ---- Pan / zoom ----

void UIBMapScreen::ApplyViewTransform()
{
	if (!MapCanvas) { return; }

	// Soft clamp: keep at least a sliver of map in view. Pan/zoom persist
	// across opens (map muscle memory), so without this a hard fling could
	// lose the map permanently. Canvas is centered in its clip parent per the
	// WBP contract (wiring doc §5), so overlap per axis needs
	// |pan| <= (scaled + view)/2 - margin. Skipped before first layout.
	if (const UPanelWidget* ClipParent = MapCanvas->GetParent())
	{
		const FVector2D View = ClipParent->GetCachedGeometry().GetLocalSize();
		if (View.X > 1.0f && View.Y > 1.0f)
		{
			constexpr float Margin = 64.0f;
			const FVector2D Limit = (MapCanvasSize * ZoomLevel + View) * 0.5f - FVector2D(Margin, Margin);
			PanOffset.X = FMath::Clamp(PanOffset.X, -Limit.X, Limit.X);
			PanOffset.Y = FMath::Clamp(PanOffset.Y, -Limit.Y, Limit.Y);
		}
	}

	MapCanvas->SetRenderTransformPivot(FVector2D(0.5f, 0.5f));
	MapCanvas->SetRenderScale(FVector2D(ZoomLevel, ZoomLevel));
	MapCanvas->SetRenderTranslation(PanOffset);
}

FReply UIBMapScreen::NativeOnMouseButtonDown(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent)
{
	if (InMouseEvent.GetEffectingButton() == EKeys::LeftMouseButton)
	{
		// Markers consume their own clicks, so a down that reaches the
		// screen is always empty map: start panning.
		bPanning = true;
		return FReply::Handled().CaptureMouse(TakeWidget());
	}
	if (InMouseEvent.GetEffectingButton() == EKeys::RightMouseButton)
	{
		SelectMarker(nullptr); // dismiss the info card
		return FReply::Handled();
	}
	return Super::NativeOnMouseButtonDown(InGeometry, InMouseEvent);
}

FReply UIBMapScreen::NativeOnMouseButtonUp(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent)
{
	if (bPanning && InMouseEvent.GetEffectingButton() == EKeys::LeftMouseButton)
	{
		bPanning = false;
		return FReply::Handled().ReleaseMouseCapture();
	}
	return Super::NativeOnMouseButtonUp(InGeometry, InMouseEvent);
}

FReply UIBMapScreen::NativeOnMouseMove(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent)
{
	if (bPanning)
	{
		// Cursor delta is absolute (screen) space; route it through the
		// geometry so DPI scaling doesn't desync the drag from the cursor.
		const FVector2D Abs = InMouseEvent.GetScreenSpacePosition();
		PanOffset += InGeometry.AbsoluteToLocal(Abs)
			- InGeometry.AbsoluteToLocal(Abs - InMouseEvent.GetCursorDelta());
		ApplyViewTransform();
		return FReply::Handled();
	}
	return Super::NativeOnMouseMove(InGeometry, InMouseEvent);
}

FReply UIBMapScreen::NativeOnMouseWheel(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent)
{
	const float OldZoom = ZoomLevel;
	ZoomLevel = FMath::Clamp(ZoomLevel + InMouseEvent.GetWheelDelta() * ZoomStep * ZoomLevel, MinZoom, MaxZoom);
	if (FMath::IsNearlyEqual(OldZoom, ZoomLevel)) { return FReply::Handled(); }

	// Zoom toward the cursor: keep the point under the mouse stationary by
	// scaling its pivot-relative offset along with the canvas.
	const FVector2D LocalCenter = InGeometry.GetLocalSize() * 0.5f;
	const FVector2D LocalMouse = InGeometry.AbsoluteToLocal(InMouseEvent.GetScreenSpacePosition());
	const FVector2D MouseFromCenter = LocalMouse - LocalCenter - PanOffset;
	PanOffset -= MouseFromCenter * (ZoomLevel / OldZoom - 1.0f);

	ApplyViewTransform();
	return FReply::Handled();
}

// ---- Selection / deploy ----

void UIBMapScreen::HandleMarkerClicked(UIBMapMarkerWidget* Marker)
{
	SelectMarker(Marker);
}

void UIBMapScreen::SelectMarker(UIBMapMarkerWidget* Marker)
{
	if (SelectedMarker == Marker) { return; }

	if (SelectedMarker) { SelectedMarker->SetSelected(false); }
	SelectedMarker = Marker;

	if (SelectedMarker)
	{
		SelectedMarker->SetSelected(true);
		BP_OnPOISelected(SelectedMarker->GetPOI());
	}
	else
	{
		BP_OnPOIDeselected();
	}
}

UIBMapPOIComponent* UIBMapScreen::GetSelectedPOI() const
{
	return SelectedMarker ? SelectedMarker->GetPOI() : nullptr;
}

void UIBMapScreen::ActivateSelectedPOI()
{
	UIBMapPOIComponent* POI = GetSelectedPOI();
	UIBMapSubsystem* MapSubsystem = GetWorld() ? GetWorld()->GetSubsystem<UIBMapSubsystem>() : nullptr;
	if (POI && MapSubsystem)
	{
		MapSubsystem->RequestPOIActivation(POI);
	}
}
