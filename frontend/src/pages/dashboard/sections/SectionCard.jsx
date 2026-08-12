const SectionCard = ({
    title,
    action,
    children,
    className = "",
}) => {
    return (
        <section className={`dashboard-section ${className}`}>
            <div className="dashboard-section-header">
                <h3>{title}</h3>

                {action}
            </div>

            <div className="dashboard-section-body">
                {children}
            </div>
        </section>
    );
};

export default SectionCard;