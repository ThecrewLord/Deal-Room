export default function FormSection({
    title,
    description,
    children,
    className = "",
}) {
    return (
        <section className={`shared-form-section ${className}`.trim()}>
            {(title || description) && (
                <div className="shared-form-section-heading">
                    {title && <h3>{title}</h3>}
                    {description && <p>{description}</p>}
                </div>
            )}
            {children}
        </section>
    );
}
