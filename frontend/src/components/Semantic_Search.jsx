import { useState } from "react";
import { semanticSearch } from "../services/api";


function SemanticSearch() {

    const [query, setQuery] = useState("");
    const [model, setModel] = useState("minilm");

    const [results, setResults] = useState([]);

    const [loading, setLoading] = useState(false);

    const [error, setError] = useState("");


    async function handleSearch(event) {

        event.preventDefault();

        if (!query.trim()) {
            return;
        }

        setLoading(true);
        setError("");
        setResults([]);

        try {

            const data = await semanticSearch(
                query,
                model,
                10
            );

            setResults(
                data.results || []
            );

        } catch (err) {

            setError(
                err.message ||
                "Search failed"
            );

        } finally {

            setLoading(false);
        }
    }


    return (
        <section className="semantic-search">

            <h2>
                Find Government Schemes
            </h2>

            <p>
                Describe what you need in your
                own words.
            </p>


            <form
                className="semantic-search-form"
                onSubmit={handleSearch}
            >

                <input
                    type="text"
                    value={query}
                    onChange={(event) =>
                        setQuery(event.target.value)
                    }
                    placeholder="Example: I need financial assistance for higher education"
                />


                <select
                    value={model}
                    onChange={(event) =>
                        setModel(event.target.value)
                    }
                >

                    <option value="minilm">
                        MiniLM
                    </option>

                    <option value="mpnet">
                        MPNet
                    </option>

                </select>


                <button
                    type="submit"
                    disabled={loading}
                >

                    {loading
                        ? "Searching..."
                        : "Search"}

                </button>

            </form>


            {error && (

                <p className="search-error">
                    {error}
                </p>

            )}


            {loading && (

                <p>
                    Searching government schemes...
                </p>

            )}


            {!loading &&
                results.length > 0 && (

                <div className="search-results">

                    <h3>
                        Search Results
                    </h3>


                    {results.map(
                        (scheme, index) => (

                        <div
                            key={scheme.scheme_id}
                            className="search-result-card"
                        >

                            <div className="result-rank">
                                #{index + 1}
                            </div>


                            <h4>
                                {scheme.scheme_name}
                            </h4>


                            <p>
                                {scheme.description}
                            </p>


                            {scheme.category && (

                                <p>
                                    <strong>
                                        Category:
                                    </strong>{" "}
                                    {scheme.category}
                                </p>

                            )}


                            <p className="similarity-score">

                                Semantic similarity:{" "}

                                {Number(
                                    scheme.score
                                ).toFixed(4)}

                            </p>


                            {scheme.official_url && (

                                <a
                                    href={
                                        scheme.official_url
                                    }
                                    target="_blank"
                                    rel="noreferrer"
                                >
                                    Official Website
                                </a>

                            )}

                        </div>

                    ))}

                </div>

            )}


            {!loading &&
                query.trim() &&
                results.length === 0 &&
                !error && (

                <p>
                    No matching schemes found.
                </p>

            )}

        </section>
    );
}


export default SemanticSearch;