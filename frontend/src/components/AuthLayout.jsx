import { BarChart3, CheckCircle2, ShieldCheck, TrendingUp } from "lucide-react";

export default function AuthLayout({ eyebrow, title, description, children }) {
    return (
        <div className="auth-modern-shell">
            <aside className="auth-brand-panel">
                <div className="auth-brand-mark"><BarChart3 size={20} /><span>Deal Room</span></div>
                <div className="auth-brand-copy"><span className="auth-eyebrow">{eyebrow}</span><h1>Sales Intelligence for Every Deal</h1><p>Bring pipeline visibility, technical collaboration, and deal execution into one place.</p></div>
                <div className="auth-visual" aria-hidden="true">
                    <div className="auth-visual-grid"><span /><span /><span /><span /><span /><span /></div>
                    <div className="auth-chart"><div className="auth-chart-line line-one" /><div className="auth-chart-line line-two" /><div className="auth-chart-dot dot-one" /><div className="auth-chart-dot dot-two" /><div className="auth-chart-dot dot-three" /></div>
                    <div className="auth-float-card"><TrendingUp size={15} /><div><strong>Pipeline health</strong><small>Visibility across every stage</small></div></div>
                    <div className="auth-float-card auth-float-card-two"><CheckCircle2 size={15} /><div><strong>Deal execution</strong><small>Aligned teams, clearer next steps</small></div></div>
                </div>
                <div className="auth-brand-foot"><ShieldCheck size={14} /> Role-based access built into Deal Room</div>
            </aside>
            <main className="auth-form-panel"><div className="auth-mobile-brand"><BarChart3 size={18} /><span>Deal Room</span></div><div className="auth-modern-card"><div className="auth-form-heading"><span className="auth-eyebrow">{eyebrow}</span><h2>{title}</h2><p>{description}</p></div>{children}</div></main>
        </div>
    );
}
