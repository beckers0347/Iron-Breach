#pragma once

#include "CoreMinimal.h"
#include "Components/Border.h"
#include "IBGlassBorder.generated.h"

/**
 * Paint recipe for one chamfered glass panel. Plain data: the widget keeps a
 * copy and pushes it to its Slate border. Colors for the fill and the edge
 * hairline are NOT here — they come from the UBorder's own brush
 * (tint = fill, outline = edge) and BrushColor, so SetBrush / SetBrushColor
 * keep working on a glass panel exactly as they do on a plain border.
 */
struct FIBGlassStyle
{
	/** Corner cuts in local px: top-left, top-right, bottom-right, bottom-left. */
	float ChamferTopLeft = 0.f;
	float ChamferTopRight = 14.f;
	float ChamferBottomRight = 0.f;
	float ChamferBottomLeft = 14.f;

	/** Short accent stroke along the top edge from the top-left corner; length 0 disables it. */
	FLinearColor Accent = FLinearColor(0.28f, 0.78f, 0.90f);
	float AccentLength = 58.f;
	float AccentThickness = 2.f;

	/** Second hairline inset from the edge — the bevel read. Alpha 0 disables it. */
	float BevelInset = 3.f;
	float BevelAlpha = 0.22f;

	/** Small bracket tick in the bottom-right corner, accent colored. */
	bool bCornerTick = true;

	/** Light sheen under the top edge; 0 disables. */
	float SheenAlpha = 0.045f;

	/** Navigation band: no chamfers, only the bottom edge draws a hairline. */
	bool bBottomEdgeOnly = false;

	/** Default content panel: chamfered top-right / bottom-left, accent, bevel, tick. */
	static FIBGlassStyle Panel() { return FIBGlassStyle(); }

	/** Nested well or list surface: small cuts, no accent, no tick. */
	static FIBGlassStyle Inset()
	{
		FIBGlassStyle Style;
		Style.ChamferTopRight = 8.f; Style.ChamferBottomLeft = 8.f;
		Style.AccentLength = 0.f; Style.bCornerTick = false; Style.BevelAlpha = 0.f; Style.SheenAlpha = 0.03f;
		return Style;
	}

	/** Small label chip (header identity, counters). */
	static FIBGlassStyle Chip()
	{
		FIBGlassStyle Style;
		Style.ChamferTopRight = 6.f; Style.ChamferBottomLeft = 6.f;
		Style.AccentLength = 0.f; Style.bCornerTick = false; Style.BevelAlpha = 0.f; Style.SheenAlpha = 0.06f;
		return Style;
	}

	/** Full-width navigation band: square, bottom hairline only. */
	static FIBGlassStyle Band()
	{
		FIBGlassStyle Style;
		Style.ChamferTopRight = 0.f; Style.ChamferBottomLeft = 0.f;
		Style.AccentLength = 0.f; Style.bCornerTick = false; Style.BevelAlpha = 0.f; Style.SheenAlpha = 0.04f;
		Style.bBottomEdgeOnly = true;
		return Style;
	}

	/** Stat plinth under the operative: both bottom corners cut wide, no accent. */
	static FIBGlassStyle Plinth()
	{
		FIBGlassStyle Style;
		Style.ChamferTopLeft = 0.f; Style.ChamferTopRight = 0.f;
		Style.ChamferBottomRight = 26.f; Style.ChamferBottomLeft = 26.f;
		Style.AccentLength = 0.f; Style.bCornerTick = false; Style.BevelAlpha = 0.18f; Style.SheenAlpha = 0.05f;
		return Style;
	}

	/** Dossier / inspector: one big top-right cut, the rest square. */
	static FIBGlassStyle Dossier()
	{
		FIBGlassStyle Style;
		Style.ChamferTopRight = 22.f; Style.ChamferBottomLeft = 0.f; Style.ChamferBottomRight = 0.f;
		return Style;
	}
};

/**
 * Chamfered translucent glass panel: the one content frame every native menu
 * uses (IBHangar::Panel / IBMenuLayout::Card build it). Layout, padding and
 * content are plain UBorder; only the paint is custom — fill polygon with
 * cut corners, hairline edge, inset bevel line, a short cyan accent and a
 * corner tick, all multiplied by the parent's tint/opacity.
 *
 * Fill and edge follow the border's brush: SetBrush(RoundedBrush(Fill, 0,
 * Edge, 1)) or SetBrushColor(...) restyle the panel like any other border.
 * Full-screen shades, accent bars, tab underlines and image overlays stay
 * plain UBorders — only true content panels get the bevel.
 */
UCLASS()
class IRONBREACH_API UIBGlassBorder : public UBorder
{
	GENERATED_BODY()

public:
	UIBGlassBorder(const FObjectInitializer& ObjectInitializer);

	void SetGlassStyle(const FIBGlassStyle& InStyle);
	const FIBGlassStyle& GetGlassStyle() const { return GlassStyle; }

	/** Accent stroke / corner tick color — selected and hover states re-tint it. */
	void SetAccentColor(const FLinearColor& InColor);

protected:
	virtual TSharedRef<SWidget> RebuildWidget() override;
	virtual void SynchronizeProperties() override;

private:
	void PushStyle();

	FIBGlassStyle GlassStyle;
};
