const WelcomeSection = ({ user }) => {

    const today = new Date().toLocaleDateString(undefined, {
        weekday: "long",
        month: "long",
        day: "numeric",
        year: "numeric",
    });

    return (
        <section className="dashboard-welcome">

            <div>

                <h1>
                    Welcome back, {user?.full_name || user?.name}
                </h1>

                <p>{today}</p>

            </div>

            <div className="user-summary">

                <div>
                    <span>Name</span>
                    <strong>{user?.full_name}</strong>
                </div>

                <div>
                    <span>Email</span>
                    <strong>{user?.email}</strong>
                </div>

                <div>
                    <span>Role</span>
                    <strong>{user?.active_role}</strong>
                </div>

            </div>

        </section>
    );
};

export default WelcomeSection;