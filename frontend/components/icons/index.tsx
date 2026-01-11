import type { ComponentProps } from "react";

type IconProps = ComponentProps<"svg"> & {
  size?: number;
  strokeWidth?: number;
};

const baseProps = {
  fill: "none",
  stroke: "currentColor",
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
};

export function Play({ size = 20, strokeWidth = 2, ...props }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} {...baseProps} strokeWidth={strokeWidth} {...props}>
      <polygon points="6 4 20 12 6 20 6 4" />
    </svg>
  );
}

export function TrendingUp({ size = 20, strokeWidth = 2, ...props }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} {...baseProps} strokeWidth={strokeWidth} {...props}>
      <polyline points="3 17 9 11 13 15 21 7" />
      <polyline points="14 7 21 7 21 14" />
    </svg>
  );
}

export function TrendingDown({ size = 20, strokeWidth = 2, ...props }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} {...baseProps} strokeWidth={strokeWidth} {...props}>
      <polyline points="3 7 9 13 13 9 21 17" />
      <polyline points="21 10 21 17 14 17" />
    </svg>
  );
}

export function Clock({ size = 20, strokeWidth = 2, ...props }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} {...baseProps} strokeWidth={strokeWidth} {...props}>
      <circle cx="12" cy="12" r="9" />
      <polyline points="12 7 12 12 16 14" />
    </svg>
  );
}

export function Target({ size = 20, strokeWidth = 2, ...props }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} {...baseProps} strokeWidth={strokeWidth} {...props}>
      <circle cx="12" cy="12" r="9" />
      <circle cx="12" cy="12" r="5" />
      <circle cx="12" cy="12" r="1" fill="currentColor" />
    </svg>
  );
}

export function Mic({ size = 20, strokeWidth = 2, ...props }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} {...baseProps} strokeWidth={strokeWidth} {...props}>
      <rect x="9" y="3" width="6" height="11" rx="3" />
      <path d="M5 11a7 7 0 0 0 14 0" />
      <line x1="12" y1="18" x2="12" y2="21" />
      <line x1="8" y1="21" x2="16" y2="21" />
    </svg>
  );
}

export function MicOff({ size = 20, strokeWidth = 2, ...props }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} {...baseProps} strokeWidth={strokeWidth} {...props}>
      <line x1="4" y1="4" x2="20" y2="20" />
      <path d="M9 9v2a3 3 0 0 0 5.12 2.12" />
      <path d="M14.5 5.5A3 3 0 0 0 9 7v1" />
      <path d="M5 11a7 7 0 0 0 12 4" />
      <line x1="12" y1="18" x2="12" y2="21" />
      <line x1="8" y1="21" x2="16" y2="21" />
    </svg>
  );
}

export function Video({ size = 20, strokeWidth = 2, ...props }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} {...baseProps} strokeWidth={strokeWidth} {...props}>
      <rect x="3" y="6" width="14" height="12" rx="2" />
      <polygon points="17 8 21 6 21 18 17 16" />
    </svg>
  );
}

export function VideoOff({ size = 20, strokeWidth = 2, ...props }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} {...baseProps} strokeWidth={strokeWidth} {...props}>
      <line x1="4" y1="4" x2="20" y2="20" />
      <path d="M3 7a2 2 0 0 1 2-2h6" />
      <path d="M9 9H5v8h10v-4" />
      <path d="M17 8l4-2v12l-4-2" />
    </svg>
  );
}

export function PhoneOff({ size = 20, strokeWidth = 2, ...props }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} {...baseProps} strokeWidth={strokeWidth} {...props}>
      <path d="M10 6c.6 1.8 2.2 3.4 4 4" />
      <path d="M3 7c2.5 6.5 7.5 11.5 14 14" />
      <line x1="4" y1="4" x2="20" y2="20" />
    </svg>
  );
}

export function StickyNote({ size = 20, strokeWidth = 2, ...props }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} {...baseProps} strokeWidth={strokeWidth} {...props}>
      <rect x="4" y="4" width="16" height="16" rx="2" />
      <polyline points="16 16 20 16 20 12" />
    </svg>
  );
}

