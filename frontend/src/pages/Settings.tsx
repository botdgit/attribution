import { useState } from "react";
import Navigation from "@/components/Navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { User, Globe, Shield, Bell, Trash2, Plus, X } from "lucide-react";

const Settings = () => {
  const [sites, setSites] = useState([
    { id: 1, name: "Main Store", url: "shop.company.com", locale: "US" },
    { id: 2, name: "EU Store", url: "eu.company.com", locale: "EU" },
    { id: 3, name: "UK Store", url: "uk.company.com", locale: "UK" }
  ]);

  const [userPermissions, setUserPermissions] = useState({
    globalAdmin: true,
    siteAccess: ["1", "2"], // site IDs
    localeAccess: ["US", "EU"],
    permissions: ["view", "edit", "export"]
  });

  const handleRemoveSite = (siteId: number) => {
    setSites(sites.filter(site => site.id !== siteId));
  };

  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      
      <div className="container mx-auto px-6 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">Settings</h1>
          <p className="text-muted-foreground">Manage your account, sites, and permissions</p>
        </div>

        <Tabs defaultValue="profile" className="space-y-8">
          <TabsList className="grid w-full grid-cols-4 bg-muted/50 p-1 rounded-2xl shadow-subtle">
            <TabsTrigger value="profile" className="flex items-center space-x-2 rounded-xl transition-all duration-300 ease-out data-[state=active]:shadow-medium">
              <User className="w-4 h-4" />
              <span className="font-medium">Profile</span>
            </TabsTrigger>
            <TabsTrigger value="sites" className="flex items-center space-x-2 rounded-xl transition-all duration-300 ease-out data-[state=active]:shadow-medium">
              <Globe className="w-4 h-4" />
              <span className="font-medium">Sites & Locales</span>
            </TabsTrigger>
            <TabsTrigger value="permissions" className="flex items-center space-x-2 rounded-xl transition-all duration-300 ease-out data-[state=active]:shadow-medium">
              <Shield className="w-4 h-4" />
              <span className="font-medium">Permissions</span>
            </TabsTrigger>
            <TabsTrigger value="notifications" className="flex items-center space-x-2 rounded-xl transition-all duration-300 ease-out data-[state=active]:shadow-medium">
              <Bell className="w-4 h-4" />
              <span className="font-medium">Notifications</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="profile">
            <Card className="card-enhanced">
              <CardHeader>
                <CardTitle>Profile Information</CardTitle>
                <CardDescription>
                  Update your personal information and preferences
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="firstName">First Name</Label>
                    <Input id="firstName" defaultValue="John" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="lastName">Last Name</Label>
                    <Input id="lastName" defaultValue="Doe" />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input id="email" type="email" defaultValue="john@company.com" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="company">Company</Label>
                  <Input id="company" defaultValue="Acme Corp" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="role">Role</Label>
                  <Select defaultValue="marketing-manager">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="marketing-manager">Marketing Manager</SelectItem>
                      <SelectItem value="data-analyst">Data Analyst</SelectItem>
                      <SelectItem value="marketing-director">Marketing Director</SelectItem>
                      <SelectItem value="cmo">CMO</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Button className="bg-gradient-primary">Save Changes</Button>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="sites">
            <div className="space-y-6">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <div>
                    <CardTitle>Sites & Locales</CardTitle>
                    <CardDescription>
                      Manage your store sites and regional settings
                    </CardDescription>
                  </div>
                  <Button className="bg-gradient-primary">
                    <Plus className="w-4 h-4 mr-2" />
                    Add Site
                  </Button>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {sites.map((site) => (
                      <div key={site.id} className="flex items-center justify-between p-4 border rounded-lg">
                        <div className="flex items-center space-x-4">
                          <div>
                            <h3 className="font-medium">{site.name}</h3>
                            <p className="text-sm text-muted-foreground">{site.url}</p>
                          </div>
                          <Badge variant="secondary">{site.locale}</Badge>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Button variant="outline" size="sm">Edit</Button>
                          <Button 
                            variant="ghost" 
                            size="sm"
                            onClick={() => handleRemoveSite(site.id)}
                          >
                            <X className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Default Locale Settings</CardTitle>
                  <CardDescription>
                    Set your default locale preferences for new sites
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="defaultLocale">Default Locale</Label>
                    <Select defaultValue="US">
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="US">United States</SelectItem>
                        <SelectItem value="EU">European Union</SelectItem>
                        <SelectItem value="UK">United Kingdom</SelectItem>
                        <SelectItem value="CA">Canada</SelectItem>
                        <SelectItem value="AU">Australia</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="timezone">Timezone</Label>
                    <Select defaultValue="America/New_York">
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="America/New_York">Eastern Time (ET)</SelectItem>
                        <SelectItem value="America/Chicago">Central Time (CT)</SelectItem>
                        <SelectItem value="America/Denver">Mountain Time (MT)</SelectItem>
                        <SelectItem value="America/Los_Angeles">Pacific Time (PT)</SelectItem>
                        <SelectItem value="Europe/London">GMT</SelectItem>
                        <SelectItem value="Europe/Paris">CET</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="permissions">
            <Card>
              <CardHeader>
                <CardTitle>Access Control</CardTitle>
                <CardDescription>
                  Manage your access permissions for sites and features
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-medium">Global Administrator</h3>
                      <p className="text-sm text-muted-foreground">Full access to all sites and features</p>
                    </div>
                    <Switch checked={userPermissions.globalAdmin} />
                  </div>
                  
                  <Separator />
                  
                  <div>
                    <h3 className="font-medium mb-3">Site Access</h3>
                    <div className="space-y-2">
                      {sites.map((site) => (
                        <div key={site.id} className="flex items-center justify-between">
                          <div className="flex items-center space-x-3">
                            <span>{site.name}</span>
                            <Badge variant="outline">{site.locale}</Badge>
                          </div>
                          <Switch 
                            checked={userPermissions.siteAccess.includes(site.id.toString())}
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  <Separator />
                  
                  <div>
                    <h3 className="font-medium mb-3">Feature Permissions</h3>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span>View Attribution Data</span>
                        <Switch checked={userPermissions.permissions.includes("view")} />
                      </div>
                      <div className="flex items-center justify-between">
                        <span>Edit Models & Configuration</span>
                        <Switch checked={userPermissions.permissions.includes("edit")} />
                      </div>
                      <div className="flex items-center justify-between">
                        <span>Export Data</span>
                        <Switch checked={userPermissions.permissions.includes("export")} />
                      </div>
                      <div className="flex items-center justify-between">
                        <span>Manage Users</span>
                        <Switch checked={false} />
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="notifications">
            <Card>
              <CardHeader>
                <CardTitle>Notification Preferences</CardTitle>
                <CardDescription>
                  Choose how you want to be notified about important events
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-medium">Email Notifications</h3>
                      <p className="text-sm text-muted-foreground">Receive updates via email</p>
                    </div>
                    <Switch defaultChecked />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-medium">Attribution Alerts</h3>
                      <p className="text-sm text-muted-foreground">Get notified of significant attribution changes</p>
                    </div>
                    <Switch defaultChecked />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-medium">Export Completion</h3>
                      <p className="text-sm text-muted-foreground">Notifications when exports are ready</p>
                    </div>
                    <Switch defaultChecked />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-medium">Weekly Reports</h3>
                      <p className="text-sm text-muted-foreground">Receive weekly attribution summaries</p>
                    </div>
                    <Switch />
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default Settings;