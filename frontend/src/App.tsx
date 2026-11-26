import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { PillNav } from "./components/ui/PillNav";
import { WorkspaceLayout } from "./components/WorkspaceLayout";
import { LandingPage } from "./pages/LandingPage";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { OnboardingPage } from "./pages/OnboardingPage";
import { DashboardPage } from "./pages/DashboardPage";
import { RecordsPage } from "./pages/RecordsPage";
import { PredictionsPage } from "./pages/PredictionsPage";
import { StudyPlannerPage } from "./pages/StudyPlannerPage";
import { SyllabusLabPage } from "./pages/SyllabusLabPage";
import { ClassroomChallengePage } from "./pages/ClassroomChallengePage";
import { ClassroomProjectorPage } from "./pages/ClassroomProjectorPage";
import { ProfilePage } from "./pages/ProfilePage";

export function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <PillNav />
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          <Route
            path="/onboarding"
            element={
              <WorkspaceLayout>
                <OnboardingPage />
              </WorkspaceLayout>
            }
          />
          <Route
            path="/dashboard"
            element={
              <WorkspaceLayout>
                <DashboardPage />
              </WorkspaceLayout>
            }
          />
          <Route
            path="/academics"
            element={
              <WorkspaceLayout>
                <RecordsPage />
              </WorkspaceLayout>
            }
          />
          <Route
            path="/academics/records"
            element={
              <WorkspaceLayout>
                <RecordsPage />
              </WorkspaceLayout>
            }
          />
          <Route
            path="/predictions"
            element={
              <WorkspaceLayout>
                <PredictionsPage />
              </WorkspaceLayout>
            }
          />
          <Route
            path="/study-planner"
            element={
              <WorkspaceLayout>
                <StudyPlannerPage />
              </WorkspaceLayout>
            }
          />
          <Route
            path="/syllabus-lab"
            element={
              <WorkspaceLayout>
                <SyllabusLabPage />
              </WorkspaceLayout>
            }
          />
          <Route
            path="/syllabus-lab/upload"
            element={
              <WorkspaceLayout>
                <SyllabusLabPage />
              </WorkspaceLayout>
            }
          />
          <Route
            path="/syllabus-lab/library"
            element={
              <WorkspaceLayout>
                <SyllabusLabPage />
              </WorkspaceLayout>
            }
          />
          <Route
            path="/syllabus-lab/assessments"
            element={
              <WorkspaceLayout>
                <SyllabusLabPage />
              </WorkspaceLayout>
            }
          />
          <Route
            path="/profile"
            element={
              <WorkspaceLayout>
                <ProfilePage />
              </WorkspaceLayout>
            }
          />

          {/* Integrated QR-accessible Classroom Challenge routes */}
          <Route path="/classroom-challenge" element={<ClassroomChallengePage />} />
          <Route path="/classroom-challenge/start" element={<ClassroomChallengePage />} />
          <Route
            path="/classroom-challenge/projector"
            element={<ClassroomProjectorPage />}
          />
          <Route
            path="/classroom-challenge/attempt/:attemptId"
            element={<ClassroomChallengePage />}
          />
          <Route
            path="/classroom-challenge/result/:attemptId"
            element={<ClassroomChallengePage />}
          />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
