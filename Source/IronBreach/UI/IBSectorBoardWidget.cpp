#include "UI/IBSectorBoardWidget.h"
#include "UI/IBStyleKit.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Overlay.h"
#include "Rendering/DrawElements.h"
#include "Rendering/SlateRenderer.h"
#include "Framework/Application/SlateApplication.h"
#include "Fonts/FontMeasure.h"
#include "Styling/CoreStyle.h"

namespace IBWatchBoardPaint
{
	// The Carrow coast, top to bottom, in board units. Land is west of this line,
	// the sea east. The dip between the two headlands is the harbor scar.
	const FVector2D Coast[] = {
		{0.340, 0.000}, {0.370, 0.100}, {0.420, 0.180}, {0.470, 0.260}, {0.490, 0.340}, {0.480, 0.420},
		{0.520, 0.480}, {0.580, 0.520},                       // north headland (the garrison)
		{0.560, 0.560}, {0.520, 0.600}, {0.510, 0.660}, {0.540, 0.710}, // the scar
		{0.600, 0.720},                                       // south headland
		{0.640, 0.760}, {0.660, 0.840}, {0.690, 0.920}, {0.710, 1.000}
	};
	const FVector2D SeaWallA(0.580, 0.520);
	const FVector2D SeaWallB(0.600, 0.720);
	const FVector2D WatchPos(0.545, 0.640);

	constexpr float PinHitRadius = 16.f;

	FVector2f At(const FVector2D& N, const FVector2D& Size)
	{
		return FVector2f(static_cast<float>(N.X * Size.X), static_cast<float>(N.Y * Size.Y));
	}

	void Line(FSlateWindowElementList& Out, int32 Layer, const FGeometry& Geo, const TArray<FVector2f>& Points,
		const FLinearColor& Color, float Thickness = 1.f)
	{
		if (Points.Num() < 2) { return; }
		FSlateDrawElement::MakeLines(Out, Layer, Geo.ToPaintGeometry(), Points, ESlateDrawEffect::None, Color, true, Thickness);
	}

	void Ring(FSlateWindowElementList& Out, int32 Layer, const FGeometry& Geo, const FVector2f& C, float R,
		const FLinearColor& Color, float Thickness = 1.f, int32 Segments = 40)
	{
		TArray<FVector2f> Pts;
		Pts.Reserve(Segments + 1);
		for (int32 i = 0; i <= Segments; ++i)
		{
			const float A = (2.f * PI * i) / Segments;
			Pts.Add(C + FVector2f(FMath::Cos(A), FMath::Sin(A)) * R);
		}
		Line(Out, Layer, Geo, Pts, Color, Thickness);
	}

	/** Dashed ring: every other segment drawn. */
	void DashedRing(FSlateWindowElementList& Out, int32 Layer, const FGeometry& Geo, const FVector2f& C, float R,
		const FLinearColor& Color, float Thickness = 1.f, int32 Dashes = 24)
	{
		const int32 Segments = Dashes * 2;
		for (int32 i = 0; i < Segments; i += 2)
		{
			const float A0 = (2.f * PI * i) / Segments;
			const float A1 = (2.f * PI * (i + 1)) / Segments;
			Line(Out, Layer, Geo, { C + FVector2f(FMath::Cos(A0), FMath::Sin(A0)) * R, C + FVector2f(FMath::Cos(A1), FMath::Sin(A1)) * R }, Color, Thickness);
		}
	}

	/** Filled convex-ish polygon as a triangle fan around Center (IBHexBorder's trick). */
	void Fill(FSlateWindowElementList& Out, int32 Layer, const FGeometry& Geo, const TArray<FVector2f>& Points,
		const FVector2f& Center, const FLinearColor& Color)
	{
		if (Points.Num() < 3) { return; }
		const FSlateBrush* WhiteBrush = FCoreStyle::Get().GetBrush("GenericWhiteBox");
		const FSlateResourceHandle Handle = FSlateApplication::Get().GetRenderer()->GetResourceHandle(*WhiteBrush);
		const FSlateRenderTransform& RT = Geo.GetAccumulatedRenderTransform();
		const FColor Col = Color.ToFColor(true);

		TArray<FSlateVertex> Verts;
		TArray<SlateIndex> Indices;
		Verts.Reserve(Points.Num() + 1);
		Indices.Reserve(Points.Num() * 3);
		Verts.Add(FSlateVertex::Make<ESlateVertexRounding::Disabled>(RT, Center, FVector2f(0.5f, 0.5f), Col));
		for (const FVector2f& P : Points)
		{
			Verts.Add(FSlateVertex::Make<ESlateVertexRounding::Disabled>(RT, P, FVector2f(0.5f, 0.5f), Col));
		}
		for (int32 i = 0; i < Points.Num(); ++i)
		{
			Indices.Add(0);
			Indices.Add(1 + i);
			Indices.Add(1 + ((i + 1) % Points.Num()));
		}
		FSlateDrawElement::MakeCustomVerts(Out, Layer, Handle, Verts, Indices, nullptr, 0, 0);
	}

