#pragma once

#include "CoreMinimal.h"
#include "UI/IBMenuScreen.h"
#include "IBMapScreen.generated.h"

class UCanvasPanel;
class UImage;
class UTextBlock;
class UIBMapMarkerWidget;
class UIBMapPOIComponent;
class UIBMapSubsystem;

/**
 * The zone map — the ground floor of the Director (roadmap M2 "director map
 * UI"). One zone for now; the multi-zone destination browser stacks on top of
 * this later without touching it.
 *
 *   drag ................ pan          wheel ............ zoom (cursor-centered)
 *   pin click ........... select → BP_OnPOISelected (Shane's info card)
 *   ActivateSelectedPOI . the info card's Deploy button → OnPOIActivated signal
 *
 * Player position updates live while open (Destiny doesn't do this in-zone;
 * it's a straight quality-of-life win for a 2 km walkable map).
 *
 * WBP structure (exact names, see MENUS_UI_WIRING.md §5):
 *   [clipping Overlay/SizeBox]
 *     └─ MapCanvas (Canvas Panel, Clipping = Clip to Bounds on the parent)
 *          ├─ MapImage      (Image, anchors 0..1, offsets 0 — fills the canvas)
 *          └─ (markers + PlayerMarkerImage are injected by C++)
 * MapCanvas should be authored at MapCanvasSize (default 2048²) via a Size Box
 * or canvas slot; the screen pans/zooms it with render transforms.
 */
UCLASS(Abstract)
class IRONBREACH_API UIBMapScreen : public UIBMenuScreen
{
	GENERATED_BODY()

public:
	/** Wire the info card's Deploy button here. Routes to UIBMapSubsystem. */
	UFUNCTION(BlueprintCallable, Category = "Map")
	void ActivateSelectedPOI();

	UFUNCTION(BlueprintPure, Category = "Map")
	UIBMapPOIComponent* GetSelectedPOI() const;

protected:
	virtual void NativeScreenOpened() override;
	virtual void NativeScreenClosed() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;
	virtual FReply NativeOnMouseButtonDown(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent) override;
	virtual FReply NativeOnMouseButtonUp(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent) override;
	virtual FReply NativeOnMouseMove(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent) override;
	virtual FReply NativeOnMouseWheel(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent) override;

	UFUNCTION(BlueprintImplementableEvent, Category = "Map", meta = (DisplayName = "On POI Selected"))
	void BP_OnPOISelected(UIBMapPOIComponent* POI);

	UFUNCTION(BlueprintImplementableEvent, Category = "Map", meta = (DisplayName = "On POI Deselected"))
	void BP_OnPOIDeselected();

	UFUNCTION()
	void HandleMapDataChanged();

	UFUNCTION()
	void HandleMarkerClicked(UIBMapMarkerWidget* Marker);

	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional), Category = "Map")
	TObjectPtr<UCanvasPanel> MapCanvas;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional), Category = "Map")
	TObjectPtr<UImage> MapImage;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional), Category = "Map")
	TObjectPtr<UTextBlock> ZoneNameText;

	/** Author this as an Image child of MapCanvas (so it pans/zooms with the
	 *  map); C++ only drives its position each frame while the screen is open. */
	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional), Category = "Map")
	TObjectPtr<UImage> PlayerMarkerImage;

	UPROPERTY(EditDefaultsOnly, Category = "Map")
	TSubclassOf<UIBMapMarkerWidget> MarkerClass;

	/** Authored pixel size of MapCanvas — marker math is UV * this. */
	UPROPERTY(EditDefaultsOnly, Category = "Map")
	FVector2D MapCanvasSize = FVector2D(2048.0f, 2048.0f);

	UPROPERTY(EditDefaultsOnly, Category = "Map", meta = (ClampMin = "0.1"))
	float MinZoom = 0.5f;

	UPROPERTY(EditDefaultsOnly, Category = "Map", meta = (ClampMin = "0.2"))
	float MaxZoom = 4.0f;

	UPROPERTY(EditDefaultsOnly, Category = "Map")
	float ZoomStep = 0.15f;

private:
	void RebuildMap();
	void RebuildMarkers();
	void ApplyViewTransform();
	void UpdatePlayerMarker();
	void SelectMarker(UIBMapMarkerWidget* Marker);
	void PositionOnCanvas(UWidget* Widget, const FVector2D& UV, const FVector2D& WidgetSize) const;

	UPROPERTY()
	TArray<TObjectPtr<UIBMapMarkerWidget>> Markers;

	UPROPERTY()
	TObjectPtr<UIBMapMarkerWidget> SelectedMarker;

	FVector2D PanOffset = FVector2D::ZeroVector;
	float ZoomLevel = 1.0f;
	bool bPanning = false;
	bool bMapDirty = false;
};
