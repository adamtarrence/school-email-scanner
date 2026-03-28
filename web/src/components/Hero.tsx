import DigestPreview from "./DigestPreview";

export default function Hero() {
  return (
    <section className="pt-28 pb-16 md:pt-36 md:pb-24 px-4 sm:px-6">
      <div className="max-w-6xl mx-auto grid md:grid-cols-2 gap-12 md:gap-16 items-center">
        {/* Text */}
        <div className="text-center md:text-left">
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-gray-900 leading-tight">
            Your school emails,{" "}
            <span className="text-brand">skimmed.</span>
          </h1>
          <p className="mt-5 text-lg sm:text-xl text-gray-600 max-w-lg mx-auto md:mx-0">
            Dozens of school emails become a 2-minute daily digest. Action items,
            events, and updates — grouped by child, delivered at 6 PM.
          </p>
          <div className="mt-8 flex flex-col sm:flex-row gap-3 justify-center md:justify-start">
            <a
              href="#pricing"
              className="bg-brand hover:bg-brand-dark text-white font-semibold text-lg px-8 py-4 rounded-full transition-colors text-center"
            >
              Start your free trial
            </a>
            <a
              href="#how-it-works"
              className="text-gray-600 hover:text-gray-900 font-medium text-lg px-8 py-4 rounded-full border border-gray-200 hover:border-gray-300 transition-colors text-center"
            >
              See how it works
            </a>
          </div>
          <p className="mt-4 text-sm text-gray-400">
            14-day free trial. No credit card required.
          </p>
        </div>

        {/* Digest Preview */}
        <div className="flex justify-center md:justify-end">
          <DigestPreview />
        </div>
      </div>
    </section>
  );
}
