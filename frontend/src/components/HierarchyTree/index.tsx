import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Badge } from '@/components/ui/badge'
import { cn, shortWallet } from '@/lib/utils'
import { Loader2, ChevronDown, ChevronRight } from 'lucide-react'
import { limitlessApi, boostyfiApi } from '@/lib/api'
import type { LimitlessUserTree, BoostyFiUserTree } from '@/types'
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


  const handleToggleExpand = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (hasChildren) {
      setIsExpanded(!isExpanded)
    }
  }

  const handleNodeClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (onUserClick) {
      onUserClick(node.id)
    }
  }

  return (
    <li>
      <div
        className={cn(
          'node-box',
          hasChildren && 'has-children',
          isHighlighted && 'highlighted',
          variant
        )}
        data-level={level}
      >
        {/* Expand/Collapse button */}
        {hasChildren && (
          <button
            onClick={handleToggleExpand}
            className="expand-toggle-btn"
            title={isExpanded ? 'Свернуть' : 'Развернуть'}
          >
            {childrenLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : isExpanded ? (
              <ChevronDown className="w-4 h-4" />
            ) : (
              <ChevronRight className="w-4 h-4" />
            )}
          </button>
        )}
        
        {/* Clickable node content */}
        <div className="node-content" onClick={handleNodeClick}>
          <span className="node-username">{node.username || `User ${node.original_id}`}</span>
          <span className="node-wallet">{shortWallet(node.wallet)}</span>
          <div className="node-badges">
            {/* Team Contribution - общий объем команды */}
            <Badge variant="default" className="text-xs">
              📊 ${Number(node.team_volume || 0).toFixed(0)}
            </Badge>
            {/* Purchases - личные покупки */}
            {Number(node.direct_volume) > 0 && (
              <Badge variant="success" className="text-xs">
                💰 ${Number(node.direct_volume).toFixed(0)}
              </Badge>
            )}
            {/* Direct Referrals - количество рефералов */}
            {childrenCount > 0 && (
              <Badge variant="secondary" className="text-xs">
                👥 {childrenCount}
              </Badge>
            )}
            {/* Assigned Sellers - селлеры, управляющие этим кошельком */}
            {node.assigned_sellers && node.assigned_sellers.length > 0 && (
              <Badge variant="outline" className="text-xs bg-amber-500/10 text-amber-600 border-amber-500/30">
                🏷️ {node.assigned_sellers.map(s => s.seller_name).join(', ')}
              </Badge>
            )}
          </div>
        </div>
      </div>

      {/* Children */}
      {hasChildren && isExpanded && !childrenLoading && loadedChildren.length > 0 && (
        <ul className="children-list">
          {loadedChildren.map((child) => (
            <TreeNodeComponent
              key={child.id}
              node={child}
              variant={variant}
              searchTerm={searchTerm}
              level={level + 1}
              maxDepth={maxDepth}
              onUserClick={onUserClick}
            />
          ))}
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
