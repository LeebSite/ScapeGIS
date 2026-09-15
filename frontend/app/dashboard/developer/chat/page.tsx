"use client";

import { ChatbotPanel } from "@/components/ai/chatbot-panel";

export default function ChatPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">AI Assistant</h2>
        <p className="text-muted-foreground">
          Get instant insights and recommendations from our AI-powered GIS assistant
        </p>
      </div>

      <div className="h-[calc(100vh-280px)]">
        <ChatbotPanel className="h-full" />
      </div>
    </div>
  );
}

