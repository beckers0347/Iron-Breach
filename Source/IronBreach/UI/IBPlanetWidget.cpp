#include "UI/IBPlanetWidget.h"
#include "UI/IBPaintKit.h"
#include "UI/IBStyleKit.h"
#include "IronBreach.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Image.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Materials/MaterialInterface.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Engine/TextureRenderTarget2D.h"
#include "Engine/World.h"
#include "Kismet/KismetRenderingLibrary.h"
#include "TextureResource.h"

namespace IBPlanetLayout
{
	constexpr float CardW      = 400.f;  // UIBWatchScreen's card width — keep in sync
	constexpr float PillarW    = 72.f;   // the deck's left pillar
	constexpr float ConsoleH   = 84.f;   // the deck's console along the bottom
	constexpr float TanHalfFov = 0.36397f; // tan(20 deg): 40 deg vertical field of view
	constexpr float SectorDist = 1.55f;
	constexpr float DropDist   = 1.04f;
	constexpr float SpinRate   = 2.f * PI / 260.f; // one turn every ~4 minutes

	const FVector Sun = FVector(0.60f, 0.38f, 0.58f).GetSafeNormal();

	inline FVector LL2V(float LatDeg, float LonDeg)
	{
		const float La = FMath::DegreesToRadians(LatDeg), Lo = FMath::DegreesToRadians(LonDeg);
		const float Cl = FMath::Cos(La);
		// -sin(lon) so that, facing the globe with north up, east is to the right
		return FVector(Cl * FMath::Cos(Lo), FMath::Sin(La), -Cl * FMath::Sin(Lo));
	}

	inline float SmoothStep(float A, float B, float X)
	{
		const float T = FMath::Clamp((X - A) / (B - A), 0.f, 1.f);
		return T * T * (3.f - 2.f * T);
	}

	inline FLinearColor Col(float R, float G, float B, float A = 1.f) { return FLinearColor(R, G, B, A); }
}

namespace IBPL = IBPlanetLayout;

// ============================================================================ layout / lifecycle

void UIBPlanetWidget::BoardRect(const FVector2D& ScreenSize, FVector2D& OutPos, FVector2D& OutSize)
{
	const float Vista = FMath::Max(420.f, static_cast<float>(ScreenSize.X) - IBPL::CardW - 56.f);
	const float AX = 92.f, AY = 150.f;
	const float AW = Vista - AX - 12.f;
	const float AH = static_cast<float>(ScreenSize.Y) - AY - 120.f;
	float W = AW, H = W / 1.5f;
	if (H > AH) { H = AH; W = H * 1.5f; }
	OutPos = FVector2D(AX + (AW - W) * 0.5f, AY + (AH - H) * 0.5f);
	OutSize = FVector2D(W, H);
}

void UIBPlanetWidget::NativeOnInitialized()
{
	Super::NativeOnInitialized();
	BuildLayout();
	LoadMaterials();
	SetVisibility(ESlateVisibility::Visible); // we are the hit target for drag / zoom / pins

	// pins start where the data says; BakeMap() snaps them to the coast once the world exists
	Pins.Reset();
	int32 i = 0;
	for (const FIBSector& S : IBWatch::Sectors())
	{
		FSectorPin P;
		P.Id = S.Id;
		P.Lat = S.Latitude;
		P.Lon = S.Longitude;
		P.Unit = IBPL::LL2V(P.Lat, P.Lon);
		P.Phase = 0.13f * (i++);
		Pins.Add(P);
	}
	BakeMap();
}

void UIBPlanetWidget::BuildLayout()
{
	if (!WidgetTree || PlanetImage) { return; }
	UOverlay* Root = Cast<UOverlay>(WidgetTree->RootWidget);
	if (!Root)
	{
		Root = WidgetTree->ConstructWidget<UOverlay>(UOverlay::StaticClass());
		WidgetTree->RootWidget = Root;
	}
	PlanetImage = WidgetTree->ConstructWidget<UImage>(UImage::StaticClass());
	PlanetImage->SetVisibility(ESlateVisibility::HitTestInvisible);
	PlanetImage->SetColorAndOpacity(FLinearColor::White);
	PlanetImage->SetBrushTintColor(FSlateColor(FLinearColor::White));
	if (UOverlaySlot* S = Root->AddChildToOverlay(PlanetImage))
	{
		S->SetHorizontalAlignment(HAlign_Fill);
		S->SetVerticalAlignment(VAlign_Fill);
	}
}

void UIBPlanetWidget::LoadMaterials()
{
	MapMaterial = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/IronBreach/Watch/M_WatchMap.M_WatchMap"));
	PlanetMaterial = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/IronBreach/Watch/M_WatchPlanet.M_WatchPlanet"));
	if (!PlanetMaterial || !MapMaterial)
	{
		UE_LOG(LogIronBreach, Warning, TEXT("[Watch] planet materials missing (run Scripts/ib_build_watch_materials.py) — the deck shows space only"));
	}
	if (PlanetMaterial && PlanetImage)
	{
		PlanetMID = UMaterialInstanceDynamic::Create(PlanetMaterial, this);
		PlanetImage->SetBrushFromMaterial(PlanetMID);
	}
	else if (PlanetImage)
	{
		PlanetImage->SetColorAndOpacity(IBStyle::Ink());
	}
}

// ============================================================================ the world

void UIBPlanetWidget::BakeMap()
{
	if (!MapMaterial) { return; }
	if (!MapRT)
	{
		MapRT = NewObject<UTextureRenderTarget2D>(this, TEXT("WatchMapRT"));
		MapRT->RenderTargetFormat = RTF_RGBA8;
		MapRT->SRGB = false;                 // data, not color: read back linearly, sampled LinearColor
		MapRT->bAutoGenerateMips = true;
		MapRT->MipsSamplerFilter = TF_Bilinear;
		MapRT->AddressX = TA_Wrap;
		MapRT->AddressY = TA_Clamp;
		MapRT->ClearColor = FLinearColor::Black;
		MapRT->InitAutoFormat(MapW, MapH);
		MapRT->UpdateResourceImmediate(true);
	}
	UKismetRenderingLibrary::DrawMaterialToRenderTarget(this, MapRT, MapMaterial);
	++BakeAttempts;
	if (ReadBackMap())
	{
		bMapReady = true;
		PlaceSectors();
		PickStorm();
		if (PlanetMID) { PlanetMID->SetTextureParameterValue(TEXT("Map"), MapRT); }
		UE_LOG(LogIronBreach, Log, TEXT("[Watch] world baked on attempt %d — sea level %.3f"), BakeAttempts, SeaLevel);
	}
	else
	{
		BakeRetry = 0.5f; // the map shader may still be compiling: try again shortly
	}
}

