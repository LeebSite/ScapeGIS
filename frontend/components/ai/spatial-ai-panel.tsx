"use client";

import { useState, useRef, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Send, Bot, Loader2, Download, Layers } from "lucide-react";
import { cn } from "@/lib/utils";

interface AnalysisResult {
  id: string;
  query: string;
  result: string;
  mapData?: {
    type: "3d" | "2d";
    layers: string[];
  };
  attributes?: Record<string, any>;
  timestamp: Date;
}

interface SpatialAIPanelProps {
  className?: string;
}

export function SpatialAIPanel({ className }: SpatialAIPanelProps) {
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [analysisResults, setAnalysisResults] = useState<AnalysisResult[]>([]);
  const resultsEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    resultsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [analysisResults]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const query = input;
    setInput("");
    setIsLoading(true);

    // Simulate AI analysis
    await new Promise((resolve) => setTimeout(resolve, 2000));

    const result: AnalysisResult = {
      id: Date.now().toString(),
      query,
      result: generateMockAnalysis(query),
      mapData: {
        type: "3d",
        layers: ["land_value", "market_location", "store_location"],
      },
      attributes: {
        area: "Pekanbaru",
        analysis_type: "Land Value Analysis",
        correlation: "High",
      },
      timestamp: new Date(),
    };

    setAnalysisResults((prev) => [...prev, result]);
    setIsLoading(false);
  };

  const generateMockAnalysis = (query: string): string => {
    const lowerQuery = query.toLowerCase();
    
    if (lowerQuery.includes("land value") || lowerQuery.includes("harga tanah")) {
      return "Berikut adalah hasil peta dari analisis yang disarankan, peta diperoleh dari input lokasi toko dan lokasi pasar, memberikan gambaran wilayah harga tanah yang berkorelasi dengan referensi. Juga termasuk atribut dan analisis yang dilakukan.";
    }
    
    if (lowerQuery.includes("spatial") || lowerQuery.includes("spasial")) {
      return "Analisis spasial menunjukkan pola distribusi yang menarik. Data shapefile yang tersedia menunjukkan korelasi antara lokasi strategis dan nilai properti.";
    }
    
    return "Analisis GIS telah selesai. Hasil menunjukkan pola spasial yang relevan dengan query Anda. Data atribut tersedia untuk diunduh.";
  };

  return (
    <div className={cn("flex flex-col h-full space-y-4", className)}>
      {/* AI Query Input Card */}
      <Card className="flex-shrink-0">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-semibold flex items-center space-x-2">
            <Bot className="h-4 w-4 text-primary" />
            <span>AI Spatial Analysis</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="text-sm text-muted-foreground">
            Provide deep analysis of land value in the Pekanbaru area. Use available shapefile references and display map results for that location.
          </div>
          
          {/* 3D Map Preview */}
          <div className="relative h-32 bg-gradient-to-br from-blue-100 to-green-100 rounded-lg border-2 border-primary/20 overflow-hidden">
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="grid grid-cols-4 gap-1 p-2">
                {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
                  <div
                    key={i}
                    className={cn(
                      "w-8 h-8 rounded",
                      i % 4 === 0 ? "bg-red-400" : i % 3 === 0 ? "bg-yellow-400" : i % 2 === 0 ? "bg-green-400" : "bg-blue-400"
                    )}
                  />
                ))}
              </div>
            </div>
            <div className="absolute bottom-2 left-2 text-xs font-semibold text-primary bg-background/80 px-2 py-1 rounded">
              3D Map View
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Analysis Results */}
      <div className="flex-1 overflow-y-auto space-y-4">
        {analysisResults.map((result) => (
          <Card key={result.id}>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-semibold">Analysis Result</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="text-sm text-muted-foreground">
                {result.result}
              </div>
              
              {result.mapData && (
                <div className="flex items-center space-x-2 text-xs text-muted-foreground">
                  <Layers className="h-3 w-3" />
                  <span>Layers: {result.mapData.layers.join(", ")}</span>
                </div>
              )}
              
              {result.attributes && (
                <div className="pt-2 border-t">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-muted-foreground">Attributes & Analysis</span>
                    <Button variant="ghost" size="sm" className="h-6 px-2">
                      <Download className="h-3 w-3 mr-1" />
                      <span className="text-xs">Download</span>
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
        
        {isLoading && (
          <Card>
            <CardContent className="py-4">
              <div className="flex items-center space-x-2">
                <Loader2 className="h-4 w-4 animate-spin text-primary" />
                <span className="text-sm text-muted-foreground">Analyzing spatial data...</span>
              </div>
            </CardContent>
          </Card>
        )}
        
        <div ref={resultsEndRef} />
      </div>

      {/* Input Form */}
      <Card className="flex-shrink-0">
        <CardContent className="pt-4">
          <form onSubmit={handleSubmit} className="space-y-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="type, @ for context / for command"
              className="text-sm"
              disabled={isLoading}
            />
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground">Type Here</span>
              <Button type="submit" size="sm" disabled={isLoading || !input.trim()}>
                <Send className="h-3 w-3 mr-1" />
                <span className="text-xs">Send</span>
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

