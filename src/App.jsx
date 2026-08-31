import React from "react";
import { getCalApi } from "@calcom/embed-react";
import experienceHtml from "../component/experience.html?raw";
import educationHtml from "../component/education.html?raw";
import publicationsHtml from "../component/publications.html?raw";
import arxivHtml from "../component/arxiv.html?raw";
import mlcommonsHtml from "../component/mlcommons.html?raw";
import doctoralPublicationsHtml from "../component/doctoral-publications.html?raw";
import patentsHtml from "../component/patents.html?raw";
import mediaHtml from "../component/media.html?raw";
import softwarePackagesHtml from "../component/software-packages.html?raw";
import awardsHtml from "../component/awards.html?raw";
import talksHtml from "../component/talks.html?raw";
import blogsHtml from "../component/blogs.html?raw";
import teachingHtml from "../component/teaching.html?raw";
import tutorialsHtml from "../component/tutorials.html?raw";
import professionalServicesHtml from "../component/professional-services.html?raw";

const CONSULTING_FORM_ENDPOINT = import.meta.env.VITE_CONSULTING_FORM_ENDPOINT;

// Cal.com booking link, e.g. "rajat-ghosh/consultation". The "Book a call"
// button only renders when this is set, so the page degrades gracefully.
const CAL_LINK = import.meta.env.VITE_CAL_LINK;
const CAL_NAMESPACE = "consultation";

// Gated "My Resources" chip. This site is fully static (GitHub Pages, no
// server), so this is obfuscation, not real access control: the resource files
// still live at fixed public URLs. We store only a SHA-256 of `username:password`
// so the plaintext credential never ships in the bundle, and keep the resources
// out of sitemap.xml / robots.txt so they are not indexed.
const RESOURCES_HASH =
  "5355a870efaa9a533658b9b77e977dfe3b11bcdf7669bf802d2f03a6c2c89caf";
const RESOURCES = [
  ["omscs-cn-exam2.html", "CN Study Deck"],
  ["cn-module-07-08-question-pool.pdf", "CN Modules 7–8 — SDN (Question Pool PDF)"],
  ["cn-module-09-question-pool.pdf", "CN Module 9 — Internet Security (Question Pool PDF)"],
  ["cn-module-10-question-pool.pdf", "CN Module 10 — Surveillance & Censorship (Question Pool PDF)"],
  ["cn-module-11-question-pool.pdf", "CN Module 11 — Video & Multimedia (Question Pool PDF)"],
  ["cn-module-12-question-pool.pdf", "CN Module 12 — CDNs & Overlay Networks (Question Pool PDF)"],
];

async function sha256Hex(str) {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(str));
  return Array.from(new Uint8Array(buf))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

const navItems = [
  ["#highlights", "Highlights"],
  ["#experience", "Experience"],
  ["#education", "Education"],
  ["#pubs", "Publications"],
  ["#arxiv", "arXiv"],
  ["#mlcommons", "MLCommons"],
  ["#patents", "Patents"],
  ["#software-packages", "Software"],
  ["#awards", "Awards"],
  ["#talks", "Talks"],
  ["#blogs", "Blogs"],
  ["#teaching", "Teaching"],
  ["#tutorials", "Tutorials"],
  ["#professional-services", "Services"],
];

const sectionModules = [
  experienceHtml,
  educationHtml,
  publicationsHtml,
  arxivHtml,
  mlcommonsHtml,
  doctoralPublicationsHtml,
  patentsHtml,
  mediaHtml,
  softwarePackagesHtml,
  awardsHtml,
  talksHtml,
  blogsHtml,
  teachingHtml,
  tutorialsHtml,
  professionalServicesHtml,
];

function extractPageContent(html) {
  const doc = new DOMParser().parseFromString(html, "text/html");
  const content = doc.querySelector("[data-page-content]");
  return content ? content.innerHTML : html;
}

