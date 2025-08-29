import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Switch } from "@/components/ui/switch";
import Navigation from "@/components/Navigation";
import { 
  Database, 
  BarChart3, 
  Upload, 
  Settings, 
  CheckCircle,
  Clock,
  Zap,
  Download,
  Share,
  Calendar,
  Users
} from "lucide-react";

const Export = () => {
  const destinations = [
    {
      name: "Google BigQuery",
      icon: Database,
      status: "connected",
      description: "Data warehouse for advanced analytics",
      lastSync: "2 hours ago"
    },
    {
      name: "Tableau",
      icon: BarChart3,
      status: "connected",
      description: "Interactive visualisation platform",
      lastSync: "1 hour ago"
    },
    {
      name: "Power BI",
      icon: BarChart3,
      status: "available",
      description: "Microsoft business intelligence",
      lastSync: "Not connected"
    },
    {
      name: "Looker Studio",
      icon: BarChart3,
      status: "available",
      description: "Google's data visualisation tool",
      lastSync: "Not connected"
    },
    {
      name: "Salesforce CDP",
      icon: Users,
      status: "pending",
      description: "Customer data platform integration",
      lastSync: "Configuration needed"
    }
  ];

  const exportFormats = [
    { name: "Attribution Reports", size: "2.4 MB", lastGenerated: "30 min ago", status: "ready" },
    { name: "MMM Analysis", size: "5.1 MB", lastGenerated: "2 hours ago", status: "ready" },
    { name: "Channel Performance", size: "1.8 MB", lastGenerated: "1 day ago", status: "generating" },
    { name: "Executive Dashboard", size: "890 KB", lastGenerated: "3 hours ago", status: "ready" }
  ];

  const schedules = [
    { name: "Daily Attribution Updates", frequency: "Every day at 6:00 AM", active: true },
    { name: "Weekly MMM Reports", frequency: "Mondays at 9:00 AM", active: true },
    { name: "Monthly Executive Summary", frequency: "1st of each month", active: false },
    { name: "Real-time Channel Updates", frequency: "Every 15 minutes", active: true }
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case "connected": return "bg-accent text-accent-foreground";
      case "pending": return "bg-yellow-100 text-yellow-800";
      case "ready": return "bg-accent text-accent-foreground";
      case "generating": return "bg-blue-100 text-blue-800";
      default: return "bg-muted text-muted-foreground";
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      
      <main className="container mx-auto px-6 pt-28 pb-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">Export & Distribution</h1>
          <p className="text-muted-foreground">
            Send attribution insights to your BI tools, data warehouse, and business applications.
          </p>
        </div>

        <Tabs defaultValue="destinations" className="space-y-6">
          <TabsList className="grid w-fit grid-cols-3 bg-muted">
            <TabsTrigger value="destinations" className="flex items-center space-x-2">
              <Database className="w-4 h-4" />
              <span>Destinations</span>
            </TabsTrigger>
            <TabsTrigger value="exports" className="flex items-center space-x-2">
              <Download className="w-4 h-4" />
              <span>Export Center</span>
            </TabsTrigger>
            <TabsTrigger value="automation" className="flex items-center space-x-2">
              <Calendar className="w-4 h-4" />
              <span>Automation</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="destinations" className="space-y-6">
            <div className="grid gap-6 lg:grid-cols-2">
              <div className="space-y-6">
                <Card className="shadow-soft">
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <Database className="w-5 h-5" />
                      <span>Data Warehouses</span>
                    </CardTitle>
                    <CardDescription>
                      Send attribution data to your data warehouse
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {destinations.filter(d => d.icon === Database).map((destination) => {
                      const Icon = destination.icon;
                      
                      return (
                        <div 
                          key={destination.name}
                          className="flex items-center justify-between p-4 border rounded-lg hover:shadow-medium transition-smooth"
                        >
                          <div className="flex items-center space-x-3">
                            <div className="w-10 h-10 bg-gradient-secondary rounded-lg flex items-center justify-center">
                              <Icon className="w-5 h-5 text-primary" />
                            </div>
                            <div>
                              <div className="flex items-center space-x-2">
                                <h3 className="font-medium text-foreground">{destination.name}</h3>
                                <Badge className={getStatusColor(destination.status)}>
                                  {destination.status}
                                </Badge>
                              </div>
                              <p className="text-sm text-muted-foreground">{destination.description}</p>
                              <p className="text-xs text-muted-foreground">Last sync: {destination.lastSync}</p>
                            </div>
                          </div>
                          <Button 
                            variant={destination.status === "connected" ? "outline" : "default"}
                            size="sm"
                          >
                            {destination.status === "connected" ? "Configure" : "Connect"}
                          </Button>
                        </div>
                      );
                    })}
                  </CardContent>
                </Card>

                <Card className="shadow-soft">
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <Users className="w-5 h-5" />
                      <span>Customer Data Platforms</span>
                    </CardTitle>
                    <CardDescription>
                      Integrate with CDP for customer journey insights
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {destinations.filter(d => d.icon === Users).map((destination) => {
                      const Icon = destination.icon;
                      
                      return (
                        <div 
                          key={destination.name}
                          className="flex items-center justify-between p-4 border rounded-lg"
                        >
                          <div className="flex items-center space-x-3">
                            <div className="w-10 h-10 bg-gradient-secondary rounded-lg flex items-center justify-center">
                              <Icon className="w-5 h-5 text-primary" />
                            </div>
                            <div>
                              <div className="flex items-center space-x-2">
                                <h3 className="font-medium text-foreground">{destination.name}</h3>
                                <Badge className={getStatusColor(destination.status)}>
                                  {destination.status}
                                </Badge>
                              </div>
                              <p className="text-sm text-muted-foreground">{destination.description}</p>
                            </div>
                          </div>
                          <Button size="sm">Setup</Button>
                        </div>
                      );
                    })}
                  </CardContent>
                </Card>
              </div>

              <div className="space-y-6">
                <Card className="shadow-soft">
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <BarChart3 className="w-5 h-5" />
                      <span>BI & Visualisation Tools</span>
                    </CardTitle>
                    <CardDescription>
                      Create dashboards and reports in your BI platform
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {destinations.filter(d => d.icon === BarChart3).map((destination) => {
                      const Icon = destination.icon;
                      
                      return (
                        <div 
                          key={destination.name}
                          className="flex items-center justify-between p-4 border rounded-lg hover:shadow-medium transition-smooth"
                        >
                          <div className="flex items-center space-x-3">
                            <div className="w-10 h-10 bg-gradient-secondary rounded-lg flex items-center justify-center">
                              <Icon className="w-5 h-5 text-primary" />
                            </div>
                            <div>
                              <div className="flex items-center space-x-2">
                                <h3 className="font-medium text-foreground">{destination.name}</h3>
                                <Badge className={getStatusColor(destination.status)}>
                                  {destination.status}
                                </Badge>
                              </div>
                              <p className="text-sm text-muted-foreground">{destination.description}</p>
                              <p className="text-xs text-muted-foreground">Last sync: {destination.lastSync}</p>
                            </div>
                          </div>
                          <Button 
                            variant={destination.status === "connected" ? "outline" : "default"}
                            size="sm"
                          >
                            {destination.status === "connected" ? "View" : "Connect"}
                          </Button>
                        </div>
                      );
                    })}
                  </CardContent>
                </Card>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="exports" className="space-y-6">
            <div className="grid gap-6 lg:grid-cols-3">
              <div className="lg:col-span-2">
                <Card className="shadow-soft">
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <Download className="w-5 h-5" />
                      <span>Ready Exports</span>
                    </CardTitle>
                    <CardDescription>
                      Download or share your attribution reports
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {exportFormats.map((export_) => (
                      <div 
                        key={export_.name}
                        className="flex items-center justify-between p-4 border rounded-lg hover:shadow-medium transition-smooth"
                      >
                        <div className="flex items-center space-x-3">
                          <div className="w-10 h-10 bg-gradient-secondary rounded-lg flex items-center justify-center">
                            {export_.status === "ready" ? (
                              <CheckCircle className="w-5 h-5 text-accent" />
                            ) : (
                              <Clock className="w-5 h-5 text-primary animate-pulse" />
                            )}
                          </div>
                          <div>
                            <div className="flex items-center space-x-2">
                              <h3 className="font-medium text-foreground">{export_.name}</h3>
                              <Badge className={getStatusColor(export_.status)}>
                                {export_.status}
                              </Badge>
                            </div>
                            <p className="text-sm text-muted-foreground">
                              {export_.size} • Generated {export_.lastGenerated}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Button variant="outline" size="sm" disabled={export_.status !== "ready"}>
                            <Share className="w-4 h-4 mr-1" />
                            Share
                          </Button>
                          <Button size="sm" disabled={export_.status !== "ready"}>
                            <Download className="w-4 h-4 mr-1" />
                            Download
                          </Button>
                        </div>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              </div>

              <div>
                <Card className="shadow-soft">
                  <CardHeader>
                    <CardTitle>Export Settings</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-foreground">Include raw data</span>
                        <Switch defaultChecked />
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-foreground">Anonymize PII</span>
                        <Switch defaultChecked />
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-foreground">Compress files</span>
                        <Switch />
                      </div>
                    </div>

                    <div className="border-t pt-4">
                      <Button className="w-full bg-gradient-primary">
                        <Upload className="w-4 h-4 mr-1" />
                        Generate New Export
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="automation" className="space-y-6">
            <Card className="shadow-soft">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Calendar className="w-5 h-5" />
                  <span>Scheduled Exports</span>
                </CardTitle>
                <CardDescription>
                  Automate attribution data delivery to your tools
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {schedules.map((schedule) => (
                  <div 
                    key={schedule.name}
                    className="flex items-center justify-between p-4 border rounded-lg hover:shadow-medium transition-smooth"
                  >
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-gradient-secondary rounded-lg flex items-center justify-center">
                        <Calendar className="w-5 h-5 text-primary" />
                      </div>
                      <div>
                        <h3 className="font-medium text-foreground">{schedule.name}</h3>
                        <p className="text-sm text-muted-foreground">{schedule.frequency}</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-3">
                      <Switch checked={schedule.active} />
                      <Button variant="outline" size="sm">
                        <Settings className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                ))}

                <div className="border-t pt-4">
                  <Button variant="outline" className="w-full">
                    <Zap className="w-4 h-4 mr-1" />
                    Create New Schedule
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
};

export default Export;