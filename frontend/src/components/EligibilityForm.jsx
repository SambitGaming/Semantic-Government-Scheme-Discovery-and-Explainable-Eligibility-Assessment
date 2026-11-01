
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import "./EligibilityForm.css";

const API_BASE_URL = "http://127.0.0.1:8000";

const NUMERIC_FIELDS = [
    "age",
    "annual_income",
    "income",
    "family_income",
    "percentage",
    "marks",
    "score",
    "year",
    "year_of_study",
    "disability_percentage",
];

const COMMON_OPTIONS = {
    category: ["General", "OBC", "SC", "ST", "EWS", "Minority"],
    gender: ["Male", "Female", "Other"],
    study_mode: ["Full-time", "Part-time", "Regular", "Distance"],
    is_government_employee: ["Yes", "No"],
    receives_other_scholarship: ["Yes", "No"],
    disability: ["Yes", "No"],
    state: [
        "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar",
        "Chhattisgarh", "Goa", "Gujarat", "Haryana", "Jharkhand",
        "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra",
        "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha",
        "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana",
        "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
        "Jammu and Kashmir", "Ladakh", "Delhi", "Puducherry",
    ],
    education_level: [
        "School", "Higher Secondary", "Diploma", "Undergraduate",
        "Postgraduate", "PhD", "Other",
    ],
};

const STEP_CONFIG = [
    {
        id: "personal",
        title: "Personal details",
        subtitle: "Tell us a little about yourself.",
        icon: "👤",
        description: "Basic information used to assess scheme criteria.",
    },
    {
        id: "education",
        title: "Education details",
        subtitle: "Share your current study information.",
        icon: "🎓",
        description: "Your education and course details help identify relevant requirements.",
    },
    {
        id: "financial",
        title: "Financial details",
        subtitle: "Enter any applicable income information.",
        icon: "💰",
        description: "Income-related answers are assessed against the scheme rules.",
    },
    {
        id: "other",
        title: "Additional details",
        subtitle: "Complete any remaining questions.",
        icon: "📋",
        description: "These answers cover other scheme-specific requirements.",
    },
];

