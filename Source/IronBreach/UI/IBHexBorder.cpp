#include "UI/IBHexBorder.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/SNullWidget.h"
#include "Rendering/DrawElements.h"
#include "Framework/Application/SlateApplication.h"
#include "Styling/CoreStyle.h"
#include "Components/PanelSlot.h"

/**
 * The Slate half: paints the elongated hexagon (fill via custom verts, glow
 * outline via line batch), children on top.
 */
class SIBHexBorder : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SIBHexBorder) {}
		SLATE_DEFAULT_SLOT(FArguments, Content)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs)
	{
		ChildSlot
		[
			InArgs._Content.Widget
		];
	}

	void SetContent(const TSharedRef<SWidget>& InContent) { ChildSlot.AttachWidget(InContent); }
	void SetHexFill(const FLinearColor& InColor)          { Fill = InColor; }
	void SetHexOutline(const FLinearColor& InColor)       { Outline = InColor; }
	void SetHexThickness(float InThickness)               { Thickness = InThickness; }
	void SetHexPointFraction(float InFraction)            { PointFraction = InFraction; }
	void SetHexPadding(const FMargin& InPadding)          { ChildSlot.SetPadding(InPadding); }

	virtual int32 OnPaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
		FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override
	{
		const FVector2f Size(AllottedGeometry.GetLocalSize());
		if (Size.X > 1.f && Size.Y > 1.f)
		{
			const float Ph = FMath::Clamp(PointFraction, 0.0f, 0.4f) * Size.Y;

			// The banner silhouette: point up top, long sides, point below.
			const TArray<FVector2f> Points = {
				FVector2f(Size.X * 0.5f, 0.f),
				FVector2f(Size.X,        Ph),
				FVector2f(Size.X,        Size.Y - Ph),
				FVector2f(Size.X * 0.5f, Size.Y),
				FVector2f(0.f,           Size.Y - Ph),
				FVector2f(0.f,           Ph)
			};

			// Fill: triangle fan around the center, flat-colored white brush.
			const FSlateBrush* WhiteBrush = FCoreStyle::Get().GetBrush("GenericWhiteBox");
			const FSlateResourceHandle Handle = FSlateApplication::Get().GetRenderer()->GetResourceHandle(*WhiteBrush);
			const FSlateRenderTransform& RenderTransform = AllottedGeometry.GetAccumulatedRenderTransform();
			const FColor FillColor = Fill.ToFColor(true);

			TArray<FSlateVertex> Verts;
			TArray<SlateIndex> Indices;
			Verts.Reserve(Points.Num() + 1);
			Indices.Reserve(Points.Num() * 3);

			Verts.Add(FSlateVertex::Make<ESlateVertexRounding::Disabled>(RenderTransform, Size * 0.5f, FVector2f(0.5f, 0.5f), FillColor));
			for (const FVector2f& P : Points)
			{
				Verts.Add(FSlateVertex::Make<ESlateVertexRounding::Disabled>(RenderTransform, P, FVector2f(0.5f, 0.5f), FillColor));
			}
			for (int32 i = 0; i < Points.Num(); ++i)
			{
				Indices.Add(0);
				Indices.Add(1 + i);
				Indices.Add(1 + ((i + 1) % Points.Num()));
			}
			FSlateDrawElement::MakeCustomVerts(OutDrawElements, LayerId, Handle, Verts, Indices, nullptr, 0, 0);

			// Outline: closed loop, antialiased.
			TArray<FVector2f> Loop = Points;
			Loop.Add(Points[0]);
			FSlateDrawElement::MakeLines(OutDrawElements, LayerId + 1, AllottedGeometry.ToPaintGeometry(),
				Loop, ESlateDrawEffect::None, Outline, /*bAntialias=*/true, Thickness);
		}

		return SCompoundWidget::OnPaint(Args, AllottedGeometry, MyCullingRect, OutDrawElements, LayerId + 2, InWidgetStyle, bParentEnabled);
	}

private:
	FLinearColor Fill = FLinearColor(0.03f, 0.04f, 0.065f, 1.0f);
	FLinearColor Outline = FLinearColor(0.12f, 0.16f, 0.24f, 1.0f);
	float Thickness = 1.5f;
	float PointFraction = 0.10f;
};

// ---- UMG wrapper ----

TSharedRef<SWidget> UIBHexBorder::RebuildWidget()
{
	MyHex = SNew(SIBHexBorder);
	if (GetChildrenCount() > 0 && GetContentSlot() && GetContentSlot()->Content)
	{
		MyHex->SetContent(GetContentSlot()->Content->TakeWidget());
	}
	PushToSlate();
	return MyHex.ToSharedRef();
}

void UIBHexBorder::SynchronizeProperties()
{
	Super::SynchronizeProperties();
	PushToSlate();
}

void UIBHexBorder::ReleaseSlateResources(bool bReleaseChildren)
{
	Super::ReleaseSlateResources(bReleaseChildren);
	MyHex.Reset();
}

void UIBHexBorder::OnSlotAdded(UPanelSlot* InSlot)
{
	if (MyHex.IsValid() && InSlot && InSlot->Content)
	{
		MyHex->SetContent(InSlot->Content->TakeWidget());
	}
}

void UIBHexBorder::OnSlotRemoved(UPanelSlot* /*InSlot*/)
{
	if (MyHex.IsValid())
	{
		MyHex->SetContent(SNullWidget::NullWidget);
	}
}

void UIBHexBorder::PushToSlate()
{
	if (!MyHex.IsValid()) { return; }
	MyHex->SetHexFill(FillColor);
	MyHex->SetHexOutline(OutlineColor);
	MyHex->SetHexThickness(OutlineThickness);
	MyHex->SetHexPointFraction(PointFraction);
	MyHex->SetHexPadding(ContentPadding);
}

void UIBHexBorder::SetFillColor(FLinearColor InColor)       { FillColor = InColor; PushToSlate(); }
void UIBHexBorder::SetOutlineColor(FLinearColor InColor)    { OutlineColor = InColor; PushToSlate(); }
void UIBHexBorder::SetOutlineThickness(float InThickness)   { OutlineThickness = InThickness; PushToSlate(); }
void UIBHexBorder::SetPointFraction(float InFraction)       { PointFraction = InFraction; PushToSlate(); }
void UIBHexBorder::SetContentPadding(FMargin InPadding)     { ContentPadding = InPadding; PushToSlate(); }
