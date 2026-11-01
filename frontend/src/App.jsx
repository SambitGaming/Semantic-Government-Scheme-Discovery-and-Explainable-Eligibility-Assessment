
import { useEffect, useState } from "react";

import {
    BrowserRouter,
    Routes,
    Route,
    Link,
    NavLink,
    Navigate,
    Outlet,
    useNavigate,
    useParams,
    useLocation,
} from "react-router-dom";

import {
    getSchemes,
    semanticSearch,
} from "./services/api";

import SchemeCard from "./components/SchemeCard";
import SchemeDetails from "./components/SchemeDetails";
import EligibilityForm from "./components/EligibilityForm";
import Profile from "./components/ProfilePage";
import AuthPage from "./AuthPage";

import {
    SavedSchemesProvider,
    useSavedSchemes,
} from "./SavedSchemesContext";

import "./App.css";

// ======================================================
// STORAGE KEYS
// ======================================================

const AUTH_KEY = "sga_authenticated";
const PROFILE_KEY = "sga_user_profile";

const DEFAULT_PROFILE = {
    name: "",
    email: "",
    phone: "",
    education: "",
    state: "",
    profilePicture: "",
};

function readProfile() {
    try {
        const saved = JSON.parse(
            localStorage.getItem(PROFILE_KEY) || "{}"
        );

        if (
            !saved ||
            typeof saved !== "object" ||
            Array.isArray(saved)
        ) {
            return { ...DEFAULT_PROFILE };
        }

        return {
            ...DEFAULT_PROFILE,
            ...saved,
            profilePicture:
                typeof saved.profilePicture === "string"
                    ? saved.profilePicture
                    : "",
        };
    } catch {
        return { ...DEFAULT_PROFILE };
    }
}

// ======================================================
// REUSABLE PROFILE AVATAR
// ======================================================

function ProfileAvatar({ profile, large = false }) {
    const initial = (
        profile?.name?.trim()?.charAt(0) || "U"
    ).toUpperCase();

    return (
        <span
            className={`profile-avatar ${
                large ? "profile-avatar-large" : ""
            }`}
            aria-label={
                profile?.name
                    ? `${profile.name}'s profile picture`
                    : "Default profile picture"
            }
        >
            {profile?.profilePicture ? (
                <img
                    src={profile.profilePicture}
                    alt=""
                />
            ) : (
                initial
            )}
        </span>
    );
}

// ======================================================
// AUTHENTICATION
// ======================================================

function isAuthenticated() {
    return sessionStorage.getItem(AUTH_KEY) === "true";
}

function RequireAuth({ authenticated }) {
    return authenticated
        ? <Outlet />
        : <Navigate to="/login" replace />;
}

function GuestOnly({ authenticated, mode, onAuthenticated }) {
    if (authenticated) {
        return <Navigate to="/" replace />;
    }

    return (
        <AuthPage
            mode={mode}
            onAuthenticated={onAuthenticated}
        />
    );
}

// ======================================================
// NORMALIZE SCHEME DATA
// ======================================================

function normalizeSchemes(data) {
    const items = Array.isArray(data)
        ? data
        : Array.isArray(data?.schemes)
            ? data.schemes
            : Array.isArray(data?.results)
                ? data.results
                : [];

    return items.map((scheme, index) => ({
        ...scheme,

        scheme_id:
            scheme.scheme_id ??
            scheme.id ??
            scheme.ID ??
            scheme.schemeId ??
            `scheme-${index}`,

        scheme_name:
            scheme.scheme_name &&
            String(scheme.scheme_name).toLowerCase() !== "nan"
                ? String(scheme.scheme_name)
                : scheme.name &&
                    String(scheme.name).toLowerCase() !== "nan"
                    ? String(scheme.name)
                    : "Government Scheme",

        description:
            scheme.description &&
            String(scheme.description).toLowerCase() !== "nan"
                ? String(scheme.description)
                : "No description available.",

        category:
            scheme.category &&
            String(scheme.category).toLowerCase() !== "nan"
                ? String(scheme.category)
                : "",
    }));
}

// ======================================================
// SIDEBAR
// ======================================================

