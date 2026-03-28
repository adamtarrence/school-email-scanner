"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useState, useCallback, Suspense } from "react";
import OnboardingForm from "@/components/OnboardingForm";
import Link from "next/link";

function SuccessContent() {
  const searchParams = useSearchParams();
  const sessionId = searchParams.get("session_id");

  const [loading, setLoading] = useState(!!sessionId);
  const [error, setError] = useState(
    sessionId ? "" : "No checkout session found. Please try subscribing again."
  );
  const [sessionData, setSessionData] = useState<{
    email: string;
    customerId: string;
    subscriptionId: string;
  } | null>(null);

  const fetchSession = useCallback(async (id: string) => {
    try {
      const res = await fetch(
        `/api/session?session_id=${encodeURIComponent(id)}`
      );
      const data = await res.json();
      if (data.error) {
        setError(data.error);
      } else {
        setSessionData(data);
      }
    } catch {
      setError("Failed to load your session. Please try again.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (sessionId) {
      fetchSession(sessionId);
    }
  }, [sessionId, fetchSession]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-brand border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-500 text-sm">Loading your account...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="max-w-md text-center">
          <p className="text-gray-700 mb-4">{error}</p>
          <Link
            href="/#pricing"
            className="text-brand hover:text-brand-dark font-medium transition-colors"
          >
            Back to SchoolSkim
          </Link>
        </div>
      </div>
    );
  }

  if (!sessionData) return null;

  return (
    <OnboardingForm
      email={sessionData.email}
      stripeCustomerId={sessionData.customerId}
      stripeSubscriptionId={sessionData.subscriptionId}
    />
  );
}

export default function SuccessPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center">
          <div className="w-8 h-8 border-2 border-brand border-t-transparent rounded-full animate-spin" />
        </div>
      }
    >
      <SuccessContent />
    </Suspense>
  );
}