bool UIBPlanetWidget::ReadBackMap()
{
	if (!MapRT) { return false; }
	FTextureRenderTargetResource* Res = MapRT->GameThread_GetRenderTargetResource();
	if (!Res) { return false; }
	TArray<FColor> Px;
	FReadSurfaceDataFlags Flags(RCM_UNorm);
	Flags.SetLinearToGamma(false);
	if (!Res->ReadPixels(Px, Flags) || Px.Num() != MapW * MapH) { return false; }

	// A material that has not finished compiling draws flat: no variety = not ready.
	uint32 Hist[256] = { 0 };
	for (int32 i = 0; i < Px.Num(); i += 7) { Hist[Px[i].R]++; }
	int32 Distinct = 0;
	for (uint32 H : Hist) { if (H > 0) { ++Distinct; } }
	if (Distinct < 12) { return false; }

	// Sea level: 68 % of the surface is ocean.
	uint32 Acc = 0; const uint32 Total = static_cast<uint32>((Px.Num() + 6) / 7);
	SeaByte = 128;
	for (int32 V = 0; V < 256; ++V)
	{
		Acc += Hist[V];
		if (Acc >= Total * 68u / 100u) { SeaByte = static_cast<uint8>(V); break; }
	}
	SeaLevel = SeaByte / 255.f + 0.002f;
	MapPixels = MoveTemp(Px);
	return true;
}

bool UIBPlanetWidget::IsLand(int32 X, int32 Y) const
{
	X = ((X % MapW) + MapW) % MapW;
	Y = FMath::Clamp(Y, 0, MapH - 1);
	return MapPixels[Y * MapW + X].R > SeaByte;
}

void UIBPlanetWidget::CoastSnap(float& Lat, float& Lon) const
{
	if (MapPixels.Num() != MapW * MapH) { return; }
	const int32 X0 = FMath::RoundToInt((Lon / 360.f + 0.5f) * MapW);
	const int32 Y0 = FMath::RoundToInt((0.5f - Lat / 180.f) * MapH);
	int32 BestX = 0, BestY = 0; bool bFound = false; int32 BestD = MAX_int32;
	for (int32 R = 0; R <= 140 && !bFound; ++R)
	{
		for (int32 DX = -R; DX <= R; ++DX)
		{
			const bool bEdge = FMath::Abs(DX) == R;
			for (int32 DY = -R; DY <= R; ++DY)
			{
				if (!bEdge && FMath::Abs(DY) != R) { continue; }
				const int32 X = X0 + DX, Y = Y0 + DY;
				if (Y < 2 || Y >= MapH - 2) { continue; }
				if (!IsLand(X, Y)) { continue; }
				if (IsLand(X + 2, Y) && IsLand(X - 2, Y) && IsLand(X, Y + 2) && IsLand(X, Y - 2)) { continue; } // inland
				const int32 D = DX * DX + DY * DY;
				if (D < BestD) { BestD = D; BestX = X; BestY = Y; bFound = true; }
			}
		}
		if (bFound) { break; }
	}
	if (!bFound) { return; }
	const int32 WX = ((BestX % MapW) + MapW) % MapW;
	Lat = (0.5f - static_cast<float>(BestY) / MapH) * 180.f;
	Lon = (static_cast<float>(WX) / MapW - 0.5f) * 360.f;
}

float UIBPlanetWidget::OceanFraction(float Lat, float Lon, int32 R) const
{
	const int32 X0 = FMath::RoundToInt((Lon / 360.f + 0.5f) * MapW);
	const int32 Y0 = FMath::RoundToInt((0.5f - Lat / 180.f) * MapH);
	int32 N = 0, O = 0;
	for (int32 DY = -R; DY <= R; DY += 6)
	{
		for (int32 DX = -R; DX <= R; DX += 6)
		{
			if (DX * DX + DY * DY > R * R) { continue; }
			++N;
			if (!IsLand(X0 + DX, Y0 + DY)) { ++O; }
		}
	}
	return N > 0 ? static_cast<float>(O) / N : 0.f;
}

void UIBPlanetWidget::PlaceSectors()
{
	for (FSectorPin& P : Pins)
	{
		CoastSnap(P.Lat, P.Lon);
		P.Unit = IBPL::LL2V(P.Lat, P.Lon);
	}
	// Carrow starts left of centre, just inside the night side, facing us.
	const FIBSector* Home = IBWatch::FindSector(IBWatch::HomeSectorId());
	const FSectorPin* HomePin = Pins.FindByPredicate([Home](const FSectorPin& P) { return Home && P.Id == Home->Id; });
	if (HomePin)
	{
		const FVector Want = FVector(-0.52f, 0.12f, 0.845f).GetSafeNormal();
		float BestS = 0.f, BestD = 9.f;
		for (int32 i = 0; i < 1440; ++i)
		{
			const float S = i / 1440.f * 2.f * PI;
			const FQuat Q = FQuat(FVector(0, 0, 1), -0.22f) * (FQuat(FVector(1, 0, 0), Pitch) * FQuat(FVector(0, 1, 0), S));
			const float D = static_cast<float>(FVector::Dist(Q.RotateVector(HomePin->Unit), Want));
			if (D < BestD) { BestD = D; BestS = S; }
		}
		Spin = BestS;
	}
}

