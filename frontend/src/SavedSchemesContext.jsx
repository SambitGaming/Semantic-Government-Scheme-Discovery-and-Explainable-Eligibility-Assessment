
import {
    createContext,
    useCallback,
    useContext,
    useEffect,
    useState,
} from "react";

const SavedSchemesContext = createContext(null);

const LIBRARY_KEY = "sga_saved_schemes";

function getSchemeId(scheme) {
    return String(
        scheme?.scheme_id ??
        scheme?.id ??
        scheme?.ID ??
        scheme?.schemeId ??
        ""
    );
}

function readSavedSchemes() {
    try {
        const saved = JSON.parse(
            localStorage.getItem(LIBRARY_KEY) || "[]"
        );

        return Array.isArray(saved) ? saved : [];
    } catch {
        return [];
    }
}

export function SavedSchemesProvider({ children }) {
    const [savedSchemes, setSavedSchemes] = useState(
        readSavedSchemes
    );

    useEffect(() => {
        function syncSavedSchemes(event) {
            if (
                event.type === "storage" &&
                event.key !== LIBRARY_KEY
            ) {
                return;
            }

            setSavedSchemes(readSavedSchemes());
        }

        window.addEventListener("storage", syncSavedSchemes);

        return () => {
            window.removeEventListener(
                "storage",
                syncSavedSchemes
            );
        };
    }, []);

    const isSaved = useCallback(
        (scheme) => {
            const id = getSchemeId(scheme);

            return Boolean(id) && savedSchemes.some(
                (item) => getSchemeId(item) === id
            );
        },
        [savedSchemes]
    );

    const toggleSaved = useCallback((scheme) => {
        const id = getSchemeId(scheme);

        if (!id) {
            return;
        }

        setSavedSchemes((current) => {
            const alreadySaved = current.some(
                (item) => getSchemeId(item) === id
            );

            const updated = alreadySaved
                ? current.filter(
                    (item) => getSchemeId(item) !== id
                )
                : [...current, { ...scheme, scheme_id: id }];

            try {
                localStorage.setItem(
                    LIBRARY_KEY,
                    JSON.stringify(updated)
                );
            } catch (error) {
                console.error(
                    "Unable to save your library:",
                    error
                );
            }

            return updated;
        });
    }, []);

    const removeSaved = useCallback((scheme) => {
        const id = getSchemeId(scheme);

        setSavedSchemes((current) => {
            const updated = current.filter(
                (item) => getSchemeId(item) !== id
            );

            try {
                localStorage.setItem(
                    LIBRARY_KEY,
                    JSON.stringify(updated)
                );
            } catch (error) {
                console.error(
                    "Unable to update your library:",
                    error
                );
            }

            return updated;
        });
    }, []);

    return (
        <SavedSchemesContext.Provider
            value={{
                savedSchemes,
                isSaved,
                toggleSaved,
                removeSaved,
            }}
        >
            {children}
        </SavedSchemesContext.Provider>
    );
}

export function useSavedSchemes() {
    const context = useContext(SavedSchemesContext);

    if (!context) {
        throw new Error(
            "useSavedSchemes must be used inside SavedSchemesProvider"
        );
    }

    return context;
}
