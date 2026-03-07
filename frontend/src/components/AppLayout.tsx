import { Outlet } from "react-router-dom";
import { useState } from "react";
import { Menu, X, RefreshCw } from "lucide-react";
import AppSidebar from "./AppSidebar";
import { useIsMobile } from "@/hooks/use-mobile";
import { useBackend } from "@/context/BackendContext";

export default function AppLayout() {
  const isMobile = useIsMobile();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { error: backendError, loading, refresh } = useBackend();

  return (
    <div className="flex min-h-screen w-full bg-background">
      {isMobile ? (
        <>
          {/* Mobile hamburger */}
          <button
            onClick={() => setSidebarOpen(true)}
            className="fixed top-4 left-4 z-40 p-2 rounded-lg bg-card border border-border shadow-md"
          >
            <Menu className="w-5 h-5 text-foreground" />
          </button>

          {/* Mobile overlay */}
          {sidebarOpen && (
            <div className="fixed inset-0 z-50 flex animate-fade-in">
              <div className="absolute inset-0 bg-foreground/20" onClick={() => setSidebarOpen(false)} />
              <div className="relative z-10 animate-slide-in">
                <AppSidebar onNavigate={() => setSidebarOpen(false)} />
              </div>
              <button
                onClick={() => setSidebarOpen(false)}
                className="absolute top-4 right-4 z-20 p-2 rounded-lg bg-card border border-border shadow-md"
              >
                <X className="w-5 h-5 text-foreground" />
              </button>
            </div>
          )}
        </>
      ) : (
        <AppSidebar />
      )}
      <main className="flex-1 min-w-0 overflow-auto">
        {backendError && !loading && (
          <div className="sticky top-0 z-30 flex items-center justify-between gap-4 border-b border-destructive/30 bg-destructive/10 px-4 py-2 text-sm text-destructive">
            <span className="truncate">{backendError}</span>
            <button
              type="button"
              onClick={() => refresh()}
              className="shrink-0 flex items-center gap-1 rounded border border-destructive/50 bg-background px-2 py-1 text-destructive hover:bg-destructive/10"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Retry
            </button>
          </div>
        )}
        <Outlet />
      </main>
    </div>
  );
}
