"use client";

import React, { useState, useRef, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Send, Bot, User, Loader2, RotateCcw, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { aiAPI, ChatMessage, SPATIAL_AI_MAX_HISTORY_MESSAGES } from "@/lib/api/AIService";
import { useWorkspaceStore } from "@/lib/store";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  isError?: boolean;
  factsCount?: number;
}

interface ChatbotPanelProps {
  className?: string;
  workspaceId?: string;
  projectId?: string;
  latitude?: number;
  longitude?: number;
}

export function ChatbotPanel({
  className,
  workspaceId,
  projectId,
  latitude,
  longitude,
}: ChatbotPanelProps) {
  const { currentWorkspace } = useWorkspaceStore();
  const effectiveWorkspaceId =
    workspaceId ||
    currentWorkspace?.id ||
    (typeof window !== "undefined" ? localStorage.getItem("current_workspace_id") : null);

  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome-msg",
      role: "assistant",
      content:
        "Hello! I'm your AI GIS assistant. I can help you with spatial analysis, map insights, and property development questions. How can I assist you today?",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [lastFailedText, setLastFailedText] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const sendMessage = async (text: string, isRetry = false) => {
    const trimmed = text.trim();
    if (!trimmed || isLoading) return;

    if (!effectiveWorkspaceId) {
      const warningMessage: Message = {
        id: Date.now().toString(),
        role: "assistant",
        content:
          "Please select an active workspace in the top navigation bar to enable Spatial AI reasoning.",
        timestamp: new Date(),
        isError: true,
      };
      setMessages((prev) => [...prev, warningMessage]);
      return;
    }

    let historyPayload: ChatMessage[] = [];

    if (isRetry) {
      // Retry flow: do not duplicate user message bubble.
      // Remove any prior error bubble from the conversation
      setMessages((prev) => prev.filter((m) => !m.isError));

      // Build bounded history from successful prior turns preceding this user message
      const validPreceding = messages.filter(
        (m) => m.id !== "welcome-msg" && !m.isError
      );
      // The last element is the user turn being retried; history consists of turns before it
      const priorTurns = validPreceding.slice(0, -1);
      historyPayload = priorTurns
        .slice(-SPATIAL_AI_MAX_HISTORY_MESSAGES)
        .map((m) => ({
          role: m.role,
          content: m.content,
        }));
    } else {
      // Normal flow: create and append new user message bubble
      const userMessage: Message = {
        id: Date.now().toString(),
        role: "user",
        content: trimmed,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev.filter((m) => !m.isError), userMessage]);
      setInput("");

      // Build bounded history from all existing valid turns
      const validTurns = messages.filter(
        (m) => m.id !== "welcome-msg" && !m.isError
      );
      historyPayload = validTurns
        .slice(-SPATIAL_AI_MAX_HISTORY_MESSAGES)
        .map((m) => ({
          role: m.role,
          content: m.content,
        }));
    }

    setIsLoading(true);
    setLastFailedText(null);

    try {
      const response = await aiAPI.chat({
        workspace_id: effectiveWorkspaceId,
        project_id: projectId || undefined,
        latitude: latitude !== undefined ? latitude : undefined,
        longitude: longitude !== undefined ? longitude : undefined,
        message: trimmed,
        history: historyPayload,
      });

      const assistantText =
        response.data.answer || response.data.message || "Spatial analysis completed.";

      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: assistantText,
        timestamp: new Date(),
        factsCount: response.data.facts?.length || 0,
      };

      setMessages((prev) => [...prev, aiResponse]);
    } catch (err: any) {
      const errorDetail =
        err?.response?.data?.detail ||
        err?.message ||
        "An unexpected error occurred while communicating with the Spatial AI service.";

      const errorResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: `Error: ${errorDetail}`,
        timestamp: new Date(),
        isError: true,
      };

      setMessages((prev) => [...prev, errorResponse]);
      setLastFailedText(trimmed);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    await sendMessage(input, false);
  };

  return (
    <Card className={cn("flex flex-col h-full", className)}>
      <CardHeader className="border-b py-3 px-4 flex flex-row items-center justify-between">
        <CardTitle className="flex items-center space-x-2 text-base">
          <Bot className="h-5 w-5 text-primary" />
          <span>Spatial AI Assistant</span>
        </CardTitle>
        {!effectiveWorkspaceId && (
          <div className="flex items-center text-xs text-amber-600 bg-amber-50 dark:bg-amber-950/40 px-2 py-1 rounded">
            <AlertCircle className="h-3 w-3 mr-1" />
            <span>No workspace selected</span>
          </div>
        )}
      </CardHeader>
      <CardContent className="flex-1 flex flex-col p-0 min-h-0">
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={cn(
                "flex items-start space-x-3",
                message.role === "user" ? "justify-end" : "justify-start"
              )}
            >
              {message.role === "assistant" && (
                <div
                  className={cn(
                    "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
                    message.isError
                      ? "bg-destructive/10 text-destructive"
                      : "bg-primary/10 text-primary"
                  )}
                >
                  {message.isError ? (
                    <AlertCircle className="h-4 w-4" />
                  ) : (
                    <Bot className="h-4 w-4" />
                  )}
                </div>
              )}
              <div
                className={cn(
                  "max-w-[80%] rounded-lg px-4 py-2",
                  message.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : message.isError
                    ? "bg-destructive/10 text-destructive border border-destructive/20"
                    : "bg-muted"
                )}
              >
                <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                {message.factsCount !== undefined && message.factsCount > 0 && (
                  <p className="text-xs opacity-75 mt-1 font-medium">
                    Verified GIS Facts: {message.factsCount}
                  </p>
                )}
                <p className="text-xs opacity-70 mt-1">
                  {message.timestamp.toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </p>
              </div>
              {message.role === "user" && (
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-muted flex items-center justify-center">
                  <User className="h-4 w-4" />
                </div>
              )}
            </div>
          ))}
          {isLoading && (
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                <Bot className="h-4 w-4 text-primary" />
              </div>
              <div className="bg-muted rounded-lg px-4 py-2 flex items-center space-x-2">
                <Loader2 className="h-4 w-4 animate-spin text-primary" />
                <span className="text-xs text-muted-foreground">
                  Analyzing spatial data...
                </span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {lastFailedText && !isLoading && (
          <div className="px-4 py-2 bg-destructive/10 border-t border-destructive/20 flex items-center justify-between text-xs text-destructive">
            <span>Query failed to complete.</span>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => sendMessage(lastFailedText, true)}
              className="h-7 text-xs flex items-center space-x-1"
            >
              <RotateCcw className="h-3 w-3 mr-1" />
              Retry
            </Button>
          </div>
        )}

        <form onSubmit={handleSend} className="border-t p-4">
          <div className="flex space-x-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about spatial analysis, GIS layers, or properties..."
              className="flex-1"
              disabled={isLoading}
            />
            <Button type="submit" disabled={isLoading || !input.trim()}>
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}

/**
 * Preserved for mock demonstrations and testing purposes.
 */
export function generateMockResponse(userInput: string): string {
  const lowerInput = userInput.toLowerCase();

  if (lowerInput.includes("map") || lowerInput.includes("location")) {
    return "I can help you analyze spatial data and locations. Based on your query, I recommend checking the zoning regulations and proximity to key infrastructure. Would you like me to generate a detailed spatial analysis report?";
  }

  if (lowerInput.includes("property") || lowerInput.includes("development")) {
    return "For property development, I suggest analyzing factors like land use patterns, accessibility, and market trends. I can help you identify optimal development sites and assess potential risks. What specific aspect would you like to explore?";
  }

  if (lowerInput.includes("zoning") || lowerInput.includes("regulation")) {
    return "Zoning regulations vary by location. I can help you understand the zoning codes for specific areas, permitted uses, and development restrictions. Please provide the location or coordinates you're interested in.";
  }

  return (
    "I understand you're asking about: " +
    userInput +
    ". As your AI GIS assistant, I can help with spatial analysis, map visualization, property insights, and development planning. Could you provide more specific details about what you'd like to explore?"
  );
}
