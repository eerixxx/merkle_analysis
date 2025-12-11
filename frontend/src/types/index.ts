// Limitless Types
export interface LimitlessUser {
  id: number
  original_id: number
  username: string
  email?: string
  wallet: string
  referral_code: string
  referral_code_confirmed: boolean
  is_active: boolean
  is_superuser: boolean
  is_staff: boolean
  date_joined?: string
  created_at: string
  parent_username?: string
  children_count: number
  team_size?: number
  purchases_count: number
  pending_purchases_count?: number
  direct_volume: number
  team_volume?: number
  total_earnings: number
  pending_earnings?: number
  purchases?: LimitlessPurchase[]
  recent_earnings?: LimitlessEarning[]
  earnings_by_type?: EarningByType[]
}

export interface LimitlessUserTree extends LimitlessUser {
  children: LimitlessUserTree[]
}

export interface LimitlessPurchase {
  id: number
  original_id: number
  amount_usdt: number
  tx_hash: string
  payment_status: string
  pack_id?: number
  created_at: string
}

export interface LimitlessEarning {
  id: number
  original_id: number
  earning_type: string
  level?: number
  percentage?: number
  amount_usdt: number
  status: string
  from_username?: string
  created_at: string
}

// BoostyFi Types
export interface BoostyFiUser {
  id: number
  original_id: number
  username: string
  email?: string
  wallet: string
  evm_address?: string
  tron_address?: string
  referral_code: string
  referral_type?: string
  referral_code_confirmed: boolean
  is_active: boolean
  is_superuser: boolean
  is_staff: boolean
  locked_atla_balance: number
  unlocked_atla_balance: number
  total_atla: number
  date_joined?: string
  created_at: string
  parent_username?: string
  children_count: number
  team_size?: number
  purchases_count: number
  pending_purchases_count?: number
  direct_volume: number
  team_volume?: number
  total_earnings: number
  pending_earnings?: number
  purchases?: BoostyFiPurchase[]
  recent_earnings?: BoostyFiEarning[]
  earnings_by_type?: EarningByType[]
  earnings_by_system?: EarningBySystem[]
}

export interface BoostyFiUserTree extends BoostyFiUser {
  children: BoostyFiUserTree[]
}

export interface BoostyFiPurchase {
  id: number
  original_id: number
  amount: number
  full_amount: number
  discount_rate: number
  tx_hash: string
  payment_status: string
  payment_type: string
  jggl_pack_id?: number
  created_at: string
}

export interface BoostyFiEarning {
  id: number
  original_id: number
  earning_type: string
  generation_level?: number
  percentage?: number
  amount: number
  status: string
  referral_system_type?: number
  referral_system_name?: string
  qualification_reason?: string
  from_username?: string
  created_at: string
}

// Shared Types
export interface EarningByType {
  earning_type: string
  count: number
  total: number
}

export interface EarningBySystem {
  referral_system_type: number
  count: number
  total: number
}

export interface LimitlessStats {
  total_users: number
  total_purchases: number
  total_volume: number
  total_earnings: number
  root_users: number
}

export interface BoostyFiStats {
  total_users: number
  total_purchases: number
  total_volume: number
  total_earnings: number
  total_atla: number
  root_users: number
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface RootsResponse<T> {
  results: T[]
  total: number
  limit: number
  offset: number
  has_more: boolean
}

// Search Types
export interface SearchResponse<T> {
  results: T[]
  query: string
}

export interface AncestorsResponse<T> {
  user_id: number
  path: T[]
}

export interface GlobalSearchResponse {
  query: string
  limitless: {
    count: number
    results: LimitlessUser[]
  }
  boostyfi: {
    count: number
    results: BoostyFiUser[]
  }
}
