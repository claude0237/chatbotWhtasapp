import { useState, useEffect, useCallback } from 'react';
import { reservationsService, Reservation, ReservationService, AvailabilitySlot } from '../services/reservations';

export function useReservations(companyId: string) {
  const [reservations, setReservations] = useState<Reservation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchReservations = useCallback(async (params?: { skip?: number; limit?: number; status?: string }) => {
    try {
      setLoading(true);
      const data = await reservationsService.getReservations(companyId, params);
      setReservations(data);
      setError('');
    } catch (err: any) {
      setError(err.message || 'Failed to fetch reservations');
    } finally {
      setLoading(false);
    }
  }, [companyId]);

  const createReservation = useCallback(async (data: { service_id: string; slot_id: string; customer_id?: string; notes?: string }) => {
    const reservation = await reservationsService.createReservation(companyId, data);
    setReservations(prev => [reservation, ...prev]);
    return reservation;
  }, [companyId]);

  const confirmReservation = useCallback(async (reservationId: string) => {
    const updated = await reservationsService.confirmReservation(companyId, reservationId);
    setReservations(prev => prev.map(r => r.id === reservationId ? updated : r));
    return updated;
  }, [companyId]);

  const cancelReservation = useCallback(async (reservationId: string) => {
    const updated = await reservationsService.cancelReservation(companyId, reservationId);
    setReservations(prev => prev.map(r => r.id === reservationId ? updated : r));
    return updated;
  }, [companyId]);

  useEffect(() => { fetchReservations(); }, [fetchReservations]);

  return { reservations, loading, error, fetchReservations, createReservation, confirmReservation, cancelReservation };
}

export function useReservationServices(companyId: string) {
  const [services, setServices] = useState<ReservationService[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchServices = useCallback(async () => {
    try {
      setLoading(true);
      const data = await reservationsService.getServices(companyId);
      setServices(data);
      setError('');
    } catch (err: any) {
      setError(err.message || 'Failed to fetch services');
    } finally {
      setLoading(false);
    }
  }, [companyId]);

  const createService = useCallback(async (data: { name: string; duration: number; description?: string; price?: number }) => {
    const service = await reservationsService.createService(companyId, data);
    setServices(prev => [...prev, service]);
    return service;
  }, [companyId]);

  useEffect(() => { fetchServices(); }, [fetchServices]);

  return { services, loading, error, fetchServices, createService };
}

export function useAvailableSlots(companyId: string, serviceId: string, fromDate?: string, toDate?: string) {
  const [slots, setSlots] = useState<AvailabilitySlot[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchSlots = useCallback(async () => {
    if (!serviceId) return;
    try {
      setLoading(true);
      const data = await reservationsService.getSlots(companyId, serviceId, { from_date: fromDate, to_date: toDate });
      setSlots(data);
      setError('');
    } catch (err: any) {
      setError(err.message || 'Failed to fetch slots');
    } finally {
      setLoading(false);
    }
  }, [companyId, serviceId, fromDate, toDate]);

  useEffect(() => { fetchSlots(); }, [fetchSlots]);

  return { slots, loading, error, fetchSlots };
}
