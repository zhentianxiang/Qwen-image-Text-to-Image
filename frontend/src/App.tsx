import { BrowserRouter, Routes, Route } from "react-router-dom"
import { TooltipProvider } from "@/components/ui/tooltip"
import { Toaster } from "@/components/ui/toaster"

// Layouts
import { MainLayout } from "@/components/layout/MainLayout"
import { AuthLayout } from "@/components/layout/AuthLayout"
import { ProtectedRoute } from "@/components/auth/ProtectedRoute"

// Auth Pages
import { LoginPage } from "@/pages/auth/LoginPage"
import { RegisterPage } from "@/pages/auth/RegisterPage"

// Main Pages
import { DashboardPage } from "@/pages/dashboard/DashboardPage"
import { TextToImagePage } from "@/pages/generate/TextToImagePage"
import { ImageEditPage } from "@/pages/generate/ImageEditPage"
import { BatchEditPage } from "@/pages/generate/BatchEditPage"
import { TaskListPage } from "@/pages/tasks/TaskListPage"
import { TaskDetailPage } from "@/pages/tasks/TaskDetailPage"
import { HistoryPage } from "@/pages/history/HistoryPage"
import { ProfilePage } from "@/pages/profile/ProfilePage"
import { QuotaPage } from "@/pages/profile/QuotaPage"

// Admin Pages
import { UsersPage } from "@/pages/admin/UsersPage"
import { StatisticsPage } from "@/pages/admin/StatisticsPage"
import SystemInfoPage from "@/pages/admin/SystemInfoPage"

function App() {
  return (
    <BrowserRouter>
      <TooltipProvider>
        <Routes>
          {/* Auth Routes */}
          <Route element={<AuthLayout />}>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
          </Route>

          {/* Protected Routes */}
          <Route
            element={
              <ProtectedRoute>
                <MainLayout />
              </ProtectedRoute>
            }
          >
            {/* Dashboard */}
            <Route path="/" element={<DashboardPage />} />

            {/* Generation */}
            <Route path="/generate/text-to-image" element={<TextToImagePage />} />
            <Route path="/generate/image-edit" element={<ImageEditPage />} />
            <Route path="/generate/batch-edit" element={<BatchEditPage />} />

            {/* Tasks */}
            <Route path="/tasks" element={<TaskListPage />} />
            <Route path="/tasks/:taskId" element={<TaskDetailPage />} />

            {/* History */}
            <Route path="/history" element={<HistoryPage />} />

            {/* Profile */}
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/quota" element={<QuotaPage />} />

            {/* Admin Routes */}
            <Route
              path="/admin/users"
              element={
                <ProtectedRoute requireAdmin>
                  <UsersPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/statistics"
              element={
                <ProtectedRoute requireAdmin>
                  <StatisticsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/system"
              element={
                <ProtectedRoute requireAdmin>
                  <SystemInfoPage />
                </ProtectedRoute>
              }
            />
          </Route>
        </Routes>
        <Toaster />
      </TooltipProvider>
    </BrowserRouter>
  )
}

export default App
