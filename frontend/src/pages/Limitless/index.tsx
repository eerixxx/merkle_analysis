import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, ChevronDown, ChevronUp, Users, DollarSign, TrendingUp, Crown, ChevronLeft, ChevronRight, Home } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { StatsPanel } from '@/components/StatsPanel'
import { HierarchyTree } from '@/components/HierarchyTree'
import { UserDetailsModal } from '@/components/UserDetailsModal'
import { BlockLoader } from '@/components/BlockLoader'
import { ModeToggle } from '@/components/mode-toggle'
import { UserSearch } from '@/components/UserSearch'
import { limitlessApi } from '@/lib/api'
import type { LimitlessUserTree, LimitlessStats, LimitlessUser, RootsResponse, AncestorsResponse } from '@/types'

export function LimitlessPage() {
  const [expandLevel, setExpandLevel] = useState(0)
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null)
  const [focusedUserId, setFocusedUserId] = useState<number | null>(null)
  const [offset, setOffset] = useState(0)
  const limit = 50
  
  const { data: stats, isLoading: statsLoading } = useQuery<LimitlessStats>({
    queryKey: ['limitless', 'stats'],
    queryFn: limitlessApi.getStats,
  })
  
  // Load root users when not focused on a specific user
  const { data: rootsData, isLoading: treeLoading } = useQuery<RootsResponse<LimitlessUserTree>>({
    queryKey: ['limitless', 'roots', expandLevel, offset],
    queryFn: () => limitlessApi.getRoots(expandLevel, limit, offset),
    enabled: focusedUserId === null,
  })
  
  // Load focused user's tree with ancestors
  const { data: focusedUserData, isLoading: focusedLoading } = useQuery<AncestorsResponse<LimitlessUserTree>>({
    queryKey: ['limitless', 'ancestors', focusedUserId],
    queryFn: () => limitlessApi.getAncestors(focusedUserId!),
    enabled: focusedUserId !== null,
  })
  
  // Load focused user's subtree
  const { data: focusedUserTree, isLoading: focusedTreeLoading } = useQuery<LimitlessUserTree>({
    queryKey: ['limitless', 'tree', focusedUserId],
    queryFn: () => limitlessApi.getUserTree(focusedUserId!, 3),
    enabled: focusedUserId !== null,
  })
  
  const rootUsers = rootsData?.results
  const totalRoots = rootsData?.total || 0
  const hasMore = rootsData?.has_more || false
  const currentPage = Math.floor(offset / limit) + 1
  const totalPages = Math.ceil(totalRoots / limit)
  
  const { data: selectedUser, isLoading: userLoading } = useQuery<LimitlessUser>({
    queryKey: ['limitless', 'user', selectedUserId],
    queryFn: () => limitlessApi.getUser(selectedUserId!),
    enabled: selectedUserId !== null,
  })

  const handleExpandAll = () => setExpandLevel(3)
  const handleCollapseAll = () => setExpandLevel(0)
  const handleExpandToLevel = (level: number) => setExpandLevel(level)
  
  const handleUserSearchSelect = (userId: number) => {
    setFocusedUserId(userId)
  }
  
  const handleClearFocus = () => {
    setFocusedUserId(null)
  }

  const statsCards = stats ? [
    { title: 'Total Users', value: stats.total_users.toLocaleString(), icon: Users },
    { title: 'Total Purchases', value: stats.total_purchases.toLocaleString(), icon: TrendingUp },
    { title: 'Total Volume', value: `$${Number(stats.total_volume).toLocaleString()}`, icon: DollarSign },
    { title: 'Total Earnings', value: `$${Number(stats.total_earnings).toLocaleString()}`, icon: DollarSign },
    { title: 'Root Users', value: stats.root_users.toLocaleString(), icon: Crown },
  ] : []

  const isLoading = focusedUserId ? (focusedLoading || focusedTreeLoading) : treeLoading

  return (
    <div className="min-h-screen bg-background p-5">
      <div className="max-w-full mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <Link to="/">
            <Button variant="outline" size="sm" className="gap-2">
              <ArrowLeft className="w-4 h-4" />
              Back
            </Button>
          </Link>
          <h1 className="text-3xl font-bold text-center flex-1">Limitless Hierarchy Tree</h1>
          <ModeToggle />
        </div>
        
        {/* Stats */}
        <StatsPanel 
          stats={statsCards} 
          isLoading={statsLoading}
        />
        
        {/* Controls */}
        <div className="flex flex-wrap gap-2 justify-center mb-6">
          <Button variant="default" onClick={handleExpandAll} className="gap-1">
            <ChevronDown className="w-4 h-4" />
            Expand All
          </Button>
          <Button variant="default" onClick={handleCollapseAll} className="gap-1">
            <ChevronUp className="w-4 h-4" />
            Collapse All
          </Button>
          <Button variant="outline" onClick={() => handleExpandToLevel(1)}>Level 1</Button>
          <Button variant="outline" onClick={() => handleExpandToLevel(2)}>Level 2</Button>
          <Button variant="outline" onClick={() => handleExpandToLevel(3)}>Level 3</Button>
        </div>
        
        {/* Search */}
        <div className="max-w-lg mx-auto mb-6">
          <UserSearch 
            variant="limitless" 
            onUserSelect={handleUserSearchSelect}
          />
        </div>
        
        {/* Focused User Breadcrumb */}
        {focusedUserId && focusedUserData && (
          <div className="mb-4 flex items-center gap-2 flex-wrap">
            <Button
              variant="outline"
              size="sm"
              onClick={handleClearFocus}
              className="gap-1"
            >
              <Home className="w-4 h-4" />
              Show All Roots
            </Button>
            <span className="text-muted-foreground">|</span>
            <span className="text-sm text-muted-foreground">Path:</span>
            {focusedUserData.path.map((user, index) => (
              <span key={user.id} className="flex items-center gap-1">
                <Button
                  variant={user.id === focusedUserId ? "default" : "ghost"}
                  size="sm"
                  onClick={() => setFocusedUserId(user.id)}
                  className="h-7 px-2 text-xs"
                >
                  {user.username}
                </Button>
                {index < focusedUserData.path.length - 1 && (
                  <span className="text-muted-foreground">→</span>
                )}
              </span>
            ))}
          </div>
        )}
        
        {/* Tree */}
        <Card className="bg-card border-border">
          <CardContent className="p-6 overflow-auto">
            {isLoading ? (
              <BlockLoader />
            ) : focusedUserId && focusedUserTree ? (
              <HierarchyTree
                data={[focusedUserTree]}
                variant="limitless"
                searchTerm=""
                maxDepth={3}
                onUserClick={(userId) => setSelectedUserId(userId)}
              />
            ) : rootUsers && rootUsers.length > 0 ? (
              <HierarchyTree
                data={rootUsers}
                variant="limitless"
                searchTerm=""
                maxDepth={expandLevel}
                onUserClick={(userId) => setSelectedUserId(userId)}
              />
            ) : (
              <div className="text-center py-12 text-destructive">No root users found</div>
            )}
          </CardContent>
        </Card>
        
        {/* Pagination - only when showing all roots */}
        {!focusedUserId && totalRoots > limit && (
          <div className="flex items-center justify-center gap-4 mt-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setOffset(Math.max(0, offset - limit))}
              disabled={offset === 0 || treeLoading}
            >
              <ChevronLeft className="w-4 h-4 mr-1" />
              Previous
            </Button>
            <span className="text-sm text-muted-foreground">
              Page {currentPage} of {totalPages} ({totalRoots} root users)
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setOffset(offset + limit)}
              disabled={!hasMore || treeLoading}
            >
              Next
              <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          </div>
        )}
        
        {/* User Details Modal */}
        <UserDetailsModal
          user={selectedUser}
          isOpen={selectedUserId !== null}
          onClose={() => setSelectedUserId(null)}
          isLoading={userLoading}
          variant="limitless"
        />
      </div>
    </div>
  )
}