function ResourcesChip() {
  const [open, setOpen] = React.useState(false);
  const [unlocked, setUnlocked] = React.useState(
    () => sessionStorage.getItem("resources-unlocked") === "1",
  );
  const [error, setError] = React.useState("");
  const [checking, setChecking] = React.useState(false);

  React.useEffect(() => {
    if (!open) return;
    const onKey = (e) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open]);

  async function handleSubmit(event) {
    event.preventDefault();
    setChecking(true);
    setError("");

    const data = new FormData(event.currentTarget);
    const username = (data.get("username") || "").trim();
    const password = data.get("password") || "";
    const hash = await sha256Hex(`${username}:${password}`);

    if (hash === RESOURCES_HASH) {
      sessionStorage.setItem("resources-unlocked", "1");
      setUnlocked(true);
    } else {
      setError("Incorrect username or password.");
    }
    setChecking(false);
  }

  return (
    <>
      <button
        type="button"
        className="nav-chip"
        aria-haspopup="dialog"
        onClick={() => setOpen(true)}
      >
        My Resources
      </button>

      {open && (
        <div
          className="resource-modal-backdrop"
          role="presentation"
          onClick={() => setOpen(false)}
        >
          <div
            className="resource-modal"
            role="dialog"
            aria-modal="true"
            aria-label="My Resources"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              type="button"
              className="resource-modal-close"
              aria-label="Close"
              onClick={() => setOpen(false)}
            >
              &times;
            </button>
            <h2>My Resources</h2>

            {unlocked ? (
              <ul className="resource-list">
                {RESOURCES.map(([href, label]) => (
                  <li key={href}>
                    <a href={href} target="_blank" rel="noopener noreferrer">
                      {label}
                    </a>
                  </li>
                ))}
              </ul>
            ) : (
              <form className="resource-form" onSubmit={handleSubmit}>
                <p>Enter your credentials to view protected resources.</p>
                <label>
                  Username
                  <input type="text" name="username" autoComplete="off" required />
                </label>
                <label>
                  Password
                  <input
                    type="password"
                    name="password"
                    autoComplete="off"
                    required
                  />
                </label>
                <button className="button primary" type="submit" disabled={checking}>
                  {checking ? "Checking…" : "Unlock"}
                </button>
                {error && (
                  <p className="form-status error" role="alert">
                    {error}
                  </p>
                )}
              </form>
            )}
          </div>
        </div>
      )}
    </>
  );
}

function Header() {
  return (
    <header role="banner" className="hero">
      <div className="hero-copy">
        <h1>Rajat Ghosh, Ph.D.</h1>
        <p className="hero-subtitle">
          AI-native researcher and builder.
        </p>
      </div>

      <img
        className="headshot"
        src="assets/rajat_ghosh.jpeg"
        alt="Rajat Ghosh"
      />

      <nav aria-label="Page sections" className="site-nav">
        {navItems.map(([href, label]) => (
          <a key={href} href={href}>{label}</a>
        ))}
        <a href="resume_rajat-ghosh.pdf" target="_blank" rel="noopener noreferrer">Resume</a>
        <a href="#media" className="nav-chip">Media</a>
        <a
          href="https://substack.com/@rajatghosh1?utm_source=user-menu"
          className="nav-chip"
          target="_blank"
          rel="noopener noreferrer"
        >
          Substack
        </a>
        <ResourcesChip />
      </nav>
    </header>
  );
}

