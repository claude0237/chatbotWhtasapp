import React, { useState } from 'react';
import { AvailabilitySlot } from '../../services/reservations';

interface Props {
  slots: AvailabilitySlot[];
  onSelectSlot: (slot: AvailabilitySlot) => void;
  selectedSlotId?: string;
}

export const ReservationCalendar: React.FC<Props> = ({ slots, onSelectSlot, selectedSlotId }) => {
  const [currentDate, setCurrentDate] = useState(new Date());

  const currentMonth = currentDate.getMonth();
  const currentYear = currentDate.getFullYear();

  // Group slots by date
  const slotsByDate: Record<string, AvailabilitySlot[]> = {};
  slots.forEach(slot => {
    const date = new Date(slot.start_time).toLocaleDateString('fr-FR');
    if (!slotsByDate[date]) slotsByDate[date] = [];
    slotsByDate[date].push(slot);
  });

  const prevMonth = () => {
    setCurrentDate(prev => new Date(prev.getFullYear(), prev.getMonth() - 1, 1));
  };

  const nextMonth = () => {
    setCurrentDate(prev => new Date(prev.getFullYear(), prev.getMonth() + 1, 1));
  };

  const monthName = currentDate.toLocaleDateString('fr-FR', { month: 'long', year: 'numeric' });

  // Build calendar grid
  const firstDay = new Date(currentYear, currentMonth, 1).getDay();
  const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
  const startOffset = firstDay === 0 ? 6 : firstDay - 1;

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <button onClick={prevMonth} className="p-1 rounded hover:bg-gray-100">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <h3 className="font-semibold text-gray-900 capitalize">{monthName}</h3>
        <button onClick={nextMonth} className="p-1 rounded hover:bg-gray-100">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>

      <div className="grid grid-cols-7 gap-1 mb-2">
        {['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'].map(d => (
          <div key={d} className="text-center text-xs text-gray-500 font-medium py-1">{d}</div>
        ))}
      </div>

      <div className="grid grid-cols-7 gap-1">
        {Array.from({ length: startOffset }, (_, i) => (
          <div key={`empty-${i}`} />
        ))}
        {Array.from({ length: daysInMonth }, (_, i) => {
          const day = i + 1;
          const dateKey = new Date(currentYear, currentMonth, day).toLocaleDateString('fr-FR');
          const daySlots = slotsByDate[dateKey] || [];
          const hasSlots = daySlots.length > 0;

          return (
            <div
              key={day}
              className={`relative aspect-square flex flex-col items-center justify-center rounded text-sm cursor-default
                ${hasSlots ? 'bg-blue-50 cursor-pointer hover:bg-blue-100' : 'text-gray-400'}`}
              onClick={() => hasSlots && daySlots.length === 1 && onSelectSlot(daySlots[0])}
            >
              <span className={hasSlots ? 'font-semibold text-blue-700' : ''}>{day}</span>
              {hasSlots && (
                <span className="text-xs text-blue-500">{daySlots.length} créneau{daySlots.length > 1 ? 'x' : ''}</span>
              )}
            </div>
          );
        })}
      </div>

      {/* Slots list for selected date */}
      {Object.keys(slotsByDate).length > 0 && (
        <div className="mt-4 space-y-2">
          <h4 className="text-sm font-medium text-gray-700">Créneaux disponibles</h4>
          {slots.map(slot => (
            <button
              key={slot.id}
              onClick={() => onSelectSlot(slot)}
              className={`w-full text-left px-3 py-2 rounded border text-sm transition-colors
                ${selectedSlotId === slot.id
                  ? 'border-blue-500 bg-blue-50 text-blue-700'
                  : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'}`}
            >
              {new Date(slot.start_time).toLocaleDateString('fr-FR', { weekday: 'short', day: 'numeric', month: 'short' })}
              {' — '}
              {new Date(slot.start_time).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
              {' à '}
              {new Date(slot.end_time).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
