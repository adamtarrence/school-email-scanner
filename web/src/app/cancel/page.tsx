import Link from "next/link";

export default function CancelPage() {
  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="max-w-md text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-3">
          No worries!
        </h1>
        <p className="text-gray-600 mb-6">
          You can start your free trial anytime. We&apos;ll be here when
          you&apos;re ready to tame those school emails.
        </p>
        <Link
          href="/"
          className="inline-block bg-brand hover:bg-brand-dark text-white font-semibold px-8 py-4 rounded-full transition-colors"
        >
          Back to SchoolSkim
        </Link>
      </div>
    </div>
  );
}
