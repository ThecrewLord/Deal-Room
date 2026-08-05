import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { signup } from "../../auth/authService";

import "../../styles/auth.css";

export default function Signup(){

    const navigate=useNavigate();

    const [form,setForm]=useState({
        firstName:"",
        lastName:"",
        email:"",
        password:""
    });

    const [error,setError]=useState("");

    const handleChange=(e)=>{

        setForm({
            ...form,
            [e.target.name]:e.target.value
        });

    };

    const submit=async(e)=>{

        e.preventDefault();

        try{

            await signup(form);

            navigate("/pending");

        }catch(err){

            setError(
                err.response?.data?.message ||
                "Unable to register."
            );

        }

    };

    return(

        <div className="auth-container">

            <div className="auth-card">

                <h2>Create Account</h2>

                <form
                    onSubmit={submit}
                    className="auth-form"
                >

                    <input
                        name="firstName"
                        placeholder="First Name"
                        onChange={handleChange}
                    />

                    <input
                        name="lastName"
                        placeholder="Last Name"
                        onChange={handleChange}
                    />

                    <input
                        name="email"
                        type="email"
                        placeholder="Email"
                        onChange={handleChange}
                    />

                    <input
                        name="password"
                        type="password"
                        placeholder="Password"
                        onChange={handleChange}
                    />

                    <button>

                        Register

                    </button>

                </form>

                {error && <p>{error}</p>}

                <div className="auth-link">

                    <Link to="/login">

                        Back to Login

                    </Link>

                </div>

            </div>

        </div>

    );

}