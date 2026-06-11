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
          I build production GenAI platforms, evaluation systems, and post-training workflows that turn frontier AI research into measurable enterprise impact.
        </p>

        <div className="hero-actions">
          <a className="button primary" href="https://scholar.google.com/citations?user=rhXtLnQAAAAJ&hl=en&oi=ao" target="_blank" rel="noopener noreferrer">Google Scholar</a>
          <a className="button" href="mailto:rajat.ghosh11@gmail.com">Contact Me</a>
          <a className="button ghost" href="https://www.linkedin.com/in/i-am-rajat" target="_blank" rel="noopener noreferrer">LinkedIn</a>
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

function HtmlSection({ html }) {
  return <div dangerouslySetInnerHTML={{ __html: extractPageContent(html) }} />;
}

function Footer() {
  return (
    <footer className="site-footer">
      <span>Rajat Ghosh, Ph.D.</span>
      <a href="mailto:rajat.ghosh11@gmail.com">rajat.ghosh11@gmail.com</a>
      <span>+1 (404) 697-5789</span>
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
      <Footer />
    </main>
  );
}
