"use client";

export default function OverlayBackground() {
  return (
    <>
      <div className="w-screen h-screen bg-black/40 dark:bg-black/55" />
      <style jsx global>{`
        html, body, #__next { background: transparent !important; }
      `}</style>
    </>
  );
}


