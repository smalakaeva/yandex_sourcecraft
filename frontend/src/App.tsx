import { Navigate, Route, Routes } from 'react-router-dom';
import { AppShell } from '@/components/layout/AppShell';
import { RequireAuth } from '@/components/layout/RequireAuth';
import { AnalysisPage } from '@/pages/AnalysisPage';
import { AuthCallbackPage } from '@/pages/AuthCallbackPage';
import { ComparePage } from '@/pages/ComparePage';
import { DashboardPage } from '@/pages/DashboardPage';
import { LoginPage } from '@/pages/LoginPage';
import { MethodologyPage } from '@/pages/MethodologyPage';
import { NotFoundPage } from '@/pages/NotFoundPage';
import { RatingPage } from '@/pages/RatingPage';
import { RepoPage } from '@/pages/RepoPage';

export function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<RatingPage />} />
        <Route path="rating" element={<Navigate to="/" replace />} />
        <Route path="repo/:owner/:name" element={<RepoPage />} />
        <Route path="compare" element={<ComparePage />} />
        <Route path="methodology" element={<MethodologyPage />} />
        <Route path="login" element={<LoginPage />} />
        <Route path="auth/callback" element={<AuthCallbackPage />} />
        <Route
          path="dashboard"
          element={
            <RequireAuth>
              <DashboardPage />
            </RequireAuth>
          }
        />
        <Route
          path="dashboard/analyze/:owner/:name"
          element={
            <RequireAuth>
              <AnalysisPage />
            </RequireAuth>
          }
        />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
