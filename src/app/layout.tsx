import type { Metadata } from "next";
import "./globals.css";
import { ThemeProvider } from "@/contexts/ThemeContext";
import FullscreenHandler from "@/components/FullscreenHandler";

export const metadata: Metadata = {
  title: "Skygen UI Mock",
  description: "Replica of chat/task UI",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link 
          href="https://fonts.googleapis.com/css2?family=Figtree:wght@300;400;500;600;700;800;900&display=swap" 
          rel="stylesheet" 
        />
      </head>
      <body className="antialiased font-figtree">
        <FullscreenHandler />
        <ThemeProvider>
          {children}
        </ThemeProvider>
        <script dangerouslySetInnerHTML={{
          __html: `
            // Detect fullscreen mode changes
            function handleFullscreenChange() {
              if (document.fullscreenElement || document.webkitFullscreenElement) {
                document.body.classList.add('fullscreen');
                document.documentElement.style.height = '100vh';
                document.documentElement.style.width = '100vw';
              } else {
                document.body.classList.remove('fullscreen');
                document.documentElement.style.height = '';
                document.documentElement.style.width = '';
              }
            }
            
            // Listen for fullscreen changes
            document.addEventListener('fullscreenchange', handleFullscreenChange);
            document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
            
            // Check initial state
            handleFullscreenChange();
          `
        }} />
      </body>
    </html>
  );
}
