import React from 'react';
import { Reservation } from '../../services/reservations';

interface Props {
  reservations: Reservation[];
  loading: boolean;
  onConfirm: (id: string) => void;
  onCancel: (id: string) => void;
}

const STATUS_STYLES: Record<string, string> = {
  PENDING: 'bg-yellow-100 text-yellow-800',
  CONFIRMED: 'bg-green-100 text-green-800',
  CANCELLED: 'bg-red-100 text-red-800',
};

export const ReservationList: React.FC<Props> = ({ reservations, loading, onConfirm, onCancel }) => {
  if (loading) {
    return (
      <div className="flex items-center justify-center h-40">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (reservations.length === 0) {
    return <p className="text-center text-gray-500 py-8">No reservations found</p>;
  }

  return (
    <div className="divide-y divide-gray-200 bg-white rounded-lg border border-gray-200">
      {reservations.map(r => (
        <div key={r.id} className="p-4 flex items-center justify-between">
          <div>
            <div className="flex items-center space-x-2">
              <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${STATUS_STYLES[r.status]}`}>
                {r.status}
              </span>
              <span className="text-sm text-gray-500">{new Date(r.created_at).toLocaleDateString()}</span>
            </div>
            {r.notes && <p className="text-sm text-gray-600 mt-1">{r.notes}</p>}
          </div>
          <div className="flex space-x-2">
            {r.status === 'PENDING' && (
              <>
                <button
                  onClick={() => onConfirm(r.id)}
                  className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
                >
                  Confirm
                </button>
                <button
                  onClick={() => onCancel(r.id)}
                  className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
                >
                  Cancel
                </button>
              </>
            )}
            {r.status === 'CONFIRMED' && (
              <button
                onClick={() => onCancel(r.id)}
                className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
              >
                Cancel
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};
