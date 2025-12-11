import { Link } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ModeToggle } from '@/components/mode-toggle'
import { Rocket, Gem, ArrowRight } from 'lucide-react'

export function HomePage() {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-5 relative">
      {/* Theme Toggle */}
      <div className="absolute top-4 right-4">
        <ModeToggle />
      </div>
      
      <div className="text-center max-w-4xl">
        <h1 className="text-5xl font-bold text-foreground mb-4">
          Merkle Viewer
        </h1>
        <p className="text-muted-foreground text-lg mb-12">
          Choose a project to explore its user hierarchy tree
        </p>
        
        <div className="flex gap-6 justify-center flex-wrap">
          {/* Limitless Card */}
          <Link to="/limitless" className="group">
            <Card className="w-80 border border-border bg-card hover:bg-accent transition-all duration-300 hover:-translate-y-2 hover:shadow-xl">
              <CardHeader className="text-center pb-2">
                <div className="mb-4 group-hover:scale-110 transition-transform">
                  <div className="w-16 h-16 mx-auto rounded-full bg-violet-500/10 flex items-center justify-center">
                    <Rocket className="w-8 h-8 text-violet-500" />
                  </div>
                </div>
                <CardTitle className="text-2xl">Limitless</CardTitle>
                <CardDescription>
                  Explore the Limitless user tree with purchases, earnings, and team volumes.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex justify-around border-t border-border pt-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-foreground">2.8K+</div>
                    <div className="text-xs text-muted-foreground uppercase">Users</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-foreground">5.5K+</div>
                    <div className="text-xs text-muted-foreground uppercase">Earnings</div>
                  </div>
                </div>
              </CardContent>
              <CardFooter className="justify-center pb-6">
                <Button className="rounded-full px-8 gap-2">
                  View Tree
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </CardFooter>
            </Card>
          </Link>
          
          {/* BoostyFi Card */}
          <Link to="/boostyfi" className="group">
            <Card className="w-80 border border-border bg-card hover:bg-accent transition-all duration-300 hover:-translate-y-2 hover:shadow-xl">
              <CardHeader className="text-center pb-2">
                <div className="mb-4 group-hover:scale-110 transition-transform">
                  <div className="w-16 h-16 mx-auto rounded-full bg-emerald-500/10 flex items-center justify-center">
                    <Gem className="w-8 h-8 text-emerald-500" />
                  </div>
                </div>
                <CardTitle className="text-2xl">BoostyFi</CardTitle>
                <CardDescription>
                  Explore the BoostyFi user tree with ATLA balances, multi-system earnings.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex justify-around border-t border-border pt-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-foreground">27K+</div>
                    <div className="text-xs text-muted-foreground uppercase">Users</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-foreground">3.1K+</div>
                    <div className="text-xs text-muted-foreground uppercase">Earnings</div>
                  </div>
                </div>
              </CardContent>
              <CardFooter className="justify-center pb-6">
                <Button className="rounded-full px-8 gap-2">
                  View Tree
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </CardFooter>
            </Card>
          </Link>
        </div>
        
        <footer className="mt-16 text-muted-foreground text-sm">
          ATOM Merkle Viewer v.0.12 - alpha
        </footer>
      </div>
    </div>
  )
}
