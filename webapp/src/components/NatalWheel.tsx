import React, { useState } from 'react';

export interface PlanetData {
  name: string;
  name_ru: string;
  longitude: number;
  sign_ru: string;
  symbol: string;
  degree_in_sign: number;
  is_retrograde?: boolean;
}

export interface HouseData {
  house: number;
  degree: number;
  sign_ru: string;
  symbol: string;
}

export interface AspectData {
  planet1: string;
  planet2: string;
  aspect: string;
  symbol: string;
  orb: number;
  nature: 'harmonious' | 'tense' | 'neutral';
}

export interface NatalChartData {
  planets?: Record<string, PlanetData>;
  houses?: HouseData[];
  ascendant?: { degree: number; sign_ru: string; symbol: string };
  aspects?: AspectData[];
  sun_sign?: string;
  moon_sign?: string;
  ascendant_sign?: string;
}

interface NatalWheelProps {
  chartData?: NatalChartData | null;
  userName?: string;
}

const ZODIAC_SIGNS = [
  { name: 'Овен', symbol: '♈', element: 'fire', color: '#EF4444' },
  { name: 'Телец', symbol: '♉', element: 'earth', color: '#10B981' },
  { name: 'Близнецы', symbol: '♊', element: 'air', color: '#F59E0B' },
  { name: 'Рак', symbol: '♋', element: 'water', color: '#3B82F6' },
  { name: 'Лев', symbol: '♌', element: 'fire', color: '#EF4444' },
  { name: 'Дева', symbol: '♍', element: 'earth', color: '#10B981' },
  { name: 'Весы', symbol: '♎', element: 'air', color: '#F59E0B' },
  { name: 'Скорпион', symbol: '♏', element: 'water', color: '#3B82F6' },
  { name: 'Стрелец', symbol: '♐', element: 'fire', color: '#EF4444' },
  { name: 'Козерог', symbol: '♑', element: 'earth', color: '#10B981' },
  { name: 'Водолей', symbol: '♒', element: 'air', color: '#F59E0B' },
  { name: 'Рыбы', symbol: '♓', element: 'water', color: '#3B82F6' },
];

const PLANET_GLYPHS: Record<string, string> = {
  Sun: '☉',
  Moon: '☽',
  Mercury: '☿',
  Venus: '♀',
  Mars: '♂',
  Jupiter: '♃',
  Saturn: '♄',
  Uranus: '♅',
  Neptune: '♆',
  Pluto: '♇',
};

