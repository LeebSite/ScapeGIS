"use client";

import React, { useMemo, useRef, useState } from "react";
import { useAuthStore } from "@/lib/store";
import type { Subscription } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Info } from "lucide-react";

type Role = "user" | "assistant";

interface Message {
  id: string;
  role: Role;
  text: string;
  time?: string;
}

function hasActiveSubscription(sub?: Subscription | null) {
  return !!sub && sub.status === "active";
}

export default function ChatUI() {
  const { user } = useAuthStore();
  const enabled = useMemo(() => hasActiveSubscription(user?.subscription ?? null), [user]);

  const [messages, setMessages] = useState<Message[]>([
    {
      id: "m1",
      role: "assistant",
      text: "Welcome. Please provide the details of the data or analysis you require.",
      time: new Date().toISOString(),
    },
  ]);

  const [prompt, setPrompt] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const listRef = useRef<HTMLDivElement | null>(null);

  const scrollToBottom = () => {
    if (!listRef.current) return;
    listRef.current.scrollTop = listRef.current.scrollHeight;
  };

  const sendPrompt = async () => {
    if (!prompt.trim()) return;
    if (!enabled) return;

    const userMsg: Message = {
      id: `u_${Date.now()}`,
      role: "user",
      text: prompt.trim(),
      time: new Date().toISOString(),
    };

    setMessages((m) => [...m, userMsg]);
    setPrompt("");
    setIsLoading(true);
    scrollToBottom();

    // Mock AI reply (professional tone)
    await new Promise((r) => setTimeout(r, 900));

    const assistantMsg: Message = {
      id: `a_${Date.now()}`,
      role: "assistant",
      text:
        "Acknowledged. I have reviewed your request and prepared a concise plan to proceed. If you provide the dataset or specify the required analysis parameters, I will generate the appropriate outputs and recommendations.",
      time: new Date().toISOString(),
    };

    setMessages((m) => [...m, assistantMsg]);
    setIsLoading(false);
    // ensure scroll after rendering
    setTimeout(scrollToBottom, 50);
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between gap-2">
          <CardTitle>AI Assistant</CardTitle>
          <div className="flex items-center gap-2">
            {!enabled && (
              <div className="flex items-center gap-1 text-sm text-muted-foreground" title="Access to the AI assistant requires an active subscription. Visit Subscriptions to upgrade.">
                <Info className="h-4 w-4 text-muted-foreground" />
                <span>Subscription required</span>
              </div>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex h-[420px] flex-col">
          <div ref={listRef} className="flex-1 overflow-auto space-y-3 p-3" aria-live="polite">
            {messages.map((m) => (
              <div key={m.id} className={`flex ${m.role === "assistant" ? "justify-start" : "justify-end"}`}>
                <div className={`${m.role === "assistant" ? "bg-slate-100 text-slate-900" : "bg-primary text-primary-foreground"} max-w-[80%] rounded-lg px-4 py-2 text-sm`}> 
                  <div className="whitespace-pre-wrap">{m.text}</div>
                  <div className="mt-2 text-[10px] text-muted-foreground text-right">{new Date(m.time || "").toLocaleString()}</div>
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-slate-100 text-slate-900 max-w-[60%] rounded-lg px-4 py-2 text-sm">Typing…</div>
              </div>
            )}
          </div>

          <div className="mt-3 flex items-center gap-2">
            <Input
              placeholder={enabled ? "Type your request…" : "Subscription required to use the assistant"}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  sendPrompt();
                }
              }}
              aria-label="Assistant prompt"
              disabled={!enabled || isLoading}
            />

            <div className="flex items-center gap-2">
              <Button onClick={sendPrompt} disabled={!enabled || isLoading}>
                Send
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