function Sidebar({ onLogout, mobileOpen, setMobileOpen }) {
    const navItems = [
        {
            label: "Home",
            path: "/",
            icon: "⌂",
            end: true,
        },
        {
            label: "Browse Schemes",
            path: "/browse-schemes",
            icon: "▤",
        },
        {
            label: "My Library",
            path: "/library",
            icon: "♥",
        },
        {
            label: "Check Eligibility",
            path: "/eligibility",
            icon: "✓",
        },
        {
            label: "Personalized Recommendations",
            path: "/questionnaire",
            icon: "✧",
        },
        {
            label: "About",
            path: "/about",
            icon: "ⓘ",
        },
    ];

    return (
        <>
            <button
                type="button"
                className="sidebar-mobile-toggle"
                onClick={() => setMobileOpen((open) => !open)}
                aria-label={
                    mobileOpen ? "Close sidebar" : "Open sidebar"
                }
                aria-expanded={mobileOpen}
                aria-controls="app-sidebar"
            >
                {mobileOpen ? "✕" : "☰"}
            </button>

            {mobileOpen && (
                <button
                    type="button"
                    className="sidebar-overlay"
                    aria-label="Close sidebar"
                    onClick={() => setMobileOpen(false)}
                />
            )}

            <aside
                id="app-sidebar"
                className={`app-sidebar ${
                    mobileOpen ? "sidebar-open" : ""
                }`}
                aria-hidden={!mobileOpen}
                inert={!mobileOpen}
            >
                <Link
                    to="/"
                    className="sidebar-brand"
                    onClick={() => setMobileOpen(false)}
                >
                    <span className="brand-mark">SG</span>

                    <span>
                        <strong>Scheme Assistant</strong>
                        <small>Government scheme discovery</small>
                    </span>
                </Link>

                <p className="sidebar-section-label">
                    WORKSPACE
                </p>

                <nav
                    className="sidebar-nav"
                    aria-label="Main navigation"
                >
                    {navItems.map((item) => (
                        <NavLink
                            key={item.path}
                            to={item.path}
                            end={item.end}
                            onClick={() => setMobileOpen(false)}
                            className={({ isActive }) =>
                                `sidebar-link ${
                                    isActive ? "active" : ""
                                }`
                            }
                        >
                            <span className="sidebar-link-icon">
                                {item.icon}
                            </span>

                            <span>{item.label}</span>
                        </NavLink>
                    ))}
                </nav>

                <div className="sidebar-bottom">
                    <div className="sidebar-help">
                        <span className="sidebar-help-icon">i</span>

                        <div>
                            <strong>Need help?</strong>
                            <p>
                                Check scheme details and eligibility
                                requirements.
                            </p>
                        </div>
                    </div>

                    <button
                        type="button"
                        className="sidebar-logout"
                        onClick={onLogout}
                    >
                        <span>↪</span>
                        Logout
                    </button>
                </div>
            </aside>
        </>
    );
}

// ======================================================
// PROFILE DROPDOWN
// ======================================================

