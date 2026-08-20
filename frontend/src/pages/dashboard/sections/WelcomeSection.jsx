const WelcomeSection = ({ user }) => {
    const hour = new Date().getHours();

    const greeting =
        hour < 12
            ? "Good Morning"
            : hour < 18
            ? "Good Afternoon"
            : "Good Evening";

    const today = new Date().toLocaleDateString(undefined, {
        weekday: "long",
        day: "numeric",
        month: "long",
        year: "numeric",
    });

    const displayName =
        user?.full_name ||
        user?.name ||
        "User";

    const displayRole =
        user?.active_role || "No Active Role";

    return (
        <section className="dashboard-welcome">
            <div className="welcome-content">
                <div>
                    <h1>
                        {greeting}, {displayName}
                    </h1>

                    <p>{today}</p>

                    <span className="role-badge">
                        {displayRole}
                    </span>
                </div>
            </div>

            <div className="user-summary">
                <div>
                    <span>Name</span>

                    <strong>{displayName}</strong>
                </div>

                <div>
                    <span>Email</span>

                    <strong>{user?.email || "-"}</strong>
                </div>

                <div>
                    <span>Role</span>

                    <strong>{displayRole}</strong>
                </div>
            </div>
        </section>
    );
};

export default WelcomeSection;