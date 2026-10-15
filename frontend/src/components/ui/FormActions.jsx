export default function FormActions({ children, className = "" }) {
    return (
        <div className={`shared-form-actions ${className}`.trim()}>
            {children}
        </div>
    );
}