function ProfileMenu() {
    const [open, setOpen] = useState(false);
    const [editing, setEditing] = useState(false);
    const [profile, setProfile] = useState(readProfile);
    const [draft, setDraft] = useState(readProfile);
    const [editError, setEditError] = useState("");
    const location = useLocation();

    // Listen for profile changes in this tab and other tabs.
    useEffect(() => {
        function refreshProfile() {
            const updated = readProfile();

            setProfile(updated);
            setDraft(updated);
        }

        window.addEventListener("storage", refreshProfile);
        window.addEventListener("profile-updated", refreshProfile);
        window.addEventListener("sga-profile-updated", refreshProfile);

        return () => {
            window.removeEventListener("storage", refreshProfile);
            window.removeEventListener(
                "profile-updated",
                refreshProfile
            );
            window.removeEventListener(
                "sga-profile-updated",
                refreshProfile
            );
        };
    }, []);

    // Close the dropdown when the user navigates.
    useEffect(() => {
        setOpen(false);
        setEditing(false);
        setEditError("");

        const updated = readProfile();

        setProfile(updated);
        setDraft(updated);
    }, [location.pathname]);

    useEffect(() => {
        function closeOnEscape(event) {
            if (event.key === "Escape") {
                setOpen(false);
                setEditing(false);
                setEditError("");
            }
        }

        window.addEventListener("keydown", closeOnEscape);

        return () => {
            window.removeEventListener("keydown", closeOnEscape);
        };
    }, []);

    function beginEditing() {
        setDraft({ ...profile });
        setEditError("");
        setEditing(true);
        setOpen(true);
    }

    function updateDraft(event) {
        const { name, value } = event.target;

        setDraft((current) => ({
            ...current,
            [name]: value,
        }));

        setEditError("");
    }

    function saveProfile(event) {
        event.preventDefault();

        const updated = {
            ...draft,
            name: draft.name.trim(),
            email: draft.email.trim(),
            phone: draft.phone.trim(),
            education: draft.education.trim(),
            state: draft.state.trim(),
        };

        try {
            localStorage.setItem(
                PROFILE_KEY,
                JSON.stringify(updated)
            );

            setProfile(updated);
            setDraft(updated);
            setEditing(false);
            setOpen(false);
            setEditError("");

            window.dispatchEvent(
                new CustomEvent("profile-updated", {
                    detail: updated,
                })
            );

            window.dispatchEvent(
                new CustomEvent("sga-profile-updated", {
                    detail: updated,
                })
            );
        } catch (error) {
            console.error("Unable to save profile:", error);

            setEditError(
                "Unable to save your profile. Browser storage may be full."
            );
        }
    }

    const displayName = profile.name || "Your Profile";

    return (
        <div className="profile-menu">
            <button
                type="button"
                className="profile-trigger"
                onClick={() => {
                    const updated = readProfile();

                    setProfile(updated);
                    setDraft(updated);
                    setOpen((current) => !current);
                    setEditing(false);
                    setEditError("");
                }}
                aria-expanded={open}
                aria-haspopup="true"
            >
                <ProfileAvatar profile={profile} />

                <span className="profile-trigger-text">
                    <strong>{displayName}</strong>
                    <small>My account</small>
                </span>

                <span className="profile-chevron">
                    {open ? "▴" : "▾"}
                </span>
            </button>

            {open && (
                <>
                    <button
                        type="button"
                        className="profile-dismiss"
                        aria-label="Close profile menu"
                        onClick={() => {
                            setOpen(false);
                            setEditing(false);
                            setEditError("");
                        }}
                    />

                    <section
                        className="profile-dropdown"
                        aria-label="Profile menu"
                    >
                        {editing ? (
                            <>
                                <div className="profile-dropdown-heading">
                                    <h2>Edit your profile</h2>
                                    <p>
                                        Update your personal details.
                                        Use My Profile to change your picture.
                                    </p>
                                </div>

                                <form
                                    className="profile-edit-form"
                                    onSubmit={saveProfile}
                                >
                                    <label>
                                        Full name
                                        <input
                                            name="name"
                                            value={draft.name}
                                            onChange={updateDraft}
                                            placeholder="Enter your name"
                                            maxLength={100}
                                        />
                                    </label>

                                    <label>
                                        Email address
                                        <input
                                            name="email"
                                            type="email"
                                            value={draft.email}
                                            onChange={updateDraft}
                                            placeholder="you@example.com"
                                            maxLength={254}
                                        />
                                    </label>

                                    <label>
                                        Phone number
                                        <input
                                            name="phone"
                                            type="tel"
                                            value={draft.phone}
                                            onChange={updateDraft}
                                            placeholder="Enter phone number"
                                            maxLength={20}
                                        />
                                    </label>

                                    <label>
                                        Education level
                                        <input
                                            name="education"
                                            value={draft.education}
                                            onChange={updateDraft}
                                            placeholder="e.g. MCA student"
                                            maxLength={100}
                                        />
                                    </label>

                                    <label>
                                        State
                                        <input
                                            name="state"
                                            value={draft.state}
                                            onChange={updateDraft}
                                            placeholder="Enter your state"
                                            maxLength={100}
                                        />
                                    </label>

                                    {editError && (
                                        <p
                                            className="profile-form-error"
                                            role="alert"
                                        >
                                            {editError}
                                        </p>
                                    )}

                                    <div className="profile-form-actions">
                                        <button
                                            type="button"
                                            className="profile-cancel-button"
                                            onClick={() => {
                                                setDraft({ ...profile });
                                                setEditing(false);
                                                setEditError("");
                                            }}
                                        >
                                            Cancel
                                        </button>

                                        <button
                                            type="submit"
                                            className="profile-save-button"
                                        >
                                            Save Changes
                                        </button>
                                    </div>
                                </form>
                            </>
                        ) : (
                            <>
                                <div className="profile-dropdown-heading">
                                    <ProfileAvatar
                                        profile={profile}
                                        large
                                    />

                                    <div>
                                        <h2>{displayName}</h2>
                                        <p>
                                            {profile.email ||
                                                "Add your email address"}
                                        </p>
                                    </div>
                                </div>

                                <div className="profile-details-list">
                                    <div>
                                        <span>Phone</span>
                                        <strong>
                                            {profile.phone || "Not added"}
                                        </strong>
                                    </div>

                                    <div>
                                        <span>Education</span>
                                        <strong>
                                            {profile.education ||
                                                "Not added"}
                                        </strong>
                                    </div>

                                    <div>
                                        <span>State</span>
                                        <strong>
                                            {profile.state || "Not added"}
                                        </strong>
                                    </div>
                                </div>

                                <button
                                    type="button"
                                    className="profile-edit-button"
                                    onClick={beginEditing}
                                >
                                    ✎ Quick Edit
                                </button>

                                <Link
                                    to="/profile"
                                    className="profile-library-link"
                                    onClick={() => setOpen(false)}
                                >
                                    👤 Open Full Profile
                                </Link>

                                <Link
                                    to="/library"
                                    className="profile-library-link"
                                    onClick={() => setOpen(false)}
                                >
                                    ♥ View My Library
                                </Link>
                            </>
                        )}
                    </section>
                </>
            )}
        </div>
    );
}

