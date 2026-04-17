import React, { useEffect, useState } from "react";
import LearningMaterials from "./pages/LearningMaterials";
import { trackResource } from "./services/api";
/* Pages */
import SignIn from "./pages/SignIn";
import SignUp from "./pages/SignUp";
import VerifyEmail from "./pages/VerifyEmail";
import ForgotPassword from "./pages/ForgotPassword";
import Dashboard from "./pages/Dashboard";
import VARKQuiz from "./pages/VARKQuiz";
import DigitalAssessment from "./pages/DigitalAssessment";
import VARKResult from "./pages/VARKResult";
import ResourceViewer from "./pages/ResourceViewer";
/* ==================== CONSTANTS ==================== */
const SESSION_KEY = "currentSession";
/* ==================== MAIN APP ==================== */
export default function App() {
  // signin | signup | verify | forgot
  const [authState, setAuthState] = useState("signin");

  // logged-in user
  const [user, setUser] = useState(null);
  const [varkResult, setVarkResult] = useState(null);

  // dashboard | vark | assessment
  const [currentPage, setCurrentPage] = useState("dashboard");

  const [loading, setLoading] = useState(true);
  const [selectedResource, setSelectedResource] = useState(null);

  /* ==================== LOAD SESSION ==================== */
  useEffect(() => {
    const session = localStorage.getItem(SESSION_KEY);
    if (session) {
      setUser(JSON.parse(session));
    }
    setLoading(false);
  }, []);

  /* ==================== AUTH HANDLERS ==================== */

  // LOGIN (also used after verification)
  const handleSignIn = (userData) => {
    setUser(userData);
    setAuthState("signin");
    setCurrentPage("dashboard");
    localStorage.setItem(SESSION_KEY, JSON.stringify(userData));
  };

  // AFTER REGISTER → GO TO VERIFY
  const handleRegistered = (email) => {
    setUser({ email });
    setAuthState("verify");
  };
  

  // LOGOUT
  const handleLogout = () => {
    setUser(null);
    setAuthState("signin");
    setCurrentPage("dashboard");
    localStorage.removeItem(SESSION_KEY);
  };

  /* ==================== QUIZ HANDLERS ==================== */

  const handleVarkComplete = (result) => {
    const updatedUser = { ...user, varkResult: result };

    setUser(updatedUser);
    localStorage.setItem(SESSION_KEY, JSON.stringify(updatedUser));

    // 👇 NEW PART
    setVarkResult(result);
    setCurrentPage("varkResult");
  };

  const handleAssessmentComplete = (result) => {
    const updatedUser = {
      ...user,
      assessmentResults: [
        ...(user.assessmentResults || []),
        { ...result, date: new Date().toISOString() },
      ],
    };

    setUser(updatedUser);
    localStorage.setItem(SESSION_KEY, JSON.stringify(updatedUser));
  };

  /* ==================== LOADING SCREEN ==================== */
  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
      </div>
    );
  }

  /* ==================== AUTH FLOW ==================== */
  if (!user || authState !== "signin") {
    if (authState === "signup") {
      return (
        <SignUp
          onSwitchToSignIn={() => setAuthState("signin")}
          onRegistered={handleRegistered}
        />
      );
    }

    if (authState === "verify") {
      return (
        <VerifyEmail
          email={user?.email}
          onVerified={(verifiedUser) => handleSignIn(verifiedUser)} // ✅ DIRECT TO DASHBOARD
          onBack={() => setAuthState("signup")}
        />
      );
    }

    if (authState === "forgot") {
      return <ForgotPassword onBack={() => setAuthState("signin")} />;
    }

    // SIGN IN
    return (
      <SignIn
        onSignIn={handleSignIn}
        onSwitchToSignUp={() => setAuthState("signup")}
        onForgotPassword={() => setAuthState("forgot")}
      />
    );
  }

  /* ==================== APP PAGES ==================== */

  if (currentPage === "varkResult") {
    return (
      <VARKResult
        result={varkResult}
        onBack={() => setCurrentPage("dashboard")}
      />
    );
  }

  if (currentPage === "assessment") {
    return (
      <DigitalAssessment
        user={user}
        onComplete={handleAssessmentComplete}
        onBack={() => setCurrentPage("dashboard")}
      />
    );
  }
  if (currentPage === "vark") {
    return (
      <VARKQuiz
        user={user}
        onComplete={handleVarkComplete}
        onBack={() => setCurrentPage("dashboard")}
      />
    );
  }
  if (currentPage === "learningMaterials") {
    return (
      <LearningMaterials
        user={user}
        onBack={() => setCurrentPage("dashboard")}
        onOpenResource={async (r) => {
          try {
            await trackResource(user.id, r.id);
          } catch (err) {
            console.error("Failed to track resource:", err);
          }
          setSelectedResource(r);
          setCurrentPage("resourceViewer");
        }}
      />
    );
  }
  if (currentPage === "resourceViewer") {
    return (
      <ResourceViewer
        user={user}
        resource={selectedResource}
        onBack={() => setCurrentPage("learningMaterials")}
      />
    );
  }

  /* ==================== DASHBOARD ==================== */
  return (
    <Dashboard
      user={user}
      onNavigate={setCurrentPage}
      onLogout={handleLogout}
    />
  );
}
