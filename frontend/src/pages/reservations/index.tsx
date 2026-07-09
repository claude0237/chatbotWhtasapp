import React, { useState } from 'react';
import { useReservations, useReservationServices, useAvailableSlots } from '../../hooks/useReservations';
import { ReservationList } from '../../components/reservations/ReservationList';
import { ReservationCalendar } from '../../components/reservations/ReservationCalendar';
import { AvailabilitySlot } from '../../services/reservations';

const ReservationsPage: React.FC<{ companyId: string }> = ({ companyId }) => {
  const { reservations, loading, confirmReservation, cancelReservation } = useReservations(companyId);
  const { services } = useReservationServices(companyId);
  const [selectedServiceId, setSelectedServiceId] = useState('');
  const [selectedSlot, setSelectedSlot] = useState<AvailabilitySlot | undefined>();
  const [notes, setNotes] = useState('');
  const [tab, setTab] = useState<'list' | 'new'>('list');
  const [error, setError] = useState('');

  const { slots } = useAvailableSlots(companyId, selectedServiceId);

  const { createReservation } = useReservations(companyId);

  const handleCreateReservation = async () => {
    if (!selectedServiceId || !selectedSlot) {
      setError('Please select a service and a slot');
      return;
    }
    try {
      await createReservation({
        service_id: selectedServiceId,
        slot_id: selectedSlot.id,
        notes: notes || undefined
      });
      setTab('list');
      setSelectedSlot(undefined);
      setNotes('');
      setError('');
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Reservations</h1>
        <div className="flex space-x-2">
          <button
            onClick={() => setTab('list')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${tab === 'list' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}
          >
            List
          </button>
          <button
            onClick={() => setTab('new')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${tab === 'new' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}
          >
            + New
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-md text-sm">{error}</div>
      )}

      {tab === 'list' ? (
        <ReservationList
          reservations={reservations}
          loading={loading}
          onConfirm={confirmReservation}
          onCancel={cancelReservation}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Service</label>
              <select
                value={selectedServiceId}
                onChange={e => { setSelectedServiceId(e.target.value); setSelectedSlot(undefined); }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select a service</option>
                {services.map(s => (
                  <option key={s.id} value={s.id}>{s.name} ({s.duration} min{s.price ? ` - ${s.price}€` : ''})</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
              <textarea
                value={notes}
                onChange={e => setNotes(e.target.value)}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Optional notes..."
              />
            </div>

            {selectedSlot && (
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-md text-sm text-blue-700">
                Selected: {new Date(selectedSlot.start_time).toLocaleString('fr-FR')}
              </div>
            )}

            <button
              onClick={handleCreateReservation}
              disabled={!selectedServiceId || !selectedSlot}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Book Reservation
            </button>
          </div>

          <div>
            {selectedServiceId ? (
              <ReservationCalendar
                slots={slots}
                onSelectSlot={setSelectedSlot}
                selectedSlotId={selectedSlot?.id}
              />
            ) : (
              <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg border border-gray-200 text-gray-500">
                Select a service to see available slots
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ReservationsPage;
