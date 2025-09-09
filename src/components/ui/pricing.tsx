'use client';
import React from 'react';
import { Button } from '@/components/ui/button';
import {
	Tooltip,
	TooltipContent,
	TooltipProvider,
	TooltipTrigger,
} from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';
import { CheckCircleIcon, StarIcon } from 'lucide-react';
import Link from 'next/link';
import { motion, Transition } from 'framer-motion';

type FREQUENCY = 'monthly' | 'yearly';
const frequencies: FREQUENCY[] = ['monthly', 'yearly'];

interface Plan {
	name: string;
	info: string;
	price: {
		monthly: number;
		yearly: number;
	};
	features: {
		text: string;
		tooltip?: string;
	}[];
	btn: {
		text: string;
		href: string;
	};
	highlighted?: boolean;
}

interface PricingSectionProps extends React.ComponentProps<'div'> {
	plans: Plan[];
	heading: string;
	description?: string;
}

export function PricingSection({
	plans,
	heading,
	description,
	...props
}: PricingSectionProps) {
	const [frequency, setFrequency] = React.useState<'monthly' | 'yearly'>(
		'monthly',
	);

	return (
		<div
			className={cn(
				'flex w-full flex-col items-center justify-center space-y-16 py-16 px-6',
				props.className,
			)}
			{...props}
		>
			<div className="mx-auto max-w-2xl space-y-4 text-center">
				<h2 className="text-center text-3xl font-bold tracking-tight md:text-4xl lg:text-5xl text-white">
					{heading}
				</h2>
				{description && (
					<p className="text-white/90 text-center text-lg md:text-xl leading-relaxed mb-8">
						{description}
					</p>
				)}
			</div>
			<div className="mb-8">
				<PricingFrequencyToggle
					frequency={frequency}
					setFrequency={setFrequency}
				/>
			</div>
			<div className="mx-auto flex flex-wrap justify-center w-full max-w-7xl gap-12 md:gap-16">
				{plans.map((plan) => (
					<PricingCard plan={plan} key={plan.name} frequency={frequency} />
				))}
			</div>
		</div>
	);
}

type PricingFrequencyToggleProps = React.ComponentProps<'div'> & {
	frequency: FREQUENCY;
	setFrequency: React.Dispatch<React.SetStateAction<FREQUENCY>>;
};

export function PricingFrequencyToggle({
	frequency,
	setFrequency,
	...props
}: PricingFrequencyToggleProps) {
	return (
		<div
			className={cn(
				'bg-white/10 mx-auto flex w-fit rounded-full border border-white/20 p-1',
				props.className,
			)}
			{...props}
		>
			{frequencies.map((freq) => (
				<button
					key={freq}
					onClick={() => setFrequency(freq)}
					className="relative px-4 py-1 text-sm capitalize transition-colors"
				>
					<span className={cn(
						"relative z-10",
						frequency === freq ? "text-black font-medium" : "text-white/70 hover:text-white"
					)}>
						{freq}
					</span>
					{frequency === freq && (
						<motion.span
							layoutId="frequency"
							transition={{ type: 'spring', duration: 0.4 }}
							className="bg-white absolute inset-0 z-0 rounded-full"
						/>
					)}
				</button>
			))}
		</div>
	);
}

type PricingCardProps = React.ComponentProps<'div'> & {
	plan: Plan;
	frequency?: FREQUENCY;
};

