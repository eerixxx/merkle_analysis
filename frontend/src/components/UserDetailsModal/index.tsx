import { useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { formatCurrency } from '@/lib/utils'
import { limitlessApi, authApi, sellerApi } from '@/lib/api'
import { UserCheck, UserMinus, Loader2 } from 'lucide-react'
import type { LimitlessUser, BoostyFiUser, WalletProfile, CurrentUser, SellerInfo } from '@/types'

type UserType = LimitlessUser | BoostyFiUser

interface UserDetailsModalProps {
  user?: UserType | null
  isOpen: boolean
  onClose: () => void
  isLoading?: boolean
  variant?: 'limitless' | 'boostyfi'
}

// Type guard for BoostyFi
function isBoostyFiUser(user: UserType): user is BoostyFiUser {
  return 'total_atla' in user || 'referral_type' in user
}

export function UserDetailsModal({ user, isOpen, onClose, isLoading, variant }: UserDetailsModalProps) {
  const [walletProfile, setWalletProfile] = useState<WalletProfile | null>(null)
  const [loadingProfile, setLoadingProfile] = useState(false)
  const queryClient = useQueryClient()

  // Get current user info (only if authenticated)
  const { data: currentUser } = useQuery<CurrentUser>({
    queryKey: ['currentUser'],
    queryFn: authApi.getCurrentUser,
    enabled: authApi.isAuthenticated(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: false,
  })

  // Fetch wallet profile when modal opens with a user
  useEffect(() => {
    if (isOpen && user?.wallet && variant === 'limitless') {
      setLoadingProfile(true)
      limitlessApi.getWalletProfile(user.wallet)
        .then(setWalletProfile)
        .finally(() => setLoadingProfile(false))
    } else {
      setWalletProfile(null)
    }
  }, [isOpen, user?.wallet, variant])

  // Check if current user is a seller and has claimed this user
  const isSeller = currentUser?.is_seller ?? false
  const assignedSellers: SellerInfo[] = user?.assigned_sellers || []
  const isClaimedByMe = assignedSellers.some(s => s.seller_id === currentUser?.id)
  const canClaim = isSeller && assignedSellers.length < 5 && !isClaimedByMe

  // Claim mutation
  const claimMutation = useMutation({
    mutationFn: () => sellerApi.claim(variant || 'limitless', user!.id),
    onSuccess: () => {
      // Invalidate relevant queries to refresh data
      queryClient.invalidateQueries({ queryKey: [variant, 'user', user?.id] })
      queryClient.invalidateQueries({ queryKey: [variant, 'roots'] })
      queryClient.invalidateQueries({ queryKey: [variant, 'tree'] })
    },
  })

  // Unclaim mutation
  const unclaimMutation = useMutation({
    mutationFn: () => sellerApi.unclaim(variant || 'limitless', user!.id),
    onSuccess: () => {
      // Invalidate relevant queries to refresh data
      queryClient.invalidateQueries({ queryKey: [variant, 'user', user?.id] })
      queryClient.invalidateQueries({ queryKey: [variant, 'roots'] })
      queryClient.invalidateQueries({ queryKey: [variant, 'tree'] })
    },
  })

  const handleClaim = () => {
    if (user && variant) {
      claimMutation.mutate()
    }
  }

  const handleUnclaim = () => {
    if (user && variant) {
      unclaimMutation.mutate()
    }
  }

  if (isLoading) {
    return (
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="max-w-4xl max-h-[90vh]">
          <div className="animate-pulse space-y-4">
            <div className="h-8 bg-muted rounded w-1/2" />
            <div className="h-32 bg-muted rounded" />
            <div className="h-32 bg-muted rounded" />
          </div>
        </DialogContent>
      </Dialog>
    )
  }

  if (!user) return null

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle className="text-2xl">
            👤 {user.username || 'User'} - ID: {user.original_id}
          </DialogTitle>
        </DialogHeader>

        {/* Seller Assignment Section */}
        {(isSeller || assignedSellers.length > 0) && (
          <Card className="border-l-4 border-l-blue-500 mb-4">
            <CardHeader className="pb-2">
              <CardTitle className="text-lg flex items-center gap-2">
                <UserCheck className="w-5 h-5" />
                Seller Assignments ({assignedSellers.length}/5)
              </CardTitle>
            </CardHeader>
            <CardContent>
              {/* List of assigned sellers */}
              {assignedSellers.length > 0 ? (
                <div className="mb-4 space-y-2">
                  {assignedSellers.map((seller) => (
                    <div
                      key={seller.id}
                      className={`flex items-center justify-between p-2 rounded ${
                        seller.seller_id === currentUser?.id
                          ? 'bg-blue-500/10 border border-blue-500/30'
                          : 'bg-muted'
                      }`}
                    >
                      <div>
                        <span className="font-medium">{seller.seller_name}</span>
                        <span className="text-xs text-muted-foreground ml-2">
                          (@{seller.seller_username})
                        </span>
                        {seller.seller_id === currentUser?.id && (
                          <Badge variant="secondary" className="ml-2 text-xs">You</Badge>
                        )}
                      </div>
                      <span className="text-xs text-muted-foreground">
                        {new Date(seller.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-muted-foreground text-sm mb-4">
                  No sellers have claimed this wallet yet.
                </p>
              )}

              {/* Claim/Unclaim buttons */}
              {isSeller && (
                <div className="flex gap-2">
                  {isClaimedByMe ? (
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={handleUnclaim}
                      disabled={unclaimMutation.isPending}
                      className="gap-2"
                    >
                      {unclaimMutation.isPending ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <UserMinus className="w-4 h-4" />
                      )}
                      Remove Myself
                    </Button>
                  ) : canClaim ? (
                    <Button
                      variant="default"
                      size="sm"
                      onClick={handleClaim}
                      disabled={claimMutation.isPending}
                      className="gap-2"
                    >
                      {claimMutation.isPending ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <UserCheck className="w-4 h-4" />
                      )}
                      Claim This Wallet
                    </Button>
                  ) : (
                    <p className="text-sm text-muted-foreground">
                      Maximum 5 sellers can claim this wallet.
                    </p>
                  )}
                </div>
              )}

              {/* Error messages */}
              {claimMutation.isError && (
                <p className="text-destructive text-sm mt-2">
                  Failed to claim: {(claimMutation.error as Error)?.message || 'Unknown error'}
                </p>
              )}
              {unclaimMutation.isError && (
                <p className="text-destructive text-sm mt-2">
                  Failed to unclaim: {(unclaimMutation.error as Error)?.message || 'Unknown error'}
                </p>
              )}
            </CardContent>
          </Card>
        )}

        <ScrollArea className="h-[60vh] pr-4">
          <div className="space-y-4">
            {/* Basic Info */}
            <Card className="border-l-4 border-l-primary">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg">📋 Basic Information</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                  <div><strong className="text-muted-foreground">ID:</strong> {user.original_id}</div>
                  <div><strong className="text-muted-foreground">Username:</strong> {user.username || 'N/A'}</div>
                  {/* Show email only for BoostyFi, for Limitless it's in WalletProfile */}
                  {isBoostyFiUser(user) && (
                    <div><strong className="text-muted-foreground">Email:</strong> {user.email || 'N/A'}</div>
                  )}
                  <div><strong className="text-muted-foreground">Referral Code:</strong> {user.referral_code || 'N/A'}</div>
                  {isBoostyFiUser(user) && user.referral_type && (
                    <div><strong className="text-muted-foreground">Referral Type:</strong> {user.referral_type}</div>
                  )}
                  <div><strong className="text-muted-foreground">Created:</strong> {new Date(user.created_at).toLocaleDateString()}</div>
                  <div>
                    <strong className="text-muted-foreground">Status:</strong>{' '}
                    {user.is_active ? '✅ Active' : '❌ Inactive'}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Financial Overview */}
            <Card className="border-l-4 border-l-emerald-500">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg">💰 Financial Overview</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                  <div><strong className="text-muted-foreground">Direct Volume:</strong> {formatCurrency(user.direct_volume)}</div>
                  <div><strong className="text-muted-foreground">Team Volume:</strong> {formatCurrency(user.team_volume || 0)}</div>
                  <div><strong className="text-muted-foreground">Team Contribution:</strong> {formatCurrency((user.team_volume || 0) - user.direct_volume)}</div>
                  <div><strong className="text-muted-foreground">Purchases (Completed):</strong> {user.purchases_count}</div>
                  <div><strong className="text-muted-foreground">Purchases (Pending):</strong> {user.pending_purchases_count || 0}</div>
                  <div><strong className="text-muted-foreground">Earnings (Withdrawn):</strong> {formatCurrency(user.total_earnings)}</div>
                  <div><strong className="text-muted-foreground">Earnings (Pending):</strong> {formatCurrency(user.pending_earnings || 0)}</div>
                </div>
              </CardContent>
            </Card>

            {/* ATLA Balance (BoostyFi only) */}
            {isBoostyFiUser(user) && (
              <Card className="border-l-4 border-l-amber-500">
                <CardHeader className="pb-2">
                  <CardTitle className="text-lg">🪙 ATLA Balance</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div><strong className="text-muted-foreground">Locked:</strong> {Number(user.locked_atla_balance).toFixed(6)}</div>
                    <div><strong className="text-muted-foreground">Unlocked:</strong> {Number(user.unlocked_atla_balance).toFixed(6)}</div>
                    <div><strong className="text-muted-foreground">Total:</strong> {Number(user.total_atla).toFixed(6)}</div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Team Structure */}
            <Card className="border-l-4 border-l-blue-500">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg">👨‍👩‍👧‍👦 Team Structure</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div><strong className="text-muted-foreground">Direct Referrals:</strong> {user.children_count}</div>
                  <div><strong className="text-muted-foreground">Total Team Size:</strong> {user.team_size || 0}</div>
                  <div>
                    <strong className="text-muted-foreground">Sponsor:</strong>{' '}
                    {user.parent_username || 'Root User'}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Wallet Info */}
            <Card className="border-l-4 border-l-violet-500">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg">🔗 Wallet Information</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm font-mono break-all">
                  <div><strong className="text-muted-foreground">Main:</strong> {user.wallet || 'N/A'}</div>
                  {isBoostyFiUser(user) && (
                    <>
                      <div><strong className="text-muted-foreground">EVM:</strong> {user.evm_address || 'N/A'}</div>
                      <div><strong className="text-muted-foreground">TRON:</strong> {user.tron_address || 'N/A'}</div>
                    </>
                  )}
                  {walletProfile?.subwallets_list && walletProfile.subwallets_list.length > 0 && (
                    <div>
                      <strong className="text-muted-foreground">Subwallets:</strong>
                      <ul className="mt-1 ml-4 list-disc">
                        {walletProfile.subwallets_list.map((sw, i) => (
                          <li key={i}>{sw}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Wallet Profile - Rank Data (Limitless only) */}
            {variant === 'limitless' && (
              loadingProfile ? (
                <Card className="border-l-4 border-l-amber-500">
                  <CardContent className="py-4">
                    <div className="animate-pulse h-24 bg-muted rounded" />
                  </CardContent>
                </Card>
              ) : walletProfile ? (
                <>
                  {/* Rank & Balance */}
                  <Card className="border-l-4 border-l-amber-500">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-lg">🏆 Rank & Balance</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <strong className="text-muted-foreground">Rank:</strong>{' '}
                          <Badge variant={
                            walletProfile.rank === 'Guardian' ? 'default' :
                            walletProfile.rank === 'Visionary' ? 'secondary' :
                            walletProfile.rank === 'Partner' ? 'outline' :
                            'secondary'
                          }>
                            {walletProfile.rank || 'No Rank'}
                          </Badge>
                        </div>
                        <div><strong className="text-muted-foreground">ATLA Balance:</strong> {Number(walletProfile.atla_balance).toLocaleString()}</div>
                        <div><strong className="text-muted-foreground">JGGL:</strong> {Number(walletProfile.jggl).toLocaleString()}</div>
                        <div><strong className="text-muted-foreground">Community:</strong> {walletProfile.community_count.toLocaleString()}</div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* BoostyFi Tokens */}
                  {(Number(walletProfile.bfi_atla) > 0 || Number(walletProfile.bfi_jggl) > 0) && (
                    <Card className="border-l-4 border-l-cyan-500">
                      <CardHeader className="pb-2">
                        <CardTitle className="text-lg">🪙 BoostyFi Tokens</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div><strong className="text-muted-foreground">BFI ATLA:</strong> {Number(walletProfile.bfi_atla).toLocaleString()}</div>
                          <div><strong className="text-muted-foreground">BFI JGGL:</strong> {Number(walletProfile.bfi_jggl).toLocaleString()}</div>
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {/* LP / CHS / DSY */}
                  {(walletProfile.has_lp || walletProfile.has_chs || walletProfile.has_dsy) && (
                    <Card className="border-l-4 border-l-pink-500">
                      <CardHeader className="pb-2">
                        <CardTitle className="text-lg">📊 LP / CHS / DSY</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="grid grid-cols-3 gap-4 text-sm">
                          <div>
                            <strong className="text-muted-foreground">LP:</strong>{' '}
                            {walletProfile.has_lp ? `✅ ${Number(walletProfile.lp_shares).toLocaleString()} shares` : '❌ No'}
                          </div>
                          <div>
                            <strong className="text-muted-foreground">CHS:</strong>{' '}
                            {walletProfile.has_chs ? `✅ ${Number(walletProfile.ch_share).toLocaleString()} share` : '❌ No'}
                          </div>
                          <div>
                            <strong className="text-muted-foreground">DSY:</strong>{' '}
                            {walletProfile.has_dsy ? `✅ ${Number(walletProfile.dsy_bonus).toLocaleString()} bonus` : '❌ No'}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {/* Contact Info */}
                  {(walletProfile.email || walletProfile.telegram || walletProfile.whatsapp || walletProfile.facebook || walletProfile.viber || walletProfile.line || walletProfile.other_contact) && (
                    <Card className="border-l-4 border-l-green-500">
                      <CardHeader className="pb-2">
                        <CardTitle className="text-lg">📞 Contact Information</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                          {walletProfile.email && (
                            <div>
                              <strong className="text-muted-foreground">Email:</strong> {walletProfile.email}
                              {walletProfile.email_verified && ' ✅'}
                            </div>
                          )}
                          {walletProfile.telegram && (
                            <div><strong className="text-muted-foreground">Telegram:</strong> {walletProfile.telegram}</div>
                          )}
                          {walletProfile.whatsapp && (
                            <div><strong className="text-muted-foreground">WhatsApp:</strong> {walletProfile.whatsapp}</div>
                          )}
                          {walletProfile.facebook && (
                            <div><strong className="text-muted-foreground">Facebook:</strong> {walletProfile.facebook}</div>
                          )}
                          {walletProfile.viber && (
                            <div><strong className="text-muted-foreground">Viber:</strong> {walletProfile.viber}</div>
                          )}
                          {walletProfile.line && (
                            <div><strong className="text-muted-foreground">Line:</strong> {walletProfile.line}</div>
                          )}
                          {walletProfile.other_contact && (
                            <div><strong className="text-muted-foreground">Other:</strong> {walletProfile.other_contact}</div>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {/* Preferences */}
                  <Card className="border-l-4 border-l-indigo-500">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-lg">⚙️ Preferences & Access</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                        {walletProfile.preferred_language && (
                          <div><strong className="text-muted-foreground">Language:</strong> {walletProfile.preferred_language}</div>
                        )}
                        <div>
                          <strong className="text-muted-foreground">English:</strong>{' '}
                          {walletProfile.can_communicate_english ? '✅ Yes' : '❌ No'}
                        </div>
                        <div>
                          <strong className="text-muted-foreground">Zoom Call:</strong>{' '}
                          {walletProfile.need_private_zoom_call ? '✅ Requested' : '❌ No'}
                        </div>
                        <div>
                          <strong className="text-muted-foreground">Business Dev:</strong>{' '}
                          {walletProfile.want_business_dev_access ? '✅ Requested' : '❌ No'}
                        </div>
                        <div>
                          <strong className="text-muted-foreground">CEO Access:</strong>{' '}
                          {walletProfile.want_ceo_access ? '✅ Requested' : '❌ No'}
                        </div>
                        {walletProfile.is_seller && (
                          <div><strong className="text-muted-foreground">Seller:</strong> ✅ Yes</div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </>
              ) : null
            )}

            {/* Earnings by Type */}
            {user.earnings_by_type && user.earnings_by_type.length > 0 && (
              <Card className="border-l-4 border-l-orange-500">
                <CardHeader className="pb-2">
                  <CardTitle className="text-lg">💵 Earnings by Type</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {user.earnings_by_type.map((e, i) => (
                      <div key={i} className="flex justify-between items-center p-2 bg-muted rounded">
                        <span className="font-medium">{e.earning_type}</span>
                        <span>{formatCurrency(e.total)} ({e.count} records)</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Purchase History */}
            {user.purchases && user.purchases.length > 0 && (
              <Card className="border-l-4 border-l-emerald-500">
                <CardHeader className="pb-2">
                  <CardTitle className="text-lg">💳 Purchase History ({user.purchases.length})</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {user.purchases.slice(0, 10).map((p) => (
                      <div key={p.id} className="p-3 bg-muted rounded border-l-4 border-l-emerald-500">
                        <div className="flex justify-between items-center">
                          <span className="font-bold text-emerald-400">
                            {formatCurrency('amount_usdt' in p ? p.amount_usdt : (p as any).amount)}
                          </span>
                          <Badge variant={p.payment_status === 'COMPLETED' ? 'success' : 'warning'}>
                            {p.payment_status}
                          </Badge>
                        </div>
                        <div className="text-xs text-muted-foreground mt-1">
                          📅 {new Date(p.created_at).toLocaleString()}
                        </div>
                        <div className="text-xs text-muted-foreground mt-1 truncate">
                          🔗 TX: {p.tx_hash || 'N/A'}
                        </div>
                      </div>
                    ))}
                    {user.purchases.length > 10 && (
                      <p className="text-center text-muted-foreground text-sm">
                        ... and {user.purchases.length - 10} more
                      </p>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Recent Earnings */}
            {user.recent_earnings && user.recent_earnings.length > 0 && (
              <Card className="border-l-4 border-l-orange-500">
                <CardHeader className="pb-2">
                  <CardTitle className="text-lg">💵 Recent Earnings (last 15)</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {user.recent_earnings.map((e) => (
                      <div key={e.id} className="p-3 bg-muted rounded border-l-4 border-l-orange-500">
                        <div className="flex justify-between items-center">
                          <span className="font-bold text-orange-400">
                            {formatCurrency('amount_usdt' in e ? e.amount_usdt : (e as any).amount)}
                          </span>
                          <Badge variant={e.status === 'WITHDRAWN' ? 'success' : 'warning'}>
                            {e.status}
                          </Badge>
                        </div>
                        <div className="text-xs text-muted-foreground mt-1">
                          📅 {new Date(e.created_at).toLocaleString()} | Type: {e.earning_type}
                        </div>
                        {e.from_username && (
                          <div className="text-xs text-muted-foreground">From: {e.from_username}</div>
                        )}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  )
}
