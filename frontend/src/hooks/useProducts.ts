import { useState, useEffect, useCallback } from 'react';
import { productsService, Product, ProductCategory } from '../services/products';

export function useProducts(companyId: string) {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchProducts = useCallback(async (params?: { skip?: number; limit?: number; active_only?: boolean; search?: string }) => {
    try {
      setLoading(true);
      const data = await productsService.getProducts(companyId, params);
      setProducts(data);
      setError('');
    } catch (err: any) {
      setError(err.message || 'Failed to fetch products');
    } finally {
      setLoading(false);
    }
  }, [companyId]);

  const createProduct = useCallback(async (data: {
    name: string;
    description?: string;
    price: number;
    currency?: string;
    stock?: number;
    images?: string[];
    category_id?: string;
    metadata?: Record<string, any>;
  }) => {
    try {
      const newProduct = await productsService.createProduct(companyId, data);
      setProducts(prev => [newProduct, ...prev]);
      return newProduct;
    } catch (err: any) {
      setError(err.message || 'Failed to create product');
      throw err;
    }
  }, [companyId]);

  const updateProduct = useCallback(async (productId: string, data: {
    name?: string;
    description?: string;
    price?: number;
    currency?: string;
    stock?: number;
    images?: string[];
    category_id?: string;
    is_active?: boolean;
    metadata?: Record<string, any>;
  }) => {
    try {
      const updatedProduct = await productsService.updateProduct(companyId, productId, data);
      setProducts(prev => prev.map(p => p.id === productId ? updatedProduct : p));
      return updatedProduct;
    } catch (err: any) {
      setError(err.message || 'Failed to update product');
      throw err;
    }
  }, [companyId]);

  const deleteProduct = useCallback(async (productId: string) => {
    try {
      await productsService.deleteProduct(companyId, productId);
      setProducts(prev => prev.filter(p => p.id !== productId));
    } catch (err: any) {
      setError(err.message || 'Failed to delete product');
      throw err;
    }
  }, [companyId]);

  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  return {
    products,
    loading,
    error,
    fetchProducts,
    createProduct,
    updateProduct,
    deleteProduct,
  };
}

export function useProductCategories(companyId: string) {
  const [categories, setCategories] = useState<ProductCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchCategories = useCallback(async (params?: { skip?: number; limit?: number }) => {
    try {
      setLoading(true);
      const data = await productsService.getCategories(companyId, params);
      setCategories(data);
      setError('');
    } catch (err: any) {
      setError(err.message || 'Failed to fetch categories');
    } finally {
      setLoading(false);
    }
  }, [companyId]);

  const createCategory = useCallback(async (data: { name: string; parent_id?: string }) => {
    try {
      const newCategory = await productsService.createCategory(companyId, data);
      setCategories(prev => [...prev, newCategory]);
      return newCategory;
    } catch (err: any) {
      setError(err.message || 'Failed to create category');
      throw err;
    }
  }, [companyId]);

  const updateCategory = useCallback(async (categoryId: string, data: { name?: string; parent_id?: string }) => {
    try {
      const updatedCategory = await productsService.updateCategory(companyId, categoryId, data);
      setCategories(prev => prev.map(c => c.id === categoryId ? updatedCategory : c));
      return updatedCategory;
    } catch (err: any) {
      setError(err.message || 'Failed to update category');
      throw err;
    }
  }, [companyId]);

  const deleteCategory = useCallback(async (categoryId: string) => {
    try {
      await productsService.deleteCategory(companyId, categoryId);
      setCategories(prev => prev.filter(c => c.id !== categoryId));
    } catch (err: any) {
      setError(err.message || 'Failed to delete category');
      throw err;
    }
  }, [companyId]);

  useEffect(() => {
    fetchCategories();
  }, [fetchCategories]);

  return {
    categories,
    loading,
    error,
    fetchCategories,
    createCategory,
    updateCategory,
    deleteCategory,
  };
}
