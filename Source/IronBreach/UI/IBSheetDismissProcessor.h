#pragma once

#include "CoreMinimal.h"
#include "Framework/Application/IInputProcessor.h"
#include "Framework/Application/SlateApplication.h"
#include "InputCoreTypes.h"

/**
 * Slate input preprocessor for modal front-end sheets (operative select /
 * intake). Preprocessors see every key BEFORE focus routing, so the dismiss
 * key (Escape / gamepad B) can't be eaten by whatever widget happens to hold
 * keyboard focus — a text field, a button, or the viewport void.
 *
 * Owner registers at index 0 while the sheet is up and unregisters on
 * destruct. The callback returns true when it consumed the key.
 */
class FIBSheetDismissProcessor : public IInputProcessor
{
public:
	explicit FIBSheetDismissProcessor(TFunction<bool()> InOnDismiss)
		: OnDismiss(MoveTemp(InOnDismiss))
	{
	}

	virtual void Tick(const float DeltaTime, FSlateApplication& SlateApp, TSharedRef<ICursor> Cursor) override {}

	virtual bool HandleKeyDownEvent(FSlateApplication& SlateApp, const FKeyEvent& InKeyEvent) override
	{
		if (InKeyEvent.IsRepeat()) { return false; }
		const FKey Key = InKeyEvent.GetKey();
		if (Key == EKeys::Escape || Key == EKeys::Gamepad_FaceButton_Right)
		{
			return OnDismiss ? OnDismiss() : false;
		}
		return false;
	}

	static TSharedPtr<FIBSheetDismissProcessor> Register(TFunction<bool()> InOnDismiss)
	{
		if (!FSlateApplication::IsInitialized()) { return nullptr; }
		TSharedPtr<FIBSheetDismissProcessor> Processor = MakeShared<FIBSheetDismissProcessor>(MoveTemp(InOnDismiss));
		FSlateApplication::Get().RegisterInputPreProcessor(Processor, 0); // ahead of CommonUI / analog cursor
		return Processor;
	}

	static void Unregister(TSharedPtr<FIBSheetDismissProcessor>& Processor)
	{
		if (Processor.IsValid() && FSlateApplication::IsInitialized())
		{
			FSlateApplication::Get().UnregisterInputPreProcessor(Processor);
		}
		Processor.Reset();
	}

private:
	TFunction<bool()> OnDismiss;
};
