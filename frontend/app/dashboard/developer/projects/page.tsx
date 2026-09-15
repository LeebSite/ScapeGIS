"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Plus, Users, Map } from "lucide-react";
import { useWorkspaceStore } from "@/lib/store";
import { projectAPI } from "@/lib/api";
import type { Project } from "@/lib/types";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

export default function ProjectsPage() {
  const router = useRouter();
  const { currentWorkspace } = useWorkspaceStore();
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newProjectName, setNewProjectName] = useState("");
  const [newProjectDescription, setNewProjectDescription] = useState("");
  const [isCreating, setIsCreating] = useState(false);

  useEffect(() => {
    if (currentWorkspace?.id) {
      fetchProjects(currentWorkspace.id);
    } else {
      setIsLoading(false);
    }
  }, [currentWorkspace?.id]);

  const fetchProjects = async (workspaceId: string) => {
    setIsLoading(true);
    try {
      const res = await projectAPI.getProjects(workspaceId);
      setProjects(res.data);
    } catch (error) {
      console.error("Failed to fetch projects:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateProject = async () => {
    if (!currentWorkspace) return;
    setIsCreating(true);
    try {
      const res = await projectAPI.createProject({
        workspace_id: currentWorkspace.id,
        name: newProjectName,
        description: newProjectDescription,
      });
      setProjects([...projects, res.data]);
      setShowCreateModal(false);
      setNewProjectName("");
      setNewProjectDescription("");
      router.push(`/dashboard/developer/projects/${res.data.id}`);
    } catch (error) {
      console.error("Failed to create project:", error);
    } finally {
      setIsCreating(false);
    }
  };

  const handleProjectClick = (projectId: string) => {
    router.push(`/dashboard/developer/projects/${projectId}`);
  };

  if (!currentWorkspace) {
    return <div className="p-8">Please select a workspace first.</div>;
  }

  return (
    <div className="space-y-6 p-8">
      {/* Header Section */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Projects</h2>
          <p className="text-muted-foreground mt-1">
            Manage your GIS projects in {currentWorkspace.name}
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Create Project
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create New Project</DialogTitle>
                <DialogDescription>Add a new map project to your workspace.</DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid gap-2">
                  <Label htmlFor="name">Project Name</Label>
                  <Input
                    id="name"
                    value={newProjectName}
                    onChange={(e) => setNewProjectName(e.target.value)}
                    placeholder="My New Map"
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    value={newProjectDescription}
                    onChange={(e) => setNewProjectDescription(e.target.value)}
                    placeholder="Project details..."
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowCreateModal(false)}>Cancel</Button>
                <Button onClick={handleCreateProject} disabled={isCreating || !newProjectName}>
                  {isCreating ? "Creating..." : "Create Project"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Projects Grid */}
      {isLoading ? (
        <div>Loading projects...</div>
      ) : projects.length === 0 ? (
        <div className="text-center py-10">
          <p className="text-muted-foreground">No projects found. Create one to get started.</p>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {projects.map((project) => (
            <Card
              key={project.id}
              className="cursor-pointer hover:shadow-lg transition-shadow group"
              onClick={() => handleProjectClick(project.id)}
            >
              <CardContent className="p-0">
                {/* Map Preview Placeholder */}
                <div className="relative h-48 bg-muted overflow-hidden">
                  <div
                    className="absolute inset-0 opacity-10 bg-[url('https://api.mapbox.com/styles/v1/mapbox/light-v10/static/106.8456,-6.2088,10,0/400x300?access_token=pk.eyJ1IjoiZXhhbXBsZSIsImEiOiJjazlzdXN..." // Placeholder or pattern
                    style={{
                      backgroundImage: "radial-gradient(#ccc 1px, transparent 1px)",
                      backgroundSize: "20px 20px"
                    }}
                  />
                  <div className="absolute inset-0 flex items-center justify-center text-muted-foreground/50 group-hover:text-muted-foreground transition-colors">
                    <Map className="h-12 w-12" />
                  </div>
                </div>

                {/* Project Info */}
                <div className="p-4 space-y-2">
                  <h3 className="font-semibold text-lg leading-tight truncate">{project.name}</h3>
                  <p className="text-sm text-muted-foreground line-clamp-2">{project.description || "No description"}</p>
                  <div className="flex items-center text-xs text-muted-foreground pt-2 border-t">
                    <Map className="h-3 w-3 mr-1.5" />
                    <span>Updated {new Date(project.updated_at).toLocaleDateString()}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
