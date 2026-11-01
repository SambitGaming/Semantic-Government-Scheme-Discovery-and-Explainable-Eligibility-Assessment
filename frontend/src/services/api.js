
const API_BASE_URL = "http://127.0.0.1:8000";

// Safely read API responses, including non-JSON error messages.
async function readResponse(response, fallbackMessage) {
    const responseText = await response.text();

    let data = null;

    if (responseText) {
        try {
            data = JSON.parse(responseText);
        } catch {
            data = null;
        }
    }

    if (!response.ok) {
        const detail =
            data?.detail ||
            data?.message ||
            responseText ||
            fallbackMessage;

        throw new Error(
            `${detail} (HTTP ${response.status})`
        );
    }

    if (!responseText) {
        return null;
    }

    if (data === null) {
        throw new Error(
            "The API returned an invalid JSON response."
        );
    }

    return data;
}

// Fetch all government schemes.
export async function getSchemes() {
    const response = await fetch(
        `${API_BASE_URL}/schemes`
    );

    return await readResponse(
        response,
        "Failed to fetch schemes"
    );
}

// Fetch details for one government scheme.
export async function getScheme(schemeId) {
    if (
        schemeId === null ||
        schemeId === undefined ||
        String(schemeId).trim() === ""
    ) {
        throw new Error("Scheme ID is missing.");
    }

    const response = await fetch(
        `${API_BASE_URL}/schemes/${encodeURIComponent(
            String(schemeId)
        )}`
    );

    return await readResponse(
        response,
        "Failed to fetch scheme details"
    );
}

// Check eligibility for a selected scheme.
export async function checkEligibility(
    schemeId,
    userProfile
) {
    if (
        schemeId === null ||
        schemeId === undefined ||
        String(schemeId).trim() === ""
    ) {
        throw new Error("Scheme ID is missing.");
    }

    const response = await fetch(
        `${API_BASE_URL}/schemes/${encodeURIComponent(
            String(schemeId)
        )}/eligibility`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            body: JSON.stringify(userProfile)
        }
    );

    return await readResponse(
        response,
        "Failed to check eligibility"
    );
}

// Semantic search using MiniLM or MPNet.
export async function semanticSearch(
    query,
    model = "minilm",
    topK = 10
) {
    const cleanedQuery = String(query ?? "").trim();
    const selectedModel = String(model).toLowerCase();

    if (!cleanedQuery) {
        throw new Error(
            "Please enter a search query."
        );
    }

    if (!["minilm", "mpnet"].includes(selectedModel)) {
        throw new Error(
            'Invalid model. Choose "minilm" or "mpnet".'
        );
    }

    const parsedTopK = Number(topK);

    if (
        !Number.isInteger(parsedTopK) ||
        parsedTopK < 1 ||
        parsedTopK > 100
    ) {
        throw new Error(
            "topK must be an integer between 1 and 100."
        );
    }

    const params = new URLSearchParams({
        q: cleanedQuery,
        model: selectedModel,
        top_k: String(parsedTopK)
    });

    let response;

    try {
        response = await fetch(
            `${API_BASE_URL}/search?${params.toString()}`,
            {
                method: "GET",
                headers: {
                    "Accept": "application/json"
                }
            }
        );
    } catch (error) {
        throw new Error(
            "Cannot connect to the semantic search API. " +
            "Check that FastAPI is running at " +
            `${API_BASE_URL}. Details: ${error.message}`
        );
    }

    return await readResponse(
        response,
        "Semantic search failed"
    );
}
