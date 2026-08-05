import UserMenu from "./UserMenu";

import "../styles/header.css";

export default function Header() {

    return (

        <header className="app-header">

            <h2>

                Collaborating Opportunities

            </h2>

            <UserMenu />

        </header>

    );

}