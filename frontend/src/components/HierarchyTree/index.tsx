import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Badge } from '@/components/ui/badge'
import { cn, shortWallet } from '@/lib/utils'
import { Loader2, UserCheck } from 'lucide-react'
import { limitlessApi, boostyfiApi } from '@/lib/api'
import type { LimitlessUserTree, BoostyFiUserTree, SellerInfo } from '@/types'
import './styles.css'

type TreeNode = LimitlessUserTree | BoostyFiUserTree

interface HierarchyTreeProps {
  data: TreeNode[]
  variant?: 'limitless' | 'boostyfi'
  searchTerm?: string
  maxDepth?: number
  onUserClick?: (userId: number) => void
}

interface TreeNodeProps {
  node: TreeNode
  variant: 'limitless' | 'boostyfi'
  searchTerm: string
  level: number
  maxDepth: number
  onUserClick?: (userId: number) => void
}

function TreeNodeComponent({ node, variant, searchTerm, level, maxDepth, onUserClick }: TreeNodeProps) {
  const [isExpanded, setIsExpanded] = useState(level < maxDepth)
  const [loadedChildren, setLoadedChildren] = useState<TreeNode[]>(node.children || [])
  
  // Check if we have children data or just children_count
  const hasChildrenData = loadedChildren && loadedChildren.length > 0
  const childrenCount = hasChildrenData ? loadedChildren.length : (node.children_count || 0)
  const hasChildren = childrenCount > 0
  
  // Lazy load children when expanded
  const { data: fetchedChildren, isLoading: childrenLoading, refetch } = useQuery({
    queryKey: [variant, 'tree', node.id],
    queryFn: async () => {
      const api = variant === 'limitless' ? limitlessApi : boostyfiApi
      const result = await api.getUserTree(node.id, 5)
      return result.children || []
    },
    enabled: false,
  })
  
  // Update when maxDepth changes
  useEffect(() => {
    setIsExpanded(level < maxDepth)
  }, [level, maxDepth])
  
  // Load children when expanding and no data available
  useEffect(() => {
    if (isExpanded && !hasChildrenData && hasChildren && !childrenLoading) {
      refetch()
    }
  }, [isExpanded, hasChildrenData, hasChildren])
  
  // Update loaded children when data fetched
  useEffect(() => {
    if (fetchedChildren && fetchedChildren.length > 0) {
      setLoadedChildren(fetchedChildren)
    }
  }, [fetchedChildren])
  
  const isHighlighted = searchTerm.length >= 2 && (
    node.username?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    node.wallet?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    node.original_id?.toString().includes(searchTerm)
  )

  // Type guard for BoostyFi specific fields
  const isBoostyFi = (n: TreeNode): n is BoostyFiUserTree => {
    return 'total_atla' in n || 'referral_type' in n
  }

  // Get assigned sellers from the node
  const assignedSellers: SellerInfo[] = node.assigned_sellers || []
  const hasSellers = assignedSellers.length > 0

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (hasChildren) {
      setIsExpanded(!isExpanded)
    }
    if (onUserClick) {
      onUserClick(node.id)
    }
  }

  return (
    <li>
      <div
        onClick={handleClick}
        className={cn(
          'node-box',
          hasChildren && 'has-children',
          isHighlighted && 'highlighted',
          variant
        )}
        data-level={level}
      >
        <span className="node-username">{node.username || `User ${node.original_id}`}</span>
        <span className="node-wallet">{shortWallet(node.wallet)}</span>
        <div className="node-badges">
          {isBoostyFi(node) && node.referral_type && (
            <Badge variant="secondary" className="text-xs">
              🏷️ {node.referral_type}
            </Badge>
          )}
          {node.purchases_count > 0 && (
            <Badge variant="success" className="text-xs">
              💰 {node.purchases_count}
            </Badge>
          )}
          {Number(node.direct_volume) > 0 && (
            <Badge variant="success" className="text-xs">
              ${Number(node.direct_volume).toFixed(0)}
            </Badge>
          )}
          {Number(node.total_earnings) > 0 && (
            <Badge variant="warning" className="text-xs">
              💵 ${Number(node.total_earnings).toFixed(0)}
            </Badge>
          )}
          {isBoostyFi(node) && Number(node.total_atla) > 0 && (
            <Badge variant="destructive" className="text-xs">
              🪙 {Number(node.total_atla).toFixed(2)}
            </Badge>
          )}
          {childrenCount > 0 && (
            <Badge variant="secondary" className="text-xs">
              👥 {childrenCount}
            </Badge>
          )}
          {hasSellers && (
            <Badge variant="outline" className="text-xs bg-blue-500/10 border-blue-500/30 text-blue-600 dark:text-blue-400">
              <UserCheck className="w-3 h-3 mr-1" />
              {assignedSellers.map(s => s.seller_name).join(', ')}
            </Badge>
          )}
        </div>
      </div>

      {/* Children */}
      {hasChildren && (
        <ul className="children-list" style={{ display: isExpanded ? 'table' : 'none' }}>
          {childrenLoading ? (
            <li>
              <div className="node-box loading-node">
                <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
              </div>
            </li>
          ) : (
            loadedChildren.map((child) => (
              <TreeNodeComponent
                key={child.id}
                node={child}
                variant={variant}
                searchTerm={searchTerm}
                level={level + 1}
                maxDepth={maxDepth}
                onUserClick={onUserClick}
              />
            ))
          )}
        </ul>
      )}
    </li>
  )
}

export function HierarchyTree({ data, variant = 'limitless', searchTerm = '', maxDepth = 2, onUserClick }: HierarchyTreeProps) {
  if (!data || data.length === 0) {
    return <div className="text-center py-12 text-red-500">No root users found</div>
  }

  return (
    <ul className={cn('tree', variant)}>
      {data.map((node) => (
        <TreeNodeComponent
          key={node.id}
          node={node}
          variant={variant}
          searchTerm={searchTerm}
          level={0}
          maxDepth={maxDepth}
          onUserClick={onUserClick}
        />
      ))}
    </ul>
  )
}
