import { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import Navigation from "@/components/Navigation";
import { CheckCircle, Loader2 } from "lucide-react";

const ShopifyCallback = () => {
  const [status, setStatus] = useState<"loading"|"success"|"error">("loading");
  const [message, setMessage] = useState<string>("Finishing Shopify connection...");
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  useEffect(() => {
    // The backend already exchanged the code and redirected here with ?shop=
    const shop = searchParams.get("shop");
    if (!shop) {
      setStatus("error");
      setMessage("Missing shop parameter.");
      return;
    }
    setStatus("success");
    setMessage(`Shopify store ${shop} connected successfully.`);
    const t = setTimeout(() => navigate("/connect"), 2500);
    return () => clearTimeout(t);
  }, [searchParams, navigate]);

  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      <main className="container mx-auto px-6 pt-40 flex flex-col items-center text-center">
        {status === "loading" && <Loader2 className="w-12 h-12 animate-spin text-primary mb-4" />}
        {status === "success" && <CheckCircle className="w-12 h-12 text-green-500 mb-4" />}
        <h1 className="text-2xl font-semibold mb-2">Shopify Integration</h1>
        <p className="text-muted-foreground max-w-md">{message}</p>
      </main>
    </div>
  );
};

export default ShopifyCallback;
