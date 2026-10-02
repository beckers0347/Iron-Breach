#pragma once

#include "CoreMinimal.h"
#include "Components/Widget.h"
#include "IBMenuGlyph.generated.h"

/** Native line-art marks used by the menu chrome. No texture, no font glyph, scales with its box. */
UENUM()
enum class EIBMenuGlyph : uint8
{
	/** Breakwater insignia: a cut diamond around a double chevron. */
	Insignia,
	/** Small diamond with a lit core (counters, list marks). */
	Diamond,
	/** Eight-tooth cog (settings). */
	Cog,
	/** Right-pointing chevron. */
	Chevron,
	/** Left-pointing chevron. */
	ChevronLeft,
	/** Magnifier (search). */
	Search,
	/** Padlock (locked entries). */
	Lock,
	/** Active-tab underline: a full-width hairline with a lit diamond at its center. */
	Notch,
	/** Four-square grid (view mode). */
	Grid,
	/** Deployment target: ring, cross-hairs and a core. */
	Target,
	/** Confirmed mark. */
	Check
};

namespace IBMenuGlyphPaint { class SGlyph; }

/**
 * Painted geometric marks for the shared header and menu chrome (IBHangar::Glyph
 * builds them). Purely decorative and hit-test invisible by default; size comes
 * from SetGlyphSize and the mark scales to whatever box the layout gives it.
 */
UCLASS()
class IRONBREACH_API UIBMenuGlyph : public UWidget
{
	GENERATED_BODY()

public:
	UIBMenuGlyph(const FObjectInitializer& ObjectInitializer);

	void SetGlyph(EIBMenuGlyph InGlyph);
	void SetTint(const FLinearColor& InTint);
	void SetGlyphSize(FVector2D InSize);
	/** Stroke thickness at a 24 px box; scales with the box. */
	void SetWeight(float InWeight);

	EIBMenuGlyph GetGlyph() const { return Glyph; }

protected:
	virtual TSharedRef<SWidget> RebuildWidget() override;
	virtual void SynchronizeProperties() override;
	virtual void ReleaseSlateResources(bool bReleaseChildren) override;

private:
	void PushParams();

	EIBMenuGlyph Glyph = EIBMenuGlyph::Diamond;
	FLinearColor Tint = FLinearColor(0.28f, 0.78f, 0.90f);
	FVector2D GlyphSize = FVector2D(20.0, 20.0);
	float Weight = 1.6f;

	TSharedPtr<IBMenuGlyphPaint::SGlyph> MyGlyph;
};
