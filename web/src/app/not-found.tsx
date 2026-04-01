import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="max-w-md text-center">
        <h1 className="text-6xl font-bold text-gray-200 mb-4">404</h1>
        <h2 className="text-2xl font-bold text-gray-900 mb-3">
          Page not found
        </h2>
        <p className="text-gray-600 mb-6">
          This page doesn&apos;t exist. Maybe it was moved, or maybe it
          never was.
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
