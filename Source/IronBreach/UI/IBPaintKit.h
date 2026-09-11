#pragma once

#include "CoreMinimal.h"
#include "Rendering/DrawElements.h"
#include "Rendering/SlateRenderer.h"
#include "Framework/Application/SlateApplication.h"
#include "Fonts/FontMeasure.h"
#include "Styling/CoreStyle.h"
#include "Layout/Geometry.h"

/**
 * Painted-UI helpers shared by the Watch widgets (UIBPlanetWidget, and anything
 * else that draws with FSlateDrawElement instead of a WBP). Lines are
 * MakeLines, fills are triangle fans through MakeCustomVerts (the IBHexBorder
 * trick), text is MakeText with the core Roboto faces. Everything is in local
 * widget space; callers pass the FGeometry.
 *
 * Kept in a namespace (not anonymous) on purpose: this project builds unity,
 * and two .cpp files with the same anonymous helper names collide.
 */
namespace IBPaint
{
	inline void Line(FSlateWindowElementList& Out, int32 Layer, const FGeometry& Geo, const TArray<FVector2f>& Points,
		const FLinearColor& Color, float Thickness = 1.f, bool bAntiAlias = true)
	{
		if (Points.Num() < 2) { return; }
		FSlateDrawElement::MakeLines(Out, Layer, Geo.ToPaintGeometry(), Points, ESlateDrawEffect::None, Color, bAntiAlias, Thickness);
	}

	inline void Seg(FSlateWindowElementList& Out, int32 Layer, const FGeometry& Geo, const FVector2f& A, const FVector2f& B,
		const FLinearColor& Color, float Thickness = 1.f)
	{
		Line(Out, Layer, Geo, { A, B }, Color, Thickness);
	}

	inline void Ring(FSlateWindowElementList& Out, int32 Layer, const FGeometry& Geo, const FVector2f& C, float R,
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

	inline void DashedRing(FSlateWindowElementList& Out, int32 Layer, const FGeometry& Geo, const FVector2f& C, float R,
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

	/** Filled polygon as a triangle fan around Center — convex, or star-shaped from Center. */
	inline void Fill(FSlateWindowElementList& Out, int32 Layer, const FGeometry& Geo, const TArray<FVector2f>& Points,
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

	inline void Disc(FSlateWindowElementList& Out, int32 Layer, const FGeometry& Geo, const FVector2f& C, float R,
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

	inline void Rect(FSlateWindowElementList& Out, int32 Layer, const FGeometry& Geo, const FVector2f& TopLeft, const FVector2f& Size,
		const FLinearColor& Color)
	{
		const TArray<FVector2f> Pts = { TopLeft, TopLeft + FVector2f(Size.X, 0.f), TopLeft + Size, TopLeft + FVector2f(0.f, Size.Y) };
		Fill(Out, Layer, Geo, Pts, TopLeft + Size * 0.5f, Color);
	}

	/** Two-stop gradient; one Slate element instead of a stack of translucent rectangles. */
	inline void Gradient(FSlateWindowElementList& Out, int32 Layer, const FGeometry& Geo,
		const FVector2f& Pos, const FVector2f& Size, const FLinearColor& Start, const FLinearColor& End, bool bVertical = true)
	{
		const FVector2f Axis = bVertical ? FVector2f(0.f, Size.Y) : FVector2f(Size.X, 0.f);
		TArray<FSlateGradientStop> Stops;
		Stops.Emplace(FVector2f::ZeroVector, Start);
		Stops.Emplace(Axis, End);
		// Slate names the orientation of the stop lines, perpendicular to the color transition.
		FSlateDrawElement::MakeGradient(Out, Layer, Geo.ToPaintGeometry(Size, FSlateLayoutTransform(Pos)),
			MoveTemp(Stops), bVertical ? Orient_Horizontal : Orient_Vertical);
	}

	/** Diamond (square on its corner) outline; Half is the half-diagonal. */
	inline void Diamond(FSlateWindowElementList& Out, int32 Layer, const FGeometry& Geo, const FVector2f& C, float Half,
		const FLinearColor& Color, float Thickness = 1.5f)
	{
		Line(Out, Layer, Geo, { C + FVector2f(0, -Half), C + FVector2f(Half, 0), C + FVector2f(0, Half), C + FVector2f(-Half, 0), C + FVector2f(0, -Half) }, Color, Thickness);
	}

	inline void DiamondFill(FSlateWindowElementList& Out, int32 Layer, const FGeometry& Geo, const FVector2f& C, float Half,
		const FLinearColor& Color)
	{
		Fill(Out, Layer, Geo, { C + FVector2f(0, -Half), C + FVector2f(Half, 0), C + FVector2f(0, Half), C + FVector2f(-Half, 0) }, C, Color);
	}

	inline FVector2D Measure(const FString& Text, const FSlateFontInfo& Font)
	{
		return FSlateApplication::Get().GetRenderer()->GetFontMeasureService()->Measure(Text, Font);
	}

	inline void Label(FSlateWindowElementList& Out, int32 Layer, const FGeometry& Geo, const FVector2f& TopLeft,
		const FString& Text, const FSlateFontInfo& Font, const FLinearColor& Color)
	{
		const FVector2D Sz = Measure(Text, Font);
		FSlateDrawElement::MakeText(Out, Layer,
			Geo.ToPaintGeometry(FVector2f(static_cast<float>(Sz.X) + 4.f, static_cast<float>(Sz.Y) + 2.f), FSlateLayoutTransform(TopLeft)),
			Text, Font, ESlateDrawEffect::None, Color);
	}

	/** Label with its horizontal anchor: 0 = left edge at X, 0.5 = centered on X, 1 = right edge at X. */
	inline void LabelAt(FSlateWindowElementList& Out, int32 Layer, const FGeometry& Geo, const FVector2f& Anchor, float AlignX,
		const FString& Text, const FSlateFontInfo& Font, const FLinearColor& Color)
	{
		const FVector2D Sz = Measure(Text, Font);
		Label(Out, Layer, Geo, FVector2f(Anchor.X - static_cast<float>(Sz.X) * AlignX, Anchor.Y), Text, Font, Color);
	}

	inline FSlateFontInfo Font(const TCHAR* Face, float Size, int32 Tracking = 0)
	{
		FSlateFontInfo Info = FCoreStyle::GetDefaultFontStyle(Face, Size);
		Info.LetterSpacing = Tracking;
		return Info;
	}

	inline FLinearColor Alpha(const FLinearColor& C, float A)
	{
		return FLinearColor(C.R, C.G, C.B, C.A * A);
	}
}