	void Disc(FSlateWindowElementList& Out, int32 Layer, const FGeometry& Geo, const FVector2f& C, float R,
		const FLinearColor& Color, int32 Segments = 28)
	{
		TArray<FVector2f> Pts;
		Pts.Reserve(Segments);
		for (int32 i = 0; i < Segments; ++i)
		{
			const float A = (2.f * PI * i) / Segments;
			Pts.Add(C + FVector2f(FMath::Cos(A), FMath::Sin(A)) * R);
		}
		Fill(Out, Layer, Geo, Pts, C, Color);
	}

	FVector2D Measure(const FString& Text, const FSlateFontInfo& Font)
	{
		return FSlateApplication::Get().GetRenderer()->GetFontMeasureService()->Measure(Text, Font);
	}

	void Label(FSlateWindowElementList& Out, int32 Layer, const FGeometry& Geo, const FVector2f& TopLeft,
		const FString& Text, const FSlateFontInfo& Font, const FLinearColor& Color)
	{
		const FVector2D Sz = Measure(Text, Font);
		FSlateDrawElement::MakeText(Out, Layer,
			Geo.ToPaintGeometry(FVector2f(static_cast<float>(Sz.X) + 4.f, static_cast<float>(Sz.Y) + 2.f), FSlateLayoutTransform(TopLeft)),
			Text, Font, ESlateDrawEffect::None, Color);
	}

	FSlateFontInfo BoardFont(const TCHAR* Face, float Size, int32 Tracking)
	{
		FSlateFontInfo Font = FCoreStyle::GetDefaultFontStyle(Face, Size);
		Font.LetterSpacing = Tracking;
		return Font;
	}
}

using namespace IBWatchBoardPaint;

void UIBSectorBoardWidget::NativeOnInitialized()
{
	Super::NativeOnInitialized();
	if (WidgetTree && !WidgetTree->RootWidget)
	{
		WidgetTree->RootWidget = WidgetTree->ConstructWidget<UOverlay>(UOverlay::StaticClass());
	}
	SetVisibility(ESlateVisibility::Visible); // we ARE the hit target
	SetClipping(EWidgetClipping::ClipToBounds);
	NetLine = NSLOCTEXT("IBWatch", "NetUnknown", "BREAKWATER NET");
	NetColor = IBStyle::TextLo();
}

void UIBSectorBoardWidget::SetMarks(FName InSelected, FName InProposed, FName InArmed, FName InCurrent)
{
	SelectedId = InSelected;
	ProposedId = InProposed;
	ArmedId = InArmed;
	CurrentId = InCurrent;
}

void UIBSectorBoardWidget::SetNetLine(const FText& InLine, const FLinearColor& Color)
{
	NetLine = InLine;
	NetColor = Color;
}

void UIBSectorBoardWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);
	Pulse += InDeltaTime;
	Invalidate(EInvalidateWidgetReason::Paint);
}

FName UIBSectorBoardWidget::PinAt(const FVector2D& Local, const FVector2D& Size) const
{
	FName Best;
	float BestDist = PinHitRadius;
	for (const FIBDestination& D : IBWatch::Destinations())
	{
		const FVector2D P(D.BoardPosition.X * Size.X, D.BoardPosition.Y * Size.Y);
		const float Dist = static_cast<float>(FVector2D::Distance(P, Local));
		if (Dist < BestDist)
		{
			BestDist = Dist;
			Best = D.Id;
		}
	}
	return Best;
}

FReply UIBSectorBoardWidget::NativeOnMouseButtonDown(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent)
{
	if (InMouseEvent.GetEffectingButton() == EKeys::LeftMouseButton)
	{
		const FVector2D Local = InGeometry.AbsoluteToLocal(InMouseEvent.GetScreenSpacePosition());
		const FName Hit = PinAt(Local, InGeometry.GetLocalSize());
		if (!Hit.IsNone())
		{
			SelectedId = Hit;
			OnDestinationPicked.Broadcast(Hit);
			return FReply::Handled();
		}
	}
	return Super::NativeOnMouseButtonDown(InGeometry, InMouseEvent);
}

