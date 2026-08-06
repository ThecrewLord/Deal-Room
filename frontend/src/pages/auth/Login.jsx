import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../../context/AuthContext";

import "../../styles/auth.css";

export default function Login() {
    const navigate = useNavigate();

    const { login } = useAuth();

    const [email, setEmail] =
        useState("");

    const [password, setPassword] =
        useState("");

    const [error, setError] =
        useState("");

    const handleSubmit = async (e) => {
        e.preventDefault();

        setError("");

        try {
            const response =
                await login({
                    email,
                    password,
                });

            if (
                response.requires_role_selection
            ) {
                sessionStorage.setItem(
                    "login_response",
                    JSON.stringify(
                        response
                    )
                );

                navigate(
                    "/select-role"
                );

                return;
            }

            await new Promise(resolve => setTimeout(resolve, 0));

            navigate("/dashboard", {
                replace: true,
            });

        } catch (err) {
            const message =
                err.response?.data
                    ?.message ??
                "Login failed.";

            if (
                message.includes(
                    "awaiting administrator approval"
                )
            ) {
                navigate("/pending");
                return;
            }

            if (
                message.includes(
                    "revoked"
                )
            ) {
                navigate("/revoked");
                return;
            }

            setError(message);
        }
    };

    return (
        <div className="auth-container">
            <div className="auth-card">
                <h2>Login</h2>

                <form
                    className="auth-form"
                    onSubmit={
                        handleSubmit
                    }
                >
                    <input
                        type="email"
                        placeholder="Email"
                        value={email}
                        onChange={(e) =>
                            setEmail(
                                e.target
                                    .value
                            )
                        }
                        required
                    />

                    <input
                        type="password"
                        placeholder="Password"
                        value={password}
                        onChange={(e) =>
                            setPassword(
                                e.target
                                    .value
                            )
                        }
                        required
                    />

                    <button type="submit">
                        Login
                    </button>
                </form>

                {error && (
                    <p>{error}</p>
                )}

                <div className="auth-link">
                    <Link to="/signup">
                        Create Account
                    </Link>
                </div>
            </div>
        </div>
    );
}