import { Link, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { BarChart3, Database, Upload, ArrowRight, Settings, LogOut, Globe, User } from "lucide-react";
import FirebaseAuth from "@/components/FirebaseAuth";
const Navigation = () => {
  const location = useLocation();
  const isHomePage = location.pathname === '/';
  const currentSite = "Main Store";
  const currentLocale = "US";
  const navItems = [{
    href: "/connect",
    label: "Connect",
    icon: Database,
    description: "Data Sources & Imports"
  }, {
    href: "/intelligence",
    label: "Intelligence",
    icon: BarChart3,
    description: "Model & Attribution"
  }, {
    href: "/export",
    label: "Export",
    icon: Upload,
    description: "BI Tools & Destinations"
  }];
  return <header className="absolute top-0 left-0 right-0 z-50">
      <div className={cn(
        "container mx-auto mt-6 backdrop-blur-md px-6 py-3 rounded-2xl max-w-6xl transition-all duration-300",
        isHomePage ? "bg-white/20" : "bg-white/95 shadow-medium"
      )}>
        <div className="flex items-center justify-between">
          

          <nav className="flex items-center space-x-1">
            {navItems.map(item => {
            const Icon = item.icon;
            const isActive = location.pathname === item.href;
            return <Link key={item.href} to={item.href}>
                  <Button variant={isActive ? "default" : "ghost"} size="default" className={cn(
                    "flex items-center space-x-3 px-5 py-3 rounded-2xl transition-all duration-300 ease-out",
                    isHomePage ? "text-white" : "text-foreground",
                    isActive && "shadow-medium scale-105"
                  )}>
                    <Icon className={cn("w-5 h-5", isHomePage ? "text-white" : "text-foreground")} />
                    <div className="text-left hidden md:block">
                      <div className="text-sm font-semibold">{item.label}</div>
                      <div className="text-xs opacity-75 font-medium">{item.description}</div>
                    </div>
                  </Button>
                </Link>;
          })}
          </nav>

          <div className="flex items-center space-x-4">
            {/* Site/Locale Selector */}
            <div className="hidden lg:flex items-center space-x-3">
              <Select defaultValue={currentSite}>
                <SelectTrigger className={cn(
                  "w-36 rounded-full border-border/50 shadow-subtle hover:shadow-medium transition-all duration-300 ease-out",
                  isHomePage ? "bg-card/50 text-white" : "bg-background text-foreground"
                )}>
                  <Globe className={cn("w-4 h-4 mr-2", isHomePage ? "text-white" : "text-foreground")} />
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="rounded-2xl shadow-strong border border-border/50">
                  <SelectItem value="Main Store">Main Store</SelectItem>
                  <SelectItem value="EU Store">EU Store</SelectItem>
                  <SelectItem value="UK Store">UK Store</SelectItem>
                </SelectContent>
              </Select>
              <Select defaultValue={currentLocale}>
                <SelectTrigger className={cn(
                  "w-24 rounded-full border-border/50 shadow-subtle hover:shadow-medium transition-all duration-300 ease-out",
                  isHomePage ? "bg-card/50 text-white" : "bg-background text-foreground"
                )}>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="rounded-2xl shadow-strong border border-border/50">
                  <SelectItem value="US">US</SelectItem>
                  <SelectItem value="EU">EU</SelectItem>
                  <SelectItem value="UK">UK</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Firebase Auth UI */}
            <FirebaseAuth />
          </div>
        </div>
      </div>
    </header>;
};
export default Navigation;