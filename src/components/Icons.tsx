export const XIcon = ({ size = 18 }: { size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true">
    <path
      fill="currentColor"
      d="M17.75 3h3.07l-6.7 7.66L22 21h-6.17l-4.83-6.32L5.47 21H2.4l7.17-8.2L2 3h6.33l4.37 5.77L17.75 3Zm-1.08 16.2h1.7L7.4 4.74H5.58l11.09 14.46Z"
    />
  </svg>
);

export const CopyIcon = () => (
  <svg width="15" height="15" viewBox="0 0 16 16" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.4">
    <rect x="5" y="5" width="8.5" height="8.5" rx="1.5" />
    <path d="M3 10.5V3.8C3 3.36 3.36 3 3.8 3h6.7" />
  </svg>
);

/** Arrows drawn as SVG, so no platform can swap them for emoji. */
export const ArrowUpRight = () => (
  <svg className="arrow" width="0.8em" height="0.8em" viewBox="0 0 12 12" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M3 9L9 3M4 3h5v5" />
  </svg>
);

export const ArrowRight = () => (
  <svg className="arrow" width="0.85em" height="0.85em" viewBox="0 0 12 12" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
    <path d="M1.5 6h9M7 2.5L10.5 6 7 9.5" />
  </svg>
);
