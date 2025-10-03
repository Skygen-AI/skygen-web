"use client";

import { useScroll, useTransform, motion, MotionValue } from 'motion/react';
import React, { useRef, forwardRef, useState } from 'react';
import Link from "next/link";
import Silk from "../components/Silk";
import LogoLoop from "../components/LogoLoop";
import { LoginModal } from "../components/LoginModal";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { SiReact, SiNextdotjs, SiTypescript, SiTailwindcss, SiNodedotjs, SiPython, SiDocker, SiKubernetes } from 'react-icons/si';

import { ArrowRight, Sparkles, Star, Zap, Shield, Rocket, Menu, X, Wind, BookOpen } from "lucide-react";

interface SectionProps {
  scrollYProgress: MotionValue<number>;
}

const techLogos = [
  { node: <SiReact />, title: "React", href: "https://react.dev" },
  { node: <SiNextdotjs />, title: "Next.js", href: "https://nextjs.org" },
  { node: <SiTypescript />, title: "TypeScript", href: "https://www.typescriptlang.org" },
  { node: <SiTailwindcss />, title: "Tailwind CSS", href: "https://tailwindcss.com" },
  { node: <SiNodedotjs />, title: "Node.js", href: "https://nodejs.org" },
  { node: <SiPython />, title: "Python", href: "https://www.python.org" },
  { node: <SiDocker />, title: "Docker", href: "https://www.docker.com" },
  { node: <SiKubernetes />, title: "Kubernetes", href: "https://kubernetes.io" },
];

const Section1: React.FC<SectionProps> = ({ scrollYProgress }) => {
  // Fade to black much faster - from scroll 0 to 0.2 (representing 0 to 2 in your scale)
  const fadeToBlack = useTransform(scrollYProgress, [0, 0.1], [0, 1]);
  // Content fades out slightly slower for layered effect
  const contentOpacity = useTransform(scrollYProgress, [0, 0.12], [1, 0]);
  // Skygen text fades out even slower for more depth
  const skygenOpacity = useTransform(scrollYProgress, [0, 0.15], [1, 0]);
  
  return (
    <motion.section
      className='sticky font-semibold top-0 h-screen overflow-hidden'
    >
      {/* Black overlay that fades in on scroll */}
      <motion.div 
        style={{ opacity: fadeToBlack }}
        className="absolute inset-0 bg-black z-30"
      />
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



      {/* Content */}
      <motion.div 
        style={{ opacity: contentOpacity }}
        className="relative z-40 flex h-full flex-col"
      >
        {/* Spacer for glass nav */}
        <div className="h-20"></div>

        {/* Main Content */}
        <main className="flex-1 flex items-center justify-center px-6 lg:px-8">
          <div className="max-w-4xl text-center space-y-8">
            {/* Hero Section */}
            <div className="space-y-2">
              
              {/* Inline CSS test */}
              <motion.div 
                style={{
                  opacity: skygenOpacity,
                  fontWeight: 510,
                  fontSize: 'clamp(3rem, 6vw, 6rem)',
                  lineHeight: '1.1',
                  background: 'linear-gradient(-120deg, #ffffff 0%, #ffffff 30%,rgb(151, 151, 151) 50%, #ffffff 70%, #ffffff 100%)',
                  backgroundSize: '200% 100%',
                  WebkitBackgroundClip: 'text',
                  backgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  display: 'inline-block',
                  animation: 'shine 2s linear infinite',
                  paddingBottom: '0.1em'
                }}
                className="mt-5 text-7xl lg:text-8xl font-bold"
              >
                Skygen
              </motion.div>
              <h1 style={{ fontWeight: 250 }} className="text-3xl sm:text-5xl lg:text-6xl font-extrabold text-white leading-tight">
                New Era of AI Agents
              </h1>
            </div>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 relative z-40">
              <Link href="/get-started" className="group inline-flex items-center space-x-3 bg-white text-gray-900 px-8 py-4 rounded-full font-semibold text-lg shadow-lg hover:shadow-xl transition-all duration-200 hover:scale-105">
                <span>Get Started</span>
                <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />
              </Link>
              
              <a href="/learn-more" className="inline-flex items-center space-x-3 bg-white/10 backdrop-blur-sm border border-white/20 text-white px-8 py-4 rounded-full font-semibold text-lg hover:bg-white/20 transition-all duration-200">
                <span>Learn More</span>
                <BookOpen className="h-5 w-5" />
              </a>

            </div>
          </div>
        </main>

        {/* Footer */}
        <footer className="p-6 lg:p-8">
          <div className="flex flex-col sm:flex-row items-center justify-between">
          <h3 className="text-sm font-thin text-white/60 mb-2">© 2025 Speechka labs. All rights reserved.</h3>
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
      </motion.div>
    </motion.section>
  );
};


