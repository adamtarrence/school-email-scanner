"use client";

import { useState } from "react";

const features = [
  "Daily digest every school day at your chosen time",
  "Action items highlighted with deadlines",
  "Events extracted and organized",
  "Grouped by child — works for any school",
  "Links back to every original email",
  "Originals never touched or deleted",
  "Cancel anytime",
];

export default function Pricing() {
  const [loading, setLoading] = useState(false);

  async function handleCheckout() {
    setLoading(true);
    try {
      const res = await fetch("/api/checkout", { method: "POST" });
      const data = await res.json();
      if (data.url) {
        window.location.href = data.url;
      } else {
        alert("Error: " + (data.error || "Something went wrong. Please try again."));
      }
    } catch (err) {
      alert("Network error: " + (err instanceof Error ? err.message : String(err)));
    } finally {
      setLoading(false);
    }
  }

  return (
    <section id="pricing" className="py-16 md:py-24 px-4 sm:px-6">
      <div className="max-w-6xl mx-auto">
        <h2 className="text-3xl sm:text-4xl font-bold text-center text-gray-900 mb-4">
          Simple pricing
        </h2>
        <p className="text-center text-gray-500 mb-12 max-w-xl mx-auto">
          One plan. Everything included. Start with a free trial.
        </p>

        <div className="max-w-sm mx-auto bg-white rounded-2xl border-2 border-brand shadow-lg p-8">
          <div className="text-center mb-6">
            <div className="text-5xl font-extrabold text-gray-900">
              $3
              <span className="text-xl font-medium text-gray-500">/month</span>
            </div>
            <p className="mt-2 text-brand font-semibold">14-day free trial</p>
          </div>

          <ul className="space-y-3 mb-8">
            {features.map((feature, i) => (
              <li key={i} className="flex items-start gap-3 text-gray-700">
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 20 20"
                  fill="none"
                  className="text-brand flex-shrink-0 mt-0.5"
                >
                  <path
                    d="M5 10l3.5 3.5L15 7"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
                {feature}
              </li>
            ))}
          </ul>

          <button
            onClick={handleCheckout}
            disabled={loading}
            className="block w-full bg-brand hover:bg-brand-dark disabled:opacity-50 text-white font-semibold text-lg py-4 rounded-full transition-colors text-center cursor-pointer"
          >
            {loading ? "Redirecting..." : "Start your free trial"}
          </button>
          <p className="text-center text-xs text-gray-400 mt-3">
            No credit card required to start
          </p>
        </div>
      </div>
    </section>
  );
}
