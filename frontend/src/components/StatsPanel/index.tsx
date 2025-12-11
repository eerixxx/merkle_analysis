import { Card, CardContent } from '@/components/ui/card'
import type { LucideIcon } from 'lucide-react'

interface StatCard {
  title: string
  value: string | number
  icon: LucideIcon
}

interface StatsPanelProps {
  stats: StatCard[]
  isLoading?: boolean
}

export function StatsPanel({ stats, isLoading }: StatsPanelProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 mb-8">
        {[...Array(5)].map((_, i) => (
          <Card key={i} className="bg-card border-border animate-pulse">
            <CardContent className="p-5 text-center">
              <div className="h-4 bg-muted rounded mb-2" />
              <div className="h-8 bg-muted rounded" />
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 mb-8">
      {stats.map((stat, index) => {
        const Icon = stat.icon
        return (
          <Card key={index} className="bg-card border-border hover:bg-accent transition-colors">
            <CardContent className="p-5 text-center">
              <div className="flex items-center justify-center gap-2 mb-2 text-muted-foreground">
                <Icon className="w-4 h-4" />
                <span className="text-sm font-medium">{stat.title}</span>
              </div>
              <div className="text-2xl font-bold text-foreground">{stat.value}</div>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}
