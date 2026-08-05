import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { login, createSession } from "../../auth/authService";

import "../../styles/auth.css";

export default function Login() {

    const navigate = useNavigate();

    const [email,setEmail]=useState("");
    const [password,setPassword]=useState("");
    const [error,setError]=useState("");

    const handleSubmit=async(e)=>{

        e.preventDefault();

        setError("");

        try{

            const data=await login({
                email,
                password
            });

            if(data.status==="PENDING"){
                navigate("/pending");
                return;
            }

            if(data.status==="REVOKED"){
                navigate("/revoked");
                return;
            }

            if(data.roles.length===1){

                createSession({
                    token:data.token,
                    user:data.user,
                    activeRole:data.roles[0]
                });

                navigate("/dashboard");
                return;
            }

            sessionStorage.setItem(
                "login_response",
                JSON.stringify(data)
            );

            navigate("/select-role");

        }catch(err){

            setError(
                err.response?.data?.message ||
                "Login failed."
            );
        }

    }


    // const handleSubmit = async (e) => {
    //     e.preventDefault();

    //     const data = {
    //         token: "dummy-token",
    //         status: "APPROVED",
    //         user: {
    //             firstName: "Rajdeep",
    //             lastName: "Sidhu",
    //             email: "rajdeep@test.com",
    //         },
    //         roles: ["Admin", "Sales"],
    //     };

    //     if (data.status === "PENDING") {
    //         navigate("/pending");
    //         return;
    //     }

    //     if (data.status === "REVOKED") {
    //         navigate("/revoked");
    //         return;
    //     }

    //     if (data.roles.length === 1) {
    //         createSession({
    //             token: data.token,
    //             user: data.user,
    //             activeRole: data.roles[0],
    //         });

    //         navigate("/dashboard");
    //         return;
    //     }

    //     sessionStorage.setItem(
    //         "login_response",
    //         JSON.stringify(data)
    //     );

    //     navigate("/select-role");
    // };

    return(

        <div className="auth-container">

            <div className="auth-card">

                <h2>Login</h2>

                <form
                    onSubmit={handleSubmit}
                    className="auth-form"
                >

                    <input
                        placeholder="Email"
                        type="email"
                        value={email}
                        onChange={(e)=>setEmail(e.target.value)}
                    />

                    <input
                        placeholder="Password"
                        type="password"
                        value={password}
                        onChange={(e)=>setPassword(e.target.value)}
                    />

                    <button>

                        Login

                    </button>

                </form>

                {error && <p>{error}</p>}

                <div className="auth-link">

                    <Link to="/signup">

                        Create Account

                    </Link>

                </div>

            </div>

        </div>

    );

}