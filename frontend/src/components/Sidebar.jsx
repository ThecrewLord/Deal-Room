import { NavLink } from "react-router-dom";

import navigation from "../config/navigation";

import { getActiveRole } from "../auth/authStorage";

import "../styles/sidebar.css";

export default function Sidebar() {

    const role = getActiveRole();

    const menu = navigation[role] || [];

    return (

        <aside className="sidebar">

            <div className="sidebar-title">

                {role}

            </div>

            {menu.map((item) => (

                <NavLink

                    key={item.path}

                    to={item.path}

                    className="sidebar-link"

                >

                    {item.name}

                </NavLink>

            ))}

        </aside>

    );

}