import { useEffect } from "react";

const KOFI_SCRIPT = "https://storage.ko-fi.com/cdn/scripts/overlay-widget.js";

const KOFI_OPTIONS = {
  type: "floating-chat",
  "floating-chat.donateButton.text": "Support me",
  "floating-chat.donateButton.background-color": "#fcbf47",
  "floating-chat.donateButton.text-color": "#323842",
};

function drawKofi(): void {
  window.kofiWidgetOverlay?.draw("mattperfectnumbers", KOFI_OPTIONS);
}

/** Loads Ko-fi floating support widget site-wide. */
export function KoFiWidget() {
  useEffect(() => {
    const existing = document.querySelector(`script[src="${KOFI_SCRIPT}"]`);
    if (existing) {
      drawKofi();
      return;
    }

    const script = document.createElement("script");
    script.src = KOFI_SCRIPT;
    script.async = true;
    script.onload = () => drawKofi();
    document.body.appendChild(script);
  }, []);

  return null;
}
