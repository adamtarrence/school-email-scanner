import Link from "next/link";

export const metadata = {
  title: "Unsubscribed - SchoolSkim",
};

export default function UnsubscribePage() {
  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="max-w-md text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-3">
          You&apos;ve been unsubscribed
        </h1>
        <p className="text-gray-600 mb-6">
          You won&apos;t receive any more digest emails from SchoolSkim.
          If this was a mistake, you can resubscribe anytime.
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
