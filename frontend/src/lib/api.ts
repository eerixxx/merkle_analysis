import axios from 'axios'
import type {
  LimitlessUser,
  LimitlessUserTree,
  LimitlessStats,
  BoostyFiUser,
  BoostyFiUserTree,
  BoostyFiStats,
  PaginatedResponse,
  RootsResponse,
  SearchResponse,
  AncestorsResponse,
  WalletProfile,
  SellerAssignment,
  SellerInfo,
  CurrentUser,
} from '@/types'

// Create axios instance
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle token refresh on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid - clear tokens and redirect to login
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      
      // Redirect to login if not already there
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

// Limitless API
export const limitlessApi = {
  // Users
  getUsers: async (params?: Record<string, any>): Promise<PaginatedResponse<LimitlessUser>> => {
    const { data } = await api.get('/limitless/users/', { params })
    return data
  },

  getUser: async (id: number): Promise<LimitlessUser> => {
    const { data } = await api.get(`/limitless/users/${id}/`)
    return data
  },

  getUserTree: async (id: number, depth = 2): Promise<LimitlessUserTree> => {
    const { data } = await api.get(`/limitless/users/${id}/tree/`, { params: { depth } })
    return data
  },

  getRoots: async (depth = 1, limit = 50, offset = 0): Promise<RootsResponse<LimitlessUserTree>> => {
    const { data } = await api.get('/limitless/users/roots/', { params: { depth, limit, offset } })
    return data
  },

  // Stats
  getStats: async (): Promise<LimitlessStats> => {
    const { data } = await api.get('/limitless/users/stats/')
    return data
  },

  // Search
  searchUsers: async (query: string, limit = 20): Promise<SearchResponse<LimitlessUserTree>> => {
    const { data } = await api.get('/limitless/users/search/', { params: { q: query, limit } })
    return data
  },

  // Ancestors (path to user)
  getAncestors: async (id: number): Promise<AncestorsResponse<LimitlessUserTree>> => {
    const { data } = await api.get(`/limitless/users/${id}/ancestors/`)
    return data
  },

  // Wallet Profile (from rank export)
  getWalletProfile: async (walletAddress: string): Promise<WalletProfile | null> => {
    try {
      const { data } = await api.get(`/limitless/wallet-profiles/wallet/${walletAddress}/`)
      return data
    } catch {
      return null
    }
  },
}

// BoostyFi API
export const boostyfiApi = {
  // Users
  getUsers: async (params?: Record<string, any>): Promise<PaginatedResponse<BoostyFiUser>> => {
    const { data } = await api.get('/boostyfi/users/', { params })
    return data
  },

  getUser: async (id: number): Promise<BoostyFiUser> => {
    const { data } = await api.get(`/boostyfi/users/${id}/`)
    return data
  },

  getUserTree: async (id: number, depth = 2): Promise<BoostyFiUserTree> => {
    const { data } = await api.get(`/boostyfi/users/${id}/tree/`, { params: { depth } })
    return data
  },

  getRoots: async (depth = 1, limit = 50, offset = 0): Promise<RootsResponse<BoostyFiUserTree>> => {
    const { data } = await api.get('/boostyfi/users/roots/', { params: { depth, limit, offset } })
    return data
  },

  // Stats
  getStats: async (): Promise<BoostyFiStats> => {
    const { data } = await api.get('/boostyfi/users/stats/')
    return data
  },

  // Search
  searchUsers: async (query: string, limit = 20): Promise<SearchResponse<BoostyFiUserTree>> => {
    const { data } = await api.get('/boostyfi/users/search/', { params: { q: query, limit } })
    return data
  },

  // Ancestors (path to user)
  getAncestors: async (id: number): Promise<AncestorsResponse<BoostyFiUserTree>> => {
    const { data } = await api.get(`/boostyfi/users/${id}/ancestors/`)
    return data
  },
}

// Auth API
export const authApi = {
  login: async (username: string, password: string) => {
    const { data } = await api.post('/auth/token/', { username, password })
    localStorage.setItem('access_token', data.access)
    localStorage.setItem('refresh_token', data.refresh)
    return data
  },

  refresh: async () => {
    const refresh = localStorage.getItem('refresh_token')
    if (!refresh) throw new Error('No refresh token')
    
    const { data } = await api.post('/auth/token/refresh/', { refresh })
    localStorage.setItem('access_token', data.access)
    return data
  },

  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  },

  getCurrentUser: async (): Promise<CurrentUser> => {
    const { data } = await api.get('/users/me/')
    return data
  },

  isAuthenticated: () => {
    return !!localStorage.getItem('access_token')
  },
}

// Seller Assignment API
export const sellerApi = {
  // Claim a wallet
  claim: async (platform: 'limitless' | 'boostyfi', targetUserId: number, notes = ''): Promise<SellerAssignment> => {
    const { data } = await api.post('/core/seller-assignments/claim/', {
      platform,
      target_user_id: targetUserId,
      notes,
    })
    return data
  },

  // Unclaim a wallet
  unclaim: async (platform: 'limitless' | 'boostyfi', targetUserId: number): Promise<void> => {
    await api.post('/core/seller-assignments/unclaim/', {
      platform,
      target_user_id: targetUserId,
    })
  },

  // Get all assignments for current seller
  getMyAssignments: async (platform?: 'limitless' | 'boostyfi'): Promise<SellerAssignment[]> => {
    const params = platform ? { platform } : {}
    const { data } = await api.get('/core/seller-assignments/my_assignments/', { params })
    return data
  },

  // Get sellers for a specific user (public)
  getSellersForUser: async (platform: 'limitless' | 'boostyfi', targetUserId: number): Promise<SellerInfo[]> => {
    const { data } = await api.get('/core/seller-assignments/for_user/', {
      params: { platform, target_user_id: targetUserId },
    })
    return data.sellers
  },

  // Get sellers for multiple users at once (public)
  getBulkSellers: async (platform: 'limitless' | 'boostyfi', userIds: number[]): Promise<Record<number, SellerInfo[]>> => {
    if (userIds.length === 0) return {}
    const { data } = await api.get('/core/seller-assignments/bulk_for_users/', {
      params: { platform, user_ids: userIds.join(',') },
    })
    return data.assignments
  },
}

export default api
