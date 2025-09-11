"use client";

import { useEffect } from "react";
import { tauriBridge } from "@/lib/tauri-bridge";

declare global {
  interface Window {
    webkit?: {
      messageHandlers?: {
        overlay?: {
          postMessage: (message: any) => void;
        };
      };
    };
  }
}

export default function OverlayPage() {
  // Close on Escape
  useEffect(() => {
    const handleEscape = async (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        console.log("🔑 ESC pressed, hiding overlay");
        // Try Swift bridge first
        if (window.webkit?.messageHandlers?.overlay) {
          window.webkit.messageHandlers.overlay.postMessage({ action: 'hideOverlay' });
        } else {
          // Fallback to Tauri
          try {
            await tauriBridge.invoke("hide_overlay");
          } catch (error) {
            // Tauri not available, ignore
            console.warn('Tauri not available for overlay hide');
          }
        }
      }
    };

    // Focus window to ensure it can receive keyboard events
    window.focus();
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, []);

  return (
    <div className="w-full h-full flex items-center justify-center bg-transparent">
      <div
        className="relative w-[680px] max-w-[90vw] rounded-2xl backdrop-blur-2xl bg-white/60 dark:bg-white/10 shadow-2xl ring-1 ring-black/10 dark:ring-white/10 animate-fadeIn"
        style={{
          WebkitBackdropFilter: "saturate(180%) blur(20px)",
        }}
      >
        <div className="px-5 py-4">
          <div className="flex items-center gap-3">
            <div className="shrink-0 h-7 w-7 rounded-full bg-black/10 dark:bg-white/15 flex items-center justify-center ring-1 ring-black/10 dark:ring-white/10">
              <svg width="14" height="14" viewBox="0 0 24 24" className="text-black/70 dark:text-white/80">
                <path
                  fill="currentColor"
                  d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5A6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5M9.5 14C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5S14 7.01 14 9.5S11.99 14 9.5 14"
                />
              </svg>
            </div>
            <input
              autoFocus
              className="flex-1 bg-transparent placeholder-black/50 dark:placeholder-white/40 text-black dark:text-white text-[17px] leading-7 outline-none"
              placeholder="Enter command or query"
              aria-label="Search"
            />
            <kbd className="hidden sm:flex items-center gap-1 rounded-md px-2 py-1 text-[11px] font-medium text-black/60 dark:text-white/60 ring-1 ring-black/10 dark:ring-white/10 bg-black/5 dark:bg-white/5">
              Esc
            </kbd>
          </div>
        </div>
        <div className="px-5 pb-4">
          <div className="grid grid-cols-3 gap-2 text-[13px]">
            <div className="rounded-lg bg-black/5 dark:bg-white/5 ring-1 ring-black/10 dark:ring-white/10 px-3 py-2 text-black/70 dark:text-white/70">Open settings</div>
            <div className="rounded-lg bg-black/5 dark:bg-white/5 ring-1 ring-black/10 dark:ring-white/10 px-3 py-2 text-black/70 dark:text-white/70">Find files</div>
            <div className="rounded-lg bg-black/5 dark:bg-white/5 ring-1 ring-black/10 dark:ring-white/10 px-3 py-2 text-black/70 dark:text-white/70">Create task</div>
          </div>
        </div>
      </div>
      <style jsx global>{`
        html, body, #__next { background: transparent !important; }
      `}</style>
    </div>
  );
}
