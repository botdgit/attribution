import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import Navigation from "@/components/Navigation";
import { Brain, TrendingUp, Target, Settings, Play, BarChart3, PieChart, Activity, CheckCircle, Clock, Zap } from "lucide-react";
const Intelligence = () => {
  const modelStats = [{
    label: "Data Quality Score",
    value: 94,
    color: "bg-accent"
  }, {
    label: "Attribution Confidence",
    value: 87,
    color: "bg-primary"
  }, {
    label: "Model Accuracy",
    value: 91,
    color: "bg-gradient-accent"
  }];
  const attributionResults = [{
    channel: "Paid Search",
    attribution: 34.2,
    change: "+5.3%"
  }, {
    channel: "Social Media",
    attribution: 28.7,
    change: "+2.1%"
  }, {
    channel: "Email",
    attribution: 19.4,
    change: "-1.2%"
  }, {
    channel: "Display",
    attribution: 11.2,
    change: "+0.8%"
  }, {
    channel: "Direct",
    attribution: 6.5,
    change: "-0.4%"
  }];
  return <div className="min-h-screen bg-background">
      <Navigation />
      
      <main className="container mx-auto px-6 pt-28 pb-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">Attribution Intelligence</h1>
          <p className="text-muted-foreground">Configure causal models, analyse attribution patterns and optimise marketing performance.</p>
        </div>

        <Tabs defaultValue="configure" className="space-y-6">
          <TabsList className="grid w-fit grid-cols-3 bg-muted">
            <TabsTrigger value="configure" className="flex items-center space-x-2">
              <Settings className="w-4 h-4" />
              <span>Configure Model</span>
            </TabsTrigger>
            <TabsTrigger value="attribution" className="flex items-center space-x-2">
              <Target className="w-4 h-4" />
              <span>Attribution Analysis</span>
            </TabsTrigger>
            <TabsTrigger value="mmm" className="flex items-center space-x-2">
              <BarChart3 className="w-4 h-4" />
              <span>Custom Reports</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="configure" className="space-y-6">
            <div className="grid gap-6 lg:grid-cols-3">
              <div className="lg:col-span-2 space-y-6">
                <Card className="shadow-soft">
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <Brain className="w-5 h-5" />
                      <span>Causal Model Configuration</span>
                    </CardTitle>
                    <CardDescription>
                      Define causal relationships and attribution windows
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="space-y-2">
                        <label className="text-sm font-medium text-foreground">Attribution Window</label>
                        <div className="flex space-x-2">
                          {["7 days", "14 days", "30 days", "90 days"].map(window => <Button key={window} variant={window === "30 days" ? "default" : "outline"} size="sm">
                              {window}
                            </Button>)}
                        </div>
                      </div>
                      <div className="space-y-2">
                        <label className="text-sm font-medium text-foreground">Model Type</label>
                        <div className="flex space-x-2">
                          {["First-touch", "Last-touch", "Multi-touch", "Causal"].map(type => <Button key={type} variant={type === "Causal" ? "default" : "outline"} size="sm">
                              {type}
                            </Button>)}
                        </div>
                      </div>
                    </div>

                    <div className="border-t pt-4">
                      <h4 className="font-medium text-foreground mb-3">Channel Weightings</h4>
                      <div className="space-y-3">
                        {["Paid Search", "Social Media", "Email", "Display"].map(channel => <div key={channel} className="flex items-center justify-between">
                            <span className="text-sm text-foreground">{channel}</span>
                            <div className="flex items-center space-x-2">
                              <Progress value={Math.random() * 100} className="w-24" />
                              <span className="text-sm text-muted-foreground w-12 text-right">
                                {Math.floor(Math.random() * 40 + 10)}%
                              </span>
                            </div>
                          </div>)}
                      </div>
                    </div>

                    <div className="flex items-center space-x-2 pt-4">
                      <Button className="bg-gradient-primary">
                        <Play className="w-4 h-4 mr-1" />
                        Run Analysis
                      </Button>
                      <Button variant="outline">Save Configuration</Button>
                    </div>
                  </CardContent>
                </Card>
              </div>

              <div className="space-y-6">
                <Card className="shadow-soft">
                  <CardHeader>
                    <CardTitle className="text-lg">Model Performance</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {modelStats.map(stat => <div key={stat.label} className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-foreground">{stat.label}</span>
                          <span className="text-sm font-medium text-foreground">{stat.value}%</span>
                        </div>
                        <Progress value={stat.value} className="h-2" />
                      </div>)}
                  </CardContent>
                </Card>

                <Card className="shadow-soft">
                  <CardHeader>
                    <CardTitle className="text-lg">Recent Jobs</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {[{
                    name: "Q4 Attribution",
                    status: "completed",
                    time: "2 hours ago"
                  }, {
                    name: "Holiday Campaign",
                    status: "running",
                    time: "In progress"
                  }, {
                    name: "MMM Analysis",
                    status: "queued",
                    time: "Pending"
                  }].map(job => <div key={job.name} className="flex items-center space-x-3">
                        {job.status === "completed" && <CheckCircle className="w-4 h-4 text-accent" />}
                        {job.status === "running" && <Activity className="w-4 h-4 text-primary animate-pulse" />}
                        {job.status === "queued" && <Clock className="w-4 h-4 text-muted-foreground" />}
                        <div>
                          <p className="text-sm font-medium text-foreground">{job.name}</p>
                          <p className="text-xs text-muted-foreground">{job.time}</p>
                        </div>
                      </div>)}
                  </CardContent>
                </Card>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="attribution" className="space-y-6">
            <div className="grid gap-6 lg:grid-cols-3">
              <div className="lg:col-span-2">
                <Card className="shadow-soft">
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <TrendingUp className="w-5 h-5" />
                      <span>Attribution Results</span>
                    </CardTitle>
                    <CardDescription>
                      Cross-channel attribution analysis for the last 30 days
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {attributionResults.map(result => <div key={result.channel} className="flex items-center justify-between p-3 border rounded-lg">
                          <div className="flex items-center space-x-3">
                            <div className="w-3 h-3 bg-gradient-primary rounded-full"></div>
                            <span className="font-medium text-foreground">{result.channel}</span>
                          </div>
                          <div className="flex items-center space-x-4">
                            <span className="text-lg font-bold text-foreground">{result.attribution}%</span>
                            <Badge variant={result.change.startsWith('+') ? 'default' : 'secondary'} className={result.change.startsWith('+') ? 'bg-accent text-accent-foreground' : ''}>
                              {result.change}
                            </Badge>
                          </div>
                        </div>)}
                    </div>

                    <div className="mt-6 p-4 bg-gradient-secondary rounded-lg">
                      <div className="flex items-center space-x-2 mb-2">
                        <Zap className="w-4 h-4 text-primary" />
                        <span className="font-medium text-foreground">Key Insights</span>
                      </div>
                      <ul className="text-sm text-muted-foreground space-y-1">
                        <li>• Paid Search shows strongest incremental lift (+5.3%)</li>
                        <li>• Social Media attribution increased with new creative formats</li>
                        <li>• Consider reallocating budget from Email to high-performing channels</li>
                      </ul>
                    </div>
                  </CardContent>
                </Card>
              </div>

              <div>
                <Card className="shadow-soft">
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <PieChart className="w-5 h-5" />
                      <span>Channel Mix</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="h-32 bg-gradient-secondary rounded-lg flex items-center justify-center">
                        <PieChart className="w-12 h-12 text-primary opacity-50" />
                      </div>
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">Total Revenue Attributed</span>
                          <span className="font-medium text-foreground">$2.4M</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">Confidence Score</span>
                          <span className="font-medium text-foreground">87%</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">Data Coverage</span>
                          <span className="font-medium text-foreground">94%</span>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="mmm" className="space-y-6">
            <div className="grid gap-6 lg:grid-cols-2">
              <Card className="shadow-soft">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <BarChart3 className="w-5 h-5" />
                    <span>Custom Reports</span>
                  </CardTitle>
                  <CardDescription>
                    Advanced statistical models for marketing effectiveness
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid gap-3 md:grid-cols-2">
                    {["Adstock Models", "Saturation Curves", "Base vs. Incremental", "Seasonality Effects"].map(model => <div key={model} className="p-3 border rounded-lg hover:shadow-medium transition-smooth">
                        <h4 className="font-medium text-foreground mb-1">{model}</h4>
                        <p className="text-xs text-muted-foreground">Advanced modeling technique</p>
                        <div className="mt-2">
                          <Badge variant="outline" className="text-xs">Configured</Badge>
                        </div>
                      </div>)}
                  </div>

                  <div className="border-t pt-4">
                    <Button className="w-full bg-gradient-primary">
                      <Play className="w-4 h-4 mr-1" />
                      Generate Report
                    </Button>
                  </div>
                </CardContent>
              </Card>

              <Card className="shadow-soft">
                <CardHeader>
                  <CardTitle>Export Formats</CardTitle>
                  <CardDescription>Choose output format for your analysis</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {[{
                  format: "Executive Summary",
                  desc: "High-level insights and recommendations"
                }, {
                  format: "Technical Report",
                  desc: "Detailed statistical analysis"
                }, {
                  format: "Data Export",
                  desc: "Raw coefficients and model outputs"
                }, {
                  format: "Visualisation Pack",
                  desc: "Charts and interactive dashboards"
                }].map(item => <div key={item.format} className="flex items-center justify-between p-3 border rounded-lg">
                      <div>
                        <h4 className="font-medium text-foreground">{item.format}</h4>
                        <p className="text-xs text-muted-foreground">{item.desc}</p>
                      </div>
                      <Button variant="outline" size="sm">Select</Button>
                    </div>)}
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </main>
    </div>;
};
export default Intelligence;