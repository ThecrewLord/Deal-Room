import Card from "./Card";

export default function SectionCard({ title, description, icon: Icon, action, children, className = "" }) {
    return (
        <Card className={`ui-section-card ${className}`}>
            {(title || action) && (
                <div className="ui-section-header">
                    <div className="ui-section-title">
                        {Icon && <span className="ui-section-icon"><Icon size={15} /></span>}
                        <div>
                            {title && <h2>{title}</h2>}
                            {description && <p>{description}</p>}
                        </div>
                    </div>
                    {action}
                </div>
            )}
            {children}
        </Card>
    );
}