// ======================================================
// SHARED LAYOUT
// ======================================================

function PrivateLayout({ onLogout }) {
    const [mobileOpen, setMobileOpen] = useState(false);
    const location = useLocation();

    useEffect(() => {
        setMobileOpen(false);
    }, [location.pathname]);

    return (
        <div className="private-layout">
            <Sidebar
                onLogout={onLogout}
                mobileOpen={mobileOpen}
                setMobileOpen={setMobileOpen}
            />

            <div className="private-main">
                <header className="private-topbar">
                    <span className="private-topbar-title">
                        Smart Government Scheme Assistant
                    </span>

                    <div className="private-topbar-right">
                        <span className="private-topbar-status">
                            <span className="status-dot" />
                            Your scheme discovery workspace
                        </span>

                        <ProfileMenu />
                    </div>
                </header>

                <main className="private-content">
                    <Outlet />
                </main>

                <footer className="private-footer">
                    Verify eligibility, deadlines, and application
                    details through the relevant official government
                    source.
                </footer>
            </div>
        </div>
    );
}

// ======================================================
// HOME PAGE
// ======================================================

function Home() {
    const [searchQuery, setSearchQuery] = useState("");
    const [searchResults, setSearchResults] = useState([]);
    const [searchLoading, setSearchLoading] = useState(false);
    const [searchError, setSearchError] = useState("");
    const [searchPerformed, setSearchPerformed] = useState(false);

    async function handleSemanticSearch(event) {
        event.preventDefault();

        const query = searchQuery.trim();

        if (!query) {
            setSearchResults([]);
            setSearchError(
                "Enter a scheme name or describe what you need."
            );
            setSearchPerformed(false);
            return;
        }

        try {
            setSearchLoading(true);
            setSearchError("");
            setSearchPerformed(true);
            setSearchResults([]);

            const data = await semanticSearch(
                query,
                "minilm",
                10
            );

            const normalized = normalizeSchemes(data);

            setSearchResults(normalized);

            if (normalized.length === 0) {
                setSearchError(
                    "No matching schemes were found. Try different keywords."
                );
            }
        } catch (error) {
            console.error("Semantic search failed:", error);

            setSearchError(
                error.message || "Semantic search failed."
            );

            setSearchResults([]);
        } finally {
            setSearchLoading(false);
        }
    }

    function clearSearch() {
        setSearchQuery("");
        setSearchResults([]);
        setSearchError("");
        setSearchPerformed(false);
    }

    return (
        <div className="page-container home-page">
            <section className="home-welcome">
                <div className="home-welcome-copy">
                    <span className="page-eyebrow">
                        YOUR PERSONAL SCHEME FINDER
                    </span>

                    <h1>Find the support you deserve.</h1>

                    <p>
                        Discover government scholarships and welfare
                        schemes using a search that understands your needs.
                    </p>

                    <Link
                        to="/library"
                        className="home-library-link"
                    >
                        ♥ Explore My Library
                    </Link>
                </div>

                <div
                    className="home-decoration"
                    aria-hidden="true"
                >
                    <span className="decoration-circle decoration-circle-one" />
                    <span className="decoration-circle decoration-circle-two" />
                    <span className="decoration-document">✓</span>
                </div>
            </section>

            <section className="home-search-panel">
                <div className="search-panel-heading">
                    <span className="search-panel-icon">⌕</span>

                    <div>
                        <h2>What are you looking for?</h2>
                        <p>
                            Describe your education, needs, or the support
                            you need.
                        </p>
                    </div>
                </div>

                <form
                    className="home-search-form"
                    onSubmit={handleSemanticSearch}
                >
                    <input
                        type="search"
                        value={searchQuery}
                        onChange={(event) => {
                            setSearchQuery(event.target.value);
                            setSearchPerformed(false);
                            setSearchResults([]);
                            setSearchError("");
                        }}
                        placeholder="Example: scholarship for MCA students"
                        aria-label="Search government schemes"
                    />

                    <button
                        type="submit"
                        className="primary-button"
                        disabled={searchLoading}
                    >
                        {searchLoading
                            ? "Searching..."
                            : "Search Schemes"}

                        {!searchLoading && (
                            <span aria-hidden="true"> →</span>
                        )}
                    </button>

                    {searchQuery && (
                        <button
                            type="button"
                            className="clear-search-button"
                            onClick={clearSearch}
                            disabled={searchLoading}
                        >
                            Clear
                        </button>
                    )}
                </form>

                <div className="search-suggestions">
                    <span>Try:</span>

                    {[
                        "MCA scholarship",
                        "OBC students",
                        "low family income",
                    ].map((suggestion) => (
                        <button
                            type="button"
                            key={suggestion}
                            onClick={() => {
                                setSearchQuery(suggestion);
                                setSearchResults([]);
                                setSearchError("");
                                setSearchPerformed(false);
                            }}
                        >
                            {suggestion}
                        </button>
                    ))}
                </div>
            </section>

            {searchLoading && (
                <div className="page-message">
                    <span className="loading-spinner" />
                    Searching for schemes that match your needs...
                </div>
            )}

            {searchError && !searchLoading && (
                <div
                    className="page-message error-message"
                    role="alert"
                >
                    {searchError}
                </div>
            )}

            {searchPerformed &&
                !searchLoading &&
                !searchError && (
                    <section className="page-section search-results-section">
                        <div className="page-section-heading">
                            <div>
                                <span className="page-eyebrow">
                                    SEARCH RESULTS
                                </span>

                                <h2>Matching government schemes</h2>

                                <p>
                                    Results for{" "}
                                    <strong>"{searchQuery}"</strong>
                                </p>
                            </div>

                            <span className="result-count">
                                {searchResults.length} found
                            </span>
                        </div>

                        <div className="scheme-grid">
                            {searchResults.map((scheme, index) => (
                                <SchemeCard
                                    key={`${scheme.scheme_id}-${index}`}
                                    scheme={scheme}
                                />
                            ))}
                        </div>
                    </section>
                )}

            {!searchPerformed && !searchLoading && (
                <section className="home-empty-state">
                    <div className="empty-state-icon">⌕</div>

                    <h2>Your next opportunity starts here</h2>

                    <p>
                        Enter a search above and click{" "}
                        <strong>Search Schemes</strong> to see relevant
                        government schemes. Your results will appear here.
                    </p>
                </section>
            )}
        </div>
    );
}

