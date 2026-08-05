export const hasRole = (user, role) => {
    if (!user?.roles)
        return false;

    return user.roles.includes(role);
};

export const hasAnyRole = (
    user,
    allowedRoles
) => {
    if (!user?.roles)
        return false;

    return allowedRoles.some((role) =>
        user.roles.includes(role)
    );
};