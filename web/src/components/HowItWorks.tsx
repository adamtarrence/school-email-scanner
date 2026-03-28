const steps = [
  {
    icon: (
      <svg
        width="40"
        height="40"
        viewBox="0 0 40 40"
        fill="none"
        className="text-brand"
      >
        <circle cx="20" cy="20" r="20" fill="currentColor" opacity="0.1" />
        <path
          d="M12 16l8 5 8-5"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <rect
          x="12"
          y="14"
          width="16"
          height="12"
          rx="2"
          stroke="currentColor"
          strokeWidth="2"
        />
        <path
          d="M27 17l3-2v10l-3-2"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    ),
    title: "Forward your emails",
    description:
      "Set up a one-time forwarding rule in Gmail or Outlook. School emails automatically flow to your SchoolSkim address.",
  },
  {
    icon: (
      <svg
        width="40"
        height="40"
        viewBox="0 0 40 40"
        fill="none"
        className="text-brand"
      >
        <circle cx="20" cy="20" r="20" fill="currentColor" opacity="0.1" />
        <path
          d="M20 12l2 4 4.5.7-3.25 3.2.75 4.6L20 22.2l-4 2.3.75-4.6L13.5 16.7l4.5-.7z"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinejoin="round"
        />
        <path
          d="M14 27h12"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
        />
      </svg>
    ),
    title: "AI reads and summarizes",
    description:
      "Our AI identifies action items, extracts events, and filters out the noise — so you don't have to.",
  },
  {
    icon: (
      <svg
        width="40"
        height="40"
        viewBox="0 0 40 40"
        fill="none"
        className="text-brand"
      >
        <circle cx="20" cy="20" r="20" fill="currentColor" opacity="0.1" />
        <rect
          x="14"
          y="11"
          width="12"
          height="18"
          rx="2"
          stroke="currentColor"
          strokeWidth="2"
        />
        <path
          d="M18 26h4"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
        />
        <path
          d="M17 16h6M17 19h4"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
        />
      </svg>
    ),
    title: "Read your digest each evening",
    description:
      "A clean daily briefing lands in your inbox at your chosen time. Two minutes over dinner and you're caught up.",
  },
];

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="py-16 md:py-24 bg-gray-50 px-4 sm:px-6">
      <div className="max-w-6xl mx-auto">
        <h2 className="text-3xl sm:text-4xl font-bold text-center text-gray-900 mb-4">
          How it works
        </h2>
        <p className="text-center text-gray-500 mb-12 max-w-2xl mx-auto">
          Set it up once, then forget about it. Your digest arrives every school day.
        </p>

        <div className="grid md:grid-cols-3 gap-8 md:gap-12">
          {steps.map((step, i) => (
            <div key={i} className="text-center md:text-left">
              <div className="flex justify-center md:justify-start mb-4">
                {step.icon}
              </div>
              <div className="text-sm font-bold text-brand mb-1">
                Step {i + 1}
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">
                {step.title}
              </h3>
              <p className="text-gray-600 leading-relaxed">
                {step.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
