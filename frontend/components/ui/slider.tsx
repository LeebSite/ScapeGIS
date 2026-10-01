"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

export interface SliderProps {
  value?: number[];
  min?: number;
  max?: number;
  step?: number;
  onValueChange?: (value: number[]) => void;
  onValueCommit?: (value: number[]) => void;
  className?: string;
  disabled?: boolean;
}

export const Slider = React.forwardRef<HTMLInputElement, SliderProps>(
  ({ value = [0], min = 0, max = 100, step = 1, onValueChange, onValueCommit, className, disabled }, ref) => {
    const currentValue = value[0] ?? min;

    return (
      <div className={cn("relative flex w-full touch-none select-none items-center", className)}>
        <input
          ref={ref}
          type="range"
          min={min}
          max={max}
          step={step}
          value={currentValue}
          disabled={disabled}
          onChange={(e) => {
            const val = [parseFloat(e.target.value)];
            onValueChange?.(val);
          }}
          onMouseUp={(e) => {
            const target = e.target as HTMLInputElement;
            onValueCommit?.([parseFloat(target.value)]);
          }}
          onTouchEnd={(e) => {
            const target = e.target as HTMLInputElement;
            onValueCommit?.([parseFloat(target.value)]);
          }}
          className="w-full h-1.5 bg-secondary rounded-lg appearance-none cursor-pointer accent-primary disabled:opacity-50 disabled:cursor-not-allowed"
        />
      </div>
    );
  }
);
Slider.displayName = "Slider";
export default Slider;