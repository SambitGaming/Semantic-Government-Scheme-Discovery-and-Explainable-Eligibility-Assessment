
import { useEffect, useRef, useState } from "react";

const PROFILE_KEY = "sga_user_profile";

const DEFAULT_PROFILE = {
    name: "",
    email: "",
    phone: "",
    education: "",
    state: "",
    profilePicture: "",
};

// ======================================================
// PROFILE STORAGE
// ======================================================

function readProfile() {
    try {
        const saved = JSON.parse(
            localStorage.getItem(PROFILE_KEY) || "{}"
        );

        if (!saved || typeof saved !== "object" || Array.isArray(saved)) {
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
// IMAGE PROCESSING
// ======================================================

function compressImage(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();

        reader.onerror = () => {
            reject(new Error("Unable to read this image."));
        };

        reader.onload = () => {
            const image = new Image();

            image.onerror = () => {
                reject(
                    new Error(
                        "Unable to open this image. Please choose another."
                    )
                );
            };

            image.onload = () => {
                try {
                    const maxDimension = 512;

                    const scale = Math.min(
                        1,
                        maxDimension /
                            Math.max(image.width, image.height)
                    );

                    const canvas = document.createElement("canvas");

                    canvas.width = Math.max(
                        1,
                        Math.round(image.width * scale)
                    );

                    canvas.height = Math.max(
                        1,
                        Math.round(image.height * scale)
                    );

                    const context = canvas.getContext("2d");

                    if (!context) {
                        reject(
                            new Error("Image processing is unavailable.")
                        );
                        return;
                    }

                    context.drawImage(
                        image,
                        0,
                        0,
                        canvas.width,
                        canvas.height
                    );

                    const compressedImage = canvas.toDataURL(
                        "image/jpeg",
                        0.78
                    );

                    resolve(compressedImage);
                } catch {
                    reject(
                        new Error(
                            "Unable to process this image. Please try another."
                        )
                    );
                }
            };

            image.src = reader.result;
        };

        reader.readAsDataURL(file);
    });
}

// ======================================================
// PROFILE PAGE
// ======================================================

export default function Profile() {
    const [profile, setProfile] = useState(readProfile);
    const [message, setMessage] = useState("");
    const [messageType, setMessageType] = useState("");
    const [processingImage, setProcessingImage] = useState(false);

    const fileInputRef = useRef(null);

    // Synchronize changes made elsewhere in the application.
    useEffect(() => {
        function refreshProfile() {
            setProfile(readProfile());
        }

        window.addEventListener("storage", refreshProfile);
        window.addEventListener("profile-updated", refreshProfile);
        window.addEventListener("sga-profile-updated", refreshProfile);

        return () => {
            window.removeEventListener("storage", refreshProfile);
            window.removeEventListener("profile-updated", refreshProfile);
            window.removeEventListener(
                "sga-profile-updated",
                refreshProfile
            );
        };
    }, []);

    // ==================================================
    // INPUT HANDLING
    // ==================================================

    function handleChange(event) {
        const { name, value } = event.target;

        setProfile((previous) => ({
            ...previous,
            [name]: value,
        }));

        setMessage("");
        setMessageType("");
    }

    // ==================================================
    // UPLOAD PROFILE PICTURE
    // ==================================================

    async function handlePictureChange(event) {
        const file = event.target.files?.[0];

        // Permit selecting the same image again.
        event.target.value = "";

        if (!file) return;

        const allowedTypes = [
            "image/jpeg",
            "image/png",
            "image/webp",
        ];

        if (!allowedTypes.includes(file.type)) {
            setMessage("Please choose a JPG, PNG, or WebP image.");
            setMessageType("error");
            return;
        }

        if (file.size > 5 * 1024 * 1024) {
            setMessage("Please choose an image smaller than 5 MB.");
            setMessageType("error");
            return;
        }

        setProcessingImage(true);
        setMessage("");
        setMessageType("");

        try {
            const profilePicture = await compressImage(file);

            setProfile((previous) => ({
                ...previous,
                profilePicture,
            }));

            setMessage(
                "Picture selected. Click Save Profile to apply it."
            );

            setMessageType("success");
        } catch (error) {
            setMessage(
                error.message || "Unable to process this image."
            );

            setMessageType("error");
        } finally {
            setProcessingImage(false);
        }
    }

    // ==================================================
    // REMOVE PROFILE PICTURE
    // ==================================================

    function removePicture() {
        setProfile((previous) => ({
            ...previous,
            profilePicture: "",
        }));

        if (fileInputRef.current) {
            fileInputRef.current.value = "";
        }

        setMessage(
            "Picture removed from the preview. Click Save Profile to confirm."
        );

        setMessageType("success");
    }

    // ==================================================
    // SAVE PROFILE
    // ==================================================

    function handleSubmit(event) {
        event.preventDefault();

        if (processingImage) {
            setMessage("Please wait for the picture to finish processing.");
            setMessageType("error");
            return;
        }

        const updatedProfile = {
            ...profile,
            name: profile.name.trim(),
            email: profile.email.trim(),
            phone: profile.phone.trim(),
            education: profile.education.trim(),
            state: profile.state.trim(),
        };

        try {
            localStorage.setItem(
                PROFILE_KEY,
                JSON.stringify(updatedProfile)
            );

            setProfile(updatedProfile);

            // Notify the topbar and other components in this tab.
            window.dispatchEvent(
                new CustomEvent("profile-updated", {
                    detail: updatedProfile,
                })
            );

            window.dispatchEvent(
                new CustomEvent("sga-profile-updated", {
                    detail: updatedProfile,
                })
            );

            setMessage("Your profile has been saved successfully.");
            setMessageType("success");
        } catch (error) {
            console.error("Unable to save profile:", error);

            setMessage(
                "Unable to save your profile. Browser storage may be full. Try a smaller picture."
            );

            setMessageType("error");
        }
    }

    // ==================================================
    // AVATAR FALLBACK
    // ==================================================

    const initial = (
        profile.name.trim().charAt(0) || "U"
    ).toUpperCase();

    // ==================================================
    // RENDER
    // ==================================================

    return (
        <div className="page-container profile-page">
            <section className="page-heading-block">
                <span className="page-eyebrow">
                    YOUR ACCOUNT
                </span>

                <h1>My Profile</h1>

                <p>
                    Manage your personal details and profile picture.
                </p>
            </section>

            <section className="profile-page-card">
                <form
                    onSubmit={handleSubmit}
                    className="profile-form profile-page-form"
                >
                    {/* PROFILE PICTURE */}

                    <div className="profile-picture-section">
                        {profile.profilePicture ? (
                            <img
                                src={profile.profilePicture}
                                alt="Your profile picture"
                                className="profile-picture profile-picture-preview"
                            />
                        ) : (
                            <div
                                className="profile-picture profile-picture-preview profile-picture-placeholder"
                                aria-label="Default profile picture"
                            >
                                {initial}
                            </div>
                        )}

                        <div className="profile-picture-actions">
                            <h2>Profile picture</h2>

                            <p>
                                Choose a JPG, PNG, or WebP image.
                                Maximum original file size: 5 MB.
                            </p>

                            <div className="profile-picture-buttons">
                                <button
                                    type="button"
                                    className="primary-button profile-picture-upload"
                                    onClick={() =>
                                        fileInputRef.current?.click()
                                    }
                                    disabled={processingImage}
                                >
                                    {processingImage
                                        ? "Processing image..."
                                        : profile.profilePicture
                                            ? "Change Picture"
                                            : "Upload Picture"}
                                </button>

                                {profile.profilePicture && (
                                    <button
                                        type="button"
                                        className="remove-picture-button profile-cancel-button"
                                        onClick={removePicture}
                                        disabled={processingImage}
                                    >
                                        Remove Picture
                                    </button>
                                )}
                            </div>

                            <input
                                ref={fileInputRef}
                                id="profilePicture"
                                name="profilePictureFile"
                                type="file"
                                accept="image/jpeg,image/png,image/webp"
                                onChange={handlePictureChange}
                                hidden
                            />
                        </div>
                    </div>

                    <div className="profile-page-divider" />

                    {/* PERSONAL DETAILS */}

                    <div className="profile-form-grid">
                        <label htmlFor="name">
                            Full name

                            <input
                                id="name"
                                name="name"
                                type="text"
                                value={profile.name}
                                onChange={handleChange}
                                placeholder="Enter your full name"
                                maxLength={100}
                                autoComplete="name"
                            />
                        </label>

                        <label htmlFor="email">
                            Email address

                            <input
                                id="email"
                                name="email"
                                type="email"
                                value={profile.email}
                                onChange={handleChange}
                                placeholder="you@example.com"
                                maxLength={254}
                                autoComplete="email"
                            />
                        </label>

                        <label htmlFor="phone">
                            Phone number

                            <input
                                id="phone"
                                name="phone"
                                type="tel"
                                value={profile.phone}
                                onChange={handleChange}
                                placeholder="Enter your phone number"
                                maxLength={20}
                                autoComplete="tel"
                            />
                        </label>

                        <label htmlFor="education">
                            Education

                            <input
                                id="education"
                                name="education"
                                type="text"
                                value={profile.education}
                                onChange={handleChange}
                                placeholder="e.g. MCA student"
                                maxLength={100}
                            />
                        </label>

                        <label
                            htmlFor="state"
                            className="profile-state-field"
                        >
                            State

                            <input
                                id="state"
                                name="state"
                                type="text"
                                value={profile.state}
                                onChange={handleChange}
                                placeholder="Enter your state"
                                maxLength={100}
                                autoComplete="address-level1"
                            />
                        </label>
                    </div>

                    {/* STATUS MESSAGE */}

                    {message && (
                        <p
                            role="status"
                            aria-live="polite"
                            className={`profile-message ${
                                messageType === "error"
                                    ? "profile-form-error"
                                    : "profile-form-success"
                            }`}
                        >
                            {message}
                        </p>
                    )}

                    {/* SAVE BUTTON */}

                    <div className="profile-page-actions">
                        <button
                            type="submit"
                            className="primary-button save-profile-button"
                            disabled={processingImage}
                        >
                            Save Profile
                        </button>
                    </div>
                </form>
            </section>
        </div>
    );
}