void UIBPlanetWidget::PickStorm()
{
	// Open ocean, mid-latitude, east of home so it sits in daylight centre-right at boot.
	const FIBSector* Home = IBWatch::FindSector(IBWatch::HomeSectorId());
	const FSectorPin* HomePin = Pins.FindByPredicate([Home](const FSectorPin& P) { return Home && P.Id == Home->Id; });
	const float HomeLon = HomePin ? HomePin->Lon : 0.f;
	float BestScore = -1e9f; bool bFound = false; float BLat = 18.f, BLon = HomeLon + 48.f;
	const float Lats[] = { 14.f, 20.f, 26.f, -16.f, -22.f };
	for (float Lat : Lats)
	{
		for (int32 Lon = -180; Lon < 180; Lon += 8)
		{
			const float F = OceanFraction(Lat, static_cast<float>(Lon), 60);
			if (F < 0.92f) { continue; }
			float DL = FMath::Fmod(static_cast<float>(Lon) - HomeLon - 48.f + 540.f, 360.f) - 180.f;
			const float Score = F * 4.f - FMath::Abs(DL) / 90.f - FMath::Abs(Lat - 18.f) / 40.f;
			if (Score > BestScore) { BestScore = Score; BLat = Lat; BLon = static_cast<float>(Lon); bFound = true; }
		}
	}
	StormUnit = IBPL::LL2V(BLat, BLon);
	if (!bFound) { UE_LOG(LogIronBreach, Log, TEXT("[Watch] no open ocean for the storm — parked east of home")); }
}

// ============================================================================ camera

FQuat UIBPlanetWidget::LookAt(const FVector& PlanetUnit)
{
	// Rows (x, y, z): maps PlanetUnit -> +Z (toward the camera) with the planet's north up on screen.
	const FVector Z = PlanetUnit.GetSafeNormal();
	FVector X = FVector::CrossProduct(FVector(0, 1, 0), Z);
	if (X.SizeSquared() < 1e-8) { X = FVector(1, 0, 0); }
	X.Normalize();
	const FVector Y = FVector::CrossProduct(Z, X);
	const double m00 = X.X, m01 = X.Y, m02 = X.Z, m10 = Y.X, m11 = Y.Y, m12 = Y.Z, m20 = Z.X, m21 = Z.Y, m22 = Z.Z;
	const double Tr = m00 + m11 + m22;
	double qx, qy, qz, qw;
	if (Tr > 0.0)
	{
		const double S = FMath::Sqrt(Tr + 1.0) * 2.0;
		qx = (m21 - m12) / S; qy = (m02 - m20) / S; qz = (m10 - m01) / S; qw = 0.25 * S;
	}
	else if (m00 > m11 && m00 > m22)
	{
		const double S = FMath::Sqrt(1.0 + m00 - m11 - m22) * 2.0;
		qx = 0.25 * S; qy = (m01 + m10) / S; qz = (m02 + m20) / S; qw = (m21 - m12) / S;
	}
	else if (m11 > m22)
	{
		const double S = FMath::Sqrt(1.0 + m11 - m00 - m22) * 2.0;
		qx = (m01 + m10) / S; qy = 0.25 * S; qz = (m12 + m21) / S; qw = (m02 - m20) / S;
	}
	else
	{
		const double S = FMath::Sqrt(1.0 + m22 - m00 - m11) * 2.0;
		qx = (m02 + m20) / S; qy = (m12 + m21) / S; qz = 0.25 * S; qw = (m10 - m01) / S;
	}
	FQuat Q(qx, qy, qz, qw);
	Q.Normalize();
	return Q;
}

FQuat UIBPlanetWidget::OrbitRotation() const
{
	return FQuat(FVector(0, 0, 1), -0.22f) * (FQuat(FVector(1, 0, 0), Pitch) * FQuat(FVector(0, 1, 0), Spin));
}

float UIBPlanetWidget::OrbitDistance(const FVector2D& Size) const
{
	const float Vista = FMath::Max(420.f, static_cast<float>(Size.X) - IBPL::CardW - 56.f);
	const float Rpx = FMath::Min(static_cast<float>(Size.Y) * 0.385f, (Vista - IBPL::PillarW) * 0.42f);
	const float Ang = FMath::Atan(Rpx * 2.f * IBPL::TanHalfFov / static_cast<float>(Size.Y));
	return 1.f / FMath::Max(0.05f, FMath::Sin(Ang));
}

UIBPlanetWidget::FCam UIBPlanetWidget::OrbitCam(const FVector2D& Size) const
{
	const float Vista = FMath::Max(420.f, static_cast<float>(Size.X) - IBPL::CardW - 56.f);
	const float PCX = IBPL::PillarW + (Vista - IBPL::PillarW) * 0.5f;
	const float PCY = static_cast<float>(Size.Y) * 0.5f;
	FCam C;
	C.Dist = OrbitDistance(Size) * ZoomScale;
	C.Sx = (static_cast<float>(Size.X) * 0.5f - PCX) / static_cast<float>(Size.Y);
	C.Sy = (PCY - static_cast<float>(Size.Y) * 0.5f) / static_cast<float>(Size.Y);
	C.Q = OrbitRotation();
	return C;
}

UIBPlanetWidget::FCam UIBPlanetWidget::SectorCam(const FVector2D& Size) const
{
	FVector2D BPos, BSize;
	BoardRect(Size, BPos, BSize);
	const FIBSector* Home = IBWatch::FindSector(IBWatch::HomeSectorId());
	const FSectorPin* HomePin = Pins.FindByPredicate([Home](const FSectorPin& P) { return Home && P.Id == Home->Id; });
	FCam C;
	C.Dist = IBPL::SectorDist;
	C.Sx = (static_cast<float>(Size.X) * 0.5f - static_cast<float>(BPos.X + BSize.X * 0.5)) / static_cast<float>(Size.Y);
	C.Sy = (static_cast<float>(BPos.Y + BSize.Y * 0.62) - static_cast<float>(Size.Y) * 0.5f) / static_cast<float>(Size.Y);
	C.Q = LookAt(HomePin ? HomePin->Unit : FVector(0, 0, 1));
	return C;
}