// ======================================================
// BROWSE SCHEMES PAGE
// ======================================================

function BrowseSchemes() {
    const [schemes, setSchemes] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [filter, setFilter] = useState("");

    useEffect(() => {
        let active = true;

        async function load() {
            try {
                setLoading(true);
                setError("");

                const data = await getSchemes();

                if (active) {
                    setSchemes(normalizeSchemes(data));
                }
            } catch (error) {
                console.error("Failed to load schemes:", error);

                if (active) {
                    setError(
                        "Unable to load schemes. Check that the FastAPI server is running."
                    );
                }
            } finally {
                if (active) {
                    setLoading(false);
                }
            }
        }

        load();

        return () => {
            active = false;
        };
    }, []);

    const filteredSchemes = schemes.filter((scheme) => {
        const query = filter.trim().toLowerCase();

        if (!query) return true;

        return [
            scheme.scheme_name,
            scheme.description,
            scheme.category,
            scheme.ministry,
            scheme.Ministry,
        ]
            .filter(Boolean)
            .join(" ")
            .toLowerCase()
            .includes(query);
    });

    return (
        <div className="page-container">
            <section className="page-heading-block">
                <span className="page-eyebrow">
                    SCHEME DIRECTORY
                </span>

                <h1>Browse Government Schemes</h1>

                <p>
                    Explore government schemes and open a scheme to learn
                    about its benefits and eligibility. Use the heart to
                    save schemes to your Library.
                </p>
            </section>

            <div className="directory-toolbar">
                <input
                    type="search"
                    value={filter}
                    onChange={(event) => setFilter(event.target.value)}
                    placeholder="Filter schemes by name, category, or ministry..."
                    aria-label="Filter schemes"
                />

                <span className="result-count">
                    {loading
                        ? "Loading..."
                        : `${filteredSchemes.length} schemes`}
                </span>
            </div>

            {loading && (
                <div className="page-message">
                    Loading schemes...
                </div>
            )}

            {error && (
                <div className="page-message error-message">
                    {error}
                </div>
            )}

            {!loading && !error && filteredSchemes.length > 0 && (
                <div className="scheme-grid">
                    {filteredSchemes.map((scheme, index) => (
                        <SchemeCard
                            key={`${scheme.scheme_id}-${index}`}
                            scheme={scheme}
                        />
                    ))}
                </div>
            )}

            {!loading &&
                !error &&
                filteredSchemes.length === 0 && (
                    <div className="page-message">
                        No schemes match your filter.
                    </div>
                )}
        </div>
    );
}

