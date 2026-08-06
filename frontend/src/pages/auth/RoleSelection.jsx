import {
    useState,
} from "react";

import {
    useNavigate,
} from "react-router-dom";

import {
    useAuth,
} from "../../context/AuthContext";

import "../../styles/auth.css";

export default function RoleSelection() {

    const navigate =
        useNavigate();

    const { selectRole } =
        useAuth();

    const loginResponse =
        JSON.parse(
            sessionStorage.getItem(
                "login_response"
            )
        );

    const [role, setRole] =
        useState("");

    const [error, setError] =
        useState("");

    if (!loginResponse) {

        navigate("/login");

        return null;

    }

    async function submit() {

        if (!role) {

            setError(
                "Please select a role."
            );

            return;

        }

        try {

            await selectRole(role);

            sessionStorage.removeItem(
                "login_response"
            );

            navigate("/dashboard");

        } catch (err) {

            setError(
                err.response?.data
                    ?.message ||
                    "Unable to select role."
            );

        }

    }

    return (

        <div className="auth-container">

            <div className="auth-card">

                <h2>

                    Select Role

                </h2>

                <div className="auth-form">

                    {loginResponse.roles.map(
                        (r) => (

                            <label
                                key={r}
                            >

                                <input
                                    type="radio"
                                    value={r}
                                    checked={
                                        role === r
                                    }
                                    onChange={() =>
                                        setRole(r)
                                    }
                                />

                                {" "}

                                {r}

                            </label>

                        )
                    )}

                    {error && (

                        <p>

                            {error}

                        </p>

                    )}

                    <button
                        onClick={submit}
                    >

                        Continue

                    </button>

                </div>

            </div>

        </div>

    );

}