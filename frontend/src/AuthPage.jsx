
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import "./AuthPage.css";

const API = "http://127.0.0.1:8000";
const TOKEN_KEY = "scholarship_token";

async function apiRequest(path, token, options = {}) {
    const response = await fetch(`${API}${path}`, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            ...options.headers,
        },
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        throw new Error(
            typeof data.detail === "string"
                ? data.detail
                : "Request failed. Please try again."
        );
    }

    return data;
}

export default function AuthPage({
    mode = "login",
    onAuthenticated,
}) {
    const navigate = useNavigate();

    const [page, setPage] = useState(mode);
    const [username, setUsername] = useState("");
    const [email, setEmail] = useState("");
    const [identifier, setIdentifier] = useState("");
    const [password, setPassword] = useState("");

    const [profile, setProfile] = useState({
        age: "",
        state: "",
        annual_income: "",
        category: "",
        education_level: "",
        course: "",
        study_mode: "",
        gender: "",
        year_of_study: "",
        occupation: "",
        disability_percentage: "",
    });

    const [user, setUser] = useState(null);
    const [recommendations, setRecommendations] = useState([]);
    const [needsReview, setNeedsReview] = useState([]);
    const [message, setMessage] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    // Keep the displayed screen synchronized with the route.
    useEffect(() => {
        setPage(mode);
        setError("");
    }, [mode]);

    function updateProfile(event) {
        const { name, value } = event.target;

        setProfile((previous) => ({
            ...previous,
            [name]: value,
        }));
    }

    // Verify the existing session before loading private pages.
    useEffect(() => {
        if (
            mode !== "questionnaire" &&
            mode !== "recommendations"
        ) {
            return;
        }

        const token = localStorage.getItem(TOKEN_KEY);

        if (!token) {
            navigate("/login", { replace: true });
            return;
        }

        let cancelled = false;

        async function loadUserAndProfile() {
            try {
                const data = await apiRequest("/auth/me", token);

                if (cancelled) return;

                setUser(data.user);

                const profileData = await apiRequest(
                    "/auth/profile",
                    token
                );

                if (cancelled) return;

                if (profileData?.profile) {
                    setProfile((previous) => ({
                        ...previous,
                        ...Object.fromEntries(
                            Object.entries(profileData.profile).map(
                                ([key, value]) => [
                                    key,
                                    value == null ? "" : String(value),
                                ]
                            )
                        ),
                    }));
                }
            } catch (err) {
                if (cancelled) return;

                console.error("Session validation failed:", err);
                localStorage.removeItem(TOKEN_KEY);
                navigate("/login", { replace: true });
            }
        }

        loadUserAndProfile();

        return () => {
            cancelled = true;
        };
    }, [mode, navigate]);

    // Login or register.
    async function handleAuth(event) {
        event.preventDefault();

        setError("");
        setLoading(true);

        try {
            const registration = page === "register";

            const data = await apiRequest(
                registration ? "/auth/register" : "/auth/login",
                null,
                {
                    method: "POST",
                    body: JSON.stringify(
                        registration
                            ? { username, email, password }
                            : { identifier, password }
                    ),
                }
            );

            if (!data.access_token) {
                throw new Error(
                    "Authentication succeeded without a token. Check the backend response."
                );
            }

            localStorage.setItem(TOKEN_KEY, data.access_token);

            setUser(data.user || null);

            // Notify App.jsx that login succeeded.
            // The parent opens the protected homepage.
            if (typeof onAuthenticated === "function") {
                onAuthenticated(data);
            } else {
                navigate("/", { replace: true });
            }
        } catch (err) {
            setError(err.message || "Unable to authenticate.");
        } finally {
            setLoading(false);
        }
    }

    // Save questionnaire answers and fetch eligible scholarships.
    async function handleProfileSubmit(event) {
        event.preventDefault();

        setError("");
        setMessage("");
        setLoading(true);

        try {
            const token = localStorage.getItem(TOKEN_KEY);

            if (!token) {
                navigate("/login", { replace: true });
                return;
            }

            const payload = {};

            for (const [key, value] of Object.entries(profile)) {
                if (value === "") continue;

                if (
                    [
                        "age",
                        "year_of_study",
                        "annual_income",
                        "disability_percentage",
                    ].includes(key)
                ) {
                    payload[key] = Number(value);
                } else {
                    payload[key] = value.trim();
                }
            }

            await apiRequest("/auth/profile", token, {
                method: "PUT",
                body: JSON.stringify(payload),
            });

            const result = await apiRequest(
                "/auth/recommendations",
                token,
                { method: "POST" }
            );

            setRecommendations(result.recommendations || []);
            setNeedsReview(result.needs_review || []);
            setMessage(result.message || "");

            navigate("/recommendations", { replace: true });
        } catch (err) {
            setError(err.message || "Unable to assess eligibility.");
        } finally {
            setLoading(false);
        }
    }

    async function loadRecommendations() {
        const token = localStorage.getItem(TOKEN_KEY);

        if (!token) {
            navigate("/login", { replace: true });
            return;
        }

        setError("");
        setLoading(true);

        try {
            const result = await apiRequest(
                "/auth/recommendations",
                token,
                { method: "POST" }
            );

            setRecommendations(result.recommendations || []);
            setNeedsReview(result.needs_review || []);
            setMessage(result.message || "");
        } catch (err) {
            setError(err.message || "Unable to load recommendations.");
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        if (mode === "recommendations") {
            loadRecommendations();
        }
    }, [mode]);

    async function logout() {
        const token = localStorage.getItem(TOKEN_KEY);

        try {
            if (token) {
                await apiRequest("/auth/logout", token, {
                    method: "POST",
                });
            }
        } catch (err) {
            console.error("Server logout failed:", err);
        } finally {
            localStorage.removeItem(TOKEN_KEY);
            navigate("/login", { replace: true });
        }
    }

    function display(value) {
        if (
            value == null ||
            value === "" ||
            String(value) === "NaN"
        ) {
            return "Information not available.";
        }

        return String(value);
    }

    // ==================================================
    // QUESTIONNAIRE
    // ==================================================

    if (page === "questionnaire" || mode === "questionnaire") {
        return (
            <main className="auth-page">
                <section className="auth-card questionnaire-card">
                    <h1>Find scholarships for you</h1>

                    <p>
                        Answer these questions to find scholarships
                        that match your profile.
                    </p>

                    {user && <p>Welcome, {user.username}!</p>}

                    {error && (
                        <p className="auth-error">{error}</p>
                    )}

                    <form onSubmit={handleProfileSubmit}>
                        <div className="question-grid">
                            <label>
                                Age
                                <input
                                    name="age"
                                    type="number"
                                    min="1"
                                    max="120"
                                    value={profile.age}
                                    onChange={updateProfile}
                                    required
                                />
                            </label>

                            <label>
                                State
                                <input
                                    name="state"
                                    value={profile.state}
                                    onChange={updateProfile}
                                    placeholder="e.g. Karnataka"
                                    required
                                />
                            </label>

                            <label>
                                Annual family income (₹)
                                <input
                                    name="annual_income"
                                    type="number"
                                    min="0"
                                    value={profile.annual_income}
                                    onChange={updateProfile}
                                    required
                                />
                            </label>

                            <label>
                                Category
                                <select
                                    name="category"
                                    value={profile.category}
                                    onChange={updateProfile}
                                    required
                                >
                                    <option value="">
                                        Select category
                                    </option>

                                    {[
                                        "General",
                                        "OBC",
                                        "SC",
                                        "ST",
                                        "EWS",
                                        "Other",
                                    ].map((item) => (
                                        <option
                                            key={item}
                                            value={item}
                                        >
                                            {item}
                                        </option>
                                    ))}
                                </select>
                            </label>

                            <label>
                                Education level
                                <select
                                    name="education_level"
                                    value={profile.education_level}
                                    onChange={updateProfile}
                                    required
                                >
                                    <option value="">
                                        Select education
                                    </option>

                                    {[
                                        "School",
                                        "Undergraduate",
                                        "Postgraduate",
                                        "PhD / Research",
                                        "Other",
                                    ].map((item) => (
                                        <option
                                            key={item}
                                            value={item}
                                        >
                                            {item}
                                        </option>
                                    ))}
                                </select>
                            </label>

                            <label>
                                Course
                                <input
                                    name="course"
                                    value={profile.course}
                                    onChange={updateProfile}
                                    placeholder="e.g. MCA"
                                    required
                                />
                            </label>

                            <label>
                                Study mode
                                <select
                                    name="study_mode"
                                    value={profile.study_mode}
                                    onChange={updateProfile}
                                    required
                                >
                                    <option value="">
                                        Select mode
                                    </option>
                                    <option value="Regular">
                                        Regular
                                    </option>
                                    <option value="Distance">
                                        Distance
                                    </option>
                                    <option value="Online">
                                        Online
                                    </option>
                                </select>
                            </label>

                            <label>
                                Year of study (optional)
                                <input
                                    name="year_of_study"
                                    type="number"
                                    min="1"
                                    max="15"
                                    value={profile.year_of_study}
                                    onChange={updateProfile}
                                    placeholder="Optional"
                                />
                            </label>

                            <label>
                                Gender (optional)
                                <select
                                    name="gender"
                                    value={profile.gender}
                                    onChange={updateProfile}
                                >
                                    <option value="">
                                        Prefer not to say
                                    </option>
                                    <option value="Female">
                                        Female
                                    </option>
                                    <option value="Male">
                                        Male
                                    </option>
                                    <option value="Other">
                                        Other
                                    </option>
                                </select>
                            </label>
                        </div>

                        <button type="submit" disabled={loading}>
                            {loading
                                ? "Finding scholarships..."
                                : "Save answers and find scholarships"}
                        </button>
                    </form>

                    <button
                        type="button"
                        className="secondary-button"
                        onClick={logout}
                    >
                        Log out
                    </button>
                </section>
            </main>
        );
    }

    // ==================================================
    // RECOMMENDATIONS
    // ==================================================

    if (page === "recommendations" || mode === "recommendations") {
        return (
            <main className="auth-page">
                <section className="results-container">
                    <div className="results-heading">
                        <div>
                            <h1>Your scholarship recommendations</h1>
                            <p>{message}</p>
                        </div>

                        <button
                            type="button"
                            onClick={logout}
                        >
                            Log out
                        </button>
                    </div>

                    {error && (
                        <p className="auth-error">{error}</p>
                    )}

                    {loading && (
                        <p>Assessing your eligibility...</p>
                    )}

                    {!loading && !error && (
                        <>
                            <p>
                                {recommendations.length} matching
                                scholarship(s)
                            </p>

                            {recommendations.length === 0 && (
                                <div className="auth-card">
                                    <h2>No confirmed matches yet</h2>

                                    <p>
                                        Check your profile answers or
                                        review scholarships that need
                                        further assessment below.
                                    </p>

                                    <Link to="/questionnaire">
                                        Update questionnaire
                                    </Link>
                                </div>
                            )}

                            <div className="recommendation-grid">
                                {recommendations.map((scheme, index) => (
                                    <article
                                        className="recommendation-card"
                                        key={
                                            scheme.scheme_id ||
                                            scheme.id ||
                                            index
                                        }
                                    >
                                        <h2>
                                            {display(
                                                scheme.scheme_name ||
                                                scheme.Scholarship
                                            )}
                                        </h2>

                                        <p>
                                            {display(scheme.description)}
                                        </p>

                                        {scheme.benefits && (
                                            <p>
                                                <strong>Benefits:</strong>{" "}
                                                {display(scheme.benefits)}
                                            </p>
                                        )}

                                        {scheme.eligibility_result && (
                                            <details>
                                                <summary>
                                                    Why this was recommended
                                                </summary>

                                                <pre>
                                                    {JSON.stringify(
                                                        scheme.eligibility_result,
                                                        null,
                                                        2
                                                    )}
                                                </pre>
                                            </details>
                                        )}

                                        {(
                                            scheme.official_url ||
                                            scheme.Official_url
                                        ) && (
                                            <a
                                                href={
                                                    scheme.official_url ||
                                                    scheme.Official_url
                                                }
                                                target="_blank"
                                                rel="noreferrer"
                                            >
                                                Official scheme details
                                            </a>
                                        )}
                                    </article>
                                ))}
                            </div>

                            {needsReview.length > 0 && (
                                <section className="review-section">
                                    <h2>Needs further verification</h2>

                                    <p>
                                        These results were not counted
                                        as confirmed eligible matches.
                                    </p>

                                    {needsReview.map((scheme, index) => (
                                        <p
                                            key={
                                                scheme.scheme_id || index
                                            }
                                        >
                                            {display(
                                                scheme.scheme_name ||
                                                scheme.Scholarship
                                            )}
                                        </p>
                                    ))}
                                </section>
                            )}

                            <button
                                type="button"
                                onClick={() =>
                                    navigate("/questionnaire")
                                }
                            >
                                Update my answers
                            </button>
                        </>
                    )}
                </section>
            </main>
        );
    }

    // ==================================================
    // LOGIN AND REGISTRATION
    // ==================================================

    return (
        <main className="auth-page">
            <section className="auth-card">
                <Link to="/login" className="back-link">
                    ← Smart Government Scheme Assistant
                </Link>

                <h1>
                    {page === "register"
                        ? "Create your account"
                        : "Welcome back"}
                </h1>

                <p>
                    {page === "register"
                        ? "Create an account to discover scholarships for you."
                        : "Log in to access the Government Scheme Assistant."}
                </p>

                {error && (
                    <p className="auth-error">{error}</p>
                )}

                <form onSubmit={handleAuth}>
                    {page === "register" && (
                        <>
                            <label>
                                Username
                                <input
                                    value={username}
                                    onChange={(event) =>
                                        setUsername(event.target.value)
                                    }
                                    minLength={3}
                                    maxLength={30}
                                    autoComplete="username"
                                    required
                                />
                            </label>

                            <label>
                                Email address
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(event) =>
                                        setEmail(event.target.value)
                                    }
                                    autoComplete="email"
                                    required
                                />
                            </label>
                        </>
                    )}

                    {page === "login" && (
                        <label>
                            Username or email
                            <input
                                value={identifier}
                                onChange={(event) =>
                                    setIdentifier(event.target.value)
                                }
                                autoComplete="username"
                                required
                            />
                        </label>
                    )}

                    <label>
                        Password
                        <input
                            type="password"
                            value={password}
                            onChange={(event) =>
                                setPassword(event.target.value)
                            }
                            autoComplete={
                                page === "register"
                                    ? "new-password"
                                    : "current-password"
                            }
                            minLength={8}
                            required
                        />
                    </label>

                    <button
                        type="submit"
                        disabled={loading}
                    >
                        {loading
                            ? "Please wait..."
                            : page === "register"
                                ? "Create account"
                                : "Log in"}
                    </button>
                </form>

                <p className="auth-switch">
                    {page === "register"
                        ? "Already have an account?"
                        : "New user?"}{" "}

                    <button
                        type="button"
                        className="text-button"
                        onClick={() => {
                            setError("");
                            setPage(
                                page === "register"
                                    ? "login"
                                    : "register"
                            );
                        }}
                    >
                        {page === "register"
                            ? "Log in"
                            : "Create account"}
                    </button>
                </p>
            </section>
        </main>
    );
}
