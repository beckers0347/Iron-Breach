#include "UI/IBGlassBorder.h"
#include "UI/IBPaintKit.h"
#include "Components/BorderSlot.h"
#include "Widgets/Layout/SBorder.h"

namespace IBGlassPresentation
{
	/** Chamfered outline of a W x H panel, clockwise from the top-left, cuts clamped to the panel. */
	static void BuildShape(float W, float H, const FIBGlassStyle& Glass, float Inset, TArray<FVector2f>& Out)
	{
		const float Limit = FMath::Max(0.f, FMath::Min(W, H) * 0.45f - Inset);
		auto Cut = [&](float Value) { return FMath::Clamp(Value - Inset * 0.6f, 0.f, Limit); };
		const float TL = Cut(Glass.ChamferTopLeft), TR = Cut(Glass.ChamferTopRight);
		const float BR = Cut(Glass.ChamferBottomRight), BL = Cut(Glass.ChamferBottomLeft);
		const float X0 = Inset, Y0 = Inset, X1 = W - Inset, Y1 = H - Inset;
		Out.Reset(8);
		if (TL > 0.f) { Out.Add(FVector2f(X0, Y0 + TL)); Out.Add(FVector2f(X0 + TL, Y0)); } else { Out.Add(FVector2f(X0, Y0)); }
		if (TR > 0.f) { Out.Add(FVector2f(X1 - TR, Y0)); Out.Add(FVector2f(X1, Y0 + TR)); } else { Out.Add(FVector2f(X1, Y0)); }
		if (BR > 0.f) { Out.Add(FVector2f(X1, Y1 - BR)); Out.Add(FVector2f(X1 - BR, Y1)); } else { Out.Add(FVector2f(X1, Y1)); }
		if (BL > 0.f) { Out.Add(FVector2f(X0 + BL, Y1)); Out.Add(FVector2f(X0, Y1 - BL)); } else { Out.Add(FVector2f(X0, Y1)); }
	}

	class SGlassBorder final : public SBorder
	{
	public:
		/** The UMG border that owns this widget; its brush and BrushColor are read at paint time,
		 *  so a runtime SetBrush / SetBrushColor shows on the very next frame. */
		void SetOwner(const UIBGlassBorder* InOwner) { Owner = InOwner; Invalidate(EInvalidateWidgetReason::Paint); }

		void SetGlassStyle(const FIBGlassStyle& InGlass)
		{
			Glass = InGlass;
			Invalidate(EInvalidateWidgetReason::Paint);
		}