// ======================================================
// LIBRARY PAGE
// ======================================================

function LibraryPage() {
    const { savedSchemes } = useSavedSchemes();
    const [filter, setFilter] = useState("");

    const filteredSchemes = savedSchemes.filter((scheme) => {
        const query = filter.trim().toLowerCase();

        if (!query) return true;

        return [
            scheme.scheme_name,
            scheme.description,
            scheme.category,
            scheme.ministry,
            scheme.Ministry,
        ]
            .filter(Boolean)
            .join(" ")
            .toLowerCase()
            .includes(query);
    });

    return (
        <div className="page-container library-page">
            <section className="library-hero">
                <span className="page-eyebrow">
                    YOUR PERSONAL COLLECTION
                </span>

                <h1>My Library <span aria-hidden="true">♥</span></h1>

                <p>
                    Keep the government schemes you are interested in
                    together so you can revisit them later.
                </p>

                <div className="library-summary">
                    <span className="library-summary-icon">♥</span>

                    <div>
                        <strong>{savedSchemes.length}</strong>
                        <span>
                            {savedSchemes.length === 1
                                ? " saved scheme"
                                : " saved schemes"}
                        </span>
                    </div>
                </div>
            </section>

            {savedSchemes.length > 0 && (
                <div className="directory-toolbar library-toolbar">
                    <input
                        type="search"
                        value={filter}
                        onChange={(event) => setFilter(event.target.value)}
                        placeholder="Search your saved schemes..."
                        aria-label="Search saved schemes"
                    />

                    <span className="result-count">
                        {filteredSchemes.length} shown
                    </span>
                </div>
            )}

            {filteredSchemes.length > 0 ? (
                <div className="scheme-grid">
                    {filteredSchemes.map((scheme) => (
                        <SchemeCard
                            key={scheme.scheme_id}
                            scheme={scheme}
                        />
                    ))}
                </div>
            ) : (
                <section className="library-empty-state">
                    <div className="library-empty-heart">♡</div>

                    <h2>
                        {savedSchemes.length === 0
                            ? "Your Library is waiting"
                            : "No saved schemes match"}
                    </h2>

                    <p>
                        {savedSchemes.length === 0
                            ? "When you find a scheme you like, click the heart on its card to save it here."
                            : "Try a different search term to find a saved scheme."}
                    </p>

                    {savedSchemes.length === 0 ? (
                        <Link
                            to="/browse-schemes"
                            className="primary-button"
                        >
                            Browse Schemes →
                        </Link>
                    ) : (
                        <button
                            type="button"
                            className="primary-button"
                            onClick={() => setFilter("")}
                        >
                            Clear Search
                        </button>
                    )}
                </section>
            )}
        </div>
    );
}

