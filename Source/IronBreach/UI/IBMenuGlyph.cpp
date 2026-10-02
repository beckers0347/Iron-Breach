#include "UI/IBMenuGlyph.h"
#include "UI/IBPaintKit.h"
#include "Widgets/SLeafWidget.h"

namespace IBMenuGlyphPaint
{
	class SGlyph final : public SLeafWidget
	{
	public:
		SLATE_BEGIN_ARGS(SGlyph) {}
		SLATE_END_ARGS()

		void Construct(const FArguments&) {}

		void SetParams(EIBMenuGlyph InGlyph, const FLinearColor& InTint, const FVector2D& InSize, float InWeight)
		{
			const bool bLayout = InSize != Size;
			Glyph = InGlyph; Tint = InTint; Size = InSize; Weight = InWeight;
			Invalidate(bLayout ? EInvalidateWidgetReason::Layout : EInvalidateWidgetReason::Paint);
		}

		virtual FVector2D ComputeDesiredSize(float) const override { return Size; }

		virtual int32 OnPaint(const FPaintArgs&, const FGeometry& Geo, const FSlateRect&,
			FSlateWindowElementList& Out, int32 Layer, const FWidgetStyle& Style, bool) const override
		{
			const FVector2f Box(Geo.GetLocalSize());
			if (Box.X < 1.f || Box.Y < 1.f) { return Layer; }
			const float S = FMath::Min(Box.X, Box.Y);
			const FVector2f Origin((Box.X - S) * 0.5f, (Box.Y - S) * 0.5f);
			const FLinearColor Color = Tint * Style.GetColorAndOpacityTint();
			const float Stroke = FMath::Max(1.f, Weight * S / 24.f);
			auto P = [&](float U, float V) { return Origin + FVector2f(U * S, V * S); };
			auto Path = [&](std::initializer_list<FVector2f> Points, float Thickness)
			{
				TArray<FVector2f> Pts;
				for (const FVector2f& Q : Points) { Pts.Add(Origin + Q * S); }
				IBPaint::Line(Out, Layer, Geo, Pts, Color, Thickness);
			};

			switch (Glyph)
			{
			case EIBMenuGlyph::Insignia:
			{
				// Cut diamond, lit dark core, twin chevrons pointing down — the Breakwater mark.
				const TArray<FVector2f> Outer = { P(.5f, .02f), P(.98f, .5f), P(.5f, .98f), P(.02f, .5f) };
				IBPaint::Fill(Out, Layer, Geo, Outer, P(.5f, .5f), FLinearColor(0.f, 0.03f, 0.05f, 0.85f) * Style.GetColorAndOpacityTint());
				Path({ {.5f,.02f}, {.98f,.5f}, {.5f,.98f}, {.02f,.5f}, {.5f,.02f} }, Stroke);
				Path({ {.22f,.34f}, {.5f,.60f}, {.78f,.34f} }, Stroke * 1.5f);
				Path({ {.32f,.22f}, {.5f,.40f}, {.68f,.22f} }, Stroke * 1.1f);
				Path({ {.5f,.62f}, {.5f,.80f} }, Stroke * 1.2f);
				break;
			}
			case EIBMenuGlyph::Diamond:
				IBPaint::DiamondFill(Out, Layer, Geo, P(.5f, .5f), S * .18f, Color);
				IBPaint::Diamond(Out, Layer, Geo, P(.5f, .5f), S * .42f, Color, Stroke);
				break;
			case EIBMenuGlyph::Cog:
			{
				const FVector2f C = P(.5f, .5f);
				IBPaint::Ring(Out, Layer, Geo, C, S * .30f, Color, Stroke * 1.4f, 32);
				IBPaint::Ring(Out, Layer, Geo, C, S * .11f, Color, Stroke, 20);
				for (int32 Tooth = 0; Tooth < 8; ++Tooth)
				{
					const float A = Tooth * PI * 0.25f;
					const FVector2f Dir(FMath::Cos(A), FMath::Sin(A));
					IBPaint::Seg(Out, Layer, Geo, C + Dir * S * .32f, C + Dir * S * .47f, Color, Stroke * 2.2f);
				}
				break;
			}
			case EIBMenuGlyph::Chevron:
				Path({ {.36f,.18f}, {.66f,.5f}, {.36f,.82f} }, Stroke * 1.3f);
				break;
			case EIBMenuGlyph::ChevronLeft:
				Path({ {.64f,.18f}, {.34f,.5f}, {.64f,.82f} }, Stroke * 1.3f);
				break;
			case EIBMenuGlyph::Search:
				IBPaint::Ring(Out, Layer, Geo, P(.42f, .42f), S * .26f, Color, Stroke * 1.2f, 28);
				Path({ {.62f,.62f}, {.88f,.88f} }, Stroke * 1.6f);
				break;
			case EIBMenuGlyph::Lock:
			{
				Path({ {.22f,.46f}, {.78f,.46f}, {.78f,.90f}, {.22f,.90f}, {.22f,.46f} }, Stroke);
				TArray<FVector2f> Arc;
				for (int32 i = 0; i <= 12; ++i)
				{
					const float A = PI + PI * i / 12.f;
					Arc.Add(P(.5f + FMath::Cos(A) * .20f, .40f + FMath::Sin(A) * .24f));
				}
				Arc.Insert(P(.30f, .46f), 0); Arc.Add(P(.70f, .46f));
				IBPaint::Line(Out, Layer, Geo, Arc, Color, Stroke);
				IBPaint::DiamondFill(Out, Layer, Geo, P(.5f, .68f), S * .07f, Color);
				break;
			}
			case EIBMenuGlyph::Notch:
			{
				// Full-width hairline with a lit diamond at its center; the box height is the notch height.
				const float Y = Box.Y * 0.5f;
				IBPaint::Seg(Out, Layer, Geo, FVector2f(0.f, Y), FVector2f(Box.X, Y), Color, FMath::Max(1.f, Weight));
				IBPaint::DiamondFill(Out, Layer + 1, Geo, FVector2f(Box.X * 0.5f, Y), FMath::Clamp(Box.Y * 0.5f, 2.f, 5.f), Color);
				IBPaint::Seg(Out, Layer, Geo, FVector2f(Box.X * 0.5f - 16.f, Y), FVector2f(Box.X * 0.5f + 16.f, Y), IBPaint::Alpha(Color, .55f), FMath::Max(2.f, Weight * 2.f));
				break;
			}
			case EIBMenuGlyph::Grid:
				for (const FVector2f& Corner : { FVector2f(.14f,.14f), FVector2f(.54f,.14f), FVector2f(.14f,.54f), FVector2f(.54f,.54f) })
				{
					Path({ Corner, Corner + FVector2f(.32f, 0.f), Corner + FVector2f(.32f, .32f), Corner + FVector2f(0.f, .32f), Corner }, Stroke);
				}
				break;
			case EIBMenuGlyph::Target:
			{
				const FVector2f C = P(.5f, .5f);
				IBPaint::Ring(Out, Layer, Geo, C, S * .36f, Color, Stroke, 36);
				IBPaint::Disc(Out, Layer, Geo, C, S * .09f, Color, 16);
				Path({ {.5f,.04f}, {.5f,.26f} }, Stroke); Path({ {.5f,.74f}, {.5f,.96f} }, Stroke);
				Path({ {.04f,.5f}, {.26f,.5f} }, Stroke); Path({ {.74f,.5f}, {.96f,.5f} }, Stroke);
				break;
			}
			case EIBMenuGlyph::Check:
				Path({ {.18f,.52f}, {.42f,.76f}, {.84f,.28f} }, Stroke * 1.6f);
				break;
			default:
				break;
			}
			return Layer + 1;
		}