		virtual int32 OnPaint(const FPaintArgs& Args, const FGeometry& Geo, const FSlateRect& Cull,
			FSlateWindowElementList& Out, int32 LayerId, const FWidgetStyle& Style, bool bParentEnabled) const override
		{
			const FVector2f Size(Geo.GetLocalSize());
			const float W = Size.X, H = Size.Y;
			if (W < 2.f || H < 2.f)
			{
				return SCompoundWidget::OnPaint(Args, Geo, Cull, Out, LayerId, Style, bParentEnabled);
			}

			// One tint for everything: parent color/opacity x the border's BrushColor x the
			// disabled dim. Fill and edge colors come from the border's configured brush.
			FLinearColor FillColor(0.008f, 0.019f, 0.028f, 0.83f);
			FLinearColor EdgeColor(0.12f, 0.29f, 0.35f, 0.65f);
			FLinearColor Tint = Style.GetColorAndOpacityTint();
			if (const UIBGlassBorder* Border = Owner.Get())
			{
				const FSlateBrush& Brush = Border->Background;
				FillColor = Brush.TintColor.GetColor(Style);
				if (Brush.OutlineSettings.Width > 0.f) { EdgeColor = Brush.OutlineSettings.Color.GetColor(Style); }
				Tint *= Border->GetBrushColor();
			}
			if (!ShouldBeEnabled(bParentEnabled)) { Tint.A *= 0.7f; }
			const FLinearColor Fill = FillColor * Tint;
			const FLinearColor Edge = EdgeColor * Tint;
			const FLinearColor Accent = Glass.Accent * Tint;
			const FLinearColor Sheen = FLinearColor(1.f, 1.f, 1.f, Glass.SheenAlpha) * Tint;

			TArray<FVector2f> Shape;
			BuildShape(W, H, Glass, 0.f, Shape);
			if (Fill.A > 0.f)
			{
				IBPaint::Fill(Out, LayerId, Geo, Shape, FVector2f(W * 0.5f, H * 0.5f), Fill);
			}
			if (Glass.SheenAlpha > 0.f)
			{
				// Sheen stays between the top cuts so it never spills outside the polygon.
				const float Left = FMath::Max(Glass.ChamferTopLeft, 0.f), Right = FMath::Max(Glass.ChamferTopRight, 0.f);
				const float Width = W - Left - Right;
				if (Width > 4.f)
				{
					IBPaint::Gradient(Out, LayerId, Geo, FVector2f(Left, 0.f), FVector2f(Width, FMath::Min(H * 0.5f, 48.f)),
						Sheen, FLinearColor(Sheen.R, Sheen.G, Sheen.B, 0.f), true);
				}
			}

			if (Glass.bBottomEdgeOnly)
			{
				IBPaint::Seg(Out, LayerId + 1, Geo, FVector2f(0.f, H - 0.5f), FVector2f(W, H - 0.5f), Edge, 1.f);
			}
			else
			{
				TArray<FVector2f> Outline = Shape;
				Outline.Add(Shape[0]);
				IBPaint::Line(Out, LayerId + 1, Geo, Outline, Edge, 1.f);
				if (Glass.BevelAlpha > 0.f && W > Glass.BevelInset * 4.f && H > Glass.BevelInset * 4.f)
				{
					TArray<FVector2f> Bevel;
					BuildShape(W, H, Glass, Glass.BevelInset, Bevel);
					// Close the loop through a COPY of the first point. Bevel.Add(Bevel[0])
					// passes a reference into the same array, and Add reallocates when it
					// grows -- TArray asserts on that ("element which already comes from the
					// container being modified") and took the title screen down with it.
					if (Bevel.Num() > 0)
					{
						const FVector2f BevelFirst = Bevel[0];
						Bevel.Add(BevelFirst);
					}
					IBPaint::Line(Out, LayerId + 1, Geo, Bevel, IBPaint::Alpha(Edge, Glass.BevelAlpha), 1.f);
				}
			}

			if (Glass.AccentLength > 0.f)
			{
				const float TL = FMath::Clamp(Glass.ChamferTopLeft, 0.f, FMath::Min(W, H) * 0.45f);
				const float Length = FMath::Min(Glass.AccentLength, W - TL - 2.f);
				if (TL > 0.f)
				{
					IBPaint::Line(Out, LayerId + 1, Geo, { FVector2f(0.f, TL), FVector2f(TL, 0.f), FVector2f(TL + Length, 0.f) }, Accent, Glass.AccentThickness);
				}
				else
				{
					IBPaint::Seg(Out, LayerId + 1, Geo, FVector2f(0.f, 0.f), FVector2f(Length, 0.f), Accent, Glass.AccentThickness);
				}
			}
			if (Glass.bCornerTick && W > 40.f && H > 40.f)
			{
				const float BR = FMath::Clamp(Glass.ChamferBottomRight, 0.f, FMath::Min(W, H) * 0.45f);
				const float Tick = 12.f;
				if (BR > 0.f)
				{
					IBPaint::Line(Out, LayerId + 1, Geo, { FVector2f(W - BR - Tick, H), FVector2f(W - BR, H), FVector2f(W, H - BR), FVector2f(W, H - BR - Tick) },
						IBPaint::Alpha(Accent, 0.85f), 1.5f);
				}
				else
				{
					IBPaint::Line(Out, LayerId + 1, Geo, { FVector2f(W - Tick, H), FVector2f(W, H), FVector2f(W, H - Tick) }, IBPaint::Alpha(Accent, 0.85f), 1.5f);
				}
			}

			return SCompoundWidget::OnPaint(Args, Geo, Cull, Out, LayerId + 2, Style, bParentEnabled);
		}

	private:
		TWeakObjectPtr<const UIBGlassBorder> Owner;
		FIBGlassStyle Glass;
	};
}

UIBGlassBorder::UIBGlassBorder(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
	// Glass never draws the stock border box; the painted polygon is the frame.
	FSlateBrush Brush;
	Brush.DrawAs = ESlateBrushDrawType::RoundedBox;
	Brush.TintColor = FLinearColor(0.008f, 0.019f, 0.028f, 0.83f);
	Brush.OutlineSettings = FSlateBrushOutlineSettings(FVector4(0.f, 0.f, 0.f, 0.f), FLinearColor(0.12f, 0.29f, 0.35f, 0.65f), 1.f);
	SetBrush(Brush);
	SetPadding(FMargin(20.f));
}

void UIBGlassBorder::SetGlassStyle(const FIBGlassStyle& InStyle)
{
	GlassStyle = InStyle;
	PushStyle();
}

void UIBGlassBorder::SetAccentColor(const FLinearColor& InColor)
{
	GlassStyle.Accent = InColor;
	PushStyle();
}

void UIBGlassBorder::PushStyle()
{
	if (MyBorder.IsValid())
	{
		StaticCastSharedPtr<IBGlassPresentation::SGlassBorder>(MyBorder)->SetGlassStyle(GlassStyle);
	}
}

TSharedRef<SWidget> UIBGlassBorder::RebuildWidget()
{
	TSharedRef<IBGlassPresentation::SGlassBorder> Glass = SNew(IBGlassPresentation::SGlassBorder);
	// Colors are read from this border at paint time (Background + BrushColor), so the
	// stock SetBrush / SetBrushColor keep working at runtime without extra plumbing.
	Glass->SetOwner(this);
	MyBorder = Glass;
	if (GetChildrenCount() > 0)
	{
		CastChecked<UBorderSlot>(GetContentSlot())->BuildSlot(MyBorder.ToSharedRef());
	}
	PushStyle();
	return MyBorder.ToSharedRef();
}

void UIBGlassBorder::SynchronizeProperties()
{
	Super::SynchronizeProperties();
	PushStyle();
}
