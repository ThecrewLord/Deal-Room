import { useEffect, useState } from "react";
import adminApi from "../../api/adminApi";

export default function UserManagement() {

    const [users, setUsers] = useState([]);

    useEffect(() => {

        adminApi
            .getUsers()
            .then(setUsers);

    }, []);

    return (

        <div>

            <h2>Users</h2>

            <table>

                <thead>

                    <tr>

                        <th>Name</th>

                        <th>Email</th>

                        <th>Status</th>

                    </tr>

                </thead>

                <tbody>

                    {users.map(user => (

                        <tr key={user.user_id}>

                            <td>{user.full_name}</td>

                            <td>{user.email}</td>

                            <td>{user.status}</td>

                        </tr>

                    ))}

                </tbody>

            </table>

        </div>

    );
}