UIBPlanetWidget::FCam UIBPlanetWidget::LerpCam(const FCam& A, const FCam& B, float T)
{
	FCam C;
	C.Dist = FMath::Lerp(A.Dist, B.Dist, T);
	C.Sx = FMath::Lerp(A.Sx, B.Sx, T);
	C.Sy = FMath::Lerp(A.Sy, B.Sy, T);
	C.Q = FQuat::Slerp(A.Q, B.Q, T);
	return C;
}

FVector2D UIBPlanetWidget::Project(const FVector& World, const FVector2D& Size, const FCam& InCam, float& OutVis) const
{
	const double EZ = World.Z - InCam.Dist;
	if (EZ >= -1e-4)
	{
		OutVis = 0.f;
		return FVector2D(-9999.0, -9999.0);
	}
	const double Inv = 1.0 / (-EZ);
	const double UVX = (World.X * Inv) / (2.0 * IBPL::TanHalfFov) - InCam.Sx;
	const double UVY = (World.Y * Inv) / (2.0 * IBPL::TanHalfFov) - InCam.Sy;
	const float Lim = 1.f / InCam.Dist;
	OutVis = IBPL::SmoothStep(Lim, Lim + 0.14f, static_cast<float>(World.Z));
	return FVector2D(Size.X * 0.5 + UVX * Size.Y, Size.Y * 0.5 - UVY * Size.Y);
}

// ============================================================================ state from the screen

void UIBPlanetWidget::SetDive(float InDive)
{
	Dive = FMath::Clamp(InDive, 0.f, 1.f);
	if (Dive > 0.f) { HoverSector = NAME_None; }
}

void UIBPlanetWidget::SetDrop(float InDrop, FName SectorId)
{
	if (InDrop < 0.f)
	{
		Drop = -1.f;
		bDropFromValid = false;
		return;
	}
	Drop = FMath::Clamp(InDrop, 0.f, 1.f);
	DropSector = SectorId.IsNone() ? IBWatch::HomeSectorId() : SectorId;
	HoverSector = NAME_None;
}

void UIBPlanetWidget::SetSelection(FName SectorId, const FText& InName, const FText& InSub)
{
	SelectedSector = SectorId;
	CalloutName = InName;
	CalloutSub = InSub;
}

bool UIBPlanetWidget::GetSectorScreen(FName SectorId, FVector2D& OutLocal, float& OutVisibility) const
{
	for (const FSectorPin& P : Pins)
	{
		if (P.Id == SectorId)
		{
			OutLocal = P.Screen;
			OutVisibility = P.Vis;
			return true;
		}
	}
	return false;
}

// ============================================================================ tick

void UIBPlanetWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);
	Time += InDeltaTime;
	const FVector2D Size = MyGeometry.GetLocalSize();
	if (Size.X > 8.0 && Size.Y > 8.0) { LastSize = Size; }

	if (!bMapReady && MapMaterial)
	{
		BakeRetry -= InDeltaTime;
		if (BakeRetry <= 0.f && BakeAttempts < 60) { BakeMap(); }
	}

	if (Dive <= 0.f && Drop < 0.f && !bDragging) { Spin += IBPL::SpinRate * InDeltaTime; }
	ZoomScale += (ZoomTarget - ZoomScale) * FMath::Min(1.f, InDeltaTime * 7.f);

	const FCam CO = OrbitCam(LastSize);
	const FCam CS = SectorCam(LastSize);
	FCam C = Dive <= 0.f ? CO : (Dive >= 1.f ? CS : LerpCam(CO, CS, Dive));
	if (Drop >= 0.f)
	{
		if (!bDropFromValid) { DropFrom = C; bDropFromValid = true; }
		const FSectorPin* Target = Pins.FindByPredicate([this](const FSectorPin& P) { return P.Id == DropSector; });
		FCam To;
		To.Dist = IBPL::DropDist; To.Sx = 0.f; To.Sy = 0.f;
		To.Q = LookAt(Target ? Target->Unit : FVector(0, 0, 1));
		const float Z = Drop * Drop * Drop;                                      // fall: ease-in
		const float RQ = 1.f - FMath::Pow(1.f - FMath::Clamp(Drop * 1.6f, 0.f, 1.f), 3.f); // aim: ease-out, first
		C.Dist = FMath::Lerp(DropFrom.Dist, To.Dist, Z);
		C.Sx = FMath::Lerp(DropFrom.Sx, To.Sx, RQ);
		C.Sy = FMath::Lerp(DropFrom.Sy, To.Sy, RQ);
		C.Q = FQuat::Slerp(DropFrom.Q, To.Q, RQ);
		// Small camera tremor follows drop progress, so the pin projection and shader stay aligned.
		const float Shake = 0.0009f * IBPL::SmoothStep(0.35f, 0.85f, Drop) * (1.f - IBPL::SmoothStep(0.88f, 1.f, Drop));
		C.Sx += FMath::Sin(Drop * 148.f) * Shake;
		C.Sy += FMath::Sin(Drop * 193.f) * Shake * 0.6f;
	}
	Cam = C;

	for (FSectorPin& P : Pins)
	{
		P.Screen = Project(Cam.Q.RotateVector(P.Unit), LastSize, Cam, P.Vis);
	}

	UpdateMaterial(LastSize);
	Invalidate(EInvalidateWidgetReason::Paint);
}

void UIBPlanetWidget::UpdateMaterial(const FVector2D& Size)
{
	if (!PlanetMID) { return; }
	const FVector RX = Cam.Q.RotateVector(FVector(1, 0, 0));
	const FVector RY = Cam.Q.RotateVector(FVector(0, 1, 0));
	const FVector RZ = Cam.Q.RotateVector(FVector(0, 0, 1));
	PlanetMID->SetVectorParameterValue(TEXT("RotX"), FLinearColor(RX.X, RX.Y, RX.Z, 0.f));
	PlanetMID->SetVectorParameterValue(TEXT("RotY"), FLinearColor(RY.X, RY.Y, RY.Z, 0.f));
	PlanetMID->SetVectorParameterValue(TEXT("RotZ"), FLinearColor(RZ.X, RZ.Y, RZ.Z, 0.f));
	PlanetMID->SetVectorParameterValue(TEXT("Cam"), FLinearColor(Cam.Dist, IBPL::TanHalfFov, static_cast<float>(Size.X / FMath::Max(1.0, Size.Y)), 0.f));
	PlanetMID->SetVectorParameterValue(TEXT("Shift"), FLinearColor(Cam.Sx, Cam.Sy, 0.f, 0.f));
	PlanetMID->SetVectorParameterValue(TEXT("Sun"), FLinearColor(IBPL::Sun.X, IBPL::Sun.Y, IBPL::Sun.Z, 0.f));
	PlanetMID->SetVectorParameterValue(TEXT("Storm"), FLinearColor(StormUnit.X, StormUnit.Y, StormUnit.Z, 0.f));
	PlanetMID->SetScalarParameterValue(TEXT("Sea"), SeaLevel);
	PlanetMID->SetScalarParameterValue(TEXT("CloudT"), Time * 0.004f);
	if (bMapReady && MapRT) { PlanetMID->SetTextureParameterValue(TEXT("Map"), MapRT); }
}

