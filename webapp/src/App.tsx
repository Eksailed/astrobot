import React, { useState, useEffect } from 'react';
import { Sparkles, Moon, Sun, Compass, Disc3, ShieldAlert, Zap } from 'lucide-react';

interface ChartInfo {
  sun_sign: string;
  moon_sign: string;
  ascendant: string;
  birth_place: string;
  chart_data?: any;
}

export default function App() {
  const [activeTab, setActiveTab] = useState<'chart' | 'tarot' | 'pro'>('chart');
  const [loading, setLoading] = useState(false);
  const [chart, setChart] = useState<ChartInfo>({
    sun_sign: 'Скорпион ♏',
    moon_sign: 'Рыбы ♓',
    ascendant: 'Стрелец ♐',
    birth_place: 'Москва',
  });
  const [tarotCard, setTarotCard] = useState<any>(null);
  const [isFlipped, setIsFlipped] = useState(false);

  useEffect(() => {
    // Notify Telegram WebApp ready
    if ((window as any).Telegram?.WebApp) {
      const tg = (window as any).Telegram.WebApp;
      tg.ready();
      tg.expand();
    }
  }, []);

  const handleDrawTarot = () => {
    setLoading(true);
    setIsFlipped(false);
    setTimeout(() => {
      setTarotCard({
        name: 'Колесо Фортуны',
        position: 'Прямое положение',
        keywords: 'Судьба, поворот к лучшему, новый цикл',
        desc: 'Перед вами открывается дверь редких возможностей. Доверьтесь космическому ритму.',
      });
      setLoading(false);
      setIsFlipped(true);
    }, 800);
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
            className="flex items-center gap-1 text-xs px-3 py-1 rounded-full bg-gradient-to-r from-amber-500 to-amber-700 text-black font-semibold shadow-lg shadow-amber-500/20"
          >
            <Zap className="w-3.5 h-3.5" /> PRO
          </button>
        </div>

        {/* Content based on activeTab */}
        <div className="mt-4">
          {activeTab === 'chart' && (
            <div className="space-y-4">
              <div className="bg-slate-900/80 border border-purple-900/60 rounded-2xl p-5 backdrop-blur-md shadow-xl">
                <h2 className="text-xs uppercase tracking-widest text-purple-400 font-semibold mb-1">Ваша Космограмма</h2>
                <div className="text-2xl font-cinzel font-bold text-white mb-4">Натальная Карта</div>

                <div className="grid grid-cols-3 gap-3">
                  <div className="bg-purple-950/40 border border-purple-800/40 rounded-xl p-3 text-center">
                    <Sun className="w-5 h-5 mx-auto text-amber-400 mb-1" />
                    <div className="text-[10px] text-slate-400">Солнце</div>
                    <div className="font-semibold text-sm text-slate-200">{chart.sun_sign}</div>
                  </div>
                  <div className="bg-purple-950/40 border border-purple-800/40 rounded-xl p-3 text-center">
                    <Moon className="w-5 h-5 mx-auto text-blue-300 mb-1" />
                    <div className="text-[10px] text-slate-400">Луна</div>
                    <div className="font-semibold text-sm text-slate-200">{chart.moon_sign}</div>
                  </div>
                  <div className="bg-purple-950/40 border border-purple-800/40 rounded-xl p-3 text-center">
                    <Compass className="w-5 h-5 mx-auto text-emerald-400 mb-1" />
                    <div className="text-[10px] text-slate-400">Асцендент</div>
                    <div className="font-semibold text-sm text-slate-200">{chart.ascendant}</div>
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-purple-900/30 flex items-center justify-between text-xs text-slate-400">
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
                  Транзитная Луна в гармоничном трине к вашему натальному Солнцу. Время для творческих инсайтов, диалога с партнером и спокойного фокуса.
                </p>
              </div>
            </div>
          )}

          {activeTab === 'tarot' && (
            <div className="space-y-4 text-center">
              <div className="text-xl font-cinzel font-bold text-amber-200">Карта Дня Таро</div>
              <p className="text-xs text-slate-400">Сфокусируйтесь на волнующем вопросе и вытяните карту</p>

              <div className="py-6 flex justify-center">
                <div 
                  onClick={handleDrawTarot}
                  className={`w-48 h-72 rounded-2xl cursor-pointer transition-all duration-700 transform ${
                    isFlipped ? 'rotate-y-180 bg-gradient-to-b from-purple-900 to-indigo-950 border-2 border-amber-400' : 'bg-slate-900 border-2 border-purple-800/80 shadow-2xl shadow-purple-950'
                  } flex flex-col items-center justify-center p-4 relative group`}
                >
                  {!isFlipped ? (
                    <div className="space-y-2">
                      <Sparkles className="w-10 h-10 text-amber-400/80 mx-auto animate-bounce" />
                      <div className="font-cinzel text-sm text-purple-300">Коснуться колоды</div>
                    </div>
                  ) : (
                    <div className="text-left space-y-2">
                      <div className="text-xs uppercase text-amber-400 font-bold tracking-widest">{tarotCard?.position}</div>
                      <div className="text-lg font-cinzel font-bold text-white">{tarotCard?.name}</div>
                      <div className="text-[11px] text-purple-300">{tarotCard?.keywords}</div>
                      <p className="text-[11px] text-slate-300 mt-2 border-t border-purple-800/50 pt-2 leading-relaxed">
                        {tarotCard?.desc}
                      </p>
                    </div>
                  )}
                </div>
              </div>

              <button
                onClick={handleDrawTarot}
                disabled={loading}
                className="w-full py-3 rounded-xl bg-purple-600 hover:bg-purple-500 font-medium text-sm transition-all shadow-lg shadow-purple-700/30"
              >
                {loading ? 'Тасуем карты...' : 'Вытянуть карту'}
              </button>
            </div>
          )}

          {activeTab === 'pro' && (
            <div className="space-y-4">
              <div className="bg-gradient-to-b from-amber-500/10 via-purple-950/40 to-slate-950 border border-amber-500/40 rounded-2xl p-5">
                <div className="flex items-center gap-2 mb-2">
                  <Zap className="w-6 h-6 text-amber-400" />
                  <h3 className="font-cinzel text-xl font-bold text-amber-200">Подписка PRO</h3>
                </div>
                <div className="text-3xl font-bold text-white mb-4">
                  299 ₽ <span className="text-xs text-slate-400 font-normal">/ месяц (150 ⭐️)</span>
                </div>

                <div className="space-y-2 text-xs text-slate-300 mb-6">
                  <div className="flex items-center gap-2">✓ <span>Безлимитный ИИ-астролог (Qwen 2.5 72B)</span></div>
                  <div className="flex items-center gap-2">✓ <span>Неограниченные расклады Таро</span></div>
                  <div className="flex items-center gap-2">✓ <span>Синастрия (анализ совместимости)</span></div>
                  <div className="flex items-center gap-2">✓ <span>Прогноз транзитов на месяц вперед</span></div>
                </div>

                <button 
                  onClick={() => {
                    if ((window as any).Telegram?.WebApp) {
                      (window as any).Telegram.WebApp.openTelegramLink('https://t.me/AstroPersonalBot?start=pro');
                    }
                  }}
                  className="w-full py-3 rounded-xl bg-gradient-to-r from-amber-400 to-amber-600 text-slate-950 font-bold text-sm shadow-xl shadow-amber-500/30 hover:brightness-110"
                >
                  Оформить через Telegram Stars
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Bottom Disclaimer & Tab Navigation */}
      <div>
        <div className="flex items-center justify-center gap-1 text-[10px] text-slate-500 text-center mb-3">
          <ShieldAlert className="w-3 h-3 text-slate-500" />
          <span>18+ Развлекательный сервис. Астрология не является научным методом.</span>
        </div>

        {/* Tab Bar */}
        <div className="bg-slate-900/90 border border-purple-900/60 rounded-2xl p-1.5 flex justify-around backdrop-blur-lg">
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
              activeTab === 'pro' ? 'bg-amber-500/20 text-amber-300 shadow' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            ⭐ Pro
          </button>
        </div>
      </div>
    </div>
  );
}
