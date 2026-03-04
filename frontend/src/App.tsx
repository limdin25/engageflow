import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { useEffect } from "react";
import { toast } from "sonner";
import AppLayout from "./components/AppLayout";
import DashboardPage from "./pages/DashboardPage";
import InboxPage from "./pages/InboxPage";
import ProfilesPage from "./pages/ProfilesPage";
import CommunitiesPage from "./pages/CommunitiesPage";
import KeywordsPage from "./pages/KeywordsPage";
import AutomationPage from "./pages/AutomationPage";
import LogsPage from "./pages/LogsPage";
import AnalyticsPage from "./pages/AnalyticsPage";
import NotFound from "./pages/NotFound";
import LockScreen from "./pages/LockScreen";
import OwnerPage from "./pages/OwnerPage";
import ConnectPage from "./pages/ConnectPage";
import { isUnlocked } from "./lib/lockscreen";
import { BackendProvider } from "./context/BackendContext";

const queryClient = new QueryClient();

function RequireUnlock({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  if (!isUnlocked()) {
    return <Navigate to="/lock" state={{ from: location }} replace />;
  }
  return <>{children}</>;
}

function GlobalErrorBridge() {
  useEffect(() => {
    const onUnhandledRejection = (event: PromiseRejectionEvent) => {
      const reason = event.reason;
      
      // Extract error message from various error formats
      let message = "Request failed";
      
      if (reason instanceof Error) {
        message = reason.message;
      } else if (reason?.message) {
        message = reason.message;
      } else if (typeof reason === "string") {
        message = reason;
      }
      
      // Don't show generic "Internal server error" - backend should provide specific messages
      if (message === "Internal server error" || message === "Internal Server Error") {
        message = "Request failed - please try again";
      }
      
      toast.error(message);
    };
    window.addEventListener("unhandledrejection", onUnhandledRejection);
    return () => window.removeEventListener("unhandledrejection", onUnhandledRejection);
  }, []);

  return null;
}

const App = () => (
  <QueryClientProvider client={queryClient}>
    <BackendProvider>
      <TooltipProvider>
        <GlobalErrorBridge />
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Routes>
            <Route path="/lock" element={<LockScreen />} />
            <Route path="/owner" element={<OwnerPage />} />
            <Route path="/connect" element={<ConnectPage />} />
            <Route element={<RequireUnlock><AppLayout /></RequireUnlock>}>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/inbox" element={<InboxPage />} />
              <Route path="/profiles" element={<ProfilesPage />} />
              <Route path="/communities" element={<CommunitiesPage />} />
              <Route path="/keywords" element={<KeywordsPage />} />
              <Route path="/automation" element={<AutomationPage />} />
              <Route path="/logs" element={<LogsPage />} />
              <Route path="/analytics" element={<AnalyticsPage />} />
            </Route>
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </BackendProvider>
  </QueryClientProvider>
);

export default App;
