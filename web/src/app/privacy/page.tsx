import Link from "next/link";
import Header from "@/components/Header";
import Footer from "@/components/Footer";

export const metadata = {
  title: "Privacy Policy - SchoolSkim",
};

export default function PrivacyPage() {
  return (
    <>
      <Header />
      <main className="pt-24 pb-16 px-4 sm:px-6">
        <div className="max-w-3xl mx-auto">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Privacy Policy
          </h1>
          <p className="text-sm text-gray-400 mb-8">
            Effective April 1, 2026
          </p>

          <div className="space-y-8 text-gray-700 text-[15px] leading-relaxed">
            <section>
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                What SchoolSkim Does
              </h2>
              <p>
                SchoolSkim summarizes your school emails into a short daily
                digest. You forward emails from your child&apos;s school to a
                unique SchoolSkim address, and we send you a summary each
                evening.
              </p>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                Information We Collect
              </h2>
              <ul className="list-disc pl-5 space-y-2">
                <li>
                  <strong>Account information:</strong> your email address,
                  timezone, and preferred delivery time.
                </li>
                <li>
                  <strong>Children&apos;s information:</strong> first names,
                  grade levels, and school names you provide during onboarding.
                  This is used solely to organize your digest by child.
                </li>
                <li>
                  <strong>Forwarded school emails:</strong> the subject, sender,
                  and body of emails you forward to your SchoolSkim address.
                </li>
                <li>
                  <strong>Payment information:</strong> processed and stored
                  entirely by Stripe. We never see or store your card number.
                </li>
              </ul>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                How We Use Your Information
              </h2>
              <ul className="list-disc pl-5 space-y-2">
                <li>
                  Forwarded emails are sent to Anthropic&apos;s Claude AI to
                  generate your daily digest summary. Anthropic does not use this
                  data to train its models.
                </li>
                <li>
                  Your children&apos;s names and school info are included in the
                  AI prompt so the digest can be organized by child.
                </li>
                <li>
                  Your email address is used to deliver your digest and
                  service-related communications.
                </li>
              </ul>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                Data Retention
              </h2>
              <ul className="list-disc pl-5 space-y-2">
                <li>
                  Raw forwarded emails are stored in Amazon S3 and automatically
                  deleted after <strong>7 days</strong>.
                </li>
                <li>
                  Parsed email data in our database is automatically deleted
                  after <strong>30 days</strong>.
                </li>
                <li>
                  Digest summaries (the output, not the original emails) are
                  retained in our database.
                </li>
                <li>
                  Account information is retained until you cancel your
                  subscription or request deletion.
                </li>
              </ul>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                Third-Party Services
              </h2>
              <p className="mb-2">
                We use the following services to operate SchoolSkim:
              </p>
              <ul className="list-disc pl-5 space-y-2">
                <li>
                  <strong>Anthropic (Claude AI):</strong> generates digest
                  summaries from your forwarded emails.
                </li>
                <li>
                  <strong>Amazon Web Services:</strong> email receiving (SES),
                  data storage (DynamoDB, S3), and compute (Lambda).
                </li>
                <li>
                  <strong>Stripe:</strong> payment processing and subscription
                  management.
                </li>
                <li>
                  <strong>Vercel:</strong> web application hosting.
                </li>
              </ul>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                What We Don&apos;t Do
              </h2>
              <ul className="list-disc pl-5 space-y-2">
                <li>We do not sell, rent, or share your data with third parties for marketing purposes.</li>
                <li>We do not use your data for advertising.</li>
                <li>We do not collect information directly from children.</li>
              </ul>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                Children&apos;s Privacy (COPPA)
              </h2>
              <p>
                SchoolSkim is a service for parents. We do not knowingly collect
                personal information directly from children under 13. The
                children&apos;s names and school information we store are
                provided by the parent and used solely to organize the
                parent&apos;s digest.
              </p>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                Your Rights
              </h2>
              <ul className="list-disc pl-5 space-y-2">
                <li>
                  You can cancel your subscription at any time through
                  Stripe&apos;s customer portal.
                </li>
                <li>
                  You can request deletion of all your data by emailing{" "}
                  <a
                    href="mailto:hello@schoolskim.com"
                    className="text-brand hover:underline"
                  >
                    hello@schoolskim.com
                  </a>
                  .
                </li>
                <li>
                  Every digest email includes an unsubscribe link.
                </li>
              </ul>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                Changes to This Policy
              </h2>
              <p>
                We may update this policy from time to time. If we make
                significant changes, we&apos;ll notify you by email.
              </p>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                Contact
              </h2>
              <p>
                Questions about this policy? Email us at{" "}
                <a
                  href="mailto:hello@schoolskim.com"
                  className="text-brand hover:underline"
                >
                  hello@schoolskim.com
                </a>
                .
              </p>
            </section>
          </div>

          <div className="mt-12 pt-8 border-t border-gray-100">
            <Link
              href="/"
              className="text-brand hover:underline text-sm"
            >
              &larr; Back to SchoolSkim
            </Link>
          </div>
        </div>
      </main>
      <Footer />
    </>
  );
}
