
def _get_user_info(chat_id, message=None, telegram_user=None, pushNamer=None, category="Discord"):
    """Extrai informações do usuário do objeto."""
    short_chat_id = chat_id[:8] 

    if category == "Discord":
            
        return {
            "id": short_chat_id,
            "name": f"User {message.author}",
            "username": str(message.author),
            "platform": "Discord"
        }
    elif category == "Telegram":
        return {
            "id": short_chat_id,
            "name": telegram_user.full_name or telegram_user.first_name or f"User {telegram_user.id}",
            "username": telegram_user.username,
            "platform": "Telegram"
        }
    elif category == "WhatsApp":
        pushNamer = f"{pushNamer}"
        
        return {
            "id": short_chat_id,
            "name": f"User {pushNamer}",
            "username": str(pushNamer),
            "platform": "WhatsApp"
        }
