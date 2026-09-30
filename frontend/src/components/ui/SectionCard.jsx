import Card from "./Card";

export default function SectionCard({
    title,
    description,
    icon: Icon,
    action,
    children,
    className = "",
    collapsible = false,
    collapsed = false,
    onToggle,
}) {
    return (
        <Card className={`ui-section-card ${className}`}>
            {(title || action) && (
                <div
                    className="ui-section-header"
                    onClick={collapsible ? onToggle : undefined}
                    style={collapsible ? { cursor: "pointer" } : undefined}
                >
                    <div className="ui-section-title">
                        {collapsible && (
                            <span style={{ marginRight: 6 }}>
                                {collapsed ? "▸" : "▾"}
                            </span>
                        )}
                        {Icon && (
                            <span className="ui-section-icon">
                                <Icon size={15} />
                            </span>
                        )}
                        <div>
                            {title && <h2>{title}</h2>}
                            {description && <p>{description}</p>}
                        </div>
                    </div>
                    {action}
                </div>
            )}
            {(!collapsible || !collapsed) && children}
        </Card>
    );
}