export function Lightbulb({ size = 20, strokeWidth = 2, ...props }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} {...baseProps} strokeWidth={strokeWidth} {...props}>
      <path d="M9 18h6" />
      <path d="M10 22h4" />
      <path d="M8 14a4 4 0 1 1 8 0c0 2-2 3-2 4h-4c0-1-2-2-2-4" />
    </svg>
  );
}

export function AlertCircle({ size = 20, strokeWidth = 2, ...props }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} {...baseProps} strokeWidth={strokeWidth} {...props}>
      <circle cx="12" cy="12" r="9" />
      <line x1="12" y1="8" x2="12" y2="12" />
      <circle cx="12" cy="16" r="1" fill="currentColor" stroke="none" />
    </svg>
  );
}

export function CheckCircle2({ size = 20, strokeWidth = 2, ...props }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} {...baseProps} strokeWidth={strokeWidth} {...props}>
      <circle cx="12" cy="12" r="9" />
      <polyline points="8 12 11 15 16 9" />
    </svg>
  );
}

export function Maximize2({ size = 20, strokeWidth = 2, ...props }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} {...baseProps} strokeWidth={strokeWidth} {...props}>
      <polyline points="15 3 21 3 21 9" />
      <polyline points="9 21 3 21 3 15" />
      <line x1="21" y1="3" x2="14" y2="10" />
      <line x1="3" y1="21" x2="10" y2="14" />
    </svg>
  );
}

export function Minimize2({ size = 20, strokeWidth = 2, ...props }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} {...baseProps} strokeWidth={strokeWidth} {...props}>
      <polyline points="4 14 10 14 10 20" />
      <polyline points="20 10 14 10 14 4" />
    </svg>
  );
}

export function Search({ size = 20, strokeWidth = 2, ...props }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} {...baseProps} strokeWidth={strokeWidth} {...props}>
      <circle cx="11" cy="11" r="7" />
      <line x1="20" y1="20" x2="16.5" y2="16.5" />
    </svg>
  );
}

export function Eye({ size = 20, strokeWidth = 2, ...props }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} {...baseProps} strokeWidth={strokeWidth} {...props}>
      <path d="M2 12s4-6 10-6 10 6 10 6-4 6-10 6-10-6-10-6" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );
}

export function Users({ size = 20, strokeWidth = 2, ...props }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} {...baseProps} strokeWidth={strokeWidth} {...props}>
      <circle cx="8" cy="9" r="3" />
      <circle cx="16" cy="9" r="3" />
      <path d="M2 19c0-2.8 3-5 6-5" />
      <path d="M22 19c0-2.8-3-5-6-5" />
    </svg>
  );
}

export function MessageSquare({ size = 20, strokeWidth = 2, ...props }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} {...baseProps} strokeWidth={strokeWidth} {...props}>
      <rect x="3" y="4" width="18" height="14" rx="2" />
      <polyline points="7 20 7 18 17 18 17 20" />
    </svg>
  );
}

export function ArrowLeft({ size = 20, strokeWidth = 2, ...props }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} {...baseProps} strokeWidth={strokeWidth} {...props}>
      <line x1="19" y1="12" x2="5" y2="12" />
      <polyline points="12 19 5 12 12 5" />
    </svg>
  );
}

export function LayoutDashboard({ size = 20, strokeWidth = 2, ...props }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} {...baseProps} strokeWidth={strokeWidth} {...props}>
      <rect x="3" y="3" width="7" height="9" rx="1" />
      <rect x="14" y="3" width="7" height="5" rx="1" />
      <rect x="14" y="10" width="7" height="11" rx="1" />
      <rect x="3" y="14" width="7" height="7" rx="1" />
    </svg>
  );
}

export function LibraryIcon({ size = 20, strokeWidth = 2, ...props }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} {...baseProps} strokeWidth={strokeWidth} {...props}>
      <rect x="3" y="4" width="6" height="16" rx="1" />
      <rect x="9" y="4" width="6" height="16" rx="1" />
      <rect x="15" y="4" width="6" height="16" rx="1" />
    </svg>
  );
}

export function LogOut({ size = 20, strokeWidth = 2, ...props }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} {...baseProps} strokeWidth={strokeWidth} {...props}>
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
      <polyline points="16 17 21 12 16 7" />
      <line x1="21" y1="12" x2="9" y2="12" />
    </svg>
  );
}