function formatLabel(field = "") {
    return String(field)
        .replace(/_/g, " ")
        .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function isNumericField(field) {
    return NUMERIC_FIELDS.includes(String(field).toLowerCase());
}

function isEmpty(value) {
    return value === undefined || value === null || String(value).trim() === "";
}

// Safely extracts readable errors from strings, objects, arrays and FastAPI responses.
function getErrorMessage(value, fallback = "Something went wrong. Please try again.") {
    if (typeof value === "string" && value.trim()) {
        return value;
    }

    if (Array.isArray(value)) {
        const messages = value
            .map((item) => getErrorMessage(item, ""))
            .filter(Boolean);

        return messages.length ? messages.join("; ") : fallback;
    }

    if (value && typeof value === "object") {
        for (const key of ["detail", "message", "error", "msg"]) {
            if (value[key] !== undefined && value[key] !== null) {
                const message = getErrorMessage(value[key], "");

                if (message) {
                    return message;
                }
            }
        }

        try {
            return JSON.stringify(value);
        } catch {
            return fallback;
        }
    }

    return fallback;
}

function cleanDisplayValue(value, fallback = "Not provided") {
    if (isEmpty(value)) return fallback;

    if (typeof value === "object") {
        return getErrorMessage(value, fallback);
    }

    const text = String(value).trim();

    if (["nan", "null", "undefined"].includes(text.toLowerCase())) {
        return fallback;
    }

    return text;
}

function getFieldGroup(field) {
    const name = String(field).toLowerCase();

    if (
        [
            "age", "state", "gender", "category", "disability",
            "disability_percentage", "occupation", "marital_status",
            "is_government_employee",
        ].includes(name)
    ) {
        return "personal";
    }

    if (
        [
            "education_level", "course", "study_mode", "year",
            "year_of_study", "marks", "percentage", "score",
            "institution", "college", "university", "stream",
        ].includes(name)
    ) {
        return "education";
    }

    if (
        [
            "annual_income", "income", "family_income",
            "parent_income", "family_annual_income",
        ].includes(name)
    ) {
        return "financial";
    }

    return "other";
}

function getFieldHint(field) {
    const name = String(field).toLowerCase();

    const hints = {
        age: "Enter your age in completed years.",
        state: "Select the state or territory relevant to your application.",
        category: "Choose the category that applies to you.",
        annual_income: "Enter the annual income in rupees (₹).",
        family_income: "Enter the total annual family income in rupees (₹).",
        income: "Enter the applicable income amount in rupees (₹).",
        percentage: "Enter your percentage as a number.",
        marks: "Enter your marks as a number.",
        year_of_study: "Enter your current year of study.",
        disability_percentage: "Enter the percentage, if applicable.",
        study_mode: "Choose the mode in which you are studying.",
        education_level: "Select your current or relevant education level.",
        course: "Enter the course you are pursuing.",
    };

    return hints[name] || "Choose or enter the answer that best matches your details.";
}

function getRuleOptions(rule) {
    if (rule.operator !== "IN") return [];

    return String(rule.value ?? "")
        .split("|")
        .map((item) => item.trim())
        .filter(Boolean);
}

function DynamicField({ rule, value, onChange, error }) {
    const field = rule.field;
    const label = formatLabel(field);
    const ruleOptions = getRuleOptions(rule);
    const commonOptions = COMMON_OPTIONS[String(field).toLowerCase()];
    const options = rule.operator === "IN" ? ruleOptions : commonOptions;

    const controlId = `eligibility-${field}`;
    const hint = getFieldHint(field);

    return (
        <div className={`ef-field ${error ? "ef-field-error" : ""}`}>
            <label className="ef-label" htmlFor={controlId}>
                {label}
                <span className="ef-required" aria-label="required">*</span>
            </label>

            {options ? (
                <select
                    id={controlId}
                    className="ef-control"
                    value={value ?? ""}
                    onChange={(event) => onChange(event.target.value)}
                    aria-invalid={Boolean(error)}
                    aria-describedby={`${controlId}-hint`}
                >
                    <option value="">Select {label.toLowerCase()}</option>
                    {options.map((option) => (
                        <option key={option} value={option}>
                            {option}
                        </option>
                    ))}
                </select>
            ) : isNumericField(field) ? (
                <input
                    id={controlId}
                    className="ef-control"
                    type="number"
                    min="0"
                    step="any"
                    inputMode="decimal"
                    value={value ?? ""}
                    onChange={(event) => onChange(event.target.value)}
                    placeholder={`Enter ${label.toLowerCase()}`}
                    aria-invalid={Boolean(error)}
                    aria-describedby={`${controlId}-hint`}
                />
            ) : (
                <input
                    id={controlId}
                    className="ef-control"
                    type="text"
                    value={value ?? ""}
                    onChange={(event) => onChange(event.target.value)}
                    placeholder={`Enter ${label.toLowerCase()}`}
                    aria-invalid={Boolean(error)}
                    aria-describedby={`${controlId}-hint`}
                />
            )}

            <small id={`${controlId}-hint`} className="ef-field-hint">
                {hint}
                {rule.operator === "IN" && ruleOptions.length > 0
                    ? ` Allowed options: ${ruleOptions.join(", ")}.`
                    : ""}
            </small>

            {error && <span className="ef-inline-error">{error}</span>}
        </div>
    );
}

function getResultMessage(result) {
    if (result?.eligible === true) {
        return {
            title: "You appear to be eligible!",
            description:
                "Your submitted details satisfy the eligibility rules evaluated by the system. Review the official guidelines before applying.",
            icon: "✓",
            type: "success",
        };
    }

    if (result?.eligible === false) {
        return {
            title: "Some criteria are not satisfied",
            description:
                "One or more evaluated criteria did not match your answers. Review the explanations below to understand the result.",
            icon: "!",
            type: "failure",
        };
    }

    return {
        title: "Assessment completed",
        description:
            "The assessment has returned a result. Review the details below and verify the official scheme requirements.",
        icon: "i",
        type: "neutral",
    };
}

async function readResponse(response) {
    const data = await response.json().catch(() => null);

    if (!response.ok) {
        const fallback = `Request failed with HTTP ${response.status}.`;
        throw new Error(getErrorMessage(data, fallback));
    }

    if (data === null) {
        throw new Error("The server returned an empty or invalid JSON response.");
    }

    return data;
}

export default function EligibilityForm({ schemeId }) {
    const navigate = useNavigate();

    const [rules, setRules] = useState([]);
    const [formData, setFormData] = useState({});
    const [result, setResult] = useState(null);
    const [currentStep, setCurrentStep] = useState(0);
    const [loading, setLoading] = useState(true);
    const [checking, setChecking] = useState(false);
    const [error, setError] = useState("");
    const [fieldErrors, setFieldErrors] = useState({});
    const [schemeName, setSchemeName] = useState("");

    useEffect(() => {
        let cancelled = false;

        async function loadRules() {
            try {
                setLoading(true);
                setError("");
                setRules([]);
                setResult(null);
                setFormData({});
                setFieldErrors({});
                setCurrentStep(0);

                if (!schemeId) {
                    throw new Error("Scheme ID is missing.");
                }

                const response = await fetch(
                    `${API_BASE_URL}/schemes/${encodeURIComponent(schemeId)}`
                );

                const data = await readResponse(response);

                if (!Array.isArray(data.rules)) {
                    throw new Error(
                        "The backend response does not contain a valid rules list. Check the scheme details API response."
                    );
                }

                if (!cancelled) {
                    setRules(data.rules);

                    setSchemeName(
                        data.scheme?.Scholarship ||
                        data.scheme?.scheme_name ||
                        data.Scholarship ||
                        data.scheme_name ||
                        ""
                    );

                    const initialData = {};

                    data.rules.forEach((rule) => {
                        if (rule.field) {
                            initialData[rule.field] ??= "";
                        }
                    });

                    setFormData(initialData);
                }
            } catch (err) {
                if (!cancelled) {
                    console.error("Error loading eligibility rules:", err);
                    setError(
                        getErrorMessage(
                            err?.message ?? err,
                            "Failed to load eligibility requirements."
                        )
                    );
                }
            } finally {
                if (!cancelled) setLoading(false);
            }
        }

        loadRules();

        return () => {
            cancelled = true;
        };
    }, [schemeId]);

    // Show one question per unique field; the backend still evaluates all rules.
    const uniqueRules = useMemo(() => {
        const seen = new Set();

        return rules.filter((rule) => {
            if (!rule.field || seen.has(rule.field)) return false;
            seen.add(rule.field);
            return true;
        });
    }, [rules]);

    const availableSteps = useMemo(
        () =>
            STEP_CONFIG.map((step) => ({
                ...step,
                rules: uniqueRules.filter(
                    (rule) => getFieldGroup(rule.field) === step.id
                ),
            })).filter((step) => step.rules.length > 0),
        [uniqueRules]
    );

    const reviewStepIndex = availableSteps.length;
    const isReviewStep = currentStep === reviewStepIndex;
    const activeStep = availableSteps[currentStep];

    const progress =
        availableSteps.length > 0
            ? Math.round(
                  (Math.min(currentStep + 1, availableSteps.length) /
                      (availableSteps.length + 1)) *
                      100
              )
            : 0;

    const updateField = (field, value) => {
        setFormData((previous) => ({
            ...previous,
            [field]: value,
        }));

        setFieldErrors((previous) => ({
            ...previous,
            [field]: "",
        }));

        setResult(null);
        setError("");
    };

    const validateRules = (rulesToValidate) => {
        const nextErrors = {};

        rulesToValidate.forEach((rule) => {
            if (isEmpty(formData[rule.field])) {
                nextErrors[rule.field] =
                    `Please enter ${formatLabel(rule.field).toLowerCase()}.`;
                return;
            }

            if (isNumericField(rule.field)) {
                const value = Number(formData[rule.field]);

                if (!Number.isFinite(value) || value < 0) {
                    nextErrors[rule.field] =
                        "Enter a valid non-negative number.";
                }
            }
        });

        setFieldErrors((previous) => ({
            ...previous,
            ...nextErrors,
        }));

        return nextErrors;
    };

    const handleNext = () => {
        if (!activeStep) return;

        const errors = validateRules(activeStep.rules);

        if (Object.keys(errors).length > 0) {
            const firstInvalid = activeStep.rules.find(
                (rule) => errors[rule.field]
            );

            if (firstInvalid) {
                document
                    .getElementById(`eligibility-${firstInvalid.field}`)
                    ?.focus();
            }

            return;
        }

        setCurrentStep((step) => Math.min(step + 1, reviewStepIndex));
        setError("");
    };

    const handleBack = () => {
        setCurrentStep((step) => Math.max(0, step - 1));
        setError("");
    };

    const checkEligibility = async () => {
        setError("");
        setResult(null);

        const errors = validateRules(uniqueRules);

        if (Object.keys(errors).length > 0) {
            const firstInvalid = uniqueRules.find(
                (rule) => errors[rule.field]
            );

            if (firstInvalid) {
                const stepIndex = availableSteps.findIndex((step) =>
                    step.rules.some(
                        (rule) => rule.field === firstInvalid.field
                    )
                );

                if (stepIndex >= 0) setCurrentStep(stepIndex);

                window.setTimeout(() => {
                    document
                        .getElementById(`eligibility-${firstInvalid.field}`)
                        ?.focus();
                }, 0);
            }

            setError(
                "Please complete the highlighted fields before checking eligibility."
            );
            return;
        }

        try {
            setChecking(true);

            const response = await fetch(
                `${API_BASE_URL}/schemes/${encodeURIComponent(schemeId)}/eligibility`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify(formData),
                }
            );

            const data = await readResponse(response);

            if (!data || typeof data !== "object" || Array.isArray(data)) {
                throw new Error(
                    "The server returned an unexpected eligibility result."
                );
            }

            setResult(data);
        } catch (err) {
            console.error("Eligibility check error:", err);

            setError(
                getErrorMessage(
                    err?.message ?? err,
                    "Something went wrong while checking eligibility."
                )
            );
        } finally {
            setChecking(false);
        }
    };

    const startAgain = () => {
        const cleared = {};

        uniqueRules.forEach((rule) => {
            cleared[rule.field] = "";
        });

        setFormData(cleared);
        setResult(null);
        setFieldErrors({});
        setError("");
        setCurrentStep(0);
    };

    if (loading) {
        return (
            <div className="ef-page">
                <div className="ef-status-card">
                    <span className="ef-spinner" />
                    <h2>Preparing your assessment</h2>
                    <p>Loading the eligibility requirements for this scheme...</p>
                </div>
            </div>
        );
    }

    if (error && rules.length === 0) {
        return (
            <div className="ef-page">
                <div className="ef-status-card">
                    <span className="ef-status-icon ef-status-icon-error">!</span>
                    <h2>Unable to load requirements</h2>
                    <p className="ef-error-message">{error}</p>
                    <button
                        type="button"
                        className="ef-button ef-button-primary"
                        onClick={() => navigate(-1)}
                    >
                        ← Go Back
                    </button>
                </div>
            </div>
        );
    }

    if (rules.length === 0) {
        return (
            <div className="ef-page">
                <div className="ef-status-card">
                    <span className="ef-status-icon">📋</span>
                    <h2>No eligibility rules available</h2>
                    <p>This scheme does not currently have any rules to assess.</p>
                    <button
                        type="button"
                        className="ef-button ef-button-primary"
                        onClick={() => navigate(-1)}
                    >
                        ← Go Back
                    </button>
                </div>
            </div>
        );
    }

    const resultMessage = result ? getResultMessage(result) : null;
    const ruleResults = Array.isArray(result?.rule_results)
        ? result.rule_results
        : [];

    return (
        <main className="ef-page">
            <div className="ef-shell">
                <button
                    type="button"
                    className="ef-back-link"
                    onClick={() => navigate(-1)}
                >
                    <span>←</span> Back to scheme
                </button>

                <section className="ef-hero">
                    <div className="ef-hero-orb ef-hero-orb-one" />
                    <div className="ef-hero-orb ef-hero-orb-two" />

                    <div className="ef-hero-content">
                        <span className="ef-eyebrow">
                            <span className="ef-eyebrow-dot" />
                            PERSONALIZED ELIGIBILITY ASSESSMENT
                        </span>

                        <h1>Let's find out if you qualify.</h1>
                        <p>
                            Answer a few questions to compare your details with
                            the eligibility rules for this scheme.
                        </p>

                        {schemeName && (
                            <div className="ef-scheme-pill">
                                <span>🎓</span>
                                {schemeName}
                            </div>
                        )}
                    </div>

                    <div className="ef-hero-illustration" aria-hidden="true">
                        <div className="ef-illustration-card">
                            <span className="ef-illustration-check">✓</span>
                            <div className="ef-illustration-line ef-line-long" />
                            <div className="ef-illustration-line ef-line-short" />
                            <div className="ef-illustration-progress">
                                <span />
                            </div>
                        </div>
                    </div>
                </section>

                {!result ? (
                    <div className="ef-workspace">
                        <aside className="ef-progress-panel">
                            <span className="ef-panel-kicker">YOUR PROGRESS</span>

                            <div className="ef-progress-number">
                                {Math.min(
                                    currentStep + 1,
                                    availableSteps.length + 1
                                )}
                                <span> / {availableSteps.length + 1}</span>
                            </div>

                            <div
                                className="ef-progress-track"
                                role="progressbar"
                                aria-valuenow={progress}
                                aria-valuemin={0}
                                aria-valuemax={100}
                                aria-label="Assessment progress"
                            >
                                <span style={{ width: `${progress}%` }} />
                            </div>

                            <p className="ef-progress-caption">
                                {progress}% complete
                            </p>

                            <nav
                                className="ef-step-list"
                                aria-label="Assessment steps"
                            >
                                {availableSteps.map((step, index) => {
                                    const isComplete = index < currentStep;
                                    const isActive = index === currentStep;

                                    return (
                                        <button
                                            key={step.id}
                                            type="button"
                                            className={[
                                                "ef-step-item",
                                                isActive ? "is-active" : "",
                                                isComplete ? "is-complete" : "",
                                            ].join(" ")}
                                            onClick={() => {
                                                if (index < currentStep) {
                                                    setCurrentStep(index);
                                                    setError("");
                                                }
                                            }}
                                            disabled={index >= currentStep}
                                        >
                                            <span className="ef-step-marker">
                                                {isComplete ? "✓" : step.icon}
                                            </span>
                                            <span className="ef-step-label">
                                                <strong>{step.title}</strong>
                                                <small>
                                                    {isComplete
                                                        ? "Completed"
                                                        : isActive
                                                          ? "In progress"
                                                          : `${step.rules.length} question${step.rules.length === 1 ? "" : "s"}`}
                                                </small>
                                            </span>
                                        </button>
                                    );
                                })}

                                <button
                                    type="button"
                                    className={`ef-step-item ${
                                        isReviewStep ? "is-active" : ""
                                    }`}
                                    onClick={() => {
                                        if (isReviewStep) return;

                                        const remaining = availableSteps
                                            .slice(currentStep)
                                            .some((step) =>
                                                step.rules.some((rule) =>
                                                    isEmpty(formData[rule.field])
                                                )
                                            );

                                        if (!remaining) {
                                            setCurrentStep(reviewStepIndex);
                                        }
                                    }}
                                    disabled={
                                        isReviewStep ||
                                        availableSteps
                                            .slice(currentStep)
                                            .some((step) =>
                                                step.rules.some((rule) =>
                                                    isEmpty(formData[rule.field])
                                                )
                                            )
                                    }
                                >
                                    <span className="ef-step-marker">✓</span>
                                    <span className="ef-step-label">
                                        <strong>Review answers</strong>
                                        <small>Final step</small>
                                    </span>
                                </button>
                            </nav>

                            <div className="ef-privacy-note">
                                <span>🔒</span>
                                <p>
                                    Your answers are used to assess the scheme
                                    criteria. Check the site's privacy policy for
                                    information about data handling.
                                </p>
                            </div>
                        </aside>

                        <section className="ef-form-panel">
                            {!isReviewStep && activeStep ? (
                                <>
                                    <div className="ef-form-heading">
                                        <span className="ef-form-icon">
                                            {activeStep.icon}
                                        </span>
                                        <div>
                                            <span className="ef-panel-kicker">
                                                STEP {currentStep + 1}
                                            </span>
                                            <h2>{activeStep.title}</h2>
                                            <p>{activeStep.subtitle}</p>
                                        </div>
                                    </div>

                                    <div className="ef-step-intro">
                                        <span>💡</span>
                                        {activeStep.description}
                                    </div>

                                    <div className="ef-fields-grid">
                                        {activeStep.rules.map((rule) => (
                                            <DynamicField
                                                key={rule.field}
                                                rule={rule}
                                                value={formData[rule.field]}
                                                onChange={(value) =>
                                                    updateField(rule.field, value)
                                                }
                                                error={fieldErrors[rule.field]}
                                            />
                                        ))}
                                    </div>

                                    <div className="ef-form-footer">
                                        <button
                                            type="button"
                                            className="ef-button ef-button-secondary"
                                            onClick={handleBack}
                                            disabled={currentStep === 0}
                                        >
                                            ← Previous
                                        </button>

                                        <button
                                            type="button"
                                            className="ef-button ef-button-primary"
                                            onClick={handleNext}
                                        >
                                            Continue <span>→</span>
                                        </button>
                                    </div>
                                </>
                            ) : (
                                <>
                                    <div className="ef-form-heading">
                                        <span className="ef-form-icon">🔍</span>
                                        <div>
                                            <span className="ef-panel-kicker">
                                                FINAL STEP
                                            </span>
                                            <h2>Review your answers</h2>
                                            <p>
                                                Make sure everything is correct
                                                before checking eligibility.
                                            </p>
                                        </div>
                                    </div>

                                    <div className="ef-review-list">
                                        {uniqueRules.map((rule) => (
                                            <div
                                                className="ef-review-row"
                                                key={rule.field}
                                            >
                                                <div>
                                                    <span className="ef-review-label">
                                                        {formatLabel(rule.field)}
                                                    </span>
                                                    <strong>
                                                        {cleanDisplayValue(
                                                            formData[rule.field]
                                                        )}
                                                    </strong>
                                                </div>

                                                <button
                                                    type="button"
                                                    className="ef-edit-button"
                                                    onClick={() => {
                                                        const index =
                                                            availableSteps.findIndex(
                                                                (step) =>
                                                                    step.rules.some(
                                                                        (item) =>
                                                                            item.field ===
                                                                            rule.field
                                                                    )
                                                            );

                                                        if (index >= 0) {
                                                            setCurrentStep(index);
                                                        }
                                                    }}
                                                >
                                                    Edit
                                                </button>
                                            </div>
                                        ))}
                                    </div>

                                    <div className="ef-review-note">
                                        <span>ℹ️</span>
                                        This is an initial assessment based on
                                        the scheme rules available in the system.
                                        Final approval depends on the official
                                        scheme authority.
                                    </div>

                                    <div className="ef-form-footer">
                                        <button
                                            type="button"
                                            className="ef-button ef-button-secondary"
                                            onClick={handleBack}
                                        >
                                            ← Edit answers
                                        </button>

                                        <button
                                            type="button"
                                            className="ef-button ef-button-primary"
                                            onClick={checkEligibility}
                                            disabled={checking}
                                        >
                                            {checking ? (
                                                <>
                                                    <span className="ef-button-spinner" />
                                                    Checking...
                                                </>
                                            ) : (
                                                <>
                                                    Check Eligibility <span>→</span>
                                                </>
                                            )}
                                        </button>
                                    </div>
                                </>
                            )}

                            {error && (
                                <div className="ef-error-banner" role="alert">
                                    <span>!</span>
                                    <span>{error}</span>
                                </div>
                            )}

                            <p className="ef-required-note">
                                <span>*</span> All displayed questions are required
                                for this assessment.
                            </p>
                        </section>
                    </div>
                ) : (
                    <section className="ef-results-panel">
                        <div
                            className={`ef-result-banner ef-result-${resultMessage.type}`}
                        >
                            <div className="ef-result-icon">
                                {resultMessage.icon}
                            </div>
                            <div>
                                <span className="ef-panel-kicker">
                                    ASSESSMENT RESULT
                                </span>
                                <h2>{resultMessage.title}</h2>
                                <p>{resultMessage.description}</p>
                            </div>
                        </div>

                        <div className="ef-result-summary">
                            <div>
                                <span className="ef-summary-number">
                                    {ruleResults.length}
                                </span>
                                <span className="ef-summary-label">
                                    Criteria evaluated
                                </span>
                            </div>

                            <div>
                                <span className="ef-summary-number ef-summary-pass">
                                    {ruleResults.filter((item) => item.passed).length}
                                </span>
                                <span className="ef-summary-label">
                                    Criteria passed
                                </span>
                            </div>

                            <div>
                                <span className="ef-summary-number ef-summary-fail">
                                    {ruleResults.filter((item) => !item.passed).length}
                                </span>
                                <span className="ef-summary-label">
                                    Criteria not met
                                </span>
                            </div>
                        </div>

                        <div className="ef-results-heading">
                            <div>
                                <span className="ef-panel-kicker">BREAKDOWN</span>
                                <h3>Your eligibility criteria</h3>
                                <p>
                                    Review how each answer compares with the
                                    scheme requirements.
                                </p>
                            </div>

                            <button
                                type="button"
                                className="ef-button ef-button-secondary"
                                onClick={() => {
                                    setResult(null);
                                    setCurrentStep(0);
                                    setError("");
                                }}
                            >
                                Review answers
                            </button>
                        </div>

                        {ruleResults.length > 0 ? (
                            <div className="ef-result-list">
                                {ruleResults.map((rule, index) => (
                                    <article
                                        key={rule.rule_id ?? `${rule.field}-${index}`}
                                        className={`ef-result-item ${
                                            rule.passed ? "is-passed" : "is-failed"
                                        }`}
                                    >
                                        <div className="ef-result-item-icon">
                                            {rule.passed ? "✓" : "×"}
                                        </div>

                                        <div className="ef-result-item-body">
                                            <div className="ef-result-item-title">
                                                <h4>{formatLabel(rule.field)}</h4>
                                                <span
                                                    className={`ef-result-badge ${
                                                        rule.passed
                                                            ? "badge-pass"
                                                            : "badge-fail"
                                                    }`}
                                                >
                                                    {rule.passed
                                                        ? "Criteria met"
                                                        : "Criteria not met"}
                                                </span>
                                            </div>

                                            <div className="ef-comparison-grid">
                                                <div>
                                                    <span>Your answer</span>
                                                    <strong>
                                                        {cleanDisplayValue(
                                                            rule.user_value ??
                                                                formData[rule.field]
                                                        )}
                                                    </strong>
                                                </div>

                                                <div>
                                                    <span>Requirement</span>
                                                    <strong>
                                                        {cleanDisplayValue(
                                                            `${rule.operator ?? ""} ${
                                                                rule.required_value ?? ""
                                                            }`.trim(),
                                                            "See official guidelines"
                                                        )}
                                                    </strong>
                                                </div>
                                            </div>

                                            {rule.explanation && (
                                                <p className="ef-result-explanation">
                                                    {cleanDisplayValue(
                                                        rule.explanation,
                                                        ""
                                                    )}
                                                </p>
                                            )}

                                            {rule.Official_url && (
                                                <a
                                                    className="ef-result-source"
                                                    href={rule.Official_url}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                >
                                                    View source ↗
                                                </a>
                                            )}
                                        </div>
                                    </article>
                                ))}
                            </div>
                        ) : (
                            <div className="ef-no-breakdown">
                                The backend returned an overall result without
                                individual criterion details.
                            </div>
                        )}

                        <div className="ef-result-disclaimer">
                            <strong>Please note:</strong> This result is a
                            preliminary assessment, not an official approval.
                            Confirm the latest requirements and application
                            deadlines with the scheme provider.
                        </div>

                        <div className="ef-result-actions">
                            <button
                                type="button"
                                className="ef-button ef-button-secondary"
                                onClick={startAgain}
                            >
                                ↻ Start again
                            </button>

                            <button
                                type="button"
                                className="ef-button ef-button-primary"
                                onClick={() => navigate(-1)}
                            >
                                Back to Scheme <span>→</span>
                            </button>
                        </div>
                    </section>
                )}
            </div>
        </main>
    );
}
