import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import Navigation from "@/components/Navigation";
import FileUpload from "@/components/FileUpload";
import { ShoppingBag, Database, Upload, CheckCircle, Plus, Settings, FileSpreadsheet, Globe } from "lucide-react";
const Connect = () => {
  const integrations = [{
    name: "Shopify",
    icon: ShoppingBag,
    status: "connected",
    description: "E-commerce data and transactions",
    metrics: "1.2M orders • 45K customers"
  }, {
    name: "Google Analytics",
    icon: Globe,
    status: "pending",
    description: "Website traffic and user behavior",
    metrics: "Setup required"
  }, {
    name: "Facebook Ads",
    icon: Database,
    status: "available",
    description: "Advertising spend and performance",
    metrics: "Ready to connect"
  }, {
    name: "Google Ads",
    icon: Database,
    status: "available",
    description: "Search advertising data",
    metrics: "Ready to connect"
  }];
  const getStatusColor = (status: string) => {
    switch (status) {
      case "connected":
        return "bg-accent text-accent-foreground";
      case "pending":
        return "bg-yellow-100 text-yellow-800";
      default:
        return "bg-muted text-muted-foreground";
    }
  };
  const getStatusIcon = (status: string) => {
    return status === "connected" ? CheckCircle : Plus;
  };
  // Shopify OAuth handler
  const handleShopifyConnect = () => {
    const shop = prompt("Enter your Shopify store name (e.g. mystore)");
    if (!shop) return;
    const shopifyApiKey = import.meta.env.VITE_SHOPIFY_API_KEY;
    const redirectUri = `${window.location.origin}/shopify/callback`;
    const scopes = "read_orders,read_customers,read_products";
    const oauthUrl = `https://${shop}.myshopify.com/admin/oauth/authorize?client_id=${shopifyApiKey}&scope=${scopes}&redirect_uri=${encodeURIComponent(redirectUri)}&response_type=code`;
    window.location.href = oauthUrl;
  };
  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      <main className="container mx-auto px-6 pt-28 pb-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">Connect Data Sources</h1>
          <p className="text-muted-foreground">
            Integrate your marketing and e-commerce platforms to enable causal attribution analysis.
          </p>
        </div>
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Platform Integrations */}
          <div className="space-y-6">
            <Card className="shadow-soft">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Database className="w-5 h-5" />
                  <span>Platform Integrations</span>
                </CardTitle>
                <CardDescription>
                  Connect your marketing and e-commerce platforms
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {integrations.map(integration => {
                  const Icon = integration.icon;
                  const StatusIcon = getStatusIcon(integration.status);
                  const isShopify = integration.name === "Shopify";
                  return (
                    <div key={integration.name} className="flex items-center justify-between p-4 border rounded-lg hover:shadow-medium transition-smooth">
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-gradient-secondary rounded-lg flex items-center justify-center">
                          <Icon className="w-5 h-5 text-primary" />
                        </div>
                        <div>
                          <div className="flex items-center space-x-2">
                            <h3 className="font-medium text-foreground">{integration.name}</h3>
                            <Badge className={getStatusColor(integration.status)}>
                              {integration.status}
                            </Badge>
                          </div>
                          <p className="text-sm text-muted-foreground">{integration.description}</p>
                          <p className="text-xs text-muted-foreground">{integration.metrics}</p>
                        </div>
                      </div>
                      {isShopify ? (
                        <Button variant="default" size="sm" className="flex items-center space-x-1" onClick={handleShopifyConnect}>
                          <StatusIcon className="w-4 h-4" />
                          <span>Connect</span>
                        </Button>
                      ) : (
                        <Button variant={integration.status === "connected" ? "outline" : "default"} size="sm" className="flex items-center space-x-1">
                          <StatusIcon className="w-4 h-4" />
                          <span>{integration.status === "connected" ? "Configure" : "Connect"}</span>
                        </Button>
                      )}
                    </div>
                  );
                })}
              </CardContent>
            </Card>
          </div>
          {/* Adverity & Manual Imports */}
          <div className="space-y-6">
            <Card className="shadow-soft">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <FileSpreadsheet className="w-5 h-5" />
                  <span>Manual Data Import</span>
                </CardTitle>
                <CardDescription>
                  Upload CSV files or custom data sources
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="px-2">
                  <FileUpload />
                </div>
                <div className="mt-4">
                  <h4 className="font-medium text-foreground mb-2">Supported Formats</h4>
                  <div className="flex flex-wrap gap-2">
                    {["CSV", "Excel", "JSON", "Parquet"].map(format => <Badge key={format} variant="outline">{format}</Badge>)}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
export default Connect;