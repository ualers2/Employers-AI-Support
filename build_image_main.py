import subprocess
import os

os.chdir(os.path.join(os.path.dirname(__file__)))
# Adiciona o caminho do Docker Compose
os.environ["PATH"] += r";C:\Program Files\Docker\Docker\resources\bin"
path = os.path.join(os.path.dirname(__file__))
def executar_comando(comando):
    """Executa um comando sem abrir um novo terminal (funciona dentro do contêiner)."""
    subprocess.run(comando, shell=True)


executar_comando("docker-compose up --build -d api_support_dev frontend-dev")

# executar_comando("docker-compose build alfred")

# executar_comando("docker-compose up -d alfred")

# # (Opcional) parar antes, se já estiver rodando
# subprocess.Popen([
#     "docker", "compose", "--compatibility", "stop", "postgres"
# ], cwd=path).wait()

# # subir somente o serviço  em background
# subprocess.Popen([
#     "docker", "compose", "--compatibility", "up", "-d", "postgres"
# ], cwd=path).wait()