import React, { useState } from 'react';
import { useProducts, useProductCategories } from '../../hooks/useProducts';
import { ProductList } from '../../components/products/ProductList';
import { ProductForm } from '../../components/products/ProductForm';
import { Product } from '../../services/products';

const ProductsPage: React.FC<{ companyId: string }> = ({ companyId }) => {
  const { products, loading, createProduct, updateProduct, deleteProduct } = useProducts(companyId);
  const { categories } = useProductCategories(companyId);
  const [showForm, setShowForm] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | undefined>();
  const [error, setError] = useState('');

  const handleCreate = async (data: any) => {
    try {
      await createProduct(data);
      setShowForm(false);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleUpdate = async (data: any) => {
    if (!editingProduct) return;
    try {
      await updateProduct(editingProduct.id, data);
      setEditingProduct(undefined);
      setShowForm(false);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleEdit = (product: Product) => {
    setEditingProduct(product);
    setShowForm(true);
  };

  const handleDelete = async (productId: string) => {
    if (confirm('Delete this product?')) {
      await deleteProduct(productId);
    }
  };

  const handleCancel = () => {
    setShowForm(false);
    setEditingProduct(undefined);
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Products</h1>
        {!showForm && (
          <button
            onClick={() => setShowForm(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            + New Product
          </button>
        )}
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-md">
          {error}
        </div>
      )}

      {showForm ? (
        <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            {editingProduct ? 'Edit Product' : 'New Product'}
          </h2>
          <ProductForm
            product={editingProduct}
            categories={categories}
            onSubmit={editingProduct ? handleUpdate : handleCreate}
            onCancel={handleCancel}
          />
        </div>
      ) : (
        <ProductList
          products={products}
          loading={loading}
          onEdit={handleEdit}
          onDelete={handleDelete}
        />
      )}
    </div>
  );
};

export default ProductsPage;
