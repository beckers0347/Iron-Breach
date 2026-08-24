// MissionSubtitleHUD.cpp

#include "MissionSubtitleHUD.h"
#include "ActBeatProviderInterface.h"
#include "DialogueTypes.h"
#include "Engine/Canvas.h"
#include "Engine/Font.h"
#include "Engine/Engine.h"
#include "EngineUtils.h"

UObject* AMissionSubtitleHUD::FindActiveBeatProvider() const
{
	UWorld* World = GetWorld();
	if (!World)
	{
		return nullptr;
	}

	// Small, infrequent scan (once per HUD-visible frame) over actors implementing
	// the interface -- mission-scoped director actors number in the single digits,
	// so this is cheap. Swap for a cached registry later if that ever changes.
	for (TActorIterator<AActor> It(World); It; ++It)
	{
		AActor* Actor = *It;
		if (!Actor || !Actor->GetClass()->ImplementsInterface(UActBeatProviderInterface::StaticClass()))
		{
			continue;
		}

		IActBeatProviderInterface* Provider = Cast<IActBeatProviderInterface>(Actor);
		if (Provider && Provider->IsActRunning())
		{
			return Actor;
		}
	}

	return nullptr;
}

void AMissionSubtitleHUD::DrawHUD()
{
	Super::DrawHUD();

	UObject* ActiveProvider = FindActiveBeatProvider();
	if (!ActiveProvider)
	{
		return;
	}

	IActBeatProviderInterface* Provider = Cast<IActBeatProviderInterface>(ActiveProvider);
	if (!Provider)
	{
		return;
	}

	FDialogueLine Line;
	if (!Provider->GetCurrentLine(Line) || Line.Text.IsEmpty())
	{
		return;
	}

	if (!Canvas)
	{
		return;
	}

	const float CenterX = Canvas->ClipX * 0.5f;
	const float BaseY = Canvas->ClipY - BottomMarginPx;

	const UFont* Font = GEngine ? GEngine->GetLargeFont() : nullptr;
	if (!Font)
	{
		return;
	}

	float NextLineY = BaseY;
	if (Line.Speaker != EDialogueSpeaker::None)
	{
		const FText SpeakerLabel = GetSpeakerDisplayName(Line.Speaker);
		float SpeakerW = 0.f, SpeakerH = 0.f;
		Canvas->StrLen(Font, SpeakerLabel.ToString(), SpeakerW, SpeakerH);

		Canvas->SetDrawColor(SpeakerColor.ToFColor(true));
		Canvas->DrawText(Font, SpeakerLabel.ToString(), CenterX - (SpeakerW * 0.5f), NextLineY);
		NextLineY += SpeakerH + 4.0f;
	}

	const FString BodyStr = Line.Speaker == EDialogueSpeaker::None
		? FString::Printf(TEXT("%s"), *Line.Text.ToString())
		: FString::Printf(TEXT("\"%s\""), *Line.Text.ToString());

	float BodyW = 0.f, BodyH = 0.f;
	Canvas->StrLen(Font, BodyStr, BodyW, BodyH);

	Canvas->SetDrawColor(TextColor.ToFColor(true));
	Canvas->DrawText(Font, BodyStr, CenterX - (BodyW * 0.5f), NextLineY);
}
