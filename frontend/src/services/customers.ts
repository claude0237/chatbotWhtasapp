// Customers API Service
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Customer {
  id: string;
  company_id: string;
  phone_number: string;
  name?: string;
  profile_picture_url?: string;
  metadata?: Record<string, any>;
  first_seen_at: string;
  last_seen_at: string;
  created_at: string;
  updated_at: string;
}

class CustomersService {
  private getHeaders() {
    const token = localStorage.getItem('access_token');
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
    };
  }

  async getCustomers(skip = 0, limit = 100): Promise<Customer[]> {
    const response = await fetch(`${API_BASE}/customers/?skip=${skip}&limit=${limit}`, {
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to fetch customers');
    return response.json();
  }

  async getCustomer(customerId: string): Promise<Customer> {
    const response = await fetch(`${API_BASE}/customers/${customerId}`, {
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to fetch customer');
    return response.json();
  }

  async updateCustomer(customerId: string, data: Partial<Customer>): Promise<Customer> {
    const response = await fetch(`${API_BASE}/customers/${customerId}`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to update customer');
    return response.json();
  }
}

export const customersService = new CustomersService();
