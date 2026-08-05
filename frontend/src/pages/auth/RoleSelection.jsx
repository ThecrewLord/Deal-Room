import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { createSession } from "../../auth/authService";

import "../../styles/auth.css";

export default function RoleSelection(){

    const navigate=useNavigate();

    const loginResponse=JSON.parse(
        sessionStorage.getItem("login_response")
    );

    const [role,setRole]=useState("");

    if(!loginResponse){

        navigate("/login");

        return null;

    }

    const submit=()=>{

        if(!role)return;

        createSession({

            token:loginResponse.token,
            user:loginResponse.user,
            activeRole:role

        });

        sessionStorage.removeItem("login_response");

        navigate("/dashboard");

    };

    return(

        <div className="auth-container">

            <div className="auth-card">

                <h2>Select Role</h2>

                <div className="auth-form">

                    {loginResponse.roles.map(r=>(

                        <label key={r}>

                            <input
                                type="radio"
                                name="role"
                                value={r}
                                onChange={()=>setRole(r)}
                            />

                            {" "}
                            {r}

                        </label>

                    ))}

                    <button onClick={submit}>

                        Continue

                    </button>

                </div>

            </div>

        </div>

    );

}