"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { swiftBridge } from "@/lib/swift-bridge";

export default function TestOverlayPage() {
  const [overlayVisible, setOverlayVisible] = useState(false);
  const [loading, setLoading] = useState(false);
  const [outlineColor, setOutlineColor] = useState<string>("#FF4D4F");
  const [dimVisible, setDimVisible] = useState(false);
  const [outlineWidth, setOutlineWidth] = useState<number>(8);
  const [outlineBlur, setOutlineBlur] = useState<number>(28);
  const [environment, setEnvironment] = useState<'native' | 'web'>('web');

  useEffect(() => {
    setEnvironment(swiftBridge.getEnvironment());
    swiftBridge.log('Test overlay page loaded');
  }, []);

  const showOverlay = async () => {
    try {
      setLoading(true);
      swiftBridge.showOverlay();
      setOverlayVisible(true);
    } catch (error) {
      console.error("Error showing overlay:", error);
    } finally {
      setLoading(false);
    }
  };

  const hideOverlay = async () => {
    try {
      swiftBridge.hideOverlay();
      setOverlayVisible(false);
    } catch (error) {
      console.error("Error hiding overlay:", error);
    }
  };

  const startOutline = async () => {
    try {
      swiftBridge.startOutline(outlineColor, outlineWidth, outlineBlur);
    } catch (error) {
      console.error("Error starting outline:", error);
    }
  };

  const stopOutline = async () => {
    try {
      swiftBridge.stopOutline();
    } catch (error) {
      console.error("Error stopping outline:", error);
    }
  };

  const updateOutline = (color?: string, width?: number, blur?: number) => {
    try {
      swiftBridge.updateOutline(
        color ?? outlineColor,
        width ?? outlineWidth, 
        blur ?? outlineBlur
      );
    } catch (error) {
      console.error("Error updating outline:", error);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-8">
      <div className="max-w-2xl mx-auto">
        <div className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl p-8 mb-8">
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-white mb-2">Overlay System Test</h1>
            <p className="text-gray-300">
              Control panel for testing overlay functions
            </p>
            <div className="mt-2">
              <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${
                environment === 'native' 
                  ? 'bg-green-500/20 text-green-400 border border-green-500/30' 
                  : 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
              }`}>
                {environment === 'native' ? '🚀 Native Swift App' : '🌐 Web Browser'}
              </span>
            </div>
          </div>
          
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Button
                onClick={showOverlay}
                disabled={loading || overlayVisible}
                className="h-16 text-lg bg-blue-600 hover:bg-blue-700 text-white border-0"
              >
                {loading ? "Loading..." : "Show Overlay"}
              </Button>
              
              <Button
                onClick={hideOverlay}
                disabled={!overlayVisible}
                className="h-16 text-lg bg-gray-600 hover:bg-gray-700 text-white border-0"
              >
                Hide Overlay
              </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Button
                onClick={() => swiftBridge.sendMessage('showDim')}
                className="h-12 text-base bg-indigo-600 hover:bg-indigo-700 text-white border-0"
              >
                Enable Dimming
              </Button>
              <Button
                onClick={() => swiftBridge.sendMessage('hideDim')}
                className="h-12 text-base bg-slate-600 hover:bg-slate-700 text-white border-0"
              >
                Disable Dimming
              </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-center gap-3 bg-black/20 border border-white/10 rounded-xl p-4">
                <label className="text-white text-sm">Outline Color:</label>
                <input
                  type="color"
                  value={outlineColor}
                  onChange={(e) => {
                    const v = e.target.value;
                    setOutlineColor(v);
                    updateOutline(v);
                  }}
                  className="h-10 w-14 bg-transparent cursor-pointer"
                  aria-label="Select outline color"
                />
                <div className="text-xs text-gray-300">{outlineColor}</div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <Button onClick={startOutline} className="h-12 text-base bg-emerald-600 hover:bg-emerald-700 text-white border-0">Enable Outline</Button>
                <Button onClick={stopOutline} className="h-12 text-base bg-rose-600 hover:bg-rose-700 text-white border-0">Disable Outline</Button>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-black/20 border border-white/10 rounded-xl p-4">
                <label className="text-white text-sm block mb-2">Outline Width: {outlineWidth}px</label>
                <input
                  type="range"
                  min={2}
                  max={40}
                  value={outlineWidth}
                  onChange={(e) => {
                    const v = parseInt(e.target.value);
                    setOutlineWidth(v);
                    updateOutline(undefined, v);
                  }}
                  className="w-full"
                />
              </div>
              <div className="bg-black/20 border border-white/10 rounded-xl p-4">
                <label className="text-white text-sm block mb-2">Blur Strength: {outlineBlur}px</label>
                <input
                  type="range"
                  min={0}
                  max={80}
                  value={outlineBlur}
                  onChange={(e) => {
                    const v = parseInt(e.target.value);
                    setOutlineBlur(v);
                    updateOutline(undefined, undefined, v);
                  }}
                  className="w-full"
                />
              </div>
            </div>


            <div className="p-4 bg-black/20 rounded-lg border border-white/10">
              <h3 className="font-semibold mb-2 text-white">Overlay Status:</h3>
              <p className={`text-sm ${overlayVisible ? "text-green-400" : "text-gray-400"}`}>
                {overlayVisible ? "Overlay Active" : "Overlay Hidden"}
              </p>
            </div>

            <div className="space-y-2 text-sm text-gray-300">
              <h4 className="font-semibold text-white">Instructions:</h4>
              <ul className="list-disc list-inside space-y-1">
                <li>Click &quot;Show Overlay&quot; to display the overlay on top of all windows</li>
                <li>Outline is drawn natively in Swift with breathing animation</li>
                <li>Use sliders to adjust thickness and blur in real time</li>
                <li>Global hotkey: Option+Space to toggle overlay</li>
                <li>Automatic dimming and closing when clicking outside overlay</li>
                {environment === 'web' && (
                  <li className="text-amber-400">⚠️ Full functionality is only available in the native application</li>
                )}
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
