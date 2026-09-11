#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Online/IBWatchTypes.h"
#include "IBPlanetWidget.generated.h"

class UImage;
class UMaterialInterface;
class UMaterialInstanceDynamic;
class UTextureRenderTarget2D;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnIBSectorPicked, FName, SectorId);

/**
 * The planet outside the command deck window. A full-screen UImage whose brush
 * is M_WatchPlanet (a UI-domain material that ray-casts a unit sphere per
 * pixel — Scripts/ib_build_watch_materials.py has the shader); this widget
 * owns the camera, feeds the material its parameters every tick, and paints
 * everything that has to know where a point on the planet is on screen: the
 * sector pins (diamond markers with a hex-grid halo), the callout box, the
 * drop sequence and the deck framing around the glass.
 *
 * The world is generated once, at startup: M_WatchMap is drawn into a
 * 2048x1024 render target, read back to place every sector pin on a coastline
 * (kaiju come out of the sea) and to pick the sea level, then handed to the
 * planet material. No textures, no content — Shane can still swap in a real
 * planet material later by pointing PlanetMaterialPath somewhere else.
 *
 * Camera model (mirrors the mockup): the camera sits on +Z at Dist, looks down
 * -Z at the planet's centre, and the image plane is shifted by (Sx, Sy) so the
 * planet can sit left of the card. Orbit view spins freely (drag, wheel zoom);
 * the sector view parks the camera over the home sector; the drop falls onto
 * the armed sector. Dive blends orbit -> sector, Drop 0..1 plays the fall.
 */
UCLASS()
class IRONBREACH_API UIBPlanetWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	UPROPERTY(BlueprintAssignable, Category = "Watch")
	FOnIBSectorPicked OnSectorPicked;

	/** Double-click on a live sector: open its breach board. */
	UPROPERTY(BlueprintAssignable, Category = "Watch")
	FOnIBSectorPicked OnSectorOpened;

	/** 0 = orbit (pins live, drag/zoom on), 1 = parked over the home sector; eased blend in between. */
	void SetDive(float InDive);

	/** Drop sequence progress 0..1 toward SectorId; < 0 = not dropping. Fades the pins, dives the camera, flashes. */
	void SetDrop(float InDrop, FName SectorId);

	/** What the callout box beside the selected pin says. */
	void SetSelection(FName SectorId, const FText& CalloutName, const FText& CalloutSub);

	FName GetSelectedSector() const { return SelectedSector; }
	FName GetHoverSector() const { return HoverSector; }

	/** Screen (local) position of a sector pin and how visible it is (0 = behind the limb). */
	bool GetSectorScreen(FName SectorId, FVector2D& OutLocal, float& OutVisibility) const;

	/** The world has been baked and the pins snapped. */
	bool IsReady() const { return bMapReady; }

	/** Where the breach board sits for a given screen size (shared with UIBWatchScreen so the camera parks behind it). */
	static void BoardRect(const FVector2D& ScreenSize, FVector2D& OutPos, FVector2D& OutSize);

protected:
	virtual void NativeOnInitialized() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;
	virtual int32 NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
		FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;
	virtual FReply NativeOnMouseButtonDown(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent) override;
	virtual FReply NativeOnMouseButtonUp(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent) override;
	virtual FReply NativeOnMouseMove(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent) override;
	virtual FReply NativeOnMouseWheel(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent) override;
	virtual FReply NativeOnMouseButtonDoubleClick(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent) override;
	virtual void NativeOnMouseLeave(const FPointerEvent& InMouseEvent) override;

private:
	struct FCam
	{
		float Dist = 2.9f;
		float Sx = 0.f;
		float Sy = 0.f;
		FQuat Q = FQuat::Identity; // planet frame -> world (camera) frame
	};

	struct FSectorPin
	{
		FName Id;
		FVector Unit = FVector::ZAxisVector; // planet-frame unit vector
		float Lat = 0.f;
		float Lon = 0.f;
		FVector2D Screen = FVector2D::ZeroVector;
		float Vis = 0.f;
		float Phase = 0.f;
	};

	void BuildLayout();
	void LoadMaterials();
	void BakeMap();
	bool ReadBackMap();
	void PlaceSectors();
	void PickStorm();
	void UpdateMaterial(const FVector2D& Size);

	FCam OrbitCam(const FVector2D& Size) const;
	FCam SectorCam(const FVector2D& Size) const;
	static FCam LerpCam(const FCam& A, const FCam& B, float T);
	static FQuat LookAt(const FVector& PlanetUnit);
	FQuat OrbitRotation() const;
	float OrbitDistance(const FVector2D& Size) const;

	/** Local widget position of a world-frame unit vector under Cam; Vis 0..1 (limb fade). */
	FVector2D Project(const FVector& World, const FVector2D& Size, const FCam& Cam, float& OutVis) const;
	FName PinAt(const FVector2D& Local) const;

	// ---- the world (baked once) ----
	static constexpr int32 MapW = 2048;
	static constexpr int32 MapH = 1024;
	bool IsLand(int32 X, int32 Y) const;
	void CoastSnap(float& Lat, float& Lon) const;
	float OceanFraction(float Lat, float Lon, int32 RadiusTexels) const;

	UPROPERTY(Transient) TObjectPtr<UImage> PlanetImage;
	UPROPERTY(Transient) TObjectPtr<UMaterialInterface> MapMaterial;
	UPROPERTY(Transient) TObjectPtr<UMaterialInterface> PlanetMaterial;
	UPROPERTY(Transient) TObjectPtr<UMaterialInstanceDynamic> PlanetMID;
	UPROPERTY(Transient) TObjectPtr<UTextureRenderTarget2D> MapRT;

	TArray<FColor> MapPixels;
	uint8 SeaByte = 128;
	float SeaLevel = 0.5f;
	bool bMapReady = false;
	int32 BakeAttempts = 0;
	float BakeRetry = 0.f;

	TArray<FSectorPin> Pins;
	FVector StormUnit = FVector(0.3f, 0.3f, 0.9f);

	// ---- camera state ----
	float Spin = 0.f;
	float Pitch = 0.22f;
	float ZoomScale = 1.f;       // multiplier on the fitted orbit distance
	float ZoomTarget = 1.f;
	float Dive = 0.f;
	float Drop = -1.f;
	FName DropSector;
	FCam DropFrom;
	bool bDropFromValid = false;
	FCam Cam;
	FVector2D LastSize = FVector2D(1600.0, 900.0);
	float Time = 0.f;

	// ---- interaction ----
	FName SelectedSector;
	FName HoverSector;
	FText CalloutName;
	FText CalloutSub;
	bool bDragging = false;
	FVector2D DragLast = FVector2D::ZeroVector;
	float DragMoved = 0.f;
	FName PressSector;
};
