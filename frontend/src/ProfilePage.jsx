import { useState } from "react";
import { Link } from "react-router-dom";

import "./ProfilePage.css";

const PROFILE_KEY = "sga_user_profile";

const EMPTY_PROFILE = {
    name: "",
    email: "",
    phone: "",
    education: "",
    state: "",
};

function readProfile() {
    try {
        const saved = JSON.parse(
            localStorage.getItem(PROFILE_KEY) || "{}"
        );

        return {
            ...EMPTY_PROFILE,
            ...(saved && typeof saved === "object" ? saved : {}),
        };
    } catch {
        return { ...EMPTY_PROFILE };
    }
}

function ProfilePage() {
    const [profile, setProfile] = useState(readProfile);
    const [draft, setDraft] = useState(readProfile);
    const [editing, setEditing] = useState(false);
    const [message, setMessage] = useState("");

    function handleChange(event) {
        const { name, value } = event.target;

        setDraft((current) => ({
            ...current,
            [name]: value,
        }));
    }

    function startEditing() {
        setDraft({ ...profile });
        setMessage("");
        setEditing(true);
    }

    function cancelEditing() {
        setDraft({ ...profile });
        setEditing(false);
        setMessage("");
    }

    function saveProfile(event) {
        event.preventDefault();

        const updated = {
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
            setMessage("Your profile has been saved.");
        } catch (error) {
            console.error("Unable to save profile:", error);
            setMessage(
                "Unable to save your profile. Check your browser storage."
            );
        }
    }

    const initial = profile.name.trim().charAt(0).toUpperCase() || "U";

    return (
        <div className="page-container profile-page">
            <section className="profile-page-hero">
                <span className="page-eyebrow">YOUR ACCOUNT</span>
                <h1>My Profile</h1>
                <p>
                    Manage your personal details to make your scheme
                    discovery experience easier.
                </p>
            </section>

            <section className="profile-page-card">
                <div className="profile-page-heading">
                    <div className="profile-page-avatar">
                        {initial}
                    </div>

                    <div>
                        <h2>{profile.name || "Your Profile"}</h2>
                        <p>
                            {profile.email || "Add your email address"}
                        </p>
                    </div>
                </div>

                {message && (
                    <p className="profile-page-message" role="status">
                        {message}
                    </p>
                )}

                {editing ? (
                    <form
                        className="profile-page-form"
                        onSubmit={saveProfile}
                    >
                        <label>
                            Full name
                            <input
                                name="name"
                                value={draft.name}
                                onChange={handleChange}
                                placeholder="Enter your full name"
                                maxLength={100}
                            />
                        </label>

                        <label>
                            Email address
                            <input
                                type="email"
                                name="email"
                                value={draft.email}
                                onChange={handleChange}
                                placeholder="you@example.com"
                                maxLength={254}
                            />
                        </label>

                        <label>
                            Phone number
                            <input
                                type="tel"
                                name="phone"
                                value={draft.phone}
                                onChange={handleChange}
                                placeholder="Enter your phone number"
                                maxLength={20}
                            />
                        </label>

                        <label>
                            Education level
                            <input
                                name="education"
                                value={draft.education}
                                onChange={handleChange}
                                placeholder="e.g. MCA student"
                                maxLength={100}
                            />
                        </label>

                        <label>
                            State
                            <input
                                name="state"
                                value={draft.state}
                                onChange={handleChange}
                                placeholder="Enter your state"
                                maxLength={100}
                            />
                        </label>

                        <div className="profile-page-actions">
                            <button
                                type="button"
                                className="profile-cancel-button"
                                onClick={cancelEditing}
                            >
                                Cancel
                            </button>

                            <button
                                type="submit"
                                className="primary-button"
                            >
                                Save Changes
                            </button>
                        </div>
                    </form>
                ) : (
                    <>
                        <div className="profile-page-details">
                            <div>
                                <span>Full name</span>
                                <strong>{profile.name || "Not added"}</strong>
                            </div>

                            <div>
                                <span>Email address</span>
                                <strong>{profile.email || "Not added"}</strong>
                            </div>

                            <div>
                                <span>Phone number</span>
                                <strong>{profile.phone || "Not added"}</strong>
                            </div>

                            <div>
                                <span>Education level</span>
                                <strong>
                                    {profile.education || "Not added"}
                                </strong>
                            </div>

                            <div>
                                <span>State</span>
                                <strong>{profile.state || "Not added"}</strong>
                            </div>
                        </div>

                        <button
                            type="button"
                            className="primary-button"
                            onClick={startEditing}
                        >
                            ✎ Edit Profile
                        </button>
                    </>
                )}

                <Link to="/library" className="profile-page-library-link">
                    ♥ Go to My Library
                </Link>
            </section>
        </div>
    );
}

export default ProfilePage;