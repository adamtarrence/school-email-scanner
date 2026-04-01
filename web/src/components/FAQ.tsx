"use client";

import { useState } from "react";

const faqs = [
  {
    q: "What email clients does it work with?",
    a: "Any email client that supports forwarding rules — Gmail, Outlook, Apple Mail, Yahoo Mail, and most others. You set up a one-time forwarding rule and SchoolSkim handles the rest.",
  },
  {
    q: "How do I set up email forwarding?",
    a: "After signing up, you'll get a personal forwarding address (e.g. u-abc123@schoolskim.com). In Gmail: Settings → Forwarding → Add forwarding address, then create a filter to forward emails from your school's domain. Step-by-step instructions are included in your welcome email.",
  },
  {
    q: "What schools and districts does it work with?",
    a: "Any school that sends email. SchoolSkim works by forwarding — it doesn't need a direct integration with your school or district. If your school sends emails, SchoolSkim can summarize them.",
  },
  {
    q: "Can I add multiple children?",
    a: "Yes. During onboarding you add each child's name, grade, and school. SchoolSkim groups digest items by child so you always know which update is for whom.",
  },
  {
    q: "What time does the digest arrive?",
    a: "Every school day at the time you choose during onboarding — most parents pick sometime between 5–7 PM. No digest on weekends or school holidays.",
  },
  {
    q: "Is my data private?",
    a: "Yes. SchoolSkim only reads forwarded copies of your emails — your originals stay in your inbox exactly as they arrived, untouched. We never modify, move, or delete anything in your email account. Forwarded content is processed by AI for summarization and is not sold or shared.",
  },
  {
    q: "What if an important email gets missed?",
    a: "Your original emails are never touched — they remain in your inbox exactly as before. The digest links back to each original so you can read the full message anytime. SchoolSkim is a read-only summary layer on top of your existing inbox, not a replacement for it.",
  },
  {
    q: "What about emails that just link to a school portal post?",
    a: "Some schools send emails that say \"your teacher posted an assignment\" but the actual content is behind a login on Schoology, Canvas, or a similar portal. SchoolSkim handles these in two ways: if the linked page is publicly accessible, we fetch the content and include it in your digest. If it requires a login (most portal posts do), we still include a line in your digest noting that something was posted, along with a direct link — so you always know something exists even if we can't read the full content for you.",
  },
  {
    q: "What about safety alerts and emergency notifications?",
    a: "SchoolSkim's digest is designed for routine school communication — newsletters, reminders, and events. For time-sensitive messages like safety alerts, weather closures, or lockdown notifications, we strongly recommend setting up a separate inbox rule to flag those as high priority so they reach you immediately. In Gmail: Settings → Filters → Create a new filter for your school's emergency sender (e.g. SafeArrival, your district's alert system), then mark as Important and apply a Star. That way critical messages land in your inbox the moment they arrive — completely independent of SchoolSkim.",
  },
  {
    q: "How do I cancel?",
    a: "Cancel anytime — no questions asked. Click 'Manage subscription' in any digest email, or email hello@schoolskim.com and we'll cancel it for you immediately.",
  },
];

function FAQItem({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border-b border-gray-100 last:border-0">
      <button
        onClick={() => setOpen(!open)}
        className="w-full text-left py-5 flex justify-between items-start gap-4 cursor-pointer"
      >
        <span className="font-semibold text-gray-900 text-base">{q}</span>
        <svg
          width="20"
          height="20"
          viewBox="0 0 20 20"
          fill="none"
          className={`flex-shrink-0 mt-0.5 text-gray-400 transition-transform duration-200 ${open ? "rotate-180" : ""}`}
        >
          <path
            d="M5 7.5l5 5 5-5"
            stroke="currentColor"
            strokeWidth="1.75"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </button>
      {open && (
        <p className="pb-5 text-gray-600 leading-relaxed text-sm">{a}</p>
      )}
    </div>
  );
}

export default function FAQ() {
  return (
    <section id="faq" className="py-16 md:py-24 bg-gray-50 px-4 sm:px-6">
      <div className="max-w-3xl mx-auto">
        <h2 className="text-3xl sm:text-4xl font-bold text-center text-gray-900 mb-4">
          Frequently asked questions
        </h2>
        <p className="text-center text-gray-500 mb-12">
          Still have questions?{" "}
          <a
            href="mailto:hello@schoolskim.com"
            className="text-brand hover:text-brand-dark font-medium transition-colors"
          >
            Email us
          </a>{" "}
          and we&apos;ll get back to you same day.
        </p>

        <div className="bg-white rounded-2xl border border-gray-200 px-6 divide-y-0">
          {faqs.map((faq, i) => (
            <FAQItem key={i} q={faq.q} a={faq.a} />
          ))}
        </div>
      </div>
    </section>
  );
}
