import React from "react";
import experienceHtml from "../component/experience.html?raw";
import educationHtml from "../component/education.html?raw";
import publicationsHtml from "../component/publications.html?raw";
import arxivHtml from "../component/arxiv.html?raw";
import mlcommonsHtml from "../component/mlcommons.html?raw";
import doctoralPublicationsHtml from "../component/doctoral-publications.html?raw";
import patentsHtml from "../component/patents.html?raw";
import awardsHtml from "../component/awards.html?raw";
import talksHtml from "../component/talks.html?raw";
import blogsHtml from "../component/blogs.html?raw";
import teachingHtml from "../component/teaching.html?raw";
import professionalServicesHtml from "../component/professional-services.html?raw";

const CONSULTING_FORM_ENDPOINT = import.meta.env.VITE_CONSULTING_FORM_ENDPOINT;

const navItems = [
  ["#highlights", "Highlights"],
  ["#experience", "Experience"],
  ["#education", "Education"],
  ["#pubs", "Publications"],
  ["#arxiv", "arXiv"],
  ["#mlcommons", "MLCommons"],
  ["#patents", "Patents"],
  ["#awards", "Awards"],
  ["#talks", "Talks"],
  ["#blogs", "Blogs"],
  ["#teaching", "Teaching"],
  ["#professional-services", "Services"],
  ["#ai-consulting", "AI Consulting"],
];

const sectionModules = [
  experienceHtml,
  educationHtml,
  publicationsHtml,
  arxivHtml,
  mlcommonsHtml,
  doctoralPublicationsHtml,
  patentsHtml,
  awardsHtml,
  talksHtml,
  blogsHtml,
  teachingHtml,
  professionalServicesHtml,
];

function extractPageContent(html) {
  const doc = new DOMParser().parseFromString(html, "text/html");
  const content = doc.querySelector("[data-page-content]");
  return content ? content.innerHTML : html;
}

function Header() {
  return (
    <header role="banner" className="hero">
      <div className="hero-copy">
        <h1>Rajat Ghosh, Ph.D.</h1>
        <p className="hero-subtitle">
          AI-native researcher and builder.
        </p>

        <div className="hero-actions">
          <a className="button primary" href="#ai-consulting">AI Consulting</a>
        </div>
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