export const NatalWheel: React.FC<NatalWheelProps> = ({ chartData, userName }) => {
  const [selectedPlanet, setSelectedPlanet] = useState<PlanetData | null>(null);
  const [selectedSign, setSelectedSign] = useState<string | null>(null);

  const cx = 200;
  const cy = 200;
  const rOuter = 190;
  const rZodiac = 158;
  const rHouses = 120;
  const rAspects = 100;

  // Traditional Western Astrology: Ascendant sits at 9 o'clock (180 deg in standard SVG)
  // If ASC is present, rotate wheel so ASC degree maps to 180°
  const ascDegree = chartData?.ascendant?.degree ?? 0;
  const rotationOffset = 180 - ascDegree;

  // Degree to Cartesian coordinates on SVG
  const degToCoord = (deg: number, radius: number) => {
    const angleRad = ((deg + rotationOffset) * Math.PI) / 180;
    return {
      x: cx + radius * Math.cos(angleRad),
      y: cy + radius * Math.sin(angleRad),
    };
  };

  // Helper for drawing SVG arc
  const describeArc = (x: number, y: number, rOut: number, rIn: number, startAngle: number, endAngle: number) => {
    const startOuter = degToCoord(startAngle, rOut);
    const endOuter = degToCoord(endAngle, rOut);
    const startInner = degToCoord(endAngle, rIn);
    const endInner = degToCoord(startAngle, rIn);

    const largeArcFlag = endAngle - startAngle <= 180 ? '0' : '1';

    return [
      `M ${startOuter.x} ${startOuter.y}`,
      `A ${rOut} ${rOut} 0 ${largeArcFlag} 1 ${endOuter.x} ${endOuter.y}`,
      `L ${startInner.x} ${startInner.y}`,
      `A ${rIn} ${rIn} 0 ${largeArcFlag} 0 ${endInner.x} ${endInner.y}`,
      'Z',
    ].join(' ');
  };

  const planetsList: PlanetData[] = chartData?.planets
    ? Object.values(chartData.planets)
    : [
        { name: 'Sun', name_ru: 'Солнце', longitude: 235, sign_ru: 'Скорпион', symbol: '♏', degree_in_sign: 25 },
        { name: 'Moon', name_ru: 'Луна', longitude: 340, sign_ru: 'Рыбы', symbol: '♓', degree_in_sign: 10 },
        { name: 'Mercury', name_ru: 'Меркурий', longitude: 220, sign_ru: 'Скорпион', symbol: '♏', degree_in_sign: 10 },
        { name: 'Venus', name_ru: 'Венера', longitude: 250, sign_ru: 'Стрелец', symbol: '♐', degree_in_sign: 10 },
        { name: 'Mars', name_ru: 'Марс', longitude: 130, sign_ru: 'Лев', symbol: '♌', degree_in_sign: 10 },
        { name: 'Jupiter', name_ru: 'Юпитер', longitude: 40, sign_ru: 'Телец', symbol: '♉', degree_in_sign: 10 },
        { name: 'Saturn', name_ru: 'Сатурн', longitude: 335, sign_ru: 'Рыбы', symbol: '♓', degree_in_sign: 5 },
      ];

  const aspectsList = chartData?.aspects ?? [];

  return (
    <div className="flex flex-col items-center select-none w-full">
      {/* SVG Cosmogram Wheel */}
      <div className="relative w-full max-w-[340px] aspect-square drop-shadow-2xl">
        <svg
          viewBox="0 0 400 400"
          className="w-full h-full transform transition-all duration-700 ease-out"
        >
          <defs>
            {/* Radial glow background */}
            <radialGradient id="spaceGradient" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#0B0F19" />
              <stop offset="70%" stopColor="#111827" />
              <stop offset="100%" stopColor="#030712" />
            </radialGradient>

            <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* Background circle */}
          <circle cx={cx} cy={cy} r={rOuter} fill="url(#spaceGradient)" stroke="#374151" strokeWidth="1" />

          {/* 1. Zodiac Signs Ring (12 sectors) */}
          {ZODIAC_SIGNS.map((z, idx) => {
            const startDeg = idx * 30;
            const endDeg = (idx + 1) * 30;
            const midDeg = startDeg + 15;
            const midCoord = degToCoord(midDeg, (rOuter + rZodiac) / 2);
            const isSignSelected = selectedSign === z.name;

            return (
              <g key={z.name} className="cursor-pointer" onClick={() => setSelectedSign(z.name)}>
                <path
                  d={describeArc(cx, cy, rOuter, rZodiac, startDeg, endDeg)}
                  fill={isSignSelected ? z.color + '44' : idx % 2 === 0 ? '#1e1b4b22' : '#312e8111'}
                  stroke="#4b5563"
                  strokeWidth="0.7"
                  className="hover:fill-purple-600/30 transition-colors"
                />
                <text
                  x={midCoord.x}
                  y={midCoord.y}
                  textAnchor="middle"
                  dominantBaseline="central"
                  fill={z.color}
                  fontSize="13"
                  fontWeight="bold"
                  className="pointer-events-none drop-shadow"
                >
                  {z.symbol}
                </text>
              </g>
            );
          })}

          {/* 2. Middle Ring (Houses border) */}
          <circle cx={cx} cy={cy} r={rHouses} fill="none" stroke="#4B5563" strokeWidth="0.8" strokeDasharray="3,3" />

          {/* 3. House Cusps Radial Lines (12 houses) */}
          {(chartData?.houses ?? Array.from({ length: 12 }, (_, i) => ({ house: i + 1, degree: i * 30 }))).map((h) => {
            const inner = degToCoord(h.degree, rAspects);
            const outer = degToCoord(h.degree, rZodiac);
            const isAxis = h.house === 1 || h.house === 4 || h.house === 7 || h.house === 10;

            return (
              <line
                key={`house-line-${h.house}`}
                x1={inner.x}
                y1={inner.y}
                x2={outer.x}
                y2={outer.y}
                stroke={isAxis ? '#F59E0B' : '#6B7280'}
                strokeWidth={isAxis ? '1.8' : '0.6'}
                opacity={isAxis ? 0.9 : 0.4}
              />
            );
          })}

          {/* 4. Aspect Lines (Inside center disk) */}
          <circle cx={cx} cy={cy} r={rAspects} fill="#030712" stroke="#374151" strokeWidth="0.8" />

          {aspectsList.map((asp, idx) => {
            const p1 = planetsList.find((p) => p.name_ru === asp.planet1);
            const p2 = planetsList.find((p) => p.name_ru === asp.planet2);
            if (!p1 || !p2) return null;

            const c1 = degToCoord(p1.longitude, rAspects);
            const c2 = degToCoord(p2.longitude, rAspects);

            let strokeColor = '#9CA3AF';
            if (asp.nature === 'harmonious') strokeColor = '#10B981'; // Trine/Sextile - Green
            if (asp.nature === 'tense') strokeColor = '#EF4444'; // Square/Opposition - Red

            const isHighlighted =
              selectedPlanet &&
              (selectedPlanet.name_ru === asp.planet1 || selectedPlanet.name_ru === asp.planet2);

            return (
              <line
                key={`asp-${idx}`}
                x1={c1.x}
                y1={c1.y}
                x2={c2.x}
                y2={c2.y}
                stroke={strokeColor}
                strokeWidth={isHighlighted ? '2' : '0.7'}
                opacity={selectedPlanet ? (isHighlighted ? 1 : 0.15) : 0.4}
                className="transition-all duration-300"
              />
            );
          })}

          {/* 5. Planets plotted on the circle */}
          {planetsList.map((planet) => {
            const coord = degToCoord(planet.longitude, (rHouses + rAspects) / 2);
            const glyph = PLANET_GLYPHS[planet.name] || '✦';
            const isSelected = selectedPlanet?.name === planet.name;

            return (
              <g
                key={planet.name}
                className="cursor-pointer group"
                onClick={() => setSelectedPlanet(isSelected ? null : planet)}
              >
                {/* Highlight ring */}
                {isSelected && (
                  <circle
                    cx={coord.x}
                    cy={coord.y}
                    r="12"
                    fill="none"
                    stroke="#F59E0B"
                    strokeWidth="1.5"
                    className="animate-pulse"
                  />
                )}
                {/* Planet dot */}
                <circle
                  cx={coord.x}
                  cy={coord.y}
                  r="9"
                  fill={isSelected ? '#7C3AED' : '#1E1B4B'}
                  stroke={isSelected ? '#FCD34D' : '#A78BFA'}
                  strokeWidth="1"
                  className="transition-transform group-hover:scale-125"
                />
                {/* Glyph */}
                <text
                  x={coord.x}
                  y={coord.y + 0.5}
                  textAnchor="middle"
                  dominantBaseline="central"
                  fill={isSelected ? '#FFF' : '#DDD6FE'}
                  fontSize="10"
                  fontWeight="bold"
                >
                  {glyph}
                </text>
              </g>
            );
          })}

          {/* Center Point */}
          <circle cx={cx} cy={cy} r="3" fill="#F59E0B" />
          <text
            x={cx}
            y={cy + 16}
            textAnchor="middle"
            fill="#6B7280"
            fontSize="8"
            letterSpacing="1"
          >
            {userName ? userName.toUpperCase().slice(0, 10) : 'NATAL'}
          </text>
        </svg>
      </div>

      {/* Selected Planet / Sign Card */}
      <div className="w-full mt-3">
        {selectedPlanet ? (
          <div className="bg-gradient-to-r from-purple-950/80 to-slate-900 border border-purple-500/40 rounded-xl p-3 text-xs shadow-lg animate-fadeIn flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-purple-600/40 flex items-center justify-center text-amber-300 text-base font-bold border border-purple-400/30">
                {PLANET_GLYPHS[selectedPlanet.name] || '✦'}
              </div>
              <div>
                <div className="font-bold text-white text-sm">
                  {selectedPlanet.name_ru} {selectedPlanet.is_retrograde && <span className="text-amber-400">℞</span>}
                </div>
                <div className="text-slate-300">
                  {selectedPlanet.sign_ru} {selectedPlanet.degree_in_sign}°
                </div>
              </div>
            </div>
            <button
              onClick={() => setSelectedPlanet(null)}
              className="text-slate-400 hover:text-white px-2 py-1 text-xs"
            >
              ✕
            </button>
          </div>
        ) : selectedSign ? (
          <div className="bg-slate-900/80 border border-purple-800/40 rounded-xl p-3 text-xs flex items-center justify-between">
            <div>
              <span className="font-bold text-amber-300">Знак: {selectedSign}</span>
              <span className="text-slate-400 ml-2">Нажмите на планеты для деталей аспектов</span>
            </div>
            <button onClick={() => setSelectedSign(null)} className="text-slate-400 px-2">✕</button>
          </div>
        ) : (
          <div className="text-center text-[11px] text-slate-400 py-1 italic">
            Нажмите на любую планету или знак зодиака на колесе для подробностей
          </div>
        )}
      </div>
    </div>
  );
};
