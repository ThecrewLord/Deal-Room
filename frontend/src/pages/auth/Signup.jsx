import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import authService from "../../auth/authService";

import "../../styles/auth.css";

export default function Signup() {
    const navigate = useNavigate();

    const [form, setForm] = useState({
        full_name: "",
        email: "",
        password: "",
    });

    const [error, setError] = useState("");

    const handleChange = (e) => {
        setForm((previous) => ({
            ...previous,
            [e.target.name]: e.target.value,
        }));
    };

    const submit = async (e) => {
        e.preventDefault();

        setError("");

        try {
            await authService.signup(form);

            navigate("/pending");
        } catch (err) {
            setError(
                err.response?.data?.message ??
                    "Unable to register."
            );
        }
    };

    return (
        <div className="auth-container">
            <div className="auth-card">
                <h2>Create Account</h2>

                <form
                    className="auth-form"
                    onSubmit={submit}
                >
                    <input
                        name="full_name"
                        placeholder="Full Name"
                        value={form.full_name}
                        onChange={handleChange}
                        required
                    />

                    <input
                        name="email"
                        type="email"
                        placeholder="Email"
                        value={form.email}
                        onChange={handleChange}
                        required
                    />

                    <input
                        name="password"
                        type="password"
                        placeholder="Password"
                        value={form.password}
                        onChange={handleChange}
                        required
                    />

                    <button type="submit">
                        Register
                    </button>
                </form>

                {error && (
                    <p>{error}</p>
                )}

                <div className="auth-link">
                    <Link to="/login">
                        Back to Login
                    </Link>
                </div>
            </div>
        </div>
    );
}