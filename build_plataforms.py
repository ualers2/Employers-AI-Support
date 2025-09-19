import subprocess, os, shutil, time

os.chdir("Back-End")

def executar_comando(comando):
    subprocess.run(comando, shell=True, check=True)

def build_tag_push(servico, ignore_file, repo_name):
    
    # 1️⃣ Copia o dockerignore específico
    shutil.copy(ignore_file, ".dockerignore")

    # 2️⃣ Build da imagem local
    executar_comando(f"docker-compose build {servico}")

    # 3️⃣ Tag da imagem local para o Docker Hub
    executar_comando(f"docker tag {servico.replace('-build', '')}-server:latest mediacutsstudio/{repo_name}:latest")

    # 4️⃣ Push da imagem para o Docker Hub
    executar_comando(f"docker push mediacutsstudio/{repo_name}:latest")

    # 5️⃣ Remove o dockerignore temporário
    os.remove(".dockerignore")

# Executa para cada serviço
build_tag_push("whatsapp-build", ".dockerignore.whatsapp", "whatsapp-server")
build_tag_push("discord-build", ".dockerignore.discord", "discord-server")
build_tag_push("telegram-build", ".dockerignore.telegram", "telegram-server")
