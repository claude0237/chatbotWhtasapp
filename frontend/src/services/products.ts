// Products API Service — uses shared axios instance
import api from '../lib/api';

export interface Product {
  id: string;
  company_id: string;
  name: string;
  description: string | null;
  price: number;
  currency: string;
  stock: number;
  images: string[] | null;
  category_id: string | null;
  is_active: boolean;
  metadata: Record<string, any> | null;
  created_at: string;
  updated_at: string;
}

export interface ProductCategory {
  id: string;
  company_id: string;
  name: string;
  is_active: boolean;
  parent_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateProductData {
  name: string;
  description?: string;
  price: number;
  currency?: string;
  stock?: number;
  images?: string[];
  category_id?: string;
  metadata?: Record<string, any>;
}

export interface UpdateProductData extends Partial<CreateProductData> {
  is_active?: boolean;
}

class ProductsService {
  async getProducts(companyId: string, params?: { skip?: number; limit?: number; active_only?: boolean; search?: string }): Promise<Product[]> {
    const r = await api.get(`/companies/${companyId}/products`, { params });
    return r.data;
  }

  async getProduct(companyId: string, productId: string): Promise<Product> {
    const r = await api.get(`/companies/${companyId}/products/${productId}`);
    return r.data;
  }

  async createProduct(companyId: string, data: CreateProductData): Promise<Product> {
    const r = await api.post(`/companies/${companyId}/products`, data);
    return r.data;
  }

  async updateProduct(companyId: string, productId: string, data: UpdateProductData): Promise<Product> {
    const r = await api.put(`/companies/${companyId}/products/${productId}`, data);
    return r.data;
  }

  async deleteProduct(companyId: string, productId: string): Promise<void> {
    await api.delete(`/companies/${companyId}/products/${productId}`);
  }

  async getCategories(companyId: string): Promise<ProductCategory[]> {
    const r = await api.get(`/companies/${companyId}/products/categories`);
    return r.data;
  }

  async createCategory(companyId: string, data: { name: string; is_active?: boolean; parent_id?: string }): Promise<ProductCategory> {
    const r = await api.post(`/companies/${companyId}/products/categories`, data);
    return r.data;
  }

  async updateCategory(companyId: string, categoryId: string, data: { name?: string; is_active?: boolean; parent_id?: string }): Promise<ProductCategory> {
    const r = await api.put(`/companies/${companyId}/products/categories/${categoryId}`, data);
    return r.data;
  }

  async deleteCategory(companyId: string, categoryId: string): Promise<void> {
    await api.delete(`/companies/${companyId}/products/categories/${categoryId}`);
  }
}

export const productsService = new ProductsService();
