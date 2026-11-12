import { MAP_CITIES, MAP_HEIGHT, MAP_WIDTH, POLAND_PATH, UKRAINE_PATH } from "./mapPaths";

/** Poland and Ukraine, the two markets Fence has salary data for. `focus` dims the other country. */
export default function CoverageMap({ labels = false, focus }: { labels?: boolean; focus?: "Poland" | "Ukraine" }) {
  return (
    <svg className="coverage-map" viewBox={`0 0 ${MAP_WIDTH} ${MAP_HEIGHT}`} role="img" aria-label="Map of Poland and Ukraine with major university cities">
      <path className={`coverage-map__poland ${focus === "Ukraine" ? "is-dim" : ""}`} d={POLAND_PATH} />
      <path className={`coverage-map__ukraine ${focus === "Poland" ? "is-dim" : ""}`} d={UKRAINE_PATH} />
      {MAP_CITIES.map((city) => (
        <g key={city.name} className="coverage-map__city">
          <circle cx={city.x} cy={city.y} r={city.major ? 9 : 6} />
          {labels && <text x={city.x + (city.anchor === "start" ? 14 : -14)} y={city.y + 6} textAnchor={city.anchor}>{city.name}</text>}
        </g>
      ))}
    </svg>
  );
}
