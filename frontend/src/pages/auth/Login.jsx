import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import AuthLayout from "../../components/AuthLayout";
import { useAuth } from "../../context/AuthContext";
import "../../styles/auth.css";

export default function Login() {
    const navigate = useNavigate();
    const { login } = useAuth();

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [submitting, setSubmitting] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError("");
        setSubmitting(true);

        try {
            const response = await login({
                email: email.trim().toLowerCase(),
                password,
            });

            if (response.requires_role_selection) {
                navigate("/select-role", { replace: true });
                return;
            }

            navigate("/dashboard", { replace: true });
        } catch (err) {
            const message =
                err?.response?.data?.message ||
                err?.response?.data?.error ||
                err?.message ||
                "Invalid email or password.";

            setError(message);
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <AuthLayout
            eyebrow="DEAL ROOM"
            title="Welcome back"
            description="Sign in to continue managing your opportunities and deals."
        >
            <form
                className="auth-modern-form"
                onSubmit={handleSubmit}
                noValidate
            >
                <label className="auth-field">
                    <span>Email</span>
                    <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="you@company.com"
                        required
                        autoComplete="email"
                    />
                </label>

                <label className="auth-field">
                    <span>Password</span>
                    <input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="Enter your password"
                        required
                        autoComplete="current-password"
                    />
                </label>

                {error && (
                    <div className="auth-error" role="alert">
                        {error}
                    </div>
                )}

                <button
                    className="auth-submit"
                    type="submit"
                    disabled={submitting}
                >
                    {submitting ? "Signing in…" : "Login"}
                </button>
            </form>

            <p className="auth-footer-link">
                Don't have an account?{" "}
                <Link to="/signup">Create Account</Link>
            </p>
        </AuthLayout>
    );
}
