import { useState, useEffect } from 'react';
import { customersService, Customer } from '../services/customers';

export function useCustomers(skip = 0, limit = 100) {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchCustomers = async () => {
    try {
      setLoading(true);
      const data = await customersService.getCustomers(skip, limit);
      setCustomers(data);
      setError('');
    } catch (err: any) {
      setError(err.message || 'Failed to fetch customers');
    } finally {
      setLoading(false);
    }
  };

  const updateCustomer = async (customerId: string, data: Partial<Customer>) => {
    try {
      const updated = await customersService.updateCustomer(customerId, data);
      setCustomers(customers.map(c => c.id === customerId ? updated : c));
      return updated;
    } catch (err: any) {
      throw new Error(err.message || 'Failed to update customer');
    }
  };

  useEffect(() => {
    fetchCustomers();
  }, [skip, limit]);

  return {
    customers,
    loading,
    error,
    fetchCustomers,
    updateCustomer,
  };
}

export function useCustomer(customerId: string) {
  const [customer, setCustomer] = useState<Customer | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchCustomer = async () => {
    try {
      setLoading(true);
      const data = await customersService.getCustomer(customerId);
      setCustomer(data);
      setError('');
    } catch (err: any) {
      setError(err.message || 'Failed to fetch customer');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (customerId) {
      fetchCustomer();
    }
  }, [customerId]);

  return {
    customer,
    loading,
    error,
    fetchCustomer,
  };
}
