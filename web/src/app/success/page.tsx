import Link from "next/link";

export default function SuccessPage() {
  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="max-w-md text-center">
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
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
        <h1 className="text-3xl font-bold text-gray-900 mb-3">
          Welcome to SchoolSkim!
        </h1>
        <p className="text-gray-600 mb-6">
          Your 14-day free trial has started. Next up: set up email forwarding
          so we can start building your daily digest.
        </p>
        <div className="bg-gray-50 rounded-xl p-6 text-left mb-6">
          <h2 className="font-semibold text-gray-900 mb-3">
            Your forwarding address:
          </h2>
          <div className="bg-white border border-gray-200 rounded-lg px-4 py-3 font-mono text-sm text-brand select-all">
            u-demo@schoolskim.com
          </div>
          <p className="text-sm text-gray-500 mt-3">
            Set up a forwarding rule in Gmail or Outlook to send school emails
            to this address. You&apos;ll get your first digest this evening.
          </p>
        </div>
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
