"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useState, useCallback, Suspense } from "react";
import Link from "next/link";

interface AccountStatus {
  email: string;
  paused: boolean;
  status: string;
  digestTime: string;
  timezone: string;
  childCount: number;
}

function Spinner() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="w-8 h-8 border-2 border-brand border-t-transparent rounded-full animate-spin" />
    </div>
  );
}

function AccountContent() {
  const searchParams = useSearchParams();
  const uid = searchParams.get("uid") || "";
  const token = searchParams.get("token") || "";

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [data, setData] = useState<AccountStatus | null>(null);
  const [working, setWorking] = useState(false);

  const load = useCallback(async () => {
    if (!uid || !token) {
      setError(
        "This account link is missing information. Please use the link from your SchoolSkim email."
      );
      setLoading(false);
      return;
    }
    try {
      const res = await fetch(
        `/api/account?uid=${encodeURIComponent(uid)}&token=${encodeURIComponent(token)}`
      );
      const json = await res.json();
      if (!res.ok) {
        setError(json.error || "We couldn't load your account.");
      } else {
        setData(json);
        setError("");
      }
    } catch {
      setError("We couldn't load your account. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [uid, token]);

  useEffect(() => {
    load();
  }, [load]);

  async function runAction(action: "pause" | "resume") {
    setWorking(true);
    setError("");
    try {
      const res = await fetch(
        `/api/${action}?uid=${encodeURIComponent(uid)}&token=${encodeURIComponent(token)}`,
        { method: "POST" }
      );
      if (!res.ok) {
        const json = await res.json().catch(() => ({}));
        setError(
          json.error
            ? `Something went wrong (${json.error}). Please try again.`
            : "Something went wrong. Please try again."
        );
      } else {
        await load();
      }
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setWorking(false);
    }
  }

  if (loading) return <Spinner />;

  if (error && !data) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="max-w-md text-center">
          <p className="text-gray-700 mb-4">{error}</p>
          <Link
            href="/"
            className="text-brand hover:text-brand-dark font-medium transition-colors"
          >
            Back to SchoolSkim
          </Link>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const cancelled = data.status === "inactive";

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12">
      <div className="max-w-lg w-full">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-gray-900">
            Your SchoolSkim account
          </h1>
          {data.email && (
            <p className="text-gray-500 mt-1 text-sm">{data.email}</p>
          )}
        </div>

        {/* Status pill */}
        <div className="flex justify-center mb-6">
          {cancelled ? (
            <span className="inline-flex items-center gap-2 bg-gray-100 text-gray-600 rounded-full px-4 py-1.5 text-sm font-medium">
              Subscription cancelled
            </span>
          ) : data.paused ? (
            <span className="inline-flex items-center gap-2 bg-amber-100 text-amber-800 rounded-full px-4 py-1.5 text-sm font-medium">
              <span className="w-2 h-2 rounded-full bg-amber-500" />
              Paused for the summer
            </span>
          ) : (
            <span className="inline-flex items-center gap-2 bg-green-100 text-green-700 rounded-full px-4 py-1.5 text-sm font-medium">
              <span className="w-2 h-2 rounded-full bg-green-500" />
              Active
            </span>
          )}
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 mb-6 text-sm">
            {error}
          </div>
        )}

        {cancelled ? (
          <div className="bg-gray-50 rounded-xl p-6 text-center">
            <p className="text-gray-600 text-sm mb-4">
              Your subscription is cancelled, so there&apos;s nothing to pause.
              You can resubscribe anytime.
            </p>
            <Link
              href="/#pricing"
              className="inline-block bg-brand hover:bg-brand-dark text-white font-semibold px-6 py-3 rounded-full transition-colors"
            >
              Resubscribe
            </Link>
          </div>
        ) : data.paused ? (
          <>
            {/* Warning: the mitigation for manual-resume-only */}
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-5 mb-6">
              <h2 className="font-semibold text-amber-900 text-sm mb-2">
                While you&apos;re paused
              </h2>
              <ul className="text-amber-800 text-sm space-y-2 list-disc list-inside">
                <li>
                  School emails you forward are <strong>not processed</strong> —
                  they&apos;re discarded, not saved.
                </li>
                <li>
                  Make sure your Gmail/Outlook forwarding rule still{" "}
                  <strong>keeps a copy in your own inbox</strong> (don&apos;t
                  auto-archive or delete) so you can read them yourself.
                </li>
                <li>
                  You <strong>won&apos;t be charged</strong> while paused.
                </li>
                <li>
                  We&apos;ll email you when school is starting back up — or
                  resume anytime below.
                </li>
              </ul>
            </div>

            <button
              type="button"
              onClick={() => runAction("resume")}
              disabled={working}
              className="w-full bg-brand text-white font-semibold py-3 rounded-xl hover:bg-brand-dark transition-colors disabled:opacity-60"
            >
              {working ? "Resuming…" : "Resume my digests"}
            </button>
          </>
        ) : (
          <>
            <div className="bg-gray-50 rounded-xl p-5 mb-6">
              <h2 className="font-semibold text-gray-900 text-sm mb-2">
                Pause for the summer
              </h2>
              <p className="text-gray-600 text-sm">
                Going on break? Pause SchoolSkim and we&apos;ll stop processing
                forwarded emails and stop billing until you resume. Your account
                and settings stay exactly as they are.
              </p>
            </div>

            <button
              type="button"
              onClick={() => runAction("pause")}
              disabled={working}
              className="w-full bg-amber-500 text-white font-semibold py-3 rounded-xl hover:bg-amber-600 transition-colors disabled:opacity-60"
            >
              {working ? "Pausing…" : "Pause for the summer"}
            </button>
          </>
        )}

        <div className="text-center mt-8">
          <Link
            href="/"
            className="text-brand hover:text-brand-dark font-medium transition-colors text-sm"
          >
            Back to SchoolSkim
          </Link>
        </div>
      </div>
    </div>
  );
}

export default function AccountPage() {
  return (
    <Suspense fallback={<Spinner />}>
      <AccountContent />
    </Suspense>
  );
}