FReply UIBSectorBoardWidget::NativeOnMouseMove(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent)
{
	const FVector2D Local = InGeometry.AbsoluteToLocal(InMouseEvent.GetScreenSpacePosition());
	HoverId = PinAt(Local, InGeometry.GetLocalSize());
	SetCursor(HoverId.IsNone() ? EMouseCursor::Default : EMouseCursor::Hand);
	return Super::NativeOnMouseMove(InGeometry, InMouseEvent);
}

void UIBSectorBoardWidget::NativeOnMouseLeave(const FPointerEvent& InMouseEvent)
{
	HoverId = NAME_None;
	SetCursor(EMouseCursor::Default);
	Super::NativeOnMouseLeave(InMouseEvent);
}

int32 UIBSectorBoardWidget::NativePaint(const FPaintArgs& Args, const FGeometry& Geo, const FSlateRect& MyCullingRect,
	FSlateWindowElementList& Out, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const
{
	const FVector2D Size = Geo.GetLocalSize();
	if (Size.X < 40.0 || Size.Y < 40.0)
	{
		return Super::NativePaint(Args, Geo, MyCullingRect, Out, LayerId, InWidgetStyle, bParentEnabled);
	}

	const FSlateFontInfo FontTitle = BoardFont(TEXT("Bold"), 9.f, 400);
	const FSlateFontInfo FontPin   = BoardFont(TEXT("Bold"), 9.f, 250);
	const FSlateFontInfo FontSub   = BoardFont(TEXT("Regular"), 8.f, 200);
	const FSlateFontInfo FontTiny  = BoardFont(TEXT("Regular"), 7.f, 300);

	const FLinearColor Grid   = IBStyle::Line() * FLinearColor(0.45f, 0.8f, 1.f, 0.22f);
	const FLinearColor Coastl = FLinearColor(0.22f, 0.65f, 0.76f, 0.8f);
	const FLinearColor Land   = FLinearColor(0.008f, 0.021f, 0.030f, 1.f);
	const FLinearColor Sea    = IBStyle::Cyan() * FLinearColor(1.f, 1.f, 1.f, 0.16f);

	int32 L = LayerId;

	// ---- land mass (fan from deep inland; the coast is star-shaped from there) ----
	{
		TArray<FVector2f> Poly;
		for (const FVector2D& C : Coast) { Poly.Add(At(C, Size)); }
		Poly.Add(At(FVector2D(0.0, 1.0), Size));
		Poly.Add(At(FVector2D(0.0, 0.0), Size));
		Fill(Out, L, Geo, Poly, At(FVector2D(0.20, 0.50), Size), Land);
	}
	++L;

	// ---- grid ----
	for (int32 i = 1; i < 12; ++i)
	{
		const float X = static_cast<float>(Size.X * i / 12.0);
		Line(Out, L, Geo, { FVector2f(X, 0.f), FVector2f(X, static_cast<float>(Size.Y)) }, Grid, 1.f);
	}
	for (int32 i = 1; i < 8; ++i)
	{
		const float Y = static_cast<float>(Size.Y * i / 8.0);
		Line(Out, L, Geo, { FVector2f(0.f, Y), FVector2f(static_cast<float>(Size.X), Y) }, Grid, 1.f);
	}
	// sea swell hatching
	{
		const FVector2D Swell[] = { {0.78, 0.22}, {0.86, 0.34}, {0.74, 0.46}, {0.90, 0.58}, {0.80, 0.70}, {0.88, 0.86}, {0.66, 0.30}, {0.72, 0.12} };
		for (int32 i = 0; i < static_cast<int32>(UE_ARRAY_COUNT(Swell)); ++i)
		{
			const FVector2f C = At(Swell[i], Size) + FVector2f(FMath::Sin(Pulse * 0.6f + i) * 4.f, 0.f);
			Line(Out, L, Geo, { C - FVector2f(14.f, 0.f), C + FVector2f(14.f, 0.f) }, Sea, 1.f);
			Line(Out, L, Geo, { C - FVector2f(8.f, -4.f), C + FVector2f(8.f, 4.f) }, Sea, 1.f);
		}
	}
	++L;

	// ---- range rings out from CARROW-1 ----
	{
		const FVector2f W = At(WatchPos, Size);
		const float Base = static_cast<float>(Size.X) * 0.11f;
		DashedRing(Out, L, Geo, W, Base * 1.f, IBStyle::Line() * FLinearColor(1, 1, 1, 0.9f), 1.f, 28);
		DashedRing(Out, L, Geo, W, Base * 2.f, IBStyle::Line() * FLinearColor(1, 1, 1, 0.7f), 1.f, 40);
		DashedRing(Out, L, Geo, W, Base * 3.f, IBStyle::Line() * FLinearColor(1, 1, 1, 0.5f), 1.f, 52);
		// sweep hand
		const float A = Pulse * 0.35f;
		Line(Out, L, Geo, { W, W + FVector2f(FMath::Cos(A), FMath::Sin(A)) * Base * 3.f }, IBStyle::Cyan() * FLinearColor(1, 1, 1, 0.22f), 1.f);
	}
	++L;

	// ---- coastline + sea wall ----
	{
		TArray<FVector2f> C;
		for (const FVector2D& P : Coast) { C.Add(At(P, Size)); }
		Line(Out, L, Geo, C, FLinearColor(Coastl.R, Coastl.G, Coastl.B, 0.10f), 6.f);
		Line(Out, L, Geo, C, Coastl, 1.1f);
		// surf line, a touch offshore
		TArray<FVector2f> Surf;
		for (const FVector2D& P : Coast) { Surf.Add(At(P, Size) + FVector2f(7.f, 0.f)); }
		Line(Out, L, Geo, Surf, IBStyle::Cyan() * FLinearColor(1, 1, 1, 0.28f), 1.f);

		const FVector2f A = At(SeaWallA, Size);
		const FVector2f B = At(SeaWallB, Size);
		Line(Out, L, Geo, { A, B }, IBStyle::TextHi() * FLinearColor(1, 1, 1, 0.85f), 3.f);
		// wall ticks
		const FVector2f Dir = (B - A).GetSafeNormal();
		const FVector2f Nrm(-Dir.Y, Dir.X);
		for (int32 i = 1; i < 6; ++i)
		{
			const FVector2f P = A + (B - A) * (i / 6.f);
			Line(Out, L, Geo, { P - Nrm * 4.f, P + Nrm * 4.f }, IBStyle::TextHi() * FLinearColor(1, 1, 1, 0.6f), 1.f);
		}
		Label(Out, L, Geo, (A + B) * 0.5f + FVector2f(12.f, -6.f), TEXT("SEA WALL"), FontTiny, IBStyle::TextLo());
	}
	++L;

	// ---- pins ----
	for (const FIBDestination& D : IBWatch::Destinations())
	{
		const FVector2f P = At(D.BoardPosition, Size);
		const FLinearColor Kind = IBWatch::KindColor(D.Kind);
		const bool bLocked = !D.CanDeploy() && D.Kind != EIBDestinationKind::Bastion;
		const bool bHere = (D.Id == CurrentId);

		if (D.Kind == EIBDestinationKind::Bastion)
		{
			// the citadel: a diamond
			const float R = 8.f;
			Line(Out, L, Geo, { P + FVector2f(0, -R), P + FVector2f(R, 0), P + FVector2f(0, R), P + FVector2f(-R, 0), P + FVector2f(0, -R) }, Kind, 1.6f);
			if (bHere) { Disc(Out, L, Geo, P, 3.f, Kind); }
		}
		else if (bLocked)
		{
			Ring(Out, L, Geo, P, 6.f, Kind, 1.2f, 20);
			Line(Out, L, Geo, { P + FVector2f(-3, -3), P + FVector2f(3, 3) }, Kind, 1.f);
			Line(Out, L, Geo, { P + FVector2f(-3, 3), P + FVector2f(3, -3) }, Kind, 1.f);
		}
		else
		{
			Disc(Out, L, Geo, P, 6.5f, Kind);
			Disc(Out, L, Geo, P, 2.5f, IBStyle::Ink());
			if (bHere) { Ring(Out, L, Geo, P, 11.f, IBStyle::TextHi() * FLinearColor(1, 1, 1, 0.8f), 1.f); }
		}

		// marks
		if (D.Id == HoverId && D.Id != SelectedId)
		{
			Ring(Out, L + 1, Geo, P, 10.f, IBStyle::TextHi() * FLinearColor(1, 1, 1, 0.55f), 1.f);
		}
		if (D.Id == SelectedId)
		{
			Ring(Out, L + 1, Geo, P, 12.f, IBStyle::Amber(), 2.f);
			for (int32 k = 0; k < 4; ++k)
			{
				const float A = k * PI * 0.5f + PI * 0.25f;
				const FVector2f Dir(FMath::Cos(A), FMath::Sin(A));
				Line(Out, L + 1, Geo, { P + Dir * 15.f, P + Dir * 21.f }, IBStyle::Amber(), 1.5f);
			}
		}
		if (D.Id == ProposedId && D.Id != ArmedId)
		{
			const float R = 13.f + 4.f * (0.5f + 0.5f * FMath::Sin(Pulse * 4.f));
			Ring(Out, L + 1, Geo, P, R, IBStyle::Cyan() * FLinearColor(1, 1, 1, 0.9f), 1.5f);
		}
		if (D.Id == ArmedId)
		{
			const float F = FMath::Fmod(Pulse, 1.f);
			Ring(Out, L + 1, Geo, P, 13.f + 9.f * F, IBStyle::Amber() * FLinearColor(1, 1, 1, 1.f - F), 2.f);
			Ring(Out, L + 1, Geo, P, 13.f + 9.f * FMath::Fmod(F + 0.5f, 1.f), IBStyle::Amber() * FLinearColor(1, 1, 1, 1.f - FMath::Fmod(F + 0.5f, 1.f)), 1.5f);
		}

		// labels — flip to the left near the right edge
		const FString Name = D.Name.ToString();
		const FString Sub  = bHere && D.Kind == EIBDestinationKind::Bastion ? TEXT("YOU ARE HERE")
			: bHere ? FString::Printf(TEXT("%s · HERE"), *D.Codename.ToString())
			: D.Id == ArmedId ? TEXT("DEPLOYING") : D.Codename.ToString();
		const FVector2D NameSz = Measure(Name, FontPin);
		const bool bLeft = (P.X > Size.X * 0.70);
		const float TX = bLeft ? P.X - 14.f - static_cast<float>(NameSz.X) : P.X + 14.f;
		const FLinearColor NameCol = bLocked ? Kind : (D.Id == SelectedId ? IBStyle::TextHi() : Kind);
		Label(Out, L + 2, Geo, FVector2f(TX, P.Y - 14.f), Name, FontPin, NameCol);
		Label(Out, L + 2, Geo, FVector2f(TX, P.Y - 1.f), Sub, FontSub, D.Id == ArmedId ? IBStyle::Amber() : IBStyle::TextLo());
	}
	L += 3;

	// ---- chrome ----
	{
		const FString Net = NetLine.ToString();
		const FVector2D Sz = Measure(Net, FontTitle);
		Label(Out, L, Geo, FVector2f(static_cast<float>(Size.X - Sz.X) - 12.f, 10.f), Net, FontTitle, NetColor);
	}
	// scale bar bottom-left
	{
		const FVector2f A(14.f, static_cast<float>(Size.Y) - 16.f);
		const FVector2f B = A + FVector2f(static_cast<float>(Size.X) * 0.11f, 0.f);
		Line(Out, L, Geo, { A, B }, IBStyle::TextLo(), 1.f);
		Line(Out, L, Geo, { A + FVector2f(0, -4), A + FVector2f(0, 4) }, IBStyle::TextLo(), 1.f);
		Line(Out, L, Geo, { B + FVector2f(0, -4), B + FVector2f(0, 4) }, IBStyle::TextLo(), 1.f);
		Label(Out, L, Geo, B + FVector2f(8.f, -7.f), TEXT("5 KM"), FontTiny, IBStyle::TextLo());
	}
	// north
	{
		const FVector2f N(static_cast<float>(Size.X) - 26.f, static_cast<float>(Size.Y) - 34.f);
		Line(Out, L, Geo, { N + FVector2f(0, 16), N + FVector2f(0, -8) }, IBStyle::TextLo(), 1.f);
		Line(Out, L, Geo, { N + FVector2f(-4, -2), N + FVector2f(0, -8), N + FVector2f(4, -2) }, IBStyle::TextLo(), 1.f);
		Label(Out, L, Geo, N + FVector2f(-3.f, -22.f), TEXT("N"), FontTiny, IBStyle::TextLo());
	}
	++L;

	return Super::NativePaint(Args, Geo, MyCullingRect, Out, L, InWidgetStyle, bParentEnabled);
}

