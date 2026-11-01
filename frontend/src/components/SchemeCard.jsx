import { Link } from "react-router-dom";

function displayText(value, fallback = "") {
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
}

function SchemeCard({ scheme }) {
    const schemeId = String(
        scheme?.scheme_id ??
        scheme?.id ??
        scheme?.ID ??
        scheme?.schemeId ??
        ""
    ).trim();

    const schemeName = displayText(
        scheme?.scheme_name ??
        scheme?.Scholarship ??
        scheme?.name,
        "Government Scheme"
    );

    const description = displayText(
        scheme?.description ??
        scheme?.Description,
        "No description available."
    );

    const category = displayText(
        scheme?.category ??
        scheme?.Category,
        "Government Scheme"
    );

    return (
        <article className="scheme-card">
            {/* Scheme category */}
            <div className="scheme-card-top">
                <span className="scheme-card-category">
                    {category}
                </span>
            </div>

            {/* Scheme title */}
            <h3>{schemeName}</h3>

            {/* Short description */}
            <p className="scheme-description">
                {description}
            </p>

            {/* View details button */}
            <div className="scheme-card-actions">
                {schemeId ? (
                    <Link
                        to={`/schemes/${encodeURIComponent(
                            schemeId
                        )}`}
                        className="view-details-button"
                        aria-label={`View details for ${schemeName}`}
                    >
                        View Details →
                    </Link>
                ) : (
                    <button
                        type="button"
                        className="view-details-button"
                        disabled
                        title="Scheme details are unavailable because the scheme ID is missing."
                    >
                        Details Unavailable
                    </button>
                )}
            </div>
        </article>
    );
}

export default SchemeCard;
