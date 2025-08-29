import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import Navigation from "@/components/Navigation";
import { ArrowRight, BarChart3, Database, Upload, Brain, Target, Zap } from "lucide-react";
const Index = () => {
  const steps = [{
    number: "01",
    title: "Connect",
    description: "Integrate Shopify, marketing platforms, and import data via Adverity",
    icon: Database,
    href: "/connect",
    features: ["Shopify Integration", "Marketing Platforms", "Adverity Data Import", "Manual CSV Upload"]
  }, {
    number: "02",
    title: "Intelligence",
    description: "Configure causal models and analyze attribution patterns",
    icon: Brain,
    href: "/intelligence",
    features: ["Causal Model Config", "Attribution Analysis", "MMM Formats", "Performance Insights"]
  }, {
    number: "03",
    title: "Export",
    description: "Send insights to BigQuery, CDP, and BI tools",
    icon: Upload,
    href: "/export",
    features: ["BigQuery Export", "CDP Integration", "Tableau/Power BI", "Automated Reports"]
  }];
  return <div className="min-h-screen bg-background">
      <Navigation />
      
      {/* Hero Section */}
      <section className="bg-gradient-hero text-white">
        <div className="container mx-auto px-6 pt-32 pb-12 py-[600px]">
          <div className="max-w-4xl mx-auto text-center">
            
            <h1 className="text-5xl md:text-6xl font-bold mb-6 leading-tight py-[20px]">
              Intelligent Attribution
              <span className="block text-primary-glow">That Actually Works</span>
            </h1>
            <p className="text-xl text-white/90 mb-8 max-w-2xl mx-auto">Move beyond last-click attribution. Use causal intelligence to understand true marketing impact and optimise spend across channels.</p>
            <div className="flex items-center justify-center space-x-4">
              <Link to="/connect">
                <Button size="lg" className="shadow-strong hover:scale-105">
                  Get Started
                  <ArrowRight className="w-5 h-5 ml-2" />
                </Button>
              </Link>
              
            </div>
          </div>
        </div>
      </section>

      {/* Steps Section */}
      

      {/* Features Section */}
      <section className="py-20 bg-gradient-secondary">
        <div className="container mx-auto px-6">
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-3xl font-bold text-foreground mb-4">
                Why Choose Causal Attribution?
              </h2>
              
            </div>

            <div className="grid gap-8 md:grid-cols-1 lg:grid-cols-2">
              {[{
              icon: Brain,
              title: "Separates Correlation from Causation",
              description: "Most traditional attribution models capture correlations, not true causality. Causal inference explicitly asks: 'Did this marketing touch actually cause the outcome, or would it have happened anyway?' This prevents over-crediting marketing for conversions that would have occurred organically."
            }, {
              icon: Target,
              title: "Handles Incrementality",
              description: "The true business value of marketing is incremental lift, not just volume. Causal inference methods estimate the counterfactual: what would have happened without the campaign. This isolates the incremental impact of each channel or campaign."
            }, {
              icon: BarChart3,
              title: "Robust Against Biases",
              description: "Correlation-based models are easily distorted by seasonality, external shocks, and user selection bias. Causal inference controls for these biases by designing experiments or quasi-experiments, producing more reliable and unbiased attribution."
            }, {
              icon: Database,
              title: "Works Even Without Full Tracking Data",
              description: "With privacy regulations breaking down deterministic user-level tracking, causal methods work at an aggregate or experimental level, making them future-proof against signal loss without requiring following every user across devices."
            }, {
              icon: Zap,
              title: "Aligns with Finance & Strategy",
              description: "Finance teams think in terms of ROI and incremental profit, not just clicks and conversions. By quantifying the causal impact of spend, attribution aligns with financial rigor and helps marketing earn credibility in the boardroom."
            }, {
              icon: Upload,
              title: "Scalable Beyond A/B Testing",
              description: "While A/B testing is the gold standard for causality, it isn't always feasible everywhere. Causal inference generalizes the same principles to non-experimental data, allowing marketers to apply scientific measurement at scale."
            }].map(feature => {
              const Icon = feature.icon;
              return <div key={feature.title} className="text-center group">
                    <div className="mx-auto mb-6 w-14 h-14 bg-gradient-accent rounded-3xl flex items-center justify-center shadow-medium group-hover:shadow-strong group-hover:scale-110 transition-all duration-300 ease-out">
                      <Icon className="w-7 h-7 text-accent-foreground" />
                    </div>
                    <h3 className="text-lg font-bold text-foreground mb-3 tracking-tight">{feature.title}</h3>
                    <p className="text-muted-foreground leading-relaxed">{feature.description}</p>
                  </div>;
            })}
            </div>
          </div>
        </div>
      </section>
    </div>;
};
export default Index;