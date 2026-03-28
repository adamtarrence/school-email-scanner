export default function Support() {
  return (
    <section className="py-16 px-4 sm:px-6">
      <div className="max-w-2xl mx-auto text-center">
        <div className="w-14 h-14 bg-blue-50 rounded-full flex items-center justify-center mx-auto mb-5">
          <svg
            width="26"
            height="26"
            viewBox="0 0 26 26"
            fill="none"
            className="text-brand"
          >
            <path
              d="M13 2C7 2 2 7 2 13s5 11 11 11 11-5 11-11S19 2 13 2z"
              stroke="currentColor"
              strokeWidth="1.75"
            />
            <path
              d="M10 10c0-1.657 1.343-3 3-3s3 1.343 3 3c0 1.5-1.5 2.5-3 3v1.5"
              stroke="currentColor"
              strokeWidth="1.75"
              strokeLinecap="round"
            />
            <circle cx="13" cy="18.5" r="0.75" fill="currentColor" />
          </svg>
        </div>
        <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-3">
          We&apos;re here to help
        </h2>
        <p className="text-gray-600 mb-6 max-w-md mx-auto">
          Questions about setup, your digest, or your account? We respond same
          day, usually within a few hours.
        </p>
        <a
          href="mailto:hello@schoolskim.com"
          className="inline-flex items-center gap-2 bg-brand hover:bg-brand-dark text-white font-semibold px-8 py-4 rounded-full transition-colors"
        >
          <svg
            width="18"
            height="18"
            viewBox="0 0 18 18"
            fill="none"
          >
            <path
              d="M3 4h12a1 1 0 011 1v8a1 1 0 01-1 1H3a1 1 0 01-1-1V5a1 1 0 011-1z"
              stroke="white"
              strokeWidth="1.5"
            />
            <path
              d="M2 5l7 5 7-5"
              stroke="white"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
          </svg>
          hello@schoolskim.com
        </a>
        <p className="text-sm text-gray-400 mt-3">
          We typically reply within a few hours
        </p>
      </div>
    </section>
  );
}
