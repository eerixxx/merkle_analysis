import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { BlockLoader } from '@/components/BlockLoader'
import { ChevronLeft, ChevronRight, Search, UserCheck, ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react'
import { limitlessApi, boostyfiApi } from '@/lib/api'
import { shortWallet, formatCurrency, formatNumber } from '@/lib/utils'
import type { LimitlessUser, BoostyFiUser, PaginatedResponse } from '@/types'

type SortField = 'username' | 'wallet' | 'purchases_count' | 'direct_volume' | 'total_earnings' | 'children_count' | 'total_atla'
type SortOrder = 'asc' | 'desc'

interface UserTableProps {
  variant: 'limitless' | 'boostyfi'
  onUserClick?: (userId: number) => void
}

export function UserTable({ variant, onUserClick }: UserTableProps) {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [searchInput, setSearchInput] = useState('')
  const [sortField, setSortField] = useState<SortField>('username')
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc')
  const pageSize = 50
  
  const api = variant === 'limitless' ? limitlessApi : boostyfiApi
  
  const { data, isLoading } = useQuery<PaginatedResponse<LimitlessUser | BoostyFiUser>>({
    queryKey: [variant, 'users', 'table', page, search, sortField, sortOrder],
    queryFn: () => api.getUsers({
      page,
      page_size: pageSize,
      search: search || undefined,
      ordering: sortOrder === 'desc' ? `-${sortField}` : sortField,
    }),
  })
  
  const users = data?.results || []
  const totalCount = data?.count || 0
  const totalPages = Math.ceil(totalCount / pageSize)
  
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setSearch(searchInput)
    setPage(1)
  }
  
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortOrder('asc')
    }
    setPage(1)
  }
  
  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) {
      return <ArrowUpDown className="w-4 h-4 ml-1 opacity-50" />
    }
    return sortOrder === 'asc' 
      ? <ArrowUp className="w-4 h-4 ml-1" /> 
      : <ArrowDown className="w-4 h-4 ml-1" />
  }
  
  const isBoostyFi = (user: LimitlessUser | BoostyFiUser): user is BoostyFiUser => {
    return 'total_atla' in user
  }
  
  if (isLoading && users.length === 0) {
    return <BlockLoader />
  }

  return (
    <div className="space-y-4">
      {/* Search */}
      <form onSubmit={handleSearch} className="flex gap-2 max-w-md">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            type="text"
            placeholder="Search by username or wallet..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="pl-9"
          />
        </div>
        <Button type="submit" variant="default">Search</Button>
        {search && (
          <Button 
            type="button" 
            variant="outline" 
            onClick={() => {
              setSearch('')
              setSearchInput('')
              setPage(1)
            }}
          >
            Clear
          </Button>
        )}
      </form>
      
      {/* Results count */}
      <div className="text-sm text-muted-foreground">
        {totalCount.toLocaleString()} users found
        {search && ` for "${search}"`}
      </div>
      
      {/* Table */}
      <div className="border rounded-lg">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead 
                className="cursor-pointer select-none hover:bg-muted/50"
                onClick={() => handleSort('username')}
              >
                <div className="flex items-center">
                  Username
                  <SortIcon field="username" />
                </div>
              </TableHead>
              <TableHead 
                className="cursor-pointer select-none hover:bg-muted/50"
                onClick={() => handleSort('wallet')}
              >
                <div className="flex items-center">
                  Wallet
                  <SortIcon field="wallet" />
                </div>
              </TableHead>
              <TableHead>Parent</TableHead>
              <TableHead 
                className="cursor-pointer select-none hover:bg-muted/50 text-right"
                onClick={() => handleSort('purchases_count')}
              >
                <div className="flex items-center justify-end">
                  Purchases
                  <SortIcon field="purchases_count" />
                </div>
              </TableHead>
              <TableHead 
                className="cursor-pointer select-none hover:bg-muted/50 text-right"
                onClick={() => handleSort('direct_volume')}
              >
                <div className="flex items-center justify-end">
                  Volume
                  <SortIcon field="direct_volume" />
                </div>
              </TableHead>
              <TableHead 
                className="cursor-pointer select-none hover:bg-muted/50 text-right"
                onClick={() => handleSort('total_earnings')}
              >
                <div className="flex items-center justify-end">
                  Earnings
                  <SortIcon field="total_earnings" />
                </div>
              </TableHead>
              {variant === 'boostyfi' && (
                <TableHead 
                  className="cursor-pointer select-none hover:bg-muted/50 text-right"
                  onClick={() => handleSort('total_atla')}
                >
                  <div className="flex items-center justify-end">
                    ATLA
                    <SortIcon field="total_atla" />
                  </div>
                </TableHead>
              )}
              <TableHead 
                className="cursor-pointer select-none hover:bg-muted/50 text-right"
                onClick={() => handleSort('children_count')}
              >
                <div className="flex items-center justify-end">
                  Referrals
                  <SortIcon field="children_count" />
                </div>
              </TableHead>
              <TableHead>Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {users.length === 0 ? (
              <TableRow>
                <TableCell colSpan={variant === 'boostyfi' ? 9 : 8} className="text-center py-8 text-muted-foreground">
                  No users found
                </TableCell>
              </TableRow>
            ) : (
              users.map((user) => (
                <TableRow 
                  key={user.id}
                  className="cursor-pointer"
                  onClick={() => onUserClick?.(user.id)}
                >
                  <TableCell className="font-medium">
                    {user.username || `User ${user.original_id}`}
                  </TableCell>
                  <TableCell className="font-mono text-xs">
                    {shortWallet(user.wallet)}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {user.parent_username || '-'}
                  </TableCell>
                  <TableCell className="text-right">
                    {user.purchases_count > 0 && (
                      <Badge variant="success" className="text-xs">
                        {formatNumber(user.purchases_count)}
                      </Badge>
                    )}
                  </TableCell>
                  <TableCell className="text-right">
                    {Number(user.direct_volume) > 0 && (
                      <span className="text-green-600 dark:text-green-400">
                        {formatCurrency(user.direct_volume)}
                      </span>
                    )}
                  </TableCell>
                  <TableCell className="text-right">
                    {Number(user.total_earnings) > 0 && (
                      <span className="text-amber-600 dark:text-amber-400">
                        {formatCurrency(user.total_earnings)}
                      </span>
                    )}
                  </TableCell>
                  {variant === 'boostyfi' && isBoostyFi(user) && (
                    <TableCell className="text-right">
                      {Number(user.total_atla) > 0 && (
                        <span className="text-purple-600 dark:text-purple-400">
                          {formatNumber(Number(user.total_atla).toFixed(2))}
                        </span>
                      )}
                    </TableCell>
                  )}
                  {variant === 'limitless' && <></>}
                  <TableCell className="text-right">
                    {user.children_count > 0 && (
                      <Badge variant="secondary" className="text-xs">
                        👥 {formatNumber(user.children_count)}
                      </Badge>
                    )}
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-1 flex-wrap">
                      {user.is_active && (
                        <Badge variant="outline" className="text-xs text-green-600 border-green-600/30">
                          Active
                        </Badge>
                      )}
                      {user.assigned_sellers && user.assigned_sellers.length > 0 && (
                        <Badge variant="outline" className="text-xs bg-blue-500/10 border-blue-500/30 text-blue-600 dark:text-blue-400">
                          <UserCheck className="w-3 h-3 mr-1" />
                          Assigned
                        </Badge>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
      
      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-4">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage(Math.max(1, page - 1))}
            disabled={page === 1 || isLoading}
          >
            <ChevronLeft className="w-4 h-4 mr-1" />
            Previous
          </Button>
          <span className="text-sm text-muted-foreground">
            Page {page} of {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage(Math.min(totalPages, page + 1))}
            disabled={page >= totalPages || isLoading}
          >
            Next
            <ChevronRight className="w-4 h-4 ml-1" />
          </Button>
        </div>
      )}
    </div>
  )
}


