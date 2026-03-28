"use client";

import { useState } from "react";
import Link from "next/link";

interface Child {
  name: string;
  grade: string;
  school: string;
}

interface OnboardingFormProps {
  email: string;
  stripeCustomerId: string;
  stripeSubscriptionId: string;
}

const TIMEZONES = [
  { value: "America/New_York", label: "Eastern" },
  { value: "America/Chicago", label: "Central" },
  { value: "America/Denver", label: "Mountain" },
  { value: "America/Los_Angeles", label: "Pacific" },
  { value: "America/Anchorage", label: "Alaska" },
  { value: "Pacific/Honolulu", label: "Hawaii" },
];

const DIGEST_TIMES = [
  { value: "06:00", label: "6:00 AM" },
  { value: "07:00", label: "7:00 AM" },
  { value: "08:00", label: "8:00 AM" },
  { value: "17:00", label: "5:00 PM" },
  { value: "18:00", label: "6:00 PM" },
  { value: "19:00", label: "7:00 PM" },
  { value: "20:00", label: "8:00 PM" },
  { value: "21:00", label: "9:00 PM" },
];

export default function OnboardingForm({
  email,
  stripeCustomerId,
  stripeSubscriptionId,
}: OnboardingFormProps) {
  const [step, setStep] = useState(1);
  const [children, setChildren] = useState<Child[]>([
    { name: "", grade: "", school: "" },
  ]);
  const [timezone, setTimezone] = useState("America/New_York");
  const [digestTime, setDigestTime] = useState("18:00");
  const [forwardAddress, setForwardAddress] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  function updateChild(index: number, field: keyof Child, value: string) {
    setChildren((prev) =>
      prev.map((c, i) => (i === index ? { ...c, [field]: value } : c))
    );
  }

  function addChild() {
    setChildren((prev) => [...prev, { name: "", grade: "", school: "" }]);
  }

  function removeChild(index: number) {
    if (children.length > 1) {
      setChildren((prev) => prev.filter((_, i) => i !== index));
    }
  }

  function validateStep1(): boolean {
    for (const child of children) {
      if (!child.name.trim()) {
        setError("Please enter a name for each child.");
        return false;
      }
    }
    setError("");
    return true;
  }

  async function handleSubmit() {
    setSubmitting(true);
    setError("");

    try {
      const res = await fetch("/api/onboarding", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email,
          stripeCustomerId,
          stripeSubscriptionId,
          children: children.map((c) => ({
            name: c.name.trim(),
            grade: c.grade.trim(),
            school: c.school.trim(),
          })),
          timezone,
          digestTime,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data.error || "Something went wrong. Please try again.");
        setSubmitting(false);
        return;
      }

      setForwardAddress(data.forwardAddress);
      setStep(3);
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  // Step 3: Setup instructions
  if (step === 3) {
    return <SetupInstructions forwardAddress={forwardAddress} />;
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12">
      <div className="max-w-lg w-full">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg
              width="32"
              height="32"
              viewBox="0 0 32 32"
              fill="none"
              className="text-green-600"
            >
              <path
                d="M8 16l5.5 5.5L24 11"
                stroke="currentColor"
                strokeWidth="3"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">
            Welcome to SchoolSkim!
          </h1>
          <p className="text-gray-600 mt-2">
            Your 14-day free trial has started. Let&apos;s get you set up.
          </p>
        </div>

        {/* Step indicator */}
        <div className="flex items-center justify-center gap-2 mb-8">
          <div
            className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
              step === 1
                ? "bg-brand text-white"
                : "bg-gray-200 text-gray-500"
            }`}
          >
            1
          </div>
          <div className="w-8 h-px bg-gray-300" />
          <div
            className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
              step === 2
                ? "bg-brand text-white"
                : "bg-gray-200 text-gray-500"
            }`}
          >
            2
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 mb-6 text-sm">
            {error}
          </div>
        )}

        {step === 1 && (
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-1">
              Tell us about your kids
            </h2>
            <p className="text-sm text-gray-500 mb-6">
              We&apos;ll group your digest by child so you know exactly
              what&apos;s relevant to each one.
            </p>

            <div className="space-y-4">
              {children.map((child, i) => (
                <div
                  key={i}
                  className="bg-gray-50 rounded-xl p-4 relative"
                >
                  {children.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeChild(i)}
                      className="absolute top-3 right-3 text-gray-400 hover:text-red-500 transition-colors"
                      aria-label="Remove child"
                    >
                      <svg
                        width="18"
                        height="18"
                        viewBox="0 0 18 18"
                        fill="none"
                      >
                        <path
                          d="M4.5 4.5l9 9m0-9l-9 9"
                          stroke="currentColor"
                          strokeWidth="1.5"
                          strokeLinecap="round"
                        />
                      </svg>
                    </button>
                  )}
                  <div className="grid grid-cols-1 gap-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Name <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        value={child.name}
                        onChange={(e) => updateChild(i, "name", e.target.value)}
                        placeholder="e.g. Emma"
                        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Grade
                        </label>
                        <input
                          type="text"
                          value={child.grade}
                          onChange={(e) =>
                            updateChild(i, "grade", e.target.value)
                          }
                          placeholder="e.g. 3rd"
                          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          School
                        </label>
                        <input
                          type="text"
                          value={child.school}
                          onChange={(e) =>
                            updateChild(i, "school", e.target.value)
                          }
                          placeholder="e.g. Lincoln Elementary"
                          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <button
              type="button"
              onClick={addChild}
              className="mt-4 text-sm text-brand hover:text-brand-dark font-medium transition-colors"
            >
              + Add another child
            </button>

            <button
              type="button"
              onClick={() => {
                if (validateStep1()) setStep(2);
              }}
              className="mt-6 w-full bg-brand text-white font-medium py-3 rounded-xl hover:bg-brand-dark transition-colors"
            >
              Continue
            </button>
          </div>
        )}

        {step === 2 && (
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-1">
              When should we send your digest?
            </h2>
            <p className="text-sm text-gray-500 mb-6">
              Pick a time that works for your evening routine. You can change
              this later.
            </p>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Time zone
                </label>
                <select
                  value={timezone}
                  onChange={(e) => setTimezone(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand bg-white"
                >
                  {TIMEZONES.map((tz) => (
                    <option key={tz.value} value={tz.value}>
                      {tz.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Delivery time
                </label>
                <div className="grid grid-cols-4 gap-2">
                  {DIGEST_TIMES.map((t) => (
                    <button
                      key={t.value}
                      type="button"
                      onClick={() => setDigestTime(t.value)}
                      className={`py-2 px-3 rounded-lg text-sm font-medium border transition-colors ${
                        digestTime === t.value
                          ? "bg-brand text-white border-brand"
                          : "bg-white text-gray-700 border-gray-300 hover:border-brand"
                      }`}
                    >
                      {t.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex gap-3 mt-8">
              <button
                type="button"
                onClick={() => setStep(1)}
                className="flex-1 border border-gray-300 text-gray-700 font-medium py-3 rounded-xl hover:bg-gray-50 transition-colors"
              >
                Back
              </button>
              <button
                type="button"
                onClick={handleSubmit}
                disabled={submitting}
                className="flex-1 bg-brand text-white font-medium py-3 rounded-xl hover:bg-brand-dark transition-colors disabled:opacity-60"
              >
                {submitting ? "Setting up..." : "Finish setup"}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function SetupInstructions({ forwardAddress }: { forwardAddress: string }) {
  const [copied, setCopied] = useState(false);

  function copyAddress() {
    navigator.clipboard.writeText(forwardAddress);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12">
      <div className="max-w-lg w-full">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-brand/10 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg
              width="32"
              height="32"
              viewBox="0 0 32 32"
              fill="none"
              className="text-brand"
            >
              <rect
                x="4"
                y="8"
                width="24"
                height="16"
                rx="2"
                stroke="currentColor"
                strokeWidth="2"
              />
              <path
                d="M4 10l12 8 12-8"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">
            You&apos;re almost there!
          </h1>
          <p className="text-gray-600 mt-2">
            Set up email forwarding and your first digest will arrive tonight.
          </p>
        </div>

        {/* Forwarding address */}
        <div className="bg-gray-50 rounded-xl p-5 mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Your personal forwarding address
          </label>
          <div className="flex items-center gap-2">
            <div className="flex-1 bg-white border border-gray-200 rounded-lg px-4 py-3 font-mono text-sm text-brand select-all">
              {forwardAddress}
            </div>
            <button
              onClick={copyAddress}
              className="shrink-0 bg-white border border-gray-200 rounded-lg px-4 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
            >
              {copied ? "Copied!" : "Copy"}
            </button>
          </div>
        </div>

        {/* Gmail instructions */}
        <div className="border border-gray-200 rounded-xl overflow-hidden mb-4">
          <div className="bg-gray-50 px-5 py-3 border-b border-gray-200">
            <h3 className="font-semibold text-gray-900 text-sm">
              Gmail setup
            </h3>
          </div>
          <ol className="px-5 py-4 space-y-3 text-sm text-gray-700 list-decimal list-inside">
            <li>
              Open Gmail and click the{" "}
              <strong>gear icon &rarr; See all settings</strong>
            </li>
            <li>
              Go to the <strong>Forwarding and POP/IMAP</strong> tab
            </li>
            <li>
              Click <strong>Add a forwarding address</strong> and paste your
              SchoolSkim address
            </li>
            <li>
              Gmail will send a confirmation — check your inbox and click the
              link
            </li>
            <li>
              Back in settings, choose{" "}
              <strong>&ldquo;Forward a copy of incoming mail&rdquo;</strong>
            </li>
            <li>
              <em>Optional but recommended:</em> Create a filter to only forward
              emails from your school&apos;s domain (e.g.{" "}
              <code className="bg-gray-100 px-1 rounded">
                from:@lincolnschool.org
              </code>
              )
            </li>
          </ol>
        </div>

        {/* Outlook instructions */}
        <div className="border border-gray-200 rounded-xl overflow-hidden mb-8">
          <div className="bg-gray-50 px-5 py-3 border-b border-gray-200">
            <h3 className="font-semibold text-gray-900 text-sm">
              Outlook / Microsoft 365 setup
            </h3>
          </div>
          <ol className="px-5 py-4 space-y-3 text-sm text-gray-700 list-decimal list-inside">
            <li>
              Go to <strong>Settings &rarr; Mail &rarr; Rules</strong>
            </li>
            <li>
              Click <strong>Add new rule</strong>
            </li>
            <li>
              Set condition: <strong>&ldquo;From&rdquo;</strong> contains your
              school&apos;s email domain
            </li>
            <li>
              Set action: <strong>&ldquo;Forward to&rdquo;</strong> your
              SchoolSkim address
            </li>
            <li>Save the rule</li>
          </ol>
        </div>

        <div className="text-center">
          <p className="text-sm text-gray-500 mb-4">
            Once forwarding is set up, we&apos;ll start processing your school
            emails and you&apos;ll receive your first digest this evening.
          </p>
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
