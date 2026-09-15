"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Plus, Users, Map } from "lucide-react";

interface Project {
  id: string;
  name: string;
  owner: string;
  description?: string;
  updatedAt: string;
}

export default function AdminProjectsPage() {
  const router = useRouter();
  const [projects] = useState<Project[]>([
    { id: "1", name: "Untitled Project", owner: "Project id owner", updatedAt: "2 days ago" },
    { id: "2", name: "Untitled Project", owner: "Project id owner", updatedAt: "1 week ago" },
    { id: "3", name: "Untitled Project", owner: "Project id owner", updatedAt: "3 days ago" },
    { id: "4", name: "Untitled Project", owner: "Project id owner", updatedAt: "5 days ago" },
  ]);

  const handleCreateProject = () => {
    const newProjectId = `project-${Date.now()}`;
    router.push(`/dashboard/admin/projects/${newProjectId}`);
  };

  const handleJoinProject = () => {
    console.log("Join project");
  };

  const handleProjectClick = (projectId: string) => {
    router.push(`/dashboard/admin/projects/${projectId}`);
  };

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Project Page</h2>
          <p className="text-muted-foreground mt-1">
            Manage and view all GIS projects
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button onClick={handleCreateProject}>
            <Plus className="mr-2 h-4 w-4" />
            Create Project
          </Button>
          <Button variant="outline" onClick={handleJoinProject}>
            <Users className="mr-2 h-4 w-4" />
            Join Project
          </Button>
        </div>
      </div>

      {/* Projects Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {projects.map((project) => (
          <Card
            key={project.id}
            className="cursor-pointer hover:shadow-lg transition-shadow"
            onClick={() => handleProjectClick(project.id)}
          >
            <CardContent className="p-0">
              {/* Map Preview */}
              <div className="relative h-48 bg-gradient-to-br from-blue-50 via-green-50 to-blue-50 border-b overflow-hidden group">
                <div
                  className="absolute inset-0 opacity-20"
                  style={{
                    backgroundImage: `
                      linear-gradient(to right, #000 1px, transparent 1px),
                      linear-gradient(to bottom, #000 1px, transparent 1px)
                    `,
                    backgroundSize: "20px 20px",
                  }}
                />
                {/* Sample map features */}
                <div className="absolute top-1/4 left-1/4 w-16 h-16 bg-primary/30 rounded-full border-2 border-primary shadow-sm transition-transform group-hover:scale-110" />
                <div className="absolute top-1/2 right-1/4 w-12 h-12 bg-green-500/30 rounded-full border-2 border-green-500 shadow-sm transition-transform group-hover:scale-110" />
                <div className="absolute bottom-1/4 left-1/3 w-20 h-20 bg-blue-500/30 rounded-full border-2 border-blue-500 shadow-sm transition-transform group-hover:scale-110" />
              </div>
              
              {/* Project Info */}
              <div className="p-4 space-y-2">
                <h3 className="font-semibold text-lg leading-tight">{project.name}</h3>
                <p className="text-sm text-muted-foreground">{project.owner}</p>
                <div className="flex items-center text-xs text-muted-foreground pt-2 border-t">
                  <Map className="h-3 w-3 mr-1.5" />
                  <span>Updated {project.updatedAt}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