// ============================================================================ input

FName UIBPlanetWidget::PinAt(const FVector2D& Local) const
{
	if (Dive > 0.f || Drop >= 0.f) { return NAME_None; }
	FName Best; double BestD = 20.0;
	for (const FSectorPin& P : Pins)
	{
		if (P.Vis <= 0.05f) { continue; }
		const double D = FVector2D::Distance(P.Screen, Local);
		if (D < BestD) { BestD = D; Best = P.Id; }
	}
	return Best;
}

FReply UIBPlanetWidget::NativeOnMouseButtonDown(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent)
{
	if (InMouseEvent.GetEffectingButton() != EKeys::LeftMouseButton || Dive > 0.f || Drop >= 0.f)
	{
		return Super::NativeOnMouseButtonDown(InGeometry, InMouseEvent);
	}
	const FVector2D Local = InGeometry.AbsoluteToLocal(InMouseEvent.GetScreenSpacePosition());
	PressSector = PinAt(Local);
	if (PressSector.IsNone())
	{
		bDragging = true;
		DragLast = Local;
		DragMoved = 0.f;
		return FReply::Handled().CaptureMouse(TakeWidget());
	}
	return FReply::Handled();
}

FReply UIBPlanetWidget::NativeOnMouseButtonUp(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent)
{
	if (InMouseEvent.GetEffectingButton() != EKeys::LeftMouseButton)
	{
		return Super::NativeOnMouseButtonUp(InGeometry, InMouseEvent);
	}
	if (bDragging)
	{
		bDragging = false;
		return FReply::Handled().ReleaseMouseCapture();
	}
	if (!PressSector.IsNone())
	{
		const FVector2D Local = InGeometry.AbsoluteToLocal(InMouseEvent.GetScreenSpacePosition());
		if (PinAt(Local) == PressSector)
		{
			SelectedSector = PressSector;
			OnSectorPicked.Broadcast(PressSector);
		}
		PressSector = NAME_None;
		return FReply::Handled();
	}
	return Super::NativeOnMouseButtonUp(InGeometry, InMouseEvent);
}

FReply UIBPlanetWidget::NativeOnMouseButtonDoubleClick(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent)
{
	if (InMouseEvent.GetEffectingButton() == EKeys::LeftMouseButton && Dive <= 0.f && Drop < 0.f)
	{
		const FVector2D Local = InGeometry.AbsoluteToLocal(InMouseEvent.GetScreenSpacePosition());
		const FName Hit = PinAt(Local);
		const FIBSector* S = IBWatch::FindSector(Hit);
		if (S && S->bLive)
		{
			SelectedSector = Hit;
			OnSectorOpened.Broadcast(Hit);
			return FReply::Handled();
		}
	}
	return Super::NativeOnMouseButtonDoubleClick(InGeometry, InMouseEvent);
}

FReply UIBPlanetWidget::NativeOnMouseMove(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent)
{
	const FVector2D Local = InGeometry.AbsoluteToLocal(InMouseEvent.GetScreenSpacePosition());
	if (bDragging)
	{
		const FVector2D D = Local - DragLast;
		Spin += static_cast<float>(D.X) * 0.0062f * FMath::Pow(ZoomScale, 1.2f);
		Pitch = FMath::Clamp(Pitch + static_cast<float>(D.Y) * 0.004f, -0.55f, 0.7f);
		DragLast = Local;
		DragMoved += static_cast<float>(FMath::Abs(D.X) + FMath::Abs(D.Y));
		return FReply::Handled();
	}
	HoverSector = PinAt(Local);
	SetCursor(!HoverSector.IsNone() ? EMouseCursor::Hand : (Dive <= 0.f && Drop < 0.f ? EMouseCursor::GrabHand : EMouseCursor::Default));
	return Super::NativeOnMouseMove(InGeometry, InMouseEvent);
}

FReply UIBPlanetWidget::NativeOnMouseWheel(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent)
{
	if (Dive > 0.f || Drop >= 0.f) { return Super::NativeOnMouseWheel(InGeometry, InMouseEvent); }
	ZoomTarget = FMath::Clamp(ZoomTarget * FMath::Exp(-InMouseEvent.GetWheelDelta() * 0.09f), 0.5f, 1.6f);
	return FReply::Handled();
}

void UIBPlanetWidget::NativeOnMouseLeave(const FPointerEvent& InMouseEvent)
{
	HoverSector = NAME_None;
	if (!bDragging) { SetCursor(EMouseCursor::Default); }
	Super::NativeOnMouseLeave(InMouseEvent);
}

// ============================================================================ paint

