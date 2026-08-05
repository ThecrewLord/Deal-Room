import { useEffect, useState } from "react";
import adminApi from "../../api/adminApi";

const AVAILABLE_ROLES = [
    "Admin",
    "Sales",
    "Delivery",
    "Solution Engineer",
];

export default function UserApproval() {

    const [users, setUsers] = useState([]);

    async function loadUsers() {
        const data = await adminApi.getPending();
        setUsers(data);
    }

    useEffect(() => {
        loadUsers();
    }, []);

    async function approve(user, roles) {

        await adminApi.approve(
            user.user_id,
            roles,
        );

        loadUsers();
    }

    async function revoke(user) {

        await adminApi.revoke(
            user.user_id,
        );

        loadUsers();
    }

    return (

        <div>

            <h2>Pending Users</h2>

            {users.map(user => (

                <ApprovalCard
                    key={user.user_id}
                    user={user}
                    approve={approve}
                    revoke={revoke}
                />

            ))}

        </div>

    );
}

function ApprovalCard({
    user,
    approve,
    revoke,
}) {

    const [roles, setRoles] = useState([]);

    function toggle(role) {

        if (roles.includes(role)) {

            setRoles(
                roles.filter(r => r !== role)
            );

        } else {

            setRoles([
                ...roles,
                role,
            ]);

        }

    }

    return (

        <div className="approval-card">

            <h3>{user.full_name}</h3>

            <p>{user.email}</p>

            {AVAILABLE_ROLES.map(role => (

                <label key={role}>

                    <input
                        type="checkbox"
                        checked={roles.includes(role)}
                        onChange={() => toggle(role)}
                    />

                    {role}

                </label>

            ))}

            <div>

                <button
                    onClick={() =>
                        approve(user, roles)
                    }
                >
                    Approve
                </button>

                <button
                    onClick={() =>
                        revoke(user)
                    }
                >
                    Revoke
                </button>

            </div>

        </div>

    );
}