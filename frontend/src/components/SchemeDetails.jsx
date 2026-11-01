import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { getScheme } from "../services/api";
import { useSavedSchemes } from "../SavedSchemesContext";
import "../SchemeDetails.css";

function SchemeDetails() {
    const { schemeId } = useParams();
    const navigate = useNavigate();

    const { isSaved, toggleSaved } = useSavedSchemes();

    const [scheme, setScheme] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    const [expandedSections, setExpandedSections] = useState({
        Description: true,
        Benefits: true,
        Eligibility: false,
        "Required Documents": false,
        "Application Process": false,
    });

    useEffect(() => {
        let cancelled = false;

        async function loadScheme() {
            try {
                setLoading(true);
                setError("");

                const data = await getScheme(schemeId);

                if (!cancelled) {
                    setScheme(data?.scheme ?? null);
                }
            } catch (err) {
                console.error(
                    "Failed to load scheme details:",
                    err
                );

                if (!cancelled) {
                    setError(
                        "We couldn't load this scheme right now. Please try again."
                    );
                }
            } finally {
                if (!cancelled) {
                    setLoading(false);
                }
            }
        }

        loadScheme();

        return () => {
            cancelled = true;
        };
    }, [schemeId]);

    const renderValue = (
        value,
        fallback = "Information not available yet."
    ) => {
        if (value === null || value === undefined) {
            return fallback;
        }

        const text = String(value).trim();

        if (
            !text ||
            ["nan", "null", "undefined"].includes(
                text.toLowerCase()
            )
        ) {
            return fallback;
        }

        return text;
    };

    const toggleSection = (title) => {
        setExpandedSections((previous) => ({
            ...previous,
            [title]: !previous[title],
        }));
    };

    const renderContent = (value) => {
        const text = renderValue(value);

        if (text === "Information not available yet.") {
            return <p className="sd-empty">{text}</p>;
        }

        const items = text
            .split(/\n|;|\r/)
            .map((item) =>
                item.replace(/^[\s•*-]+/, "").trim()
            )
            .filter(Boolean);

        if (items.length > 1) {
            return (
                <ul className="sd-content-list">
                    {items.map((item, index) => (
                        <li key={`${item}-${index}`}>
                            {item}
                        </li>
                    ))}
                </ul>
            );
        }

        return (
            <p className="sd-content-text">{text}</p>
        );
    };

    const getOfficialLinks = () => {
        const raw =
            scheme?.Official_url ??
            scheme?.official_url;

        if (
            !raw ||
            ["nan", "null", "undefined"].includes(
                String(raw).trim().toLowerCase()
            )
        ) {
            return [];
        }

        return String(raw)
            .split(";")
            .map((url) => url.trim())
            .filter((url) => {
                try {
                    const parsed = new URL(url);

                    return (
                        parsed.protocol === "https:" ||
                        parsed.protocol === "http:"
                    );
                } catch {
                    return false;
                }
            });
    };

    const sections = [
        {
            title: "Description",
            icon: "📘",
            subtitle: "Understand what this scheme offers",
            content:
                scheme?.Description ??
                scheme?.description,
        },
        {
            title: "Benefits",
            icon: "🎁",
            subtitle: "Financial support and other benefits",
            content:
                scheme?.Benefits ??
                scheme?.benefits,
        },
        {
            title: "Eligibility",
            icon: "✅",
            subtitle: "Who can apply for this scheme",
            content:
                scheme?.Eligibility ??
                scheme?.eligibility,
        },
        {
            title: "Required Documents",
            icon: "📄",
            subtitle: "Documents you may need to prepare",
            content:
                scheme?.Required_documents ??
                scheme?.required_documents ??
                scheme?.documents_required,
        },
        {
            title: "Application Process",
            icon: "📝",
            subtitle: "How to get started",
            content:
                scheme?.Application_mode ??
                scheme?.application_mode ??
                scheme?.application_process,
        },
    ];

    if (loading) {
        return (
            <div className="sd-page">
                <div className="sd-loading">
                    <div className="sd-spinner" />
                    <h2>Loading scheme details</h2>
                    <p>
                        Getting the information ready for you...
                    </p>
                </div>
            </div>
        );
    }

    if (error || !scheme) {
        return (
            <div className="sd-page">
                <div className="sd-error-card">
                    <span className="sd-error-icon">!</span>

                    <h2>
                        {error
                            ? "Something went wrong"
                            : "Scheme not found"}
                    </h2>

                    <p>
                        {error ||
                            "We couldn't find the scheme you're looking for."}
                    </p>

                    <button
                        type="button"
                        className="sd-primary-button"
                        onClick={() =>
                            navigate("/browse-schemes")
                        }
                    >
                        ← Back to Schemes
                    </button>
                </div>
            </div>
        );
    }

    const schemeName = renderValue(
        scheme.Scholarship ??
            scheme.scheme_name ??
            scheme.name,
        "Government Scheme"
    );

    const category = renderValue(
        scheme.Category ?? scheme.category,
        "Government Scheme"
    );

    const ministry = renderValue(
        scheme.Ministry ?? scheme.ministry
    );

    const targetGroup = renderValue(
        scheme.Target_group ?? scheme.target_group
    );

    const officialLinks = getOfficialLinks();

    const libraryScheme = {
        ...scheme,
        scheme_id: String(schemeId),
        scheme_name: schemeName,
        description:
            scheme.Description ??
            scheme.description ??
            "No description available.",
        category:
            scheme.Category ??
            scheme.category ??
            "",
        ministry:
            scheme.Ministry ??
            scheme.ministry ??
            "",
        Official_url:
            scheme.Official_url ??
            scheme.official_url ??
            "",
        Benefits:
            scheme.Benefits ??
            scheme.benefits ??
            "",
        Eligibility:
            scheme.Eligibility ??
            scheme.eligibility ??
            "",
        Required_documents:
            scheme.Required_documents ??
            scheme.required_documents ??
            scheme.documents_required ??
            "",
        Application_mode:
            scheme.Application_mode ??
            scheme.application_mode ??
            scheme.application_process ??
            "",
    };

    const saved = isSaved(libraryScheme);

    const handleToggleSaved = () => {
        toggleSaved(libraryScheme);
    };

    return (
        <main className="sd-page">
            <div className="sd-container">
                <Link
                    to="/browse-schemes"
                    className="sd-back-link"
                >
                    <span aria-hidden="true">←</span>
                    Back to Schemes
                </Link>

                {/* Scheme hero */}
                <section className="sd-hero">
                    <div className="sd-hero-decoration sd-decoration-one" />
                    <div className="sd-hero-decoration sd-decoration-two" />

                    <div className="sd-hero-content">
                        <span className="sd-eyebrow">
                            <span className="sd-live-dot" />
                            GOVERNMENT SCHEME DETAILS
                        </span>

                        <span className="sd-category-pill">
                            {category}
                        </span>

                        {/* Scheme title with pink heart button */}
                        <div className="sd-title-with-heart">
                            <h1>{schemeName}</h1>

                            <button
                                type="button"
                                className={`sd-save-heart ${
                                    saved ? "is-saved" : ""
                                }`}
                                onClick={handleToggleSaved}
                                aria-label={
                                    saved
                                        ? "Remove scheme from My Library"
                                        : "Save scheme to My Library"
                                }
                                aria-pressed={saved}
                                title={
                                    saved
                                        ? "Remove from My Library"
                                        : "Save to My Library"
                                }
                            >
                                <span
                                    className="sd-heart-emoji"
                                    aria-hidden="true"
                                >
                                    {saved ? "💗" : "🤍"}
                                </span>
                            </button>
                        </div>

                        <p className="sd-hero-description">
                            Explore the scheme's benefits, eligibility
                            criteria, documents, and application information
                            in one place.
                        </p>

                        <div className="sd-hero-actions">
                            <button
                                type="button"
                                className="sd-primary-button"
                                onClick={() =>
                                    navigate(
                                        `/schemes/${encodeURIComponent(
                                            String(schemeId)
                                        )}/eligibility`
                                    )
                                }
                            >
                                Check My Eligibility <span>→</span>
                            </button>

                            {officialLinks.length > 0 && (
                                <a
                                    className="sd-secondary-button"
                                    href={officialLinks[0]}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                >
                                    Official Website ↗
                                </a>
                            )}
                        </div>

                        {saved && (
                            <p
                                className="sd-saved-message"
                                role="status"
                            >
                                💗 This scheme is in your Library.{" "}
                                <Link to="/library">
                                    View Library
                                </Link>
                            </p>
                        )}
                    </div>
                </section>

                {/* Overview cards */}
                <section className="sd-overview">
                    <article className="sd-overview-card">
                        <div className="sd-overview-icon sd-icon-blue">
                            🏛️
                        </div>
                        <div>
                            <span className="sd-overview-label">
                                Ministry / Department
                            </span>
                            <h3>{ministry}</h3>
                        </div>
                    </article>

                    <article className="sd-overview-card">
                        <div className="sd-overview-icon sd-icon-purple">
                            🎯
                        </div>
                        <div>
                            <span className="sd-overview-label">
                                Target Beneficiaries
                            </span>
                            <h3>{targetGroup}</h3>
                        </div>
                    </article>

                    <article className="sd-overview-card">
                        <div className="sd-overview-icon sd-icon-green">
                            🏷️
                        </div>
                        <div>
                            <span className="sd-overview-label">
                                Scheme Category
                            </span>
                            <h3>{category}</h3>
                        </div>
                    </article>
                </section>

                {/* Scheme contents */}
                <div className="sd-content-layout">
                    <section className="sd-main-content">
                        <div className="sd-section-heading">
                            <div>
                                <span className="sd-section-kicker">
                                    YOUR GUIDE
                                </span>
                                <h2>Everything you need to know</h2>
                                <p>
                                    Open a section to explore its details.
                                </p>
                            </div>

                            <button
                                type="button"
                                className="sd-text-button"
                                onClick={() => {
                                    const allExpanded = sections.every(
                                        (section) =>
                                            expandedSections[section.title]
                                    );

                                    setExpandedSections(
                                        Object.fromEntries(
                                            sections.map((section) => [
                                                section.title,
                                                !allExpanded,
                                            ])
                                        )
                                    );
                                }}
                            >
                                {sections.every(
                                    (section) =>
                                        expandedSections[section.title]
                                )
                                    ? "Collapse all −"
                                    : "Expand all +"}
                            </button>
                        </div>

                        <div className="sd-accordion-list">
                            {sections.map((section, index) => {
                                const isOpen = Boolean(
                                    expandedSections[section.title]
                                );

                                return (
                                    <article
                                        className={`sd-accordion ${
                                            isOpen ? "is-open" : ""
                                        }`}
                                        key={section.title}
                                    >
                                        <button
                                            type="button"
                                            className="sd-accordion-trigger"
                                            onClick={() =>
                                                toggleSection(section.title)
                                            }
                                            aria-expanded={isOpen}
                                        >
                                            <span className="sd-accordion-icon">
                                                {section.icon}
                                            </span>

                                            <span className="sd-accordion-heading">
                                                <strong>
                                                    <span className="sd-number">
                                                        {String(
                                                            index + 1
                                                        ).padStart(2, "0")}
                                                    </span>
                                                    {section.title}
                                                </strong>
                                                <small>
                                                    {section.subtitle}
                                                </small>
                                            </span>

                                            <span className="sd-chevron">
                                                {isOpen ? "−" : "+"}
                                            </span>
                                        </button>

                                        {isOpen && (
                                            <div className="sd-accordion-content">
                                                {renderContent(
                                                    section.content
                                                )}
                                            </div>
                                        )}
                                    </article>
                                );
                            })}
                        </div>
                    </section>

                    {/* Right sidebar */}
                    <aside className="sd-sidebar">
                        <div className="sd-apply-card">
                            <div className="sd-apply-icon">🚀</div>
                            <span className="sd-section-kicker">
                                NEXT STEP
                            </span>
                            <h2>Could you be eligible?</h2>
                            <p>
                                Answer a few questions about yourself to check
                                your eligibility for this scheme.
                            </p>

                            <button
                                type="button"
                                className="sd-primary-button sd-full-button"
                                onClick={() =>
                                    navigate(
                                        `/schemes/${encodeURIComponent(
                                            String(schemeId)
                                        )}/eligibility`
                                    )
                                }
                            >
                                Check Eligibility <span>→</span>
                            </button>

                            <div className="sd-apply-note">
                                <span>🔒</span>
                                Review the official scheme guidelines
                                before applying.
                            </div>
                        </div>

                        <div className="sd-checklist-card">
                            <h3>Before you apply</h3>
                            <p>A few helpful reminders</p>

                            <ul>
                                <li>
                                    <span>✓</span>
                                    Read the eligibility criteria
                                </li>
                                <li>
                                    <span>✓</span>
                                    Prepare the required documents
                                </li>
                                <li>
                                    <span>✓</span>
                                    Verify details on the official website
                                </li>
                            </ul>
                        </div>

                        <div className="sd-official-card">
                            <div className="sd-official-icon">🌐</div>
                            <div>
                                <h3>Official information</h3>
                                <p>
                                    Use the official source for the latest
                                    guidelines.
                                </p>
                            </div>

                            {officialLinks.length > 0 ? (
                                officialLinks.map((url, index) => (
                                    <a
                                        className="sd-official-link"
                                        key={`${url}-${index}`}
                                        href={url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                    >
                                        Visit official source{" "}
                                        {officialLinks.length > 1
                                            ? index + 1
                                            : ""}{" "}
                                        ↗
                                    </a>
                                ))
                            ) : (
                                <p className="sd-empty">
                                    Official link not available.
                                </p>
                            )}
                        </div>

                        <div className="sd-save-card">
                            <span className="sd-save-card-heart">
                                {saved ? "💗" : "🤍"}
                            </span>

                            <h3>
                                {saved
                                    ? "Saved for later"
                                    : "Keep this scheme handy"}
                            </h3>

                            <p>
                                {saved
                                    ? "You can revisit this scheme from your Library."
                                    : "Add this scheme to your personal Library to find it easily later."}
                            </p>

                            <button
                                type="button"
                                className="sd-save-card-button"
                                onClick={handleToggleSaved}
                            >
                                {saved
                                    ? "💗 Remove from Library"
                                    : "🤍 Save to Library"}
                            </button>

                            <Link
                                to="/library"
                                className="sd-library-link"
                            >
                                Go to My Library →
                            </Link>
                        </div>
                    </aside>
                </div>

                <footer className="sd-footer">
                    <p>
                        Please verify current eligibility rules and
                        application dates with the official scheme provider
                        before applying.
                    </p>
                    <Link to="/browse-schemes">
                        Explore more schemes →
                    </Link>
                </footer>
            </div>
        </main>
    );
}

export default SchemeDetails;
