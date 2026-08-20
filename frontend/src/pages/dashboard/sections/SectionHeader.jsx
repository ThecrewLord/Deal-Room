const SectionHeader = ({
    title,
    action,
}) => {
    return (
        <div className="dashboard-section-header">
            <h2>{title}</h2>

            {action}
        </div>
    );
};

export default SectionHeader;