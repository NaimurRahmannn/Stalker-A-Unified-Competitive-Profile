export function Sparkline({
  points,
  stroke,
}: {
  points: number[];
  stroke: string;
}) {
  const width = 180;
  const height = 52;
  const min = Math.min(...points);
  const max = Math.max(...points);
  const range = max - min || 1;
  const polylinePoints = points
    .map((point, index) => {
      const x = (index / (points.length - 1)) * width;
      const y = height - ((point - min) / range) * (height - 8) - 4;

      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  return (
    <div className="mt-5 h-13 w-full overflow-hidden" aria-hidden="true">
      <svg viewBox={`0 0 ${width} ${height}`} className="h-full w-full">
        <polyline
          points={polylinePoints}
          fill="none"
          stroke={stroke}
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="2.4"
        />
      </svg>
    </div>
  );
}
