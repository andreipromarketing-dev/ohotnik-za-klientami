import React, { useState, useEffect } from 'react';
import { Play, Pause, Square, Download, Search, MapPin, Filter, AlertCircle, CheckCircle2 } from 'lucide-react';

const NICHES = [
  "Отели, гостевые дома, апартаменты",
  "Медицинские и стоматологические клиники",
  "SPA-центры и эстетическая медицина",
  "Строительные и ремонтные компании",
  "Аренда техники, яхт, оборудования",
  "Частные школы и детские центры",
  "Малые производства (мебель, стройматериалы)",
  "Автосервисы (средний и премиум сегмент)"
];

const REGIONS = ["Республика Крым", "Краснодарский край", "Ростовская область", "Вся Россия"];

export default function App() {
  const [isParsing, setIsParsing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [limit, setLimit] = useState(100);
  const [results, setResults] = useState<any[]>([]);

  // Simulation logic for the UI preview
  useEffect(() => {
    let interval: any;
    if (isParsing && progress < limit) {
      interval = setInterval(() => {
        setProgress(p => p + 1);
        const status = Math.random() > 0.6 ? '🔥 Горячий' : Math.random() > 0.3 ? '🟡 Тёплый' : '❄️ Холодный';
        setResults(prev => [{
          id: prev.length + 1,
          status,
          name: `Бизнес Объект #${prev.length + 1}`,
          phone: status !== '❄️ Холодный' ? `+7 (9${Math.floor(Math.random()*90)+10}) ${Math.floor(Math.random()*900)+100}-XX-XX` : 'Нет',
          category: 'Отели',
          city: 'Ялта',
          source: 'Авито',
          date: new Date().toLocaleTimeString()
        }, ...prev]);
      }, 800);
    } else if (progress >= limit) {
      setIsParsing(false);
    }
    return () => clearInterval(interval);
  }, [isParsing, progress, limit]);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        
        {/* Header */}
        <header className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
              <Search className="text-indigo-600" />
              Охотник за клиентами v1.0
            </h1>
            <p className="text-slate-500 mt-1">ЮгСпецСети | AI-интеграция</p>
          </div>
          <div className="flex items-center gap-2 text-sm font-medium text-emerald-600 bg-emerald-50 px-3 py-1.5 rounded-full">
            <CheckCircle2 size={16} />
            Система готова
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Settings Sidebar */}
          <div className="space-y-6">
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 space-y-5">
              <h2 className="font-semibold text-lg flex items-center gap-2">
                <Filter size={18} className="text-slate-400"/>
                Блок 1. Выбор аудитории
              </h2>
              
              <div className="space-y-3">
                <label className="block text-sm font-medium text-slate-700">Целевая ниша</label>
                <select className="w-full rounded-xl border-slate-200 bg-slate-50 px-4 py-2.5 text-sm focus:ring-2 focus:ring-indigo-500 outline-none">
                  {NICHES.map(n => <option key={n}>{n}</option>)}
                </select>
                
                <label className="block text-sm font-medium text-slate-700 mt-4">Своя ниша (опционально)</label>
                <input type="text" placeholder="Например: Барбершопы" className="w-full rounded-xl border-slate-200 bg-slate-50 px-4 py-2.5 text-sm focus:ring-2 focus:ring-indigo-500 outline-none" />
              </div>
            </div>

            <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 space-y-5">
              <h2 className="font-semibold text-lg flex items-center gap-2">
                <MapPin size={18} className="text-slate-400"/>
                Блок 2. Настройки поиска
              </h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Регион</label>
                  <select className="w-full rounded-xl border-slate-200 bg-slate-50 px-4 py-2.5 text-sm focus:ring-2 focus:ring-indigo-500 outline-none">
                    {REGIONS.map(n => <option key={n}>{n}</option>)}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Источники</label>
                  <div className="space-y-2">
                    <label className="flex items-center gap-2 text-sm">
                      <input type="checkbox" defaultChecked className="rounded text-indigo-600 focus:ring-indigo-500" />
                      Авито (приоритет)
                    </label>
                    <label className="flex items-center gap-2 text-sm opacity-50">
                      <input type="checkbox" disabled className="rounded" />
                      2GIS (в разработке)
                    </label>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Лимит: {limit}</label>
                  <input 
                    type="range" 
                    min="50" max="500" step="10"
                    value={limit}
                    onChange={(e) => setLimit(Number(e.target.value))}
                    className="w-full accent-indigo-600"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Main Content Area */}
          <div className="lg:col-span-2 space-y-6">
            
            {/* Controls & Progress */}
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 space-y-6">
              <div className="flex flex-wrap gap-3">
                <button 
                  onClick={() => setIsParsing(true)}
                  disabled={isParsing}
                  className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white px-6 py-2.5 rounded-xl font-medium transition-colors"
                >
                  <Play size={18} /> Старт
                </button>
                <button 
                  onClick={() => setIsParsing(false)}
                  disabled={!isParsing}
                  className="flex items-center gap-2 bg-amber-100 hover:bg-amber-200 text-amber-800 disabled:opacity-50 px-6 py-2.5 rounded-xl font-medium transition-colors"
                >
                  <Pause size={18} /> Пауза
                </button>
                <button 
                  onClick={() => {setIsParsing(false); setProgress(0); setResults([]);}}
                  className="flex items-center gap-2 bg-slate-100 hover:bg-slate-200 text-slate-700 px-6 py-2.5 rounded-xl font-medium transition-colors"
                >
                  <Square size={18} /> Стоп
                </button>
                
                <div className="flex-1"></div>
                
                <button className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white px-6 py-2.5 rounded-xl font-medium transition-colors">
                  <Download size={18} /> Скачать Excel
                </button>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-sm font-medium text-slate-600">
                  <span>Прогресс сбора</span>
                  <span>{progress} / {limit} контактов</span>
                </div>
                <div className="h-3 bg-slate-100 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-indigo-600 transition-all duration-300"
                    style={{ width: `${(progress / limit) * 100}%` }}
                  ></div>
                </div>
                <div className="flex gap-4 text-sm pt-2">
                  <span className="text-rose-600 font-medium">🔥 Горячих: {results.filter(r => r.status.includes('Горячий')).length}</span>
                  <span className="text-amber-600 font-medium">🟡 Тёплых: {results.filter(r => r.status.includes('Тёплый')).length}</span>
                  <span className="text-blue-600 font-medium">❄️ Холодных: {results.filter(r => r.status.includes('Холодный')).length}</span>
                </div>
              </div>
            </div>

            {/* Table */}
            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="bg-slate-50 border-b border-slate-200 text-slate-600">
                    <tr>
                      <th className="px-4 py-3 font-medium">#</th>
                      <th className="px-4 py-3 font-medium">Статус</th>
                      <th className="px-4 py-3 font-medium">Название</th>
                      <th className="px-4 py-3 font-medium">Телефон</th>
                      <th className="px-4 py-3 font-medium">Город</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {results.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="px-4 py-8 text-center text-slate-500">
                          Нажмите «Старт» для начала сбора данных
                        </td>
                      </tr>
                    ) : (
                      results.map((row, i) => (
                        <tr key={i} className="hover:bg-slate-50">
                          <td className="px-4 py-3 text-slate-500">{row.id}</td>
                          <td className="px-4 py-3 font-medium">{row.status}</td>
                          <td className="px-4 py-3">{row.name}</td>
                          <td className="px-4 py-3 font-mono">{row.phone}</td>
                          <td className="px-4 py-3 text-slate-500">{row.city}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>
  );
}
