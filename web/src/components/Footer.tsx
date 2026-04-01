import Link from "next/link";

export default function Footer() {
  const year = new Date().getFullYear();

  return (
    <footer className="bg-gray-50 border-t border-gray-100 py-8 px-4 sm:px-6">
      <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-gray-400">
        <div className="flex items-center gap-2">
          <svg
            width="20"
            height="20"
            viewBox="0 0 28 28"
            fill="none"
            className="text-gray-300"
          >
            <rect width="28" height="28" rx="6" fill="currentColor" />
            <path
              d="M7 10l7 5 7-5"
              stroke="white"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d="M7 10v8a1 1 0 001 1h12a1 1 0 001-1v-8"
              stroke="white"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          <span>&copy; {year} SchoolSkim. All rights reserved.</span>
        </div>
        <div className="flex gap-6">
          <Link href="/privacy" className="hover:text-gray-600 transition-colors">
            Privacy Policy
          </Link>
          <Link href="/terms" className="hover:text-gray-600 transition-colors">
            Terms of Service
          </Link>
          <a
            href="mailto:hello@schoolskim.com"
            className="hover:text-gray-600 transition-colors"
          >
            Contact
          </a>
        </div>
      </div>
    </footer>
  );
}
