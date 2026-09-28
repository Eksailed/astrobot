import React, { useState, useEffect } from 'react';
import { Sparkles, Moon, Sun, Compass, Disc3, ShieldAlert, Zap, Layers, CircleDot } from 'lucide-react';
import { NatalWheel, NatalChartData } from './components/NatalWheel';

interface ChartInfo {
  sun_sign: string;
  moon_sign: string;
  ascendant: string;
  birth_place: string;
  chart_data?: NatalChartData | null;
}

export default function App() {
  const [activeTab, setActiveTab] = useState<'chart' | 'tarot' | 'pro'>('chart');
  const [chartViewMode, setChartViewMode] = useState<'wheel' | 'list'>('wheel');
  const [loading, setLoading] = useState(false);
  const [hasNoChart, setHasNoChart] = useState(false);
  const [chart, setChart] = useState<ChartInfo>({
    sun_sign: '...',
    moon_sign: '...',
    ascendant: '...',
    birth_place: 'Загрузка данных...',
    chart_data: null,
  });
  const [tarotCard, setTarotCard] = useState<any>(null);
  const [isFlipped, setIsFlipped] = useState(false);
  const [userName, setUserName] = useState<string>('');

  useEffect(() => {
    // Notify Telegram WebApp ready
    const tg = (window as any).Telegram?.WebApp;
    if (tg) {
      tg.ready();
      tg.expand();

      if (tg.initDataUnsafe?.user?.first_name) {
        setUserName(tg.initDataUnsafe.user.first_name);
      }

      // Fetch user's calculated natal chart from backend
      if (tg.initData) {
        // 1. Fetch profile & natal chart
        fetch('/api/me', {
          headers: {
            'Authorization': `tma ${tg.initData}`,
            'X-Telegram-Init-Data': tg.initData,
          },
        })
          .then((res) => (res.ok ? res.json() : null))
          .then((data) => {
            if (data?.has_chart && data.chart) {
              setHasNoChart(false);
              setChart({
                sun_sign: data.chart.sun_sign,
                moon_sign: data.chart.moon_sign,
                ascendant: data.chart.ascendant || 'Не указан',
                birth_place: data.chart.birth_place,
                chart_data: data.chart.chart_data,
              });
            } else if (data) {
              setHasNoChart(true);
              setChart({
                sun_sign: 'Не рассчитано',
                moon_sign: 'Не рассчитано',
                ascendant: 'Не рассчитано',
                birth_place: 'Данные не введены',
                chart_data: null,
              });
            }
          })
          .catch((err) => {
            console.log('Using offline demo data:', err);
          });

        // 2. Prefetch today's Tarot card (exact same as in chat)
        fetch('/api/tarot/card-of-day', {
          headers: {
            'Authorization': `tma ${tg.initData}`,
            'X-Telegram-Init-Data': tg.initData,
          },
        })
          .then((res) => (res.ok ? res.json() : null))
          .then((data) => {
            if (data?.name_ru) {
              setTarotCard({
                name: data.name_ru,
                position: data.position,
                keywords: Array.isArray(data.keywords) ? data.keywords.join(', ') : data.keywords,
                desc: data.meaning,
              });
            }
          })
          .catch(() => {});
      } else {
        // Outside Telegram (direct browser test)
        setChart({
          sun_sign: 'Скорпион ♏',
          moon_sign: 'Рыбы ♓',
          ascendant: 'Стрелец ♐',
          birth_place: 'Демо-режим',
          chart_data: null,
        });
      }
    } else {
      setChart({
        sun_sign: 'Скорпион ♏',
        moon_sign: 'Рыбы ♓',
        ascendant: 'Стрелец ♐',
        birth_place: 'Демо-режим',
        chart_data: null,
      });
    }
  }, []);

  const handleDrawTarot = () => {
    setLoading(true);
    setIsFlipped(false);

    const tg = (window as any).Telegram?.WebApp;
    if (tarotCard) {
      setTimeout(() => {
        setLoading(false);
        setIsFlipped(true);
      }, 500);
      return;
    }

    if (tg?.initData) {
      fetch('/api/tarot/card-of-day', {
        headers: {
          'Authorization': `tma ${tg.initData}`,
          'X-Telegram-Init-Data': tg.initData,
        },
      })
        .then((res) => {
          if (res.ok) return res.json();
          throw new Error('Tarot error');
        })
        .then((data) => {
          setTarotCard({
            name: data.name_ru,
            position: data.position,
            keywords: Array.isArray(data.keywords) ? data.keywords.join(', ') : data.keywords,
            desc: data.meaning,
          });
          setLoading(false);
          setIsFlipped(true);
        })
        .catch(() => {
          setLoading(false);
          setIsFlipped(true);
        });
    } else {
      setTimeout(() => {
        setTarotCard({
          name: 'Колесо Фортуны',
          position: 'Прямое положение ⬆️',
          keywords: 'Судьба, поворот к лучшему, новый цикл',
          desc: 'Перед вами открывается дверь редких возможностей. Доверьтесь космическому ритму.',
        });
        setLoading(false);
        setIsFlipped(true);
      }, 500);
    }
  };

  return (
    <div className="max-w-md mx-auto min-h-screen pb-20 p-4 font-sans flex flex-col justify-between">
      {/* Header */}
      <div>
        <div className="flex items-center justify-between py-3 border-b border-purple-900/40">
          <div className="flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-amber-400 animate-pulse" />
            <span className="font-cinzel text-xl font-bold tracking-wider text-amber-200">ASTRO AI</span>
          </div>
          <button
            onClick={() => setActiveTab('pro')}
            className="flex items-center gap-1 text-xs px-3 py-1 rounded-full bg-gradient-to-r from-amber-500 to-amber-700 text-black font-semibold shadow-lg shadow-amber-500/20 active:scale-95 transition-transform"
          >
            <Zap className="w-3.5 h-3.5" /> PRO
          </button>
        </div>

        {/* Content based on activeTab */}
        <div className="mt-4">
          {activeTab === 'chart' && (
            <div className="space-y-4">
              {hasNoChart && (
                <div className="bg-amber-950/40 border border-amber-600/50 rounded-2xl p-3.5 text-xs text-amber-200 shadow-lg">
                  <div className="font-bold flex items-center gap-1.5 mb-1 text-amber-300">
                    <span>⚠️</span> Профиль еще не заполнен
                  </div>
                  <p className="text-amber-200/90 mb-2.5 leading-relaxed">
                    Чтобы увидеть вашу настоящую карту и расчет планет по вашему городу, завершите анкету в Telegram-боте.
                  </p>
                  <button
                    onClick={() => {
                      const tg = (window as any).Telegram?.WebApp;
                      if (tg) tg.close();
                    }}
                    className="px-3 py-1.5 rounded-lg bg-amber-400 text-slate-950 font-bold text-[11px] shadow hover:bg-amber-300 active:scale-95 transition-all"
                  >
                    Перейти в бот (/start)
                  </button>
                </div>
              )}

              {/* Cosmogram Container */}
              <div className="bg-slate-900/90 border border-purple-900/60 rounded-2xl p-4 backdrop-blur-md shadow-xl">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h2 className="text-[10px] uppercase tracking-widest text-purple-400 font-semibold">
                      Персональный гороскоп
                    </h2>
                    <div className="text-xl font-cinzel font-bold text-white">Космограмма</div>
                  </div>
                  {/* View Mode Switcher */}
                  <div className="flex bg-slate-950/80 p-0.5 rounded-lg border border-purple-900/40 text-xs">
                    <button
                      onClick={() => setChartViewMode('wheel')}
                      className={`flex items-center gap-1 px-2.5 py-1 rounded-md transition-all ${
                        chartViewMode === 'wheel'
                          ? 'bg-purple-700 text-white font-medium shadow'
                          : 'text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      <CircleDot className="w-3.5 h-3.5" /> Колесо
                    </button>
                    <button
                      onClick={() => setChartViewMode('list')}
                      className={`flex items-center gap-1 px-2.5 py-1 rounded-md transition-all ${
                        chartViewMode === 'list'
                          ? 'bg-purple-700 text-white font-medium shadow'
                          : 'text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      <Layers className="w-3.5 h-3.5" /> Список
                    </button>
                  </div>
                </div>

                {/* Cosmogram Wheel View */}
                {chartViewMode === 'wheel' ? (
                  <div className="py-2">
                    <NatalWheel chartData={chart.chart_data} userName={userName} />
                  </div>
                ) : (
                  /* Cards / Grid view */
                  <div className="grid grid-cols-3 gap-2.5 py-2">
                    <div className="bg-purple-950/40 border border-purple-800/40 rounded-xl p-3 text-center">
                      <Sun className="w-5 h-5 mx-auto text-amber-400 mb-1" />
                      <div className="text-[10px] text-slate-400">Солнце</div>
                      <div className="font-semibold text-xs text-slate-200">{chart.sun_sign}</div>
                    </div>
                    <div className="bg-purple-950/40 border border-purple-800/40 rounded-xl p-3 text-center">
                      <Moon className="w-5 h-5 mx-auto text-blue-300 mb-1" />
                      <div className="text-[10px] text-slate-400">Луна</div>
                      <div className="font-semibold text-xs text-slate-200">{chart.moon_sign}</div>
                    </div>
                    <div className="bg-purple-950/40 border border-purple-800/40 rounded-xl p-3 text-center">
                      <Compass className="w-5 h-5 mx-auto text-emerald-400 mb-1" />
                      <div className="text-[10px] text-slate-400">Асцендент</div>
                      <div className="font-semibold text-xs text-slate-200">{chart.ascendant}</div>
                    </div>
                  </div>
                )}

                <div className="mt-3 pt-3 border-t border-purple-900/30 flex items-center justify-between text-xs text-slate-400">
                  <span>📍 {chart.birth_place}</span>
                  <span className="text-emerald-400">Швейцарские эфемериды ✓</span>
                </div>
              </div>

              {/* Transit preview */}
              <div className="bg-slate-900/60 border border-purple-900/40 rounded-2xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Disc3 className="w-4 h-4 text-purple-400 animate-spin" />
                  <span className="text-sm font-semibold text-purple-300">Транзиты Сегодня</span>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Транзитные аспекты рассчитаны в реальном времени к вашей натальной карте. Лунный трин благоприятствует интуиции и финансовым решениям.
                </p>
              </div>
            </div>
          )}

          {activeTab === 'tarot' && (
            <div className="space-y-4 text-center">
              <div className="text-xl font-cinzel font-bold text-amber-200">Карта Дня Таро</div>
              <p className="text-xs text-slate-400">Сфокусируйтесь на волнующем вопросе и вытяните карту</p>

              <div className="py-4 flex justify-center">
                <div
                  onClick={handleDrawTarot}
                  className={`w-52 h-76 rounded-2xl cursor-pointer transition-all duration-700 transform ${
                    isFlipped
                      ? 'bg-gradient-to-b from-purple-900/90 to-indigo-950 border-2 border-amber-400 shadow-amber-500/20'
                      : 'bg-slate-900 border-2 border-purple-800/80 shadow-2xl shadow-purple-950 hover:border-purple-600'
                  } flex flex-col items-center justify-center p-5 relative group shadow-2xl`}
                >
                  {!isFlipped ? (
                    <div className="space-y-3">
                      <Sparkles className="w-12 h-12 text-amber-400 mx-auto animate-bounce" />
                      <div className="font-cinzel text-sm text-purple-200 font-bold">Коснуться колоды</div>
                      <div className="text-[10px] text-slate-400">1 бесплатный расклад в день</div>
                    </div>
                  ) : (
                    <div className="text-left space-y-2 w-full">
                      <div className="text-xs uppercase text-amber-400 font-bold tracking-widest">
                        {tarotCard?.position}
                      </div>
                      <div className="text-lg font-cinzel font-bold text-white">{tarotCard?.name}</div>
                      <div className="text-[11px] text-purple-300 italic">{tarotCard?.keywords}</div>
                      <p className="text-[11px] text-slate-300 mt-2 border-t border-purple-800/50 pt-2 leading-relaxed max-h-36 overflow-y-auto">
                        {tarotCard?.desc}
                      </p>
                    </div>
                  )}
                </div>
              </div>

              <button
                onClick={handleDrawTarot}
                disabled={loading}
                className="w-full py-3 rounded-xl bg-purple-600 hover:bg-purple-500 font-medium text-sm transition-all shadow-lg shadow-purple-700/30 active:scale-98"
              >
                {loading ? 'Тасуем священную колоду...' : isFlipped ? 'Вытянуть другую (PRO)' : 'Вытянуть карту дня'}
              </button>
            </div>
          )}

          {activeTab === 'pro' && (
            <div className="space-y-4">
              <div className="bg-gradient-to-b from-amber-500/10 via-purple-950/40 to-slate-950 border border-amber-500/40 rounded-2xl p-5 shadow-2xl">
                <div className="flex items-center gap-2 mb-2">
                  <Zap className="w-6 h-6 text-amber-400" />
                  <h3 className="font-cinzel text-xl font-bold text-amber-200">Подписка PRO</h3>
                </div>
                <div className="text-3xl font-bold text-white mb-4">
                  299 ₽ <span className="text-xs text-slate-400 font-normal">/ месяц (150 ⭐️ Stars)</span>
                </div>

                <div className="space-y-2.5 text-xs text-slate-300 mb-6">
                  <div className="flex items-center gap-2">✓ <span>Безлимитный ИИ-астролог (Qwen 2.5 72B с памятью)</span></div>
                  <div className="flex items-center gap-2">✓ <span>Все расклады Таро (Любовь, Карьера, Выбор)</span></div>
                  <div className="flex items-center gap-2">✓ <span>Синастрия (полная совместимость с партнером)</span></div>
                  <div className="flex items-center gap-2">✓ <span>Прогноз медленных планет на 30 дней вперед</span></div>
                </div>

                <button
                  onClick={() => {
                    const tg = (window as any).Telegram?.WebApp;
                    if (tg) {
                      tg.openTelegramLink('https://t.me/Astrologyandcardsbot?start=pro');
                    } else {
                      window.open('https://t.me/Astrologyandcardsbot?start=pro', '_blank');
                    }
                  }}
                  className="w-full py-3 rounded-xl bg-gradient-to-r from-amber-400 to-amber-600 text-slate-950 font-bold text-sm shadow-xl shadow-amber-500/30 hover:brightness-110 active:scale-98 transition-all"
                >
                  ⭐️ Оформить в боте за 150 Stars
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Bottom Disclaimer & Tab Navigation */}
      <div>
        <div className="flex items-center justify-center gap-1 text-[10px] text-slate-500 text-center mb-3">
          <ShieldAlert className="w-3.5 h-3.5 text-slate-500" />
          <span>18+ Развлекательный сервис. Астрология не является научным методом.</span>
        </div>

        {/* Tab Bar */}
        <div className="bg-slate-900/95 border border-purple-900/60 rounded-2xl p-1.5 flex justify-around backdrop-blur-lg shadow-lg">
          <button
            onClick={() => setActiveTab('chart')}
            className={`flex-1 py-2 rounded-xl text-xs font-medium transition-all ${
              activeTab === 'chart' ? 'bg-purple-900/80 text-white shadow' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Натальная карта
          </button>
          <button
            onClick={() => setActiveTab('tarot')}
            className={`flex-1 py-2 rounded-xl text-xs font-medium transition-all ${
              activeTab === 'tarot' ? 'bg-purple-900/80 text-white shadow' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Таро
          </button>
          <button
            onClick={() => setActiveTab('pro')}
            className={`flex-1 py-2 rounded-xl text-xs font-medium transition-all ${
              activeTab === 'pro' ? 'bg-amber-500/20 text-amber-300 shadow font-semibold' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            ⭐ Pro
          </button>
        </div>
      </div>
    </div>
  );
}
