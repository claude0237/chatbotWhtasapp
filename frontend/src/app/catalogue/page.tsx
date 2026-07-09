'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useHashTab } from '../../hooks/useHashTab';
import AppLayout from '../../components/AppLayout';
import { productsService, Product, ProductCategory } from '../../services/products';
import { useAuth } from '../../hooks/useAuth';
import api from '../../lib/api';

const CURRENCIES = ['EUR', 'USD', 'GBP', 'MAD', 'XOF', 'XAF', 'DZD', 'TND'];

const BLANK_PRODUCT = {
  name: '', description: '', price: 0, currency: 'EUR',
  stock: 0, images: [] as string[], category_id: '', is_active: true,
};

export default function CataloguePage() {
  const { user } = useAuth();
  const companyId = (user as any)?.company_id;

  const [products,    setProducts]    = useState<Product[]>([]);
  const [categories,  setCategories]  = useState<ProductCategory[]>([]);
  const [loading,     setLoading]     = useState(true);
  const [error,       setError]       = useState('');
  const [search,      setSearch]      = useState('');
  const [filterCat,   setFilterCat]   = useState('');
  const [filterActive, setFilterActive] = useState<'all'|'active'|'inactive'>('active');
  const [activeTab,   setActiveTab]   = useHashTab<'products'|'categories'>('products');
  const [submitting,  setSubmitting]  = useState(false);
  const [uploading,   setUploading]   = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [showProductModal,  setShowProductModal]  = useState(false);
  const [showCategoryModal, setShowCategoryModal] = useState(false);
  const [editingProduct,    setEditingProduct]    = useState<Product | null>(null);
  const [editingCategory,   setEditingCategory]   = useState<ProductCategory | null>(null);

  const [productForm,  setProductForm]  = useState({ ...BLANK_PRODUCT });
  const [categoryForm, setCategoryForm] = useState({ name: '', parent_id: '', is_active: true });
  const BACKEND = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const load = useCallback(async () => {
    if (!companyId) return;
    setLoading(true);
    try {
      const [prods, cats] = await Promise.all([
        productsService.getProducts(companyId, { active_only: false, limit: 200 }),
        productsService.getCategories(companyId),
      ]);
      setProducts(prods);
      setCategories(cats);
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Erreur de chargement');
    } finally {
      setLoading(false);
    }
  }, [companyId]);

  useEffect(() => { load(); }, [load]);

  const filtered = products.filter(p => {
    if (filterActive === 'active'   && !p.is_active) return false;
    if (filterActive === 'inactive' &&  p.is_active) return false;
    if (filterCat && p.category_id !== filterCat) return false;
    if (search && !p.name.toLowerCase().includes(search.toLowerCase()) &&
        !(p.description || '').toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const catName = (id: string | null) =>
    categories.find(c => c.id === id)?.name || '—';

  function openNewProduct() {
    setEditingProduct(null);
    setProductForm({ ...BLANK_PRODUCT });
    setShowProductModal(true);
  }
  function openEditProduct(p: Product) {
    setEditingProduct(p);
    setProductForm({
      name: p.name, description: p.description || '', price: p.price,
      currency: p.currency, stock: p.stock, images: p.images || [],
      category_id: p.category_id || '', is_active: p.is_active,
    });
    setShowProductModal(true);
  }
  function openNewCategory() {
    setEditingCategory(null);
    setCategoryForm({ name: '', parent_id: '', is_active: true });
    setShowCategoryModal(true);
  }
  function openEditCategory(c: ProductCategory) {
    setEditingCategory(c);
    setCategoryForm({ name: c.name, parent_id: c.parent_id || '', is_active: c.is_active });
    setShowCategoryModal(true);
  }

  async function saveProduct(e: React.FormEvent) {
    e.preventDefault();
    if (!companyId) return;
    setSubmitting(true);
    try {
      const payload = {
        ...productForm,
        price: Number(productForm.price),
        stock: Number(productForm.stock),
        category_id: productForm.category_id || undefined,
        description: productForm.description || undefined,
      };
      if (editingProduct) {
        await productsService.updateProduct(companyId, editingProduct.id, payload);
      } else {
        await productsService.createProduct(companyId, payload);
      }
      setShowProductModal(false);
      await load();
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Erreur de sauvegarde');
    } finally {
      setSubmitting(false);
    }
  }

  async function saveCategory(e: React.FormEvent) {
    e.preventDefault();
    if (!companyId) return;
    setSubmitting(true);
    try {
      const payload = { name: categoryForm.name, is_active: categoryForm.is_active, parent_id: categoryForm.parent_id || undefined };
      if (editingCategory) {
        await productsService.updateCategory(companyId, editingCategory.id, payload);
      } else {
        await productsService.createCategory(companyId, payload);
      }
      setShowCategoryModal(false);
      await load();
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Erreur de sauvegarde');
    } finally {
      setSubmitting(false);
    }
  }

  async function uploadImage(file: File) {
    setUploading(true);
    try {
      const form = new FormData();
      form.append('file', file);
      const r = await api.post('/upload/image', form, { headers: { 'Content-Type': 'multipart/form-data' } });
      const url: string = BACKEND + r.data.url;
      setProductForm(f => ({ ...f, images: [...f.images, url] }));
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Erreur upload image');
    } finally {
      setUploading(false);
    }
  }

  async function deleteProduct(id: string) {
    if (!confirm('Supprimer ce produit ?')) return;
    try { await productsService.deleteProduct(companyId, id); await load(); }
    catch (e: any) { setError(e?.response?.data?.detail || 'Erreur'); }
  }
  async function deleteCategory(id: string) {
    if (!confirm('Supprimer cette catégorie ?')) return;
    try { await productsService.deleteCategory(companyId, id); await load(); }
    catch (e: any) { setError(e?.response?.data?.detail || 'Erreur'); }
  }

  if (loading) return <AppLayout><div className="flex items-center justify-center h-64 text-gray-400">Chargement...</div></AppLayout>;

  return (
    <AppLayout>
      <div className="max-w-6xl mx-auto">

        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-gray-900">🛍️ Catalogue produits</h1>
          <div className="flex gap-2">
            <button onClick={openNewCategory}
              className="border border-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-50 text-sm font-medium">
              + Catégorie
            </button>
            <button onClick={openNewProduct}
              className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 text-sm font-medium">
              + Produit
            </button>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-300 text-red-700 px-4 py-2 rounded-lg mb-4 flex justify-between text-sm">
            <span>{error}</span>
            <button onClick={() => setError('')}>✕</button>
          </div>
        )}

        {/* Tabs */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="-mb-px flex space-x-6">
            {([['products', `📦 Produits (${products.length})`], ['categories', `🏷️ Catégories (${categories.length})`]] as const).map(([key, label]) => (
              <button key={key} onClick={() => setActiveTab(key)}
                className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === key ? 'border-green-500 text-green-600' : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}>{label}
              </button>
            ))}
          </nav>
        </div>

        {/* ── PRODUITS ── */}
        {activeTab === 'products' && (
          <>
            {/* Filtres */}
            <div className="bg-white rounded-xl border border-gray-200 p-4 mb-5 flex flex-wrap gap-3">
              <input value={search} onChange={e => setSearch(e.target.value)}
                placeholder="Rechercher un produit..."
                className="flex-1 min-w-48 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500" />
              <select value={filterCat} onChange={e => setFilterCat(e.target.value)}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:ring-2 focus:ring-green-500">
                <option value="">Toutes catégories</option>
                {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
              <select value={filterActive} onChange={e => setFilterActive(e.target.value as any)}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white">
                <option value="active">Actifs seulement</option>
                <option value="inactive">Inactifs seulement</option>
                <option value="all">Tous</option>
              </select>
            </div>

            {filtered.length === 0 ? (
              <div className="bg-white rounded-xl border border-gray-200 p-12 text-center text-gray-400">
                <p className="text-5xl mb-3">📦</p>
                <p className="text-sm">Aucun produit. Cliquez sur « + Produit » pour commencer.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {filtered.map(p => (
                  <div key={p.id} className={`bg-white rounded-xl border shadow-sm overflow-hidden flex flex-col ${!p.is_active ? 'opacity-60' : ''}`}>
                    {/* Image */}
                    {p.images && p.images.length > 0 ? (
                      <img src={p.images[0]} alt={p.name} className="w-full h-36 object-cover" />
                    ) : (
                      <div className="w-full h-36 bg-gray-100 flex items-center justify-center text-4xl text-gray-300">📦</div>
                    )}
                    <div className="p-4 flex flex-col flex-1">
                      <div className="flex items-start justify-between gap-2 mb-1">
                        <h3 className="font-semibold text-gray-900 text-sm leading-tight">{p.name}</h3>
                        {!p.is_active && <span className="text-xs bg-gray-200 text-gray-500 px-2 py-0.5 rounded-full shrink-0">Inactif</span>}
                      </div>
                      {p.description && <p className="text-xs text-gray-500 mb-2 line-clamp-2">{p.description}</p>}
                      <div className="flex items-center justify-between mt-auto pt-2">
                        <div>
                          <span className="text-base font-bold text-green-700">{p.price} {p.currency}</span>
                          <span className={`ml-2 text-xs ${p.stock > 0 ? 'text-gray-500' : 'text-red-500 font-medium'}`}>
                            {p.stock > 0 ? `${p.stock} en stock` : 'Rupture'}
                          </span>
                        </div>
                        <span className="text-xs text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-full">{catName(p.category_id)}</span>
                      </div>
                      <div className="flex gap-2 mt-3 pt-3 border-t border-gray-100">
                        <button onClick={() => openEditProduct(p)}
                          className="flex-1 text-xs text-indigo-600 hover:text-indigo-800 font-medium border border-indigo-200 rounded-lg py-1.5 hover:bg-indigo-50">
                          ✏️ Modifier
                        </button>
                        <button onClick={() => deleteProduct(p.id)}
                          className="flex-1 text-xs text-red-500 hover:text-red-700 font-medium border border-red-200 rounded-lg py-1.5 hover:bg-red-50">
                          🗑️ Supprimer
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {/* ── CATÉGORIES ── */}
        {activeTab === 'categories' && (
          <div className="bg-white rounded-xl border border-gray-200 divide-y divide-gray-100">
            {categories.length === 0 ? (
              <div className="p-12 text-center text-gray-400">
                <p className="text-4xl mb-3">🏷️</p>
                <p className="text-sm">Aucune catégorie. Cliquez sur « + Catégorie » pour en créer.</p>
              </div>
            ) : (
              categories.map(c => {
                const prodCount = products.filter(p => p.category_id === c.id).length;
                const parent = categories.find(x => x.id === c.parent_id);
                return (
                  <div key={c.id} className={`flex items-center justify-between px-5 py-3 hover:bg-gray-50 ${!c.is_active ? 'opacity-60' : ''}`}>
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-gray-900 text-sm">{c.name}</span>
                      {!c.is_active && <span className="text-xs bg-gray-200 text-gray-500 px-2 py-0.5 rounded-full">Inactive</span>}
                      {parent && <span className="text-xs text-gray-400">↳ {parent.name}</span>}
                      <span className="text-xs text-gray-400">{prodCount} produit{prodCount !== 1 ? 's' : ''}</span>
                    </div>
                    <div className="flex gap-3">
                      <button onClick={() => openEditCategory(c)} className="text-xs text-indigo-600 hover:text-indigo-800 font-medium">Modifier</button>
                      <button onClick={() => deleteCategory(c.id)} className="text-xs text-red-500 hover:text-red-700 font-medium">Supprimer</button>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        )}
      </div>

      {/* ── Modal Produit ── */}
      {showProductModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl p-6 w-full max-w-lg shadow-xl max-h-[92vh] overflow-y-auto">
            <h3 className="font-bold text-gray-900 mb-4">{editingProduct ? '✏️ Modifier le produit' : '+ Nouveau produit'}</h3>
            <form onSubmit={saveProduct} className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nom *</label>
                <input required value={productForm.name} onChange={e => setProductForm(f => ({...f, name: e.target.value}))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500" placeholder="Ex: iPhone 15 Pro" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea value={productForm.description} onChange={e => setProductForm(f => ({...f, description: e.target.value}))} rows={3}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500 resize-none"
                  placeholder="Description visible par le bot dans les fiches produit..." />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Prix *</label>
                  <input required type="number" step="0.01" min="0" value={productForm.price}
                    onChange={e => setProductForm(f => ({...f, price: parseFloat(e.target.value) || 0}))}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Devise</label>
                  <select value={productForm.currency} onChange={e => setProductForm(f => ({...f, currency: e.target.value}))}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:ring-2 focus:ring-green-500">
                    {CURRENCIES.map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Stock</label>
                  <input type="number" min="0" value={productForm.stock}
                    onChange={e => setProductForm(f => ({...f, stock: parseInt(e.target.value) || 0}))}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Catégorie</label>
                  <select value={productForm.category_id} onChange={e => setProductForm(f => ({...f, category_id: e.target.value}))}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:ring-2 focus:ring-green-500">
                    <option value="">Sans catégorie</option>
                    {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                  </select>
                </div>
              </div>
              {/* Images */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Images</label>
                <div
                  className="border-2 border-dashed border-gray-300 rounded-lg px-4 py-5 text-center cursor-pointer hover:border-green-400 transition-colors"
                  onClick={() => fileInputRef.current?.click()}
                >
                  {uploading ? (
                    <p className="text-sm text-gray-400">Envoi en cours...</p>
                  ) : (
                    <>
                      <p className="text-2xl mb-1">📷</p>
                      <p className="text-xs text-gray-500">Cliquez ou glissez une image (JPEG, PNG, WebP — max 5 Mo)</p>
                    </>
                  )}
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/jpeg,image/png,image/webp,image/gif"
                    className="hidden"
                    onChange={e => { const f = e.target.files?.[0]; if (f) uploadImage(f); e.target.value = ''; }}
                  />
                </div>
                {productForm.images.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-2">
                    {productForm.images.map((img, i) => (
                      <div key={i} className="relative group">
                        <img src={img} alt="" className="w-16 h-16 object-cover rounded-lg border" />
                        <button type="button" onClick={() => setProductForm(f => ({...f, images: f.images.filter((_, j) => j !== i)}))}
                          className="absolute -top-1 -right-1 bg-red-500 text-white rounded-full w-5 h-5 text-xs flex items-center justify-center opacity-0 group-hover:opacity-100">✕</button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              <div className="flex items-center gap-2">
                <input type="checkbox" id="prod_active" checked={productForm.is_active}
                  onChange={e => setProductForm(f => ({...f, is_active: e.target.checked}))} className="rounded" />
                <label htmlFor="prod_active" className="text-sm text-gray-700">Produit actif <span className="text-gray-400">(visible dans le bot)</span></label>
              </div>
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowProductModal(false)}
                  className="flex-1 border border-gray-300 py-2 rounded-lg text-sm hover:bg-gray-50">Annuler</button>
                <button type="submit" disabled={submitting}
                  className="flex-1 bg-green-600 text-white py-2 rounded-lg text-sm hover:bg-green-700 disabled:opacity-50">
                  {submitting ? '...' : editingProduct ? 'Enregistrer' : 'Créer'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Modal Catégorie ── */}
      {showCategoryModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl p-6 w-full max-w-sm shadow-xl">
            <h3 className="font-bold text-gray-900 mb-4">{editingCategory ? '✏️ Modifier la catégorie' : '+ Nouvelle catégorie'}</h3>
            <form onSubmit={saveCategory} className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nom *</label>
                <input required value={categoryForm.name} onChange={e => setCategoryForm(f => ({...f, name: e.target.value}))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500" placeholder="Ex: Smartphones, Vêtements..." />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Catégorie parente <span className="text-gray-400">(optionnel)</span></label>
                <select value={categoryForm.parent_id} onChange={e => setCategoryForm(f => ({...f, parent_id: e.target.value}))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:ring-2 focus:ring-green-500">
                  <option value="">Aucune (catégorie racine)</option>
                  {categories.filter(c => c.id !== editingCategory?.id).map(c => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>
              <div className="flex items-center gap-2">
                <input type="checkbox" id="cat_active" checked={categoryForm.is_active}
                  onChange={e => setCategoryForm(f => ({...f, is_active: e.target.checked}))} className="rounded" />
                <label htmlFor="cat_active" className="text-sm text-gray-700">Catégorie active <span className="text-gray-400">(visible dans le bot)</span></label>
              </div>
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowCategoryModal(false)}
                  className="flex-1 border border-gray-300 py-2 rounded-lg text-sm hover:bg-gray-50">Annuler</button>
                <button type="submit" disabled={submitting}
                  className="flex-1 bg-green-600 text-white py-2 rounded-lg text-sm hover:bg-green-700 disabled:opacity-50">
                  {submitting ? '...' : editingCategory ? 'Enregistrer' : 'Créer'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AppLayout>
  );
}
