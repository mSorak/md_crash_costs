interface KofiWidgetOverlay {
  draw: (username: string, options: Record<string, string>) => void;
}

interface Window {
  kofiWidgetOverlay?: KofiWidgetOverlay;
}