function Highlights() {
  const highlights = [
    ["GenAI Platforms", "Built company-scale LLM agents for code search, PR review, unit testing, and support automation."],
    ["Business Impact", "Delivered multi-million-dollar annual savings via productivity gains and vendor replacement."],
    ["Post-Training", "Led RLHF/post-training, evaluation, and safety pipelines for production readiness."],
    ["Cross-Functional", "Drove enterprise rollout across Product, Infra, Security, Legal, and executive stakeholders."],
    ["Research", "Published work across LLM alignment, benchmarking, AI safety, and reinforcement learning."],
  ];

  return (
    <section id="highlights" className="highlight-section">
      <h2>Highlights</h2>
      <div className="highlight-grid">
        {highlights.map(([title, detail]) => (
          <article className="highlight-card" key={title}>
            <h3>{title}</h3>
            <p>{detail}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

function AIConsulting() {
  const [formStatus, setFormStatus] = React.useState("idle");
  const [formMessage, setFormMessage] = React.useState("");

  React.useEffect(() => {
    if (!CAL_LINK) return;
    (async () => {
      const cal = await getCalApi({ namespace: CAL_NAMESPACE });
      cal("ui", { hideEventTypeDetails: false, layout: "month_view" });
    })();
  }, []);

  async function handleConsultingSubmit(event) {
    event.preventDefault();

    if (!CONSULTING_FORM_ENDPOINT) {
      setFormStatus("error");
      setFormMessage("Consultation requests are not configured yet. Please email rajat.ghosh11@gmail.com.");
      return;
    }

    setFormStatus("submitting");
    setFormMessage("");

    // Capture the form node now: React nulls event.currentTarget after the
    // synchronous handler returns, so it is unusable past the await below.
    const form = event.currentTarget;
    const formData = new FormData(form);
    const name = formData.get("name");
    formData.append("_subject", `AI consulting request from ${name}`);

    try {
      const response = await fetch(CONSULTING_FORM_ENDPOINT, {
        method: "POST",
        body: formData,
        headers: {
          Accept: "application/json",
        },
      });

      if (!response.ok) {
        throw new Error("Form submission failed");
      }

      form.reset();
      setFormStatus("success");
      setFormMessage("Thanks. Your request was sent successfully.");
    } catch {
      setFormStatus("error");
      setFormMessage("Sorry, the request could not be sent. Please email rajat.ghosh11@gmail.com.");
    }
  }

  return (
    <section id="ai-consulting" className="consulting-section">
      <div className="consulting-copy">
        <h2>AI Consulting</h2>
        <p>
          Advisory and hands-on support for teams building GenAI platforms, evaluation systems, post-training workflows, and AI-native developer tools.
        </p>
        {CAL_LINK && (
          <div className="consulting-booking">
            <p>Prefer to talk it through? Book a time that works for you.</p>
            <button
              type="button"
              className="button primary"
              data-cal-namespace={CAL_NAMESPACE}
              data-cal-link={CAL_LINK}
              data-cal-config='{"layout":"month_view"}'
            >
              Book a call
            </button>
          </div>
        )}
      </div>

      <form
        className="consulting-form"
        onSubmit={handleConsultingSubmit}
      >
        <label>
          Name
          <input type="text" name="name" autoComplete="name" required />
        </label>

        <label>
          Email
          <input type="email" name="email" autoComplete="email" required />
        </label>

        <label>
          Organization
          <input type="text" name="organization" autoComplete="organization" />
        </label>

        <label>
          Consulting Area
          <select name="consulting_area" defaultValue="GenAI platform strategy">
            <option>GenAI platform strategy</option>
            <option>LLM evaluation and benchmarking</option>
            <option>Post-training and alignment</option>
            <option>AI agents for engineering workflows</option>
            <option>AI safety and risk evaluation</option>
            <option>Other</option>
          </select>
        </label>

        <label className="full-span">
          What are you trying to build?
          <textarea name="project_details" rows="5" required />
        </label>

        <button className="button primary" type="submit" disabled={formStatus === "submitting"}>
          {formStatus === "submitting" ? "Sending..." : "Request Consultation"}
        </button>

        {formMessage && (
          <p className={`form-status ${formStatus}`} role="status">
            {formMessage}
          </p>
        )}
      </form>
    </section>
  );
}

function HtmlSection({ html }) {
  return <div dangerouslySetInnerHTML={{ __html: extractPageContent(html) }} />;
}

function Footer() {
  return (
    <footer className="site-footer">
      <span>Rajat Ghosh, Ph.D.</span>
      <a href="mailto:rajat.ghosh11@gmail.com">rajat.ghosh11@gmail.com</a>
      <span>+1 (404) 697-5789</span>
      <a href="https://scholar.google.com/citations?user=rhXtLnQAAAAJ&hl=en&oi=ao" target="_blank" rel="noopener noreferrer">Google Scholar</a>
      <a href="https://www.linkedin.com/in/i-am-rajat" target="_blank" rel="noopener noreferrer">LinkedIn</a>
      <a href="resume_rajat-ghosh.pdf" target="_blank" rel="noopener noreferrer">Resume</a>
    </footer>
  );
}

export default function App() {
  return (
    <main className="site-shell">
      <Header />
      <Highlights />
      {sectionModules.map((html, index) => (
        <HtmlSection key={index} html={html} />
      ))}
      <AIConsulting />
      <Footer />
    </main>
  );
}
