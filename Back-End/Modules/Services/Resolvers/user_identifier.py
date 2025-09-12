from Modules.Models.postgressSQL import db, User, Message, Config, AlfredFile, AgentStatus

def resolve_user_identifier(identifier):
    """
    Aceita:
     - None -> retorna None
     - número (string ou int) -> busca por id
     - string com @ -> busca por email
     - string sem @ -> tenta converter para int, senão retorna None
    Retorna User instance ou None.
    """
    if not identifier:
        return None

    # Se já for int
    try:
        uid = int(identifier)
        return User.query.get(uid)
    except (ValueError, TypeError):
        pass

    # se parecer email
    if isinstance(identifier, str) and "@" in identifier:
        return User.query.filter_by(email=identifier).first()

    # fallback: tenta buscar por email ignorando espaços
    return User.query.filter_by(email=str(identifier).strip()).first()
