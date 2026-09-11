#include "UI/IBMenuBackdrop.h"
#include "UI/IBPaintKit.h"
#include "Widgets/SLeafWidget.h"

namespace IBMenuBackdropPaint
{
	class SBackdrop : public SLeafWidget
	{
	public:
		SLATE_BEGIN_ARGS(SBackdrop) {} SLATE_END_ARGS()
		void Construct(const FArguments&) {}
		virtual FVector2D ComputeDesiredSize(float) const override { return FVector2D::ZeroVector; }
		virtual int32 OnPaint(const FPaintArgs&, const FGeometry& G, const FSlateRect&,
			FSlateWindowElementList& Out, int32 Layer, const FWidgetStyle&, bool) const override
		{
			const FVector2f Size(G.GetLocalSize());
			IBPaint::Gradient(Out, Layer, G, FVector2f::ZeroVector, Size,
				FLinearColor(.008f, .017f, .022f, .97f), FLinearColor(.004f, .008f, .014f, .94f), false);
			const FLinearColor Grid(.15f, .29f, .32f, .055f);
			for (float X = 0; X < Size.X; X += 80.f)
				IBPaint::Seg(Out, Layer + 1, G, {X, 0}, {X, Size.Y}, Grid);
			for (float Y = 0; Y < Size.Y; Y += 80.f)
				IBPaint::Seg(Out, Layer + 1, G, {0, Y}, {Size.X, Y}, Grid);
			// Quiet architectural lines at the edges; no fabricated tactical data.
			for (int32 i = 0; i < 5; ++i)
			{
				const float X = Size.X - 180.f + i * 34.f;
				IBPaint::Seg(Out, Layer + 1, G, {X, Size.Y}, {Size.X, Size.Y - 180.f + i * 34.f}, Grid, 2.f);
			}
			const FLinearColor Stroke(.30f, .53f, .55f, .32f);
			IBPaint::Line(Out, Layer + 2, G, {{28, 100}, {28, 28}, {100, 28}}, Stroke);
			IBPaint::Line(Out, Layer + 2, G, {{Size.X - 100, Size.Y - 28}, {Size.X - 28, Size.Y - 28}, {Size.X - 28, Size.Y - 100}}, Stroke);
			return Layer + 2;
		}
	};
}

TSharedRef<SWidget> UIBMenuBackdrop::RebuildWidget()
{
	return SNew(IBMenuBackdropPaint::SBackdrop);
}
