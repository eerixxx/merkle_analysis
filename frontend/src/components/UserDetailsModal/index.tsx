import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { formatCurrency } from '@/lib/utils'
import type { LimitlessUser, BoostyFiUser } from '@/types'

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

export function UserDetailsModal({ user, isOpen, onClose, isLoading }: UserDetailsModalProps) {
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

        <ScrollArea className="h-[70vh] pr-4">
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
                  <div><strong className="text-muted-foreground">Email:</strong> {user.email || 'N/A'}</div>
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
                </div>
              </CardContent>
            </Card>

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