const Section2: React.FC<SectionProps> = ({ scrollYProgress }) => {
  // Fade in faster from scroll 0.1 to 0.2 (much quicker transition)
  const fadeIn = useTransform(scrollYProgress, [0.1, 0.2], [0, 1]);
  
  return (
    <motion.section
      style={{ opacity: fadeIn }}
      className='relative h-screen bg-gradient-to-t to-[#1a1919] from-[#06060e] text-white '
    >
      <div className='absolute bottom-0 left-0 right-0 top-0 bg-[linear-gradient(to_right,#4f4f4f2e_1px,transparent_1px),linear-gradient(to_bottom,#4f4f4f2e_1px,transparent_1px)] bg-[size:54px_54px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)]'></div>
      <article className='container mx-auto relative z-10 '>
                <h1 className='text-6xl leading-[100%] py-10 font-semibold  tracking-tight '>
          Images That doesn&apos;t Make any sense <br /> but still in this section
        </h1>
        <div className='grid grid-cols-4 gap-4'>
          <img
            src='https://images.unsplash.com/photo-1717893777838-4e222311630b?w=1200&auto=format&fit=crop'
            alt='img'
            className=' object-cover w-full rounded-md h-full'
          />
          <img
            src='https://images.unsplash.com/photo-1717618389115-88db6d7d8f77?w=500&auto=format&fit=crop'
            alt='img'
            className=' object-cover w-full rounded-md'
          />
          <img
            src='https://images.unsplash.com/photo-1717588604557-55b2888f59a6?w=500&auto=format&fit=crop'
            alt='img'
            className=' object-cover w-full rounded-md h-full'
          />
          <img
            src='https://images.unsplash.com/photo-1713417338603-1b6b72fcade2?w=500&auto=format&fit=crop'
            alt='img'
            className=' object-cover w-full rounded-md h-full'
          />
          
                </div>
                <h1 style={{ fontWeight: 250 }} className="text-3xl sm:text-5xl lg:text-6xl font-extrabold text-white leading-tight mb-20">
          Possibilities of Skygen
        </h1>
        
        
        {/* Половина страницы пустого места */}
        <div className="h-[50vh]"></div>
          
        
        
        <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold text-white text-center mb-8">
          Technologies We Support
        </h2>
        
        <div className="w-screen relative left-1/2 transform -translate-x-1/2 h-32">
          <LogoLoop
            logos={techLogos}
            speed={60}
            direction="left"
            logoHeight={64}
            gap={60}
            pauseOnHover={false}
            scaleOnHover={false}
            fadeOut={true}
            fadeOutColor="#000000"
            ariaLabel="Technology partners"
          />
    </div>
      </article>
    </motion.section>
  );
};

const Component = () => {
  const container = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: container,
    offset: ['start start', 'end end'],
  });

  return (
    <>
      {/* Navigation Bar - Always on top, independent of animations */}
      <HeroHeader />
      
      <main ref={container} className='relative h-[400vh] bg-black'>
                <Section1 scrollYProgress={scrollYProgress} />
        <Section2 scrollYProgress={scrollYProgress} />
      </main>
      
      {/* Большая пауза перед финальным текстом */}
      <div className="h-[100vh] bg-[#06060e]"></div>
      
      {/* Финальный Skygen текст */}
      <div className="bg-[#06060e] py-20">
        <h1 className='text-[16vw] leading-[120%] uppercase font-semibold text-center bg-gradient-to-r from-gray-400 to-gray-800 bg-clip-text text-transparent'>
          Skygen
        </h1>
      </div>
    </>
  );
};

const menuItems = [
    { name: 'About', href: '/features' },
    { name: 'Skygen Setup', href: '/skygen-setup' },
    { name: 'Pricing', href: '/pricing' },
    { name: 'Docs', href: '/docs' },
    { name: 'Contact', href: '/contact' },
];

