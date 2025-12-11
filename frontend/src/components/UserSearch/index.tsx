import { useState, useEffect, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search, User, Wallet, Loader2 } from 'lucide-react'
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { limitlessApi, boostyfiApi } from '@/lib/api'
import type { SearchResponse } from '@/types'

interface BaseUser {
  id: number
  username: string
  wallet: string
  referral_code: string
  children_count: number
  direct_volume: number | string
  total_earnings: number | string
}

interface UserSearchProps {
  variant: 'limitless' | 'boostyfi'
  onUserSelect: (userId: number) => void
  className?: string
}

export function UserSearch({ variant, onUserSelect, className }: UserSearchProps) {
  const [open, setOpen] = useState(false)
  const [searchValue, setSearchValue] = useState('')
  const [debouncedValue, setDebouncedValue] = useState('')

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(searchValue)
    }, 300)
    return () => clearTimeout(timer)
  }, [searchValue])

  const { data: searchResults, isLoading } = useQuery<SearchResponse<BaseUser>>({
    queryKey: [variant, 'search', debouncedValue],
    queryFn: async () => {
      if (variant === 'limitless') {
        return limitlessApi.searchUsers(debouncedValue, 15) as Promise<SearchResponse<BaseUser>>
      }
      return boostyfiApi.searchUsers(debouncedValue, 15) as Promise<SearchResponse<BaseUser>>
    },
    enabled: debouncedValue.length >= 2,
    staleTime: 30000,
  })

  const handleSelect = useCallback((userId: number) => {
    onUserSelect(userId)
    setOpen(false)
    setSearchValue('')
  }, [onUserSelect])

  const truncateWallet = (wallet: string) => {
    if (!wallet || wallet.length < 12) return wallet
    return `${wallet.slice(0, 6)}...${wallet.slice(-4)}`
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className={cn("w-full max-w-lg justify-start gap-2", className)}
        >
          <Search className="h-4 w-4 shrink-0 opacity-50" />
          <span className="text-muted-foreground">Search users by name, wallet, or code...</span>
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[400px] p-0" align="start">
        <Command shouldFilter={false}>
          <CommandInput
            placeholder="Search users..."
            value={searchValue}
            onValueChange={setSearchValue}
          />
          <CommandList>
            {isLoading && debouncedValue.length >= 2 && (
              <div className="flex items-center justify-center py-6">
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                <span className="text-sm text-muted-foreground">Searching...</span>
              </div>
            )}
            
            {!isLoading && debouncedValue.length >= 2 && searchResults?.results?.length === 0 && (
              <CommandEmpty>No users found for "{debouncedValue}"</CommandEmpty>
            )}
            
            {debouncedValue.length < 2 && (
              <div className="py-6 text-center text-sm text-muted-foreground">
                Type at least 2 characters to search
              </div>
            )}
            
            {searchResults && searchResults.results && searchResults.results.length > 0 && (
              <CommandGroup heading={`Found ${searchResults.results.length} users`}>
                {searchResults.results.map((user) => (
                  <CommandItem
                    key={user.id}
                    value={user.id.toString()}
                    onSelect={() => handleSelect(user.id)}
                    className="flex flex-col items-start gap-1 py-3 cursor-pointer"
                  >
                    <div className="flex items-center gap-2 w-full">
                      <User className="h-4 w-4 shrink-0 text-muted-foreground" />
                      <span className="font-medium">{user.username}</span>
                      {user.children_count > 0 && (
                        <Badge variant="secondary" className="ml-auto text-xs">
                          👥 {user.children_count}
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground pl-6">
                      <Wallet className="h-3 w-3" />
                      <span className="font-mono">{truncateWallet(user.wallet)}</span>
                      {user.referral_code && (
                        <>
                          <span className="mx-1">•</span>
                          <span>Code: {user.referral_code}</span>
                        </>
                      )}
                    </div>
                    {Number(user.direct_volume) > 0 && (
                      <div className="flex items-center gap-2 text-xs text-muted-foreground pl-6">
                        <span>💰 ${Number(user.direct_volume).toLocaleString()}</span>
                        {Number(user.total_earnings) > 0 && (
                          <span>📊 ${Number(user.total_earnings).toLocaleString()}</span>
                        )}
                      </div>
                    )}
                  </CommandItem>
                ))}
              </CommandGroup>
            )}
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  )
}
