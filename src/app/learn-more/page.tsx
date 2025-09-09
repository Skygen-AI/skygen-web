"use client";

import Silk from "../../components/Silk";
import GlassSurface from "../../components/GlassSurface";
import { Menu, Bot } from "lucide-react";

export default function LearnMorePage() {
  return (
    <div className="relative h-dvh w-dvw overflow-hidden">
      {/* Silk Background */}
      <div className="absolute inset-0">
        <Silk
          speed={3}
          scale={1.2}
          color="#333333"
          noiseIntensity={0.8}
          rotation={0.1}
        />
      </div>

      {/* Gradient Overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-purple-900/20 via-transparent to-blue-900/20" />

      {/* Glass Navigation Bar */}
      <div className="absolute top-4 left-4 right-4 z-20 flex items-center gap-4">
        <GlassSurface
          width="100%"
          height={70}
          borderRadius={32}
          brightness={10}
          opacity={0.15}
          backgroundOpacity={0.1}
          saturation={1.2}
          className="flex-1"
        >
          <div className="flex items-center justify-between w-full px-6">
            {/* Logo */}
            <div className="flex items-center space-x-3">

              <span className="text-xl font-bold text-white">Skygen</span>
            </div>

            {/* Placeholder right content (optional) */}
            <div className="hidden md:flex items-center" />

            {/* Mobile Menu Button */}
            <button className="md:hidden p-2 rounded-lg bg-white/20 backdrop-blur-sm border border-white/30 text-white">
              <Menu className="h-5 w-5" />
            </button>
          </div>
        </GlassSurface>

        {/* Login Button - После справа от GlassSurface */}
        <button className="bg-white/20 hover:bg-white/30 backdrop-blur-sm border border-white/30 text-white px-4 py-2 rounded-full text-sm font-medium transition-all duration-200 whitespace-nowrap">
          Login
        </button>
      </div>

      {/* Content */}
      <div className="relative z-10 flex h-full flex-col">
        {/* Spacer for glass nav */}
        <div className="h-20"></div>

        {/* Main Content */}
        <main className="flex-1 px-6 lg:px-8">
          <div className="mx-auto max-w-3xl text-left">
            <h1 className="text-white text-4xl sm:text-6xl font-extrabold leading-tight tracking-tight mb-8">
              Learn more
            </h1>
            <div className="space-y-6 text-lg leading-8 text-white/80">
              <p>
                Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Eu facilisis sed odio morbi quis commodo odio aenean. Egestas erat imperdiet sed euismod nisi porta lorem mollis aliquam. Elementum tempus egestas sed sed risus pretium quam vulputate dignissim.
              </p>
              <p>
                Vitae suscipit tellus mauris a diam maecenas sed enim ut. Nisl suscipit adipiscing bibendum est ultricies integer quis. Nunc faucibus a pellentesque sit amet porttitor eget dolor morbi. Amet risus nullam eget felis eget nunc lobortis mattis aliquam. Accumsan tortor posuere ac ut consequat semper viverra nam libero.
              </p>
              <p>
                Eget velit aliquet sagittis id consectetur purus ut faucibus. Amet mauris commodo quis imperdiet massa tincidunt nunc pulvinar sapien. In egestas erat imperdiet sed euismod nisi porta. Enim facilisis gravida neque convallis a cras semper. Quam adipiscing vitae proin sagittis nisl rhoncus mattis.
              </p>
              <p>
                Magna etiam tempor orci eu lobortis elementum nibh tellus molestie. Aenean vel elit scelerisque mauris pellentesque pulvinar pellentesque habitant morbi. Quis hendrerit dolor magna eget est lorem ipsum dolor. Diam donec adipiscing tristique risus nec feugiat in fermentum posuere.
              </p>
              <p>
                Commodo nulla facilisi nullam vehicula ipsum a arcu cursus. Amet mauris commodo quis imperdiet massa tincidunt nunc. Nibh ipsum consequat nisl vel pretium lectus quam id leo in. Magna ac placerat vestibulum lectus mauris ultrices eros in cursus. Sit amet facilisis magna etiam tempor orci eu lobortis.
              </p>
            </div>
          </div>
        </main>

        {/* Footer */}
        <footer className="p-6 lg:p-8">
          <div className="flex flex-col sm:flex-row items-center justify-between">
            <p className="text-white/60 text-sm"></p>
            <div className="flex items-center space-x-6 mt-4 sm:mt-0">
              <a href="#" className="text-white/60 hover:text-white transition-colors text-sm">
                Privacy Policy
              </a>
              <a href="#" className="text-white/60 hover:text-white transition-colors text-sm">
                Terms of Service
              </a>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}