const HeroHeader = () => {
    const [menuState, setMenuState] = React.useState(false);
    const [isScrolled, setIsScrolled] = React.useState(false);
    const [isLoginModalOpen, setIsLoginModalOpen] = React.useState(false);

    React.useEffect(() => {
        const handleScroll = () => {
            setIsScrolled(window.scrollY > 50);
        };
        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    return (
        <>
            <LoginModal 
                isOpen={isLoginModalOpen} 
                onClose={() => setIsLoginModalOpen(false)} 
            />
            <header>
                <nav
                    data-state={menuState && 'active'}
                    className="fixed z-50 w-full px-2 group">
                <div className={cn('mx-auto mt-2 px-6 transition-all duration-700 lg:px-12', isScrolled ? 'max-w-4xl bg-background/50 rounded-2xl border backdrop-blur-lg lg:px-5' : 'max-w-6xl')}>
                    <div className="relative flex flex-wrap items-center justify-between gap-6 py-3 lg:gap-0 lg:py-4">
                        <div className="flex w-full justify-between lg:w-auto">
                            <Link
                                href="/"
                                aria-label="home"
                                className="flex items-center space-x-2">
                                <SkygenLogo />
                            </Link>

                            <button
                                onClick={() => setMenuState(!menuState)}
                                aria-label={menuState == true ? 'Close Menu' : 'Open Menu'}
                                className="relative z-20 -m-2.5 -mr-4 block cursor-pointer p-2.5 lg:hidden">
                                <Menu className="in-data-[state=active]:rotate-180 group-data-[state=active]:scale-0 group-data-[state=active]:opacity-0 m-auto size-6 duration-200" />
                                <X className="group-data-[state=active]:rotate-0 group-data-[state=active]:scale-100 group-data-[state=active]:opacity-100 absolute inset-0 m-auto size-6 -rotate-180 scale-0 opacity-0 duration-200" />
                            </button>
                        </div>

                        <div className="absolute inset-0 m-auto hidden size-fit lg:block">
                            <ul className="flex gap-8 text-sm">
                                {menuItems.map((item, index) => (
                                    <li key={index}>
                                        <Link
                                            href={item.href}
                                            className="text-white hover:text-white/80 block duration-150">
                                            <span>{item.name}</span>
                                        </Link>
                                    </li>
                                ))}
                            </ul>
                        </div>

                        <div className="bg-background group-data-[state=active]:block lg:group-data-[state=active]:flex mb-6 hidden w-full flex-wrap items-center justify-end space-y-8 rounded-3xl border p-6 shadow-2xl shadow-zinc-300/20 md:flex-nowrap lg:m-0 lg:flex lg:w-fit lg:gap-6 lg:space-y-0 lg:border-transparent lg:bg-transparent lg:p-0 lg:shadow-none dark:shadow-none dark:lg:bg-transparent">
                            <div className="lg:hidden">
                                <ul className="space-y-6 text-base">
                                    {menuItems.map((item, index) => (
                                        <li key={index}>
                                            <Link
                                                href={item.href}
                                                className="text-white hover:text-white/80 block duration-150">
                                                <span>{item.name}</span>
                                            </Link>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                            <div className="flex w-full flex-col space-y-3 sm:flex-row sm:gap-3 sm:space-y-0 md:w-fit">
                                <Button
                                    asChild
                                    variant="outline"
                                    size="sm"
                                    className={cn(isScrolled && 'lg:hidden')}>
                                    <Link href="/register">
                                        <span>Sign Up</span>
                                    </Link>
                                </Button>
                                <Link href="/login">
                                    <Button
                                        size="sm"
                                        className={cn(isScrolled && 'lg:hidden')}>
                                        <span>Login</span>
                                    </Button>
                                </Link>
                                <Button
                                    asChild
                                    size="sm"
                                    className={cn(isScrolled ? 'lg:inline-flex' : 'hidden')}>
                                    <Link href="/get-started">
                                        <span>Get Started</span>
                                    </Link>
                                </Button>
                            </div>
                        </div>
                    </div>
                </div>
            </nav>
        </header>
        </>
    );
};

const SkygenLogo = ({ className }: { className?: string }) => {
    return (
        <div className={cn('flex items-center space-x-2', className)}>
            <span style={{ display: "inline-block", transform: "translateX(6px)" }}>
                <Wind className="h-6 w-6 text-white" style={{ transform: "scaleX(-1)" }} />
            </span>
            <span className="text-xl font-bold text-white">Skygen</span>
        </div>
    );
};

export default Component;


