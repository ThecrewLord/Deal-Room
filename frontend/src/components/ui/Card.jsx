export default function Card({ children, className = "", padding = true }) {
    return <section className={`ui-card ${padding ? "ui-card-padded" : ""} ${className}`}>{children}</section>;
}
