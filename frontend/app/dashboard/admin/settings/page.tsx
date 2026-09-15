"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function AdminSettingsPage() {
  const [settings, setSettings] = useState({
    platformName: "Scapegis",
    supportEmail: "support@scapegis.com",
    maxMapsPerUser: "100",
    aiQueryLimit: "1000",
    maintenanceMode: false,
  });

  const handleSave = () => {
    // In production, this would save to API
    console.log("Saving settings:", settings);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Settings</h2>
        <p className="text-muted-foreground mt-1">
          Manage platform settings and configuration
        </p>
      </div>

      {/* General Settings */}
      <Card>
        <CardHeader>
          <CardTitle>General Settings</CardTitle>
          <CardDescription>Basic platform configuration</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="platformName">Platform Name</Label>
            <Input
              id="platformName"
              value={settings.platformName}
              onChange={(e) =>
                setSettings({ ...settings, platformName: e.target.value })
              }
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="supportEmail">Support Email</Label>
            <Input
              id="supportEmail"
              type="email"
              value={settings.supportEmail}
              onChange={(e) =>
                setSettings({ ...settings, supportEmail: e.target.value })
              }
            />
          </div>
        </CardContent>
      </Card>

      {/* Limits */}
      <Card>
        <CardHeader>
          <CardTitle>User Limits</CardTitle>
          <CardDescription>Configure default user limits</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="maxMaps">Max Maps Per User</Label>
            <Input
              id="maxMaps"
              type="number"
              value={settings.maxMapsPerUser}
              onChange={(e) =>
                setSettings({ ...settings, maxMapsPerUser: e.target.value })
              }
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="aiQueryLimit">AI Query Limit (per month)</Label>
            <Input
              id="aiQueryLimit"
              type="number"
              value={settings.aiQueryLimit}
              onChange={(e) =>
                setSettings({ ...settings, aiQueryLimit: e.target.value })
              }
            />
          </div>
        </CardContent>
      </Card>

      {/* System Settings */}
      <Card>
        <CardHeader>
          <CardTitle>System Settings</CardTitle>
          <CardDescription>Platform maintenance and system controls</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <Label htmlFor="maintenance">Maintenance Mode</Label>
              <p className="text-sm text-muted-foreground">
                Enable to put the platform in maintenance mode
              </p>
            </div>
            <input
              id="maintenance"
              type="checkbox"
              checked={settings.maintenanceMode}
              onChange={(e) =>
                setSettings({ ...settings, maintenanceMode: e.target.checked })
              }
              className="h-4 w-4 rounded border-gray-300"
            />
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end">
        <Button onClick={handleSave}>Save Changes</Button>
      </div>
    </div>
  );
}

