
def _get_user_info(message, chat_id, telegram_user=None, category="Discord"):
    """Extrai informações do usuário do objeto."""
    if category == "Discord":
            
        short_chat_id = chat_id[:8] 
        return {
            "id": short_chat_id,
            "name": f"User {message.author}",
            "username": str(message.author),
            "platform": "Discord"
        }
    elif category == "Telegram":
        return {
            "id": str(telegram_user.id),
            "name": telegram_user.full_name or telegram_user.first_name or f"User {telegram_user.id}",
            "username": telegram_user.username,
            "platform": "Telegram"
        }
