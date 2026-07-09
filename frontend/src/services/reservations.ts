// Reservations API Service
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ReservationService {
  id: string;
  company_id: string;
  name: string;
  description: string | null;
  duration: number;
  price: number | null;
  is_active: boolean;
  created_at: string;
}

export interface AvailabilitySlot {
  id: string;
  service_id: string;
  start_time: string;
  end_time: string;
  is_available: boolean;
}

export interface Reservation {
  id: string;
  company_id: string;
  customer_id: string | null;
  service_id: string;
  slot_id: string;
  status: 'PENDING' | 'CONFIRMED' | 'CANCELLED';
  notes: string | null;
  confirmed_at: string | null;
  cancelled_at: string | null;
  created_at: string;
}

class ReservationsApiService {
  private getHeaders() {
    const token = localStorage.getItem('access_token');
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
    };
  }

  async getReservations(companyId: string, params?: { skip?: number; limit?: number; status?: string }): Promise<Reservation[]> {
    const queryParams = new URLSearchParams();
    if (params?.skip !== undefined) queryParams.append('skip', params.skip.toString());
    if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString());
    if (params?.status) queryParams.append('status', params.status);
    const response = await fetch(`${API_BASE}/companies/${companyId}/reservations?${queryParams}`, {
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to fetch reservations');
    return response.json();
  }

  async createReservation(companyId: string, data: { service_id: string; slot_id: string; customer_id?: string; notes?: string }): Promise<Reservation> {
    const response = await fetch(`${API_BASE}/companies/${companyId}/reservations`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to create reservation');
    return response.json();
  }

  async confirmReservation(companyId: string, reservationId: string): Promise<Reservation> {
    const response = await fetch(`${API_BASE}/companies/${companyId}/reservations/${reservationId}/confirm`, {
      method: 'PUT',
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to confirm reservation');
    return response.json();
  }

  async cancelReservation(companyId: string, reservationId: string): Promise<Reservation> {
    const response = await fetch(`${API_BASE}/companies/${companyId}/reservations/${reservationId}/cancel`, {
      method: 'PUT',
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to cancel reservation');
    return response.json();
  }

  async getServices(companyId: string): Promise<ReservationService[]> {
    const response = await fetch(`${API_BASE}/companies/${companyId}/reservations/services`, {
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to fetch services');
    return response.json();
  }

  async createService(companyId: string, data: { name: string; duration: number; description?: string; price?: number }): Promise<ReservationService> {
    const response = await fetch(`${API_BASE}/companies/${companyId}/reservations/services`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to create service');
    return response.json();
  }

  async getSlots(companyId: string, serviceId: string, params?: { from_date?: string; to_date?: string }): Promise<AvailabilitySlot[]> {
    const queryParams = new URLSearchParams({ service_id: serviceId });
    if (params?.from_date) queryParams.append('from_date', params.from_date);
    if (params?.to_date) queryParams.append('to_date', params.to_date);
    const response = await fetch(`${API_BASE}/companies/${companyId}/reservations/slots?${queryParams}`, {
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to fetch slots');
    return response.json();
  }

  async addSlot(companyId: string, data: { service_id: string; start_time: string; end_time: string }): Promise<AvailabilitySlot> {
    const response = await fetch(`${API_BASE}/companies/${companyId}/reservations/slots`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to add slot');
    return response.json();
  }
}

export const reservationsService = new ReservationsApiService();