export function PricingCard({
	plan,
	className,
	frequency = frequencies[0],
	...props
}: PricingCardProps) {
	return (
		<div
			key={plan.name}
			className={cn(
				'relative flex w-full max-w-sm flex-col rounded-lg border border-white/20 bg-white/5 backdrop-blur-sm min-h-[600px]',
				className,
			)}
			{...props}
		>
			{plan.highlighted && (
				<BorderTrail
					style={{
						boxShadow:
							'0px 0px 60px 30px rgb(255 255 255 / 50%), 0 0 100px 60px rgb(0 0 0 / 50%), 0 0 140px 90px rgb(0 0 0 / 50%)',
					}}
					size={100}
				/>
			)}
			<div
				className={cn(
					'bg-white/5 rounded-t-lg border-b border-white/20 p-6',
					plan.highlighted && 'bg-white/10',
				)}
			>
				<div className="absolute top-2 right-2 z-10 flex items-center gap-2">
					{plan.highlighted && (
						<p className="bg-white/20 text-white flex items-center gap-1 rounded-md border border-white/30 px-2 py-0.5 text-xs">
							<StarIcon className="h-3 w-3 fill-current" />
							Popular
						</p>
					)}
					{frequency === 'yearly' && plan.price.monthly > 0 && (
						<p className="bg-white text-black flex items-center gap-1 rounded-md border border-white px-2 py-0.5 text-xs font-medium">
							{Math.round(
								((plan.price.monthly * 12 - plan.price.yearly) /
									plan.price.monthly /
									12) *
									100,
							)}
							% off
						</p>
					)}
				</div>

				<div className="text-xl font-semibold text-white">{plan.name}</div>
				<p className="text-white/90 text-base font-normal mt-1">{plan.info}</p>
				<h3 className="mt-3 flex items-end gap-1">
					<span className="text-4xl font-bold text-white">${plan.price[frequency]}</span>
					<span className="text-white/80 text-lg">
						{plan.name !== 'Starter'
							? '/' + (frequency === 'monthly' ? 'month' : 'year')
							: ''}
					</span>
				</h3>
			</div>
			<div
				className={cn(
					'space-y-5 px-6 py-8 text-base',
					plan.highlighted && 'bg-white/5',
				)}
			>
				{plan.features.map((feature, index) => (
					<div key={index} className="flex items-start gap-3">
						<CheckCircleIcon className="text-green-400 h-5 w-5 mt-0.5 flex-shrink-0" />
						<TooltipProvider>
							<Tooltip delayDuration={0}>
								<TooltipTrigger asChild>
									<p
										className={cn(
											'text-white/95 leading-relaxed',
											feature.tooltip &&
												'cursor-pointer border-b border-dashed border-white/40',
										)}
									>
										{feature.text}
									</p>
								</TooltipTrigger>
								{feature.tooltip && (
									<TooltipContent className="bg-black/90 border border-white/20 text-white max-w-xs">
										<p>{feature.tooltip}</p>
									</TooltipContent>
								)}
							</Tooltip>
						</TooltipProvider>
					</div>
				))}
			</div>
			<div
				className={cn(
					'mt-auto w-full border-t border-white/20 p-6',
					plan.highlighted && 'bg-white/5',
				)}
			>
				<Button
					className={cn(
						"w-full h-12 text-base font-medium transition-all duration-300 hover:scale-105 hover:shadow-lg",
						plan.highlighted 
							? "bg-white text-black hover:bg-white/90 hover:text-black border-white" 
							: "bg-gray-600 text-white hover:bg-gray-500 hover:text-white border-gray-600"
					)}
					variant="outline"
					asChild
				>
					<Link href={plan.btn.href}>{plan.btn.text}</Link>
				</Button>
			</div>
		</div>
	);
}


type BorderTrailProps = {
  className?: string;
  size?: number;
  transition?: Transition;
  delay?: number;
  onAnimationComplete?: () => void;
  style?: React.CSSProperties;
};

export function BorderTrail({
  className,
  size = 60,
  transition,
  delay,
  onAnimationComplete,
  style,
}: BorderTrailProps) {
  const BASE_TRANSITION = {
    repeat: Infinity,
    duration: 5,
    ease: 'linear' as const,
  };

  return (
    <div className='pointer-events-none absolute inset-0 rounded-[inherit] border border-transparent [mask-clip:padding-box,border-box] [mask-composite:intersect] [mask-image:linear-gradient(transparent,transparent),linear-gradient(#000,#000)]'>
      <motion.div
        className={cn('absolute aspect-square bg-zinc-500', className)}
        style={{
          width: size,
          offsetPath: `rect(0 auto auto 0 round ${size}px)`,
          ...style,
        }}
        animate={{
          offsetDistance: ['0%', '100%'],
        }}
        transition={{
          ...(transition ?? BASE_TRANSITION),
          delay: delay,
        }}
        onAnimationComplete={onAnimationComplete}
      />
    </div>
  );
}