// ======================================================
// ELIGIBILITY SCHEME PICKER
// ======================================================

function EligibilityPicker() {
    const [schemes, setSchemes] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        let active = true;

        async function load() {
            try {
                const data = await getSchemes();

                if (active) {
                    setSchemes(normalizeSchemes(data));
                }
            } catch (error) {
                console.error("Failed to load schemes:", error);

                if (active) {
                    setError("Unable to load schemes right now.");
                }
            } finally {
                if (active) {
                    setLoading(false);
                }
            }
        }

        load();

        return () => {
            active = false;
        };
    }, []);

    return (
        <div className="page-container">
            <section className="page-heading-block">
                <span className="page-eyebrow">
                    ELIGIBILITY CHECKER
                </span>

                <h1>Check your eligibility</h1>

                <p>
                    Choose a scheme to answer its eligibility questions
                    and review the result.
                </p>
            </section>

            {loading && (
                <div className="page-message">
                    Loading schemes...
                </div>
            )}

            {error && (
                <div className="page-message error-message">
                    {error}
                </div>
            )}

            {!loading && !error && (
                <div className="eligibility-picker-list">
                    {schemes.map((scheme, index) => (
                        <article
                            className="eligibility-picker-card"
                            key={`${scheme.scheme_id}-${index}`}
                        >
                            <div>
                                <h2>{scheme.scheme_name}</h2>
                                <p>{scheme.description}</p>

                                {scheme.category && (
                                    <span className="category-chip">
                                        {scheme.category}
                                    </span>
                                )}
                            </div>

                            <Link
                                to={`/schemes/${encodeURIComponent(
                                    scheme.scheme_id
                                )}/eligibility`}
                                className="primary-button"
                            >
                                Check Eligibility →
                            </Link>
                        </article>
                    ))}

                    {schemes.length === 0 && (
                        <div className="page-message">
                            No schemes are available.
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

// ======================================================
// ELIGIBILITY PAGE
// ======================================================

function EligibilityPage() {
    const { schemeId } = useParams();

    return <EligibilityForm schemeId={schemeId} />;
}

// ======================================================
// QUESTIONNAIRE AND RECOMMENDATIONS
// ======================================================

function QuestionnairePage() {
    return <AuthPage mode="questionnaire" />;
}

function RecommendationsPage() {
    return <AuthPage mode="recommendations" />;
}

// ======================================================
// ABOUT PAGE
// ======================================================

function AboutPage() {
    return (
        <div className="page-container about-page">
            <section className="about-hero">
                <span className="page-eyebrow">
                    ABOUT OUR PROJECT
                </span>

                <h1>
                    Making government schemes easier to discover.
                </h1>

                <p>
                    Smart Government Scheme Assistant helps people
                    discover government scholarships and welfare schemes,
                    understand eligibility requirements, and explore
                    opportunities relevant to their needs.
                </p>
            </section>

            <section className="about-content-grid">
                <article className="about-info-card">
                    <span className="about-icon">⌕</span>
                    <h2>Semantic Scheme Search</h2>
                    <p>
                        Search using everyday language to find relevant
                        government schemes based on the meaning of your query.
                    </p>
                </article>

                <article className="about-info-card">
                    <span className="about-icon">✓</span>
                    <h2>Eligibility Assessment</h2>
                    <p>
                        Enter the requested information to compare your
                        circumstances with the eligibility rules available
                        for a selected scheme.
                    </p>
                </article>

                <article className="about-info-card">
                    <span className="about-icon">✧</span>
                    <h2>Personalized Recommendations</h2>
                    <p>
                        Explore potential scheme matches using relevant
                        information about your education and other
                        eligibility-related details.
                    </p>
                </article>

                <article className="about-info-card">
                    <span className="about-icon">♥</span>
                    <h2>Your Personal Library</h2>
                    <p>
                        Save schemes you are interested in and return to
                        them whenever you need to review their details.
                    </p>
                </article>
            </section>

            <section className="about-mission">
                <span className="page-eyebrow">OUR MISSION</span>
                <h2>Making opportunities easier to find.</h2>

                <p>
                    Our goal is to provide a convenient platform for
                    discovering government schemes through semantic
                    search, eligibility assessment, and personalized
                    discovery.
                </p>

                <Link
                    to="/browse-schemes"
                    className="primary-button"
                >
                    Explore Government Schemes →
                </Link>
            </section>

            <p className="about-disclaimer">
                This application provides scheme discovery and eligibility
                assistance. It does not guarantee approval or benefits.
                Always verify eligibility criteria, deadlines, and application
                procedures through the relevant official government website.
            </p>
        </div>
    );
}

// ======================================================
// NOT FOUND PAGE
// ======================================================

function NotFoundPage() {
    return (
        <div className="page-container not-found-page">
            <span className="page-eyebrow">404 ERROR</span>

            <h1>We couldn't find that page.</h1>

            <p>
                The page may have moved or the address may be incorrect.
            </p>

            <Link to="/" className="primary-button">
                Return Home
            </Link>
        </div>
    );
}

// ======================================================
// APPLICATION ROUTES
// ======================================================

function AppContent() {
    const [authenticated, setAuthenticated] = useState(
        isAuthenticated
    );

    const navigate = useNavigate();

    function handleLogin() {
        sessionStorage.setItem(AUTH_KEY, "true");
        setAuthenticated(true);
        navigate("/", { replace: true });
    }

    function handleLogout() {
        sessionStorage.removeItem(AUTH_KEY);
        setAuthenticated(false);
        navigate("/login", { replace: true });
    }

    return (
        <Routes>
            <Route
                path="/login"
                element={
                    <GuestOnly
                        authenticated={authenticated}
                        mode="login"
                        onAuthenticated={handleLogin}
                    />
                }
            />

            <Route
                path="/register"
                element={
                    <GuestOnly
                        authenticated={authenticated}
                        mode="register"
                        onAuthenticated={() =>
                            navigate("/login", { replace: true })
                        }
                    />
                }
            />

            <Route
                element={
                    <RequireAuth authenticated={authenticated} />
                }
            >
                <Route
                    element={
                        <PrivateLayout onLogout={handleLogout} />
                    }
                >
                    <Route index element={<Home />} />

                    <Route
                        path="browse-schemes"
                        element={<BrowseSchemes />}
                    />

                    <Route
                        path="library"
                        element={<LibraryPage />}
                    />

                    <Route
                        path="profile"
                        element={<Profile />}
                    />

                    <Route
                        path="eligibility"
                        element={<EligibilityPicker />}
                    />

                    <Route
                        path="schemes/:schemeId"
                        element={<SchemeDetails />}
                    />

                    <Route
                        path="schemes/:schemeId/eligibility"
                        element={<EligibilityPage />}
                    />

                    <Route
                        path="questionnaire"
                        element={<QuestionnairePage />}
                    />

                    <Route
                        path="recommendations"
                        element={<RecommendationsPage />}
                    />

                    <Route
                        path="about"
                        element={<AboutPage />}
                    />

                    <Route
                        path="*"
                        element={<NotFoundPage />}
                    />
                </Route>
            </Route>
        </Routes>
    );
}

// ======================================================
// ROOT
// ======================================================

function App() {
    return (
        <SavedSchemesProvider>
            <BrowserRouter>
                <AppContent />
            </BrowserRouter>
        </SavedSchemesProvider>
    );
}

export default App;