int32 UIBPlanetWidget::NativePaint(const FPaintArgs& Args, const FGeometry& Geo, const FSlateRect& MyCullingRect,
	FSlateWindowElementList& Out, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const
{
	// the planet image first (it is a child), then everything that lives on the glass
	int32 L = Super::NativePaint(Args, Geo, MyCullingRect, Out, LayerId, InWidgetStyle, bParentEnabled) + 1;

	const FVector2D Size = Geo.GetLocalSize();
	const float W = static_cast<float>(Size.X), H = static_cast<float>(Size.Y);
	if (W < 40.f || H < 40.f) { return L; }

	const float Vista = FMath::Max(420.f, W - IBPL::CardW - 56.f);
	const float PCX = IBPL::PillarW + (Vista - IBPL::PillarW) * 0.5f;
	const FSlateFontInfo FontGlyph = IBPaint::Font(TEXT("Bold"), 9.f, 0);
	const FSlateFontInfo FontName  = IBPaint::Font(TEXT("Bold"), 10.f, 150);
	const FSlateFontInfo FontSub   = IBPaint::Font(TEXT("Regular"), 8.f, 350);

	// ---- pins ----
	const float PinsAlpha = (1.f - FMath::Clamp(Dive / 0.2f, 0.f, 1.f)) * (Drop >= 0.f ? 1.f - FMath::Clamp(Drop / 0.25f, 0.f, 1.f) : 1.f);
	if (PinsAlpha > 0.01f)
	{
		for (const FSectorPin& P : Pins)
		{
			if (P.Vis <= 0.001f) { continue; }
			const FIBSector* S = IBWatch::FindSector(P.Id);
			if (!S) { continue; }
			const float A = PinsAlpha * P.Vis;
			const FLinearColor Colr = S->Color;
			const bool bSel = (P.Id == SelectedSector);
			const bool bHov = (P.Id == HoverSector);
			const FVector2f C(static_cast<float>(P.Screen.X), static_cast<float>(P.Screen.Y));

			// hex-grid halo
			{
				const float R = bSel ? 52.f : 34.f;
				const float HA = A * (bSel ? 0.28f : (bHov ? 0.22f : 0.09f));
				const float HR = 12.f, HW = 1.7320508f * HR, HH = 1.5f * HR;
				for (int32 j = -3; j <= 3; ++j)
				{
					for (int32 i = -3; i <= 3; ++i)
					{
						const float CX = C.X + (i + ((j & 1) ? 0.5f : 0.f)) * HW;
						const float CY = C.Y + j * HH;
						const float D = FMath::Sqrt(FMath::Square(CX - C.X) + FMath::Square(CY - C.Y));
						if (D > R) { continue; }
						const float F = FMath::Pow(1.f - D / R, 1.7f);
						TArray<FVector2f> Hex;
						Hex.Reserve(7);
						for (int32 k = 0; k <= 6; ++k)
						{
							const float Ang = PI / 6.f + k * PI / 3.f;
							Hex.Add(FVector2f(CX + FMath::Cos(Ang) * HR * 0.9f, CY + FMath::Sin(Ang) * HR * 0.9f));
						}
						IBPaint::Line(Out, L, Geo, Hex, IBPaint::Alpha(Colr, HA * F), 0.7f);
					}
				}
			}
			// sonar ring for live / hot sectors
			if (S->bLive || S->bHot)
			{
				const float Ph = FMath::Fmod(Time / 2.6f + P.Phase, 1.f);
				IBPaint::Ring(Out, L + 1, Geo, C, 13.f + 36.f * Ph, IBPaint::Alpha(Colr, (1.f - Ph) * 0.55f * A), 1.2f);
			}
			if (bSel) { IBPaint::DashedRing(Out, L + 1, Geo, C, 26.f, IBPaint::Alpha(Colr, 0.35f * A), 1.f, 18); }
			// diamond marker with a soft glow
			const float Half = bSel ? 12.f : 10.f;
			IBPaint::DiamondFill(Out, L + 2, Geo, C, Half + 11.f, IBPaint::Alpha(Colr, 0.035f * A));
			IBPaint::DiamondFill(Out, L + 2, Geo, C, Half + 6.f, IBPaint::Alpha(Colr, 0.075f * A));
			IBPaint::DiamondFill(Out, L + 2, Geo, C, Half, IBPaint::Alpha(Colr, 0.25f * A));
			IBPaint::DiamondFill(Out, L + 2, Geo, C, Half - 3.f, IBPaint::Alpha(IBStyle::Ink(), 0.85f * A));
			IBPaint::Diamond(Out, L + 3, Geo, C, Half, IBPaint::Alpha(Colr, 0.98f * A), 1.2f);
			// glyph
			{
				const FVector2D Sz = IBPaint::Measure(S->Glyph, FontGlyph);
				IBPaint::Label(Out, L + 4, Geo, C - FVector2f(static_cast<float>(Sz.X) * 0.5f, static_cast<float>(Sz.Y) * 0.5f), S->Glyph, FontGlyph, IBPaint::Alpha(Colr, A));
			}
			// callout (selected) / hover label
			if (bSel || bHov)
			{
				const FString Name = bSel ? CalloutName.ToString() : S->Name.ToString();
				const FString Sub  = bSel ? CalloutSub.ToString() : S->Status.ToString();
				const FSlateFontInfo& NF = bSel ? IBPaint::Font(TEXT("Bold"), 11.f, 100) : FontName;
				const FVector2D NSz = IBPaint::Measure(Name, NF);
				const FVector2D SSz = Sub.IsEmpty() ? FVector2D::ZeroVector : IBPaint::Measure(Sub, FontSub);
				const float BW = static_cast<float>(FMath::Max(NSz.X, SSz.X)) + 26.f;
				const float BH = Sub.IsEmpty() ? 30.f : 46.f;
				const bool bLeft = C.X < PCX;
				const float Dir = bLeft ? -1.f : 1.f;
				const float Gap = bSel ? 46.f : 30.f;
				const float BX = FMath::Clamp(bLeft ? C.X - Gap - BW : C.X + Gap, IBPL::PillarW + 16.f, FMath::Max(IBPL::PillarW + 16.f, Vista - BW - 12.f));
				const float BY = FMath::Clamp(C.Y - BH - 14.f, 124.f, FMath::Max(124.f, H - IBPL::ConsoleH - BH - 12.f));
				const float NearX = bLeft ? BX + BW : BX;
				IBPaint::Line(Out, L + 3, Geo, { C + FVector2f(Dir * 13.f, -7.f), FVector2f(C.X + Dir * (Gap - 6.f), BY + BH), FVector2f(NearX, BY + BH) }, IBPaint::Alpha(Colr, 0.85f * A), 1.2f);
				IBPaint::Rect(Out, L + 3, Geo, FVector2f(BX, BY), FVector2f(BW, BH), IBPaint::Alpha(IBStyle::Ink(), 0.82f * A));
				IBPaint::Line(Out, L + 4, Geo, { FVector2f(BX, BY), FVector2f(BX + BW, BY), FVector2f(BX + BW, BY + BH), FVector2f(BX, BY + BH), FVector2f(BX, BY) }, IBPaint::Alpha(Colr, 0.48f * A), 0.8f);
				IBPaint::Rect(Out, L + 4, Geo, FVector2f(BX, BY), FVector2f(2.f, BH), IBPaint::Alpha(Colr, 0.9f * A));
				IBPaint::Label(Out, L + 5, Geo, FVector2f(BX + 14.f, BY + (Sub.IsEmpty() ? 8.f : 7.f)), Name, NF, IBPaint::Alpha(IBStyle::TextHi(), A));
				if (!Sub.IsEmpty()) { IBPaint::Label(Out, L + 5, Geo, FVector2f(BX + 14.f, BY + 26.f), Sub, FontSub, IBPaint::Alpha(Colr, A)); }
			}
		}
		L += 6;
	}

	// ---- the drop ----
	if (Drop >= 0.f)
	{
		const float K = Drop;
		const FSectorPin* Target = Pins.FindByPredicate([this](const FSectorPin& P) { return P.Id == DropSector; });
		const FVector2f C = Target ? FVector2f(static_cast<float>(Target->Screen.X), static_cast<float>(Target->Screen.Y)) : FVector2f(W * 0.5f, H * 0.5f);
		if (K < 0.3f)
		{
			const float Cc = K / 0.3f;
			for (int32 i = 0; i < 3; ++i)
			{
				const float Q = FMath::Clamp(Cc * 1.3f - i * 0.15f, 0.f, 1.f);
				IBPaint::Ring(Out, L, Geo, C, 10.f + (1.f - Q) * 170.f, IBPaint::Alpha(IBStyle::Amber(), 0.9f * Q), 1.5f, 48);
			}
		}
		if (K > 0.25f)
		{
			const float Z = FMath::Clamp((K - 0.25f) / 0.6f, 0.f, 1.f);
			for (int32 i = 0; i < 28; ++i)
			{
				const float Ang = i / 28.f * 2.f * PI + 0.3f;
				const float R0 = 70.f + 560.f * Z * Z, R1 = R0 + 40.f + 280.f * Z;
				IBPaint::Seg(Out, L, Geo, C + FVector2f(FMath::Cos(Ang), FMath::Sin(Ang)) * R0, C + FVector2f(FMath::Cos(Ang), FMath::Sin(Ang)) * R1, IBPaint::Alpha(IBStyle::TextHi(), 0.3f * Z), 1.f);
			}
			IBPaint::Rect(Out, L + 1, Geo, FVector2f(0.f, 0.f), FVector2f(W, H), FLinearColor(0.f, 0.f, 0.f, 0.6f * Z));
			IBPaint::Seg(Out, L + 2, Geo, FVector2f(C.X, C.Y - H * (1.f - Z)), FVector2f(C.X, C.Y - 16.f), IBPaint::Alpha(IBStyle::Amber(), 0.9f), 2.f);
		}
		if (K > 0.15f && K < 0.9f)
		{
			const float A = K < 0.3f ? (K - 0.15f) / 0.15f : (K > 0.8f ? 1.f - (K - 0.8f) / 0.1f : 1.f);
			const float Y = C.Y + 104.f + 12.f * K;
			const FSlateFontInfo FontBig = IBPaint::Font(TEXT("Bold"), 26.f, 400);
			const FSlateFontInfo FontMid = IBPaint::Font(TEXT("Regular"), 9.f, 500);
			const FSlateFontInfo FontLow = IBPaint::Font(TEXT("Regular"), 8.f, 400);
			IBPaint::Seg(Out, L + 3, Geo, FVector2f(C.X - 120.f, Y - 36.f), FVector2f(C.X + 120.f, Y - 36.f), IBPaint::Alpha(IBStyle::Amber(), 0.9f * A), 1.f);
			IBPaint::LabelAt(Out, L + 3, Geo, FVector2f(C.X, Y - 30.f), 0.5f, CalloutName.ToString(), FontBig, IBPaint::Alpha(IBStyle::TextHi(), A));
			IBPaint::LabelAt(Out, L + 3, Geo, FVector2f(C.X, Y + 8.f), 0.5f, CalloutSub.ToString(), FontMid, IBPaint::Alpha(IBStyle::Amber(), A));
			IBPaint::LabelAt(Out, L + 3, Geo, FVector2f(C.X, Y + 26.f), 0.5f, TEXT("DROP AUTHORIZED · THE SQUAD TRAVELS TOGETHER"), FontLow, IBPaint::Alpha(IBStyle::TextLo(), A));
		}
		L += 4;
	}

	if (Drop > 0.25f)
	{
		const float V = IBPL::SmoothStep(0.25f, 0.85f, Drop) * 0.55f;
		const FLinearColor Edge(0.f, 0.f, 0.f, V), Clear(0.f, 0.f, 0.f, 0.f);
		IBPaint::Gradient(Out, L, Geo, FVector2f(0, 0), FVector2f(W, H * 0.2f), Edge, Clear);
		IBPaint::Gradient(Out, L, Geo, FVector2f(0, H * 0.8f), FVector2f(W, H * 0.2f), Clear, Edge);
		IBPaint::Gradient(Out, L, Geo, FVector2f(0, 0), FVector2f(W * 0.16f, H), Edge, Clear, false);
		IBPaint::Gradient(Out, L, Geo, FVector2f(W * 0.84f, 0), FVector2f(W * 0.16f, H), Clear, Edge, false);
		++L;
	}

	// ---- the deck around the glass ----
	{
		const FLinearColor Edge = IBPL::Col(0.43f, 0.67f, 0.82f, 0.14f);
		// Soft contact shadow along the glass, then the bevelled pillar.
		IBPaint::Gradient(Out, L, Geo, FVector2f(IBPL::PillarW, 0), FVector2f(45.f, H),
			FLinearColor(0, 0, 0, 0.6f), FLinearColor::Transparent, false);
		// left pillar
		IBPaint::Rect(Out, L, Geo, FVector2f(0.f, 0.f), FVector2f(IBPL::PillarW, H), IBPL::Col(0.0045f, 0.006f, 0.008f));
		IBPaint::Rect(Out, L, Geo, FVector2f(0.f, 0.f), FVector2f(IBPL::PillarW * 0.45f, H), IBPL::Col(0.007f, 0.0095f, 0.0125f));
		IBPaint::Rect(Out, L, Geo, FVector2f(IBPL::PillarW - 2.f, 0.f), FVector2f(2.f, H), Edge);
		for (float Y = 60.f; Y < H; Y += 150.f) { IBPaint::Rect(Out, L + 1, Geo, FVector2f(0.f, Y), FVector2f(IBPL::PillarW, 1.f), IBPL::Col(1.f, 1.f, 1.f, 0.04f)); }
		IBPaint::Rect(Out, L + 1, Geo, FVector2f(12.f, H * 0.40f), FVector2f(46.f, 130.f), IBPL::Col(0.f, 0.f, 0.f, 0.5f));
		IBPaint::Rect(Out, L + 2, Geo, FVector2f(32.f, H * 0.40f + 18.f), FVector2f(4.f, 4.f), IBStyle::Cyan());
		IBPaint::Rect(Out, L + 2, Geo, FVector2f(32.f, H * 0.40f + 32.f), FVector2f(4.f, 4.f), IBStyle::Amber());
		// Machined inset, service seams and a grazing reflection from the planet.
		IBPaint::Gradient(Out, L + 1, Geo, FVector2f(8.f, 0), FVector2f(IBPL::PillarW - 16.f, H),
			IBPL::Col(0.018f, 0.026f, 0.034f), IBPL::Col(0.003f, 0.005f, 0.007f), false);
		IBPaint::Seg(Out, L + 2, Geo, FVector2f(8, 0), FVector2f(8, H), IBPL::Col(0.038f, 0.052f, 0.065f), 1.f);
		IBPaint::Seg(Out, L + 2, Geo, FVector2f(IBPL::PillarW - 9, 0), FVector2f(IBPL::PillarW - 9, H), IBPL::Col(0, 0, 0, 0.9f), 2.f);
		for (float Y = 140.f; Y < H - 90.f; Y += 240.f)
		{
			IBPaint::Seg(Out, L + 2, Geo, FVector2f(8, Y), FVector2f(IBPL::PillarW - 9, Y - 12), IBPL::Col(0, 0, 0, 0.9f), 2.f);
			IBPaint::Disc(Out, L + 2, Geo, FVector2f(17, Y + 12), 2.4f, IBPL::Col(0.025f, 0.032f, 0.038f), 8);
		}
		// console
		{
			TArray<FVector2f> Poly;
			TArray<FVector2f> Top;
			for (float X = 0.f; X <= W + 1.f; X += 40.f)
			{
				const float XX = FMath::Min(X, W);
				const float Y = H - IBPL::ConsoleH - 14.f * FMath::Sin(XX / W * PI);
				Poly.Add(FVector2f(XX, Y));
				Top.Add(FVector2f(XX, Y));
			}
			Poly.Add(FVector2f(W, H));
			Poly.Add(FVector2f(0.f, H));
			IBPaint::Fill(Out, L + 1, Geo, Poly, FVector2f(W * 0.5f, H), IBPL::Col(0.0035f, 0.005f, 0.007f));
			IBPaint::Line(Out, L + 2, Geo, Top, IBPL::Col(0.43f, 0.67f, 0.82f, 0.18f), 1.5f);
			for (float X = 90.f; X < W - 40.f; X += 26.f)
			{
				const float Y = H - IBPL::ConsoleH - 14.f * FMath::Sin(X / W * PI) + 8.f;
				IBPaint::Rect(Out, L + 2, Geo, FVector2f(X, Y), FVector2f(1.f, 5.f), IBPL::Col(1.f, 1.f, 1.f, 0.06f));
			}
		}
		IBPaint::Gradient(Out, L + 2, Geo, FVector2f(0, H - IBPL::ConsoleH + 18.f), FVector2f(W, IBPL::ConsoleH - 18.f),
			IBPL::Col(0.015f, 0.022f, 0.029f), IBPL::Col(0.003f, 0.004f, 0.006f));
		IBPaint::Seg(Out, L + 2, Geo, FVector2f(86, H - 20), FVector2f(W - 26, H - 20), IBPL::Col(0.031f, 0.045f, 0.057f), 1.f);
		for (float X = 280.f; X < W - 100.f; X += 330.f)
		{
			IBPaint::Seg(Out, L + 2, Geo, FVector2f(X, H - 60), FVector2f(X - 28, H), IBPL::Col(0, 0, 0, 0.8f), 2.f);
		}
		// top-right truss
		if (W > 1000.f)
		{
			IBPaint::Fill(Out, L + 1, Geo, { FVector2f(W - 640.f, 0.f), FVector2f(W - 30.f, 0.f), FVector2f(W - 30.f, 14.f), FVector2f(W - 540.f, 40.f), FVector2f(W - 640.f, 26.f) },
				FVector2f(W - 335.f, 12.f), IBPL::Col(0.0028f, 0.0038f, 0.0055f));
			IBPaint::Line(Out, L + 2, Geo, { FVector2f(W - 640.f, 26.f), FVector2f(W - 540.f, 40.f), FVector2f(W - 30.f, 14.f) }, IBPL::Col(0.43f, 0.67f, 0.82f, 0.12f), 1.f);
			IBPaint::Fill(Out, L + 1, Geo, { FVector2f(W - 90.f, 0.f), FVector2f(W, 0.f), FVector2f(W, 70.f), FVector2f(W - 18.f, 62.f), FVector2f(W - 90.f, 12.f) },
				FVector2f(W - 45.f, 30.f), IBPL::Col(0.0022f, 0.003f, 0.0045f));
		}
		L += 3;
	}

	return L;
}
