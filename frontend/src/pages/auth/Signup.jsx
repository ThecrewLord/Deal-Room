import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import AuthLayout from "../../components/AuthLayout";
import authService from "../../auth/authService";
import "../../styles/auth.css";

export default function Signup() {
    const navigate = useNavigate();
    const [form, setForm] = useState({ full_name: "", email: "", password: "" });
    const [error, setError] = useState("");
    const [submitting, setSubmitting] = useState(false);
    const handleChange = (e) => setForm((previous) => ({ ...previous, [e.target.name]: e.target.value }));
    const submit = async (e) => {
        e.preventDefault(); setError(""); setSubmitting(true);
        try { await authService.signup(form); navigate("/pending"); }
        catch (err) { setError(err.response?.data?.message ?? "Unable to register."); }
        finally { setSubmitting(false); }
    };
    return (
        <AuthLayout eyebrow="GET STARTED" title="Create your Deal Room account" description="Set up your account and get ready to collaborate on better deals.">
            <form className="auth-modern-form" onSubmit={submit} noValidate>
                <label className="auth-field"><span>Full Name</span><input id="signup-full-name" name="full_name" aria-invalid={Boolean(error)} aria-describedby={error ? "signup-error" : undefined} value={form.full_name} onChange={handleChange} placeholder="Your full name" required autoComplete="name" /></label>
                <label className="auth-field"><span>Email</span><input id="signup-email" name="email" type="email" aria-invalid={Boolean(error)} aria-describedby={error ? "signup-error" : undefined} value={form.email} onChange={handleChange} placeholder="you@company.com" required autoComplete="email" /></label>
                <label className="auth-field"><span>Password</span><input id="signup-password" name="password" type="password" aria-invalid={Boolean(error)} aria-describedby={error ? "signup-error" : undefined} value={form.password} onChange={handleChange} placeholder="Create a password" required autoComplete="new-password" /></label>
                {error && <div id="signup-error" className="auth-error" role="alert">{error}</div>}
                <button className="auth-submit" type="submit" disabled={submitting}>{submitting ? "Creating account…" : "Register"}</button>
            </form>
            <p className="auth-footer-link">Already have an account? <Link to="/login">Back to Login</Link></p>
        </AuthLayout>
    );
}