	private:
		EIBMenuGlyph Glyph = EIBMenuGlyph::Diamond;
		FLinearColor Tint = FLinearColor::White;
		FVector2D Size = FVector2D(20.0, 20.0);
		float Weight = 1.6f;
	};
}

UIBMenuGlyph::UIBMenuGlyph(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
	SetVisibility(ESlateVisibility::HitTestInvisible);
}

void UIBMenuGlyph::SetGlyph(EIBMenuGlyph InGlyph) { Glyph = InGlyph; PushParams(); }
void UIBMenuGlyph::SetTint(const FLinearColor& InTint) { Tint = InTint; PushParams(); }
void UIBMenuGlyph::SetGlyphSize(FVector2D InSize) { GlyphSize = InSize; PushParams(); }
void UIBMenuGlyph::SetWeight(float InWeight) { Weight = InWeight; PushParams(); }

void UIBMenuGlyph::PushParams()
{
	if (MyGlyph.IsValid()) { MyGlyph->SetParams(Glyph, Tint, GlyphSize, Weight); }
}

TSharedRef<SWidget> UIBMenuGlyph::RebuildWidget()
{
	MyGlyph = SNew(IBMenuGlyphPaint::SGlyph);
	PushParams();
	return MyGlyph.ToSharedRef();
}

void UIBMenuGlyph::SynchronizeProperties()
{
	Super::SynchronizeProperties();
	PushParams();
}

void UIBMenuGlyph::ReleaseSlateResources(bool bReleaseChildren)
{
	Super::ReleaseSlateResources(bReleaseChildren);
	MyGlyph.Reset();
}
