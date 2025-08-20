from telegram import User


def format_user_for_log(user: User) -> str:
    parts = [str(user.id)]
    if user.username:
        parts.append(f"@{user.username}")
    elif user.full_name:
        parts.append(user.full_name)
    else:
        parts.append("—")
    return " ".join(parts)


def format_user_for_admin(user: User) -> str:
    if user.username:
        return f"@{user.username}"
    elif user.full_name:
        return user.full_name
    return f"id:{user.id}"
