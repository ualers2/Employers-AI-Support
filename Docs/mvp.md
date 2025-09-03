# Inicio do mvp versao 1 (07:00 - 27/06/2025)

---
# Problemas resolvidos
- Suporte 24/7 
- Pagar salario de 600 a 1200 R$ a um humano dedicado a dar suporte
- Chat bots para gerenciamento de tickets
- **Redução do Tempo de Resposta:** O suporte humano, mesmo que 24/7, pode ter gargalos no tempo de resposta, especialmente em picos de demanda. Seu agente resolve isso ao fornecer **respostas instantâneas e consistentes**, eliminando filas e esperas.
* **Padronização e Qualidade do Atendimento:** A resposta humana pode variar de acordo com o operador. Um agente de IA garante **respostas padronizadas e de alta qualidade**, baseadas em sua base de conhecimento, eliminando erros ou inconsistências.
- **Disponibilidade em Múltiplos Canais:** Mencionar que o suporte está disponível em Telegram, Discord e WhatsApp já é uma característica, mas como problema resolvido, isso significa **unificar o atendimento em diversas plataformas**, onde antes poderia haver a necessidade de equipes separadas ou ferramentas distintas.
- **Escalabilidade Ilimitada:** Um agente de IA pode lidar com **um número virtualmente ilimitado de usuários simultaneamente** sem aumento de custo marginal, algo impossível com equipes humanas. Isso resolve o problema de escalar o suporte sem aumentar desproporcionalmente as despesas.
- **Otimização de Recursos Humanos:** Em vez de substituir totalmente os humanos, o agente **libera a equipe de suporte para tarefas mais complexas e estratégicas**, que realmente exigem inteligência emocional e resolução de problemas não repetitivos. Isso resolve o problema de sobrecarga e subutilização do potencial humano.
- **Armazenamento e Recuperação de Conhecimento:** O agente centraliza e utiliza uma **base de conhecimento viva e atualizável**, resolvendo o problema da dispersão de informações e da dificuldade de acesso a dados relevantes para o suporte.



# Caracteristicas do mvp
- Suporte 24/7 em telegram, discord e whatsapp para saas
- Projeto real e eficiente para portifolio e curriculo
- Agent para a biblioteca softwareai
- Controle e visualizacao de metricas geradas pelo agente 
- Upload de arquivos para a base de conhecimento de forma facilitada pela ui
- Controle de estados (iniciar resetar deletar) do agente de forma facilitada pela ui
Suas características atuais são sólidas para um MVP. Para torná-las ainda mais atrativas e completas, sugiro as seguintes adições, que enfatizam a robustez e a usabilidade do seu sistema:
- **Dashboards de Desempenho e Interações:** Além do controle e visualização de métricas, especificar que o MVP incluirá **dashboards visuais** para facilitar a interpretação dos dados. Isso pode incluir:
    * Número de interações por período e por plataforma.
    * Tipos de perguntas mais frequentes.
    * Taxa de resolução automática versus interações que podem necessitar de revisão.
- **Gerenciamento Centralizado de Configurações:** A capacidade de o agente ser inicializado com chaves do DB já é um bom começo. Adicione que o MVP terá uma **interface para gerenciamento dessas configurações** (tokens, IDs de canal, nome do Alfred, instruções gerais) diretamente do painel web, sem necessidade de manipulação de arquivos ou acesso direto ao banco de dados.
- **Interface Intuitiva para Upload de Conhecimento:** Detalhe que o "upload de arquivos para a base de conhecimento de forma facilitada pela UI" implica em um **sistema de upload "drag-and-drop" ou um seletor de arquivos simples**, com feedback visual sobre o status do upload e processamento.
- **Sistema de Log e Auditoria Acessível:** Além dos logs internos, o MVP pode oferecer uma **visualização simplificada dos logs do agente** na UI, permitindo que os administradores monitorem o funcionamento e identifiquem problemas rapidamente.
- **Persistência de Interações:** Deixe claro que as conversas (interações) com o agente são **registradas e armazenadas de forma persistente** no Firebase, permitindo auditoria e análise posterior.
- **Comunicação Bidirecional com Firebase:** Reforce que o sistema não apenas lê configurações do Firebase, mas também **grava status e logs de operações** de contêineres e agentes, fornecendo um ponto central de monitoramento.
























## Requisitos de Backend/Endpoints para o Agente de Suporte Media Cuts Studio [x]

### 1. Endpoint Geral de Configuração

Este endpoint será o principal para buscar e salvar todas as configurações exibidas no `ConfigPanel`.

  * **Endpoint:** `/api/config`
  * **Métodos:** `GET`, `POST`

#### 1.1. Buscar Configurações (GET)

  * **Objetivo:** Obter todas as configurações atuais do bot e do agente Alfred.
  * **Método:** `GET`
  * **URL:** `/api/config`
  * **Parâmetros de Requisição:** Nenhum.
  * **Resposta (JSON):**
    ```json
    {
        "botToken": "string",          // Ocultado ou tratado com segurança no frontend
        "channelId": "string",
        "autoModeration": boolean,
        "aiModeration": boolean,
        "aiModerationModel": "string", // Ex: "ominilatest", "gpt-4", "claude-3"
        "deleteSpam": boolean,
        "banThreshold": number,        // Inteiro, min 1, max 10
        "alfredName": "string",
        "alfredModel": "string",       // Ex: "gpt-4.1-nano", "claude-3-opus"
        "alfredInstructions": "string", // Conteúdo markdown das instruções
        "toolsEnabled": boolean
    }
    ```
  * **Códigos de Status:**
      * `200 OK`: Configurações retornadas com sucesso.
      * `500 Internal Server Error`: Erro no servidor ao buscar as configurações.

#### 1.2. Salvar Configurações (POST)

  * **Objetivo:** Persistir as configurações atualizadas do bot e do agente Alfred.
  * **Método:** `POST`
  * **URL:** `/api/config`
  * **Corpo da Requisição (JSON):**
    ```json
    {
        "botToken": "string",          // Opcional, se o token só for enviado na primeira configuração ou for gerenciado de outra forma segura
        "channelId": "string",
        "autoModeration": boolean,
        "aiModeration": boolean,
        "aiModerationModel": "string",
        "deleteSpam": boolean,
        "banThreshold": number,
        "alfredName": "string",
        "alfredModel": "string",
        "alfredInstructions": "string",
        "toolsEnabled": boolean
    }
    ```
      * **Observações:** O `botToken` deve ser tratado com extrema segurança. Idealmente, ele só seria enviado uma vez e armazenado de forma criptografada no backend, ou via variáveis de ambiente. Para atualizações futuras, talvez não precise ser enviado novamente, a menos que seja especificamente alterado.
  * **Resposta (JSON):**
    ```json
    {
        "message": "Configurações atualizadas com sucesso."
    }
    ```
  * **Códigos de Status:**
      * `200 OK`: Configurações salvas com sucesso.
      * `400 Bad Request`: Dados de entrada inválidos (ex: `banThreshold` fora do range).
      * `500 Internal Server Error`: Erro no servidor ao salvar as configurações.

## Requisitos de Backend/Endpoints para o Gerenciador de Arquivos do Alfred [x]

### 1. Upload de Arquivos do Alfred

Este endpoint será responsável por receber novos arquivos ou atualizações de arquivos existentes para o agente Alfred.

  * **Endpoint:** `/api/alfred-files/upload`
  * **Método:** `POST`
  * **Objetivo:** Permite que o usuário envie novos arquivos (como `.md` ou `.txt`) que serão utilizados como base de conhecimento ou instruções para o agente Alfred. Inclui campos para metadados opcionais como `channelId` e `caption`.
  * **Corpo da Requisição (`multipart/form-data`):**
      * `file`: O arquivo real a ser carregado (ex: `manifesto_da_marca.md`).
      * `channelId` (opcional): String, ID do canal associado ao arquivo, se aplicável.
      * `caption` (opcional): String, uma descrição ou anotação sobre o arquivo/upload.
  * **Resposta (JSON):**
    ```json
    {
        "message": "Arquivo carregado com sucesso.",
        "fileId": "string", // ID único do arquivo no backend
        "fileName": "string",
        "size": "string",   // Ex: "15.2 KB"
        "lastModified": "string" // Data e hora da última modificação
    }
    ```
  * **Códigos de Status:**
      * `200 OK`: Arquivo carregado/atualizado com sucesso.
      * `400 Bad Request`: Arquivo ausente, formato inválido ou outros problemas de validação.
      * `500 Internal Server Error`: Erro no servidor ao processar o upload.

-----

### 2. Listagem de Arquivos do Alfred

Este endpoint é fundamental para popular a seção "Arquivos de Configuração do Alfred" do seu frontend.

  * **Endpoint:** `/api/alfred-files`
  * **Método:** `GET`
  * **Objetivo:** Retorna uma lista de todos os arquivos de configuração que o agente Alfred tem acesso, incluindo seus metadados.
  * **Parâmetros de Requisição:** Nenhum.
  * **Resposta (JSON):**
    ```json
    [
        {
            "id": "string", // ID único do arquivo
            "name": "string",
            "type": "string", // Ex: "document"
            "size": "string",
            "lastModified": "string", // Formato ISO 8601 ou similar
            "url": "string" // URL para download ou visualização direta, se aplicável
        }
        // ... outros arquivos
    ]
    ```
  * **Códigos de Status:**
      * `200 OK`: Lista de arquivos retornada com sucesso.
      * `500 Internal Server Error`: Erro no servidor ao buscar a lista.

-----

### 3. Edição/Atualização de Conteúdo de Arquivo do Alfred

Este endpoint permite que o conteúdo de um arquivo existente seja modificado diretamente via frontend.

  * **Endpoint:** `/api/alfred-files/{fileId}/content`
  * **Método:** `PUT` ou `PATCH`
  * **Objetivo:** Atualizar o conteúdo de um arquivo específico do Alfred. Isso é usado quando o usuário clica em "Editar" e depois em "Salvar".
  * **Parâmetros de URL:**
      * `fileId`: ID único do arquivo a ser atualizado.
  * **Corpo da Requisição (JSON):**
    ```json
    {
        "content": "string" // O novo conteúdo completo do arquivo
    }
    ```
  * **Resposta (JSON):**
    ```json
    {
        "message": "Conteúdo do arquivo atualizado com sucesso.",
        "fileId": "string",
        "lastModified": "string" // Nova data/hora de modificação
    }
    ```
  * **Códigos de Status:**
      * `200 OK`: Conteúdo do arquivo atualizado com sucesso.
      * `400 Bad Request`: Conteúdo inválido na requisição.
      * `404 Not Found`: Arquivo com o `fileId` especificado não encontrado.
      * `500 Internal Server Error`: Erro no servidor ao atualizar o arquivo.

-----

### 4. Visualização de Conteúdo de Arquivo do Alfred

Este endpoint seria usado para buscar o conteúdo de um arquivo para exibição no frontend (quando o usuário clica em "Visualizar").

  * **Endpoint:** `/api/alfred-files/{fileId}/content`
  * **Método:** `GET`
  * **Objetivo:** Obter o conteúdo textual de um arquivo específico.
  * **Parâmetros de URL:**
      * `fileId`: ID único do arquivo.
  * **Resposta (`text/plain` ou JSON):**
      * **Opção 1 (Simples):** Retorna o conteúdo como texto simples.
        ```
        Conteúdo do manifesto da marca...
        ```
      * **Opção 2 (Com metadados):** Retorna o conteúdo e metadados em JSON.
        ```json
        {
            "id": "string",
            "name": "string",
            "content": "string",
            "lastModified": "string"
        }
        ```
  * **Códigos de Status:**
      * `200 OK`: Conteúdo retornado com sucesso.
      * `404 Not Found`: Arquivo não encontrado.
      * `500 Internal Server Error`: Erro no servidor.

-----

### 5. Download de Arquivo do Alfred

Este endpoint permite que os usuários baixem os arquivos diretamente do backend.

  * **Endpoint:** `/api/alfred-files/{fileId}/download`
  * **Método:** `GET`
  * **Objetivo:** Iniciar o download de um arquivo específico.
  * **Parâmetros de URL:**
      * `fileId`: ID único do arquivo.
  * **Resposta (`application/octet-stream` ou tipo MIME do arquivo):**
      * O corpo da resposta será o próprio conteúdo binário do arquivo, com headers HTTP apropriados (`Content-Disposition: attachment; filename="nome_do_arquivo.md"`).
  * **Códigos de Status:**
      * `200 OK`: Arquivo entregue para download.
      * `404 Not Found`: Arquivo não encontrado.
      * `500 Internal Server Error`: Erro no servidor.

-----

### 6. Exclusão de Arquivo do Alfred (Considerar adicionar)

Embora não esteja explicitamente no seu código React atual, a funcionalidade de "lixeira" (`Trash2` icon) sugere a necessidade de um endpoint para remover arquivos.

  * **Endpoint:** `/api/alfred-files/{fileId}`
  * **Método:** `DELETE`
  * **Objetivo:** Remover um arquivo de configuração do Alfred.
  * **Parâmetros de URL:**
      * `fileId`: ID único do arquivo a ser excluído.
  * **Resposta (JSON):**
    ```json
    {
        "message": "Arquivo excluído com sucesso."
    }
    ```
  * **Códigos de Status:**
      * `200 OK`: Arquivo excluído com sucesso.
      * `404 Not Found`: Arquivo não encontrado.
      * `500 Internal Server Error`: Erro no servidor.

-----

### Considerações Importantes para o Backend:

  * **Autenticação e Autorização:** Assim como nas configurações do bot, todos esses endpoints de gerenciamento de arquivos devem ser **protegidos**. Apenas usuários com permissão devem poder carregar, editar, baixar ou excluir arquivos.
  * **Armazenamento de Arquivos:** Os arquivos devem ser armazenados de forma persistente. Isso pode ser feito em:
      * **Sistema de arquivos local:** Para ambientes controlados e de menor escala.
      * **Cloud Storage:** Como Google Cloud Storage, AWS S3, Azure Blob Storage, que são escaláveis e robustos.
      * **Banco de dados:** Se os arquivos forem pequenos e predominantemente textuais (como `.md`), eles podem ser armazenados diretamente em um campo `TEXT` ou `BLOB` em um banco de dados.
  * **Integração com o Agente Alfred:** É crucial que, após o upload ou edição de um arquivo, o backend notifique o agente Alfred (ou o recarregue, dependendo da arquitetura) para que ele possa **utilizar o conteúdo atualizado** imediatamente. Isso pode envolver um mecanismo de "hot-reload" ou cache.
  * **Segurança de Conteúdo:** Se os arquivos puderem conter informações sensíveis ou código, implemente validações para evitar injeção de código ou conteúdo malicioso.
  * **Controle de Versão (Opcional):** Para arquivos críticos como instruções do Alfred, um sistema de controle de versão (mesmo que simples no banco de dados) pode ser benéfico para reverter a versões anteriores.

## Requisitos de Backend/Endpoints para o Painel de Mensagens [x]

### 1. Listar Mensagens Recentes

Este é o endpoint principal para alimentar o `MessagePanel` com dados.

  * **Endpoint:** `/api/messages/recent`
  * **Método:** `GET`
  * **Objetivo:** Obter uma lista das mensagens mais recentes trocadas entre os usuários e o agente Alfred. Isso incluirá tanto as mensagens dos usuários quanto as respostas do Alfred, além do status de cada interação.
  * **Parâmetros de Requisição (Query Parameters - Opcionais para filtragem/paginação):**
      * `limit`: **Número** (inteiro). Opcional. O número máximo de mensagens a serem retornadas (ex: `?limit=10`). Padrão pode ser 5 ou 10.
      * `status`: **String**. Opcional. Filtra mensagens por status (ex: `?status=pending`). Valores possíveis: `pending`, `responded`, `resolved`.
      * `after_id`: **String**. Opcional. Usado para paginação ou buscar novas mensagens após um ID específico, para evitar duplicatas e otimizar o carregamento.
  * **Resposta (JSON):**
    ```json
    [
        {
            "id": "string",         // ID único da mensagem/interação
            "user": "string",       // Nome de exibição do usuário
            "userId": "string",     // ID ou username da plataforma (Telegram/Discord) do usuário
            "message": "string",    // O texto da mensagem (do usuário ou do Alfred)
            "timestamp": "string",  // Data e hora da mensagem (formato ISO 8601, ex: "YYYY-MM-DDTHH:MM:SSZ")
            "status": "string"      // "pending", "responded", "resolved"
        }
        // ... outras mensagens
    ]
    ```
      * **Considerações sobre o campo `message`:** Para simplificar, estamos considerando `message` como a "última interação" na conversa. Se você precisar de um histórico completo de cada conversa, um endpoint de detalhes da conversa (veja abaixo) seria mais adequado.
      * **Considerações sobre `status`:** O status deve ser determinado pela lógica de backend do seu agente Alfred (se um ticket foi aberto, se foi respondido, se foi marcado como resolvido).
  * **Códigos de Status:**
      * `200 OK`: Lista de mensagens retornada com sucesso.
      * `400 Bad Request`: Parâmetros de query inválidos.
      * `500 Internal Server Error`: Erro no servidor ao buscar as mensagens.

-----

### Considerações Importantes para o Backend:

  * **Fonte dos Dados:** O backend precisará acessar o **histórico de conversas** do seu agente Alfred. Isso provavelmente significa que as interações do Telegram e Discord estão sendo salvas em um banco de dados (ex: Firebase Firestore, PostgreSQL, MongoDB).
  * **Modelagem de Dados:** A estrutura do seu banco de dados para mensagens deve ser capaz de armazenar:
      * **`interaction_id`**: Um ID para agrupar todas as mensagens de uma única conversa/ticket.
      * **`message_id`**: ID de cada mensagem individual dentro de uma interação.
      * **`user_id`**: ID do usuário no Telegram/Discord.
      * **`timestamp`**: Quando a mensagem foi enviada/recebida.
      * **`sender_type`**: Se foi o `user` ou o `Alfred`.
      * **`text_content`**: O conteúdo da mensagem.
      * **`status`**: O status atual da interação (baseado na lógica do Alfred, como `pending` se o Alfred ainda precisa responder ou se um ticket está aberto).
  * **Autenticação e Autorização:** Assim como os outros painéis, este endpoint deve ser protegido para garantir que apenas usuários autorizados possam visualizar o histórico de mensagens do suporte.
  * **Paginação e Filtragem:** Implementar `limit` e `after_id` é crucial para desempenho, especialmente se houver um grande volume de mensagens.
  * **Atualizações em Tempo Real (Opcional):** Para uma experiência de usuário mais rica, considere usar WebSockets ou Server-Sent Events (SSE) para enviar novas mensagens para o frontend em tempo real, em vez de depender apenas de polling constante. Isso criaria uma dashboard de monitoramento mais dinâmica.

-----

### 2. Endpoint Opcional: Detalhes de uma Conversa/Ticket

Se você quiser que os usuários possam clicar em uma mensagem no `MessagePanel` e ver o histórico completo daquela interação, você precisaria de um endpoint adicional.

  * **Endpoint:** `/api/messages/{interactionId}`
  * **Método:** `GET`
  * **Objetivo:** Retornar o histórico completo de mensagens para uma interação ou ticket específico.
  * **Parâmetros de URL:**
      * `interactionId`: O ID único da interação/conversa.
  * **Resposta (JSON):**
    ```json
    {
        "interactionId": "string",
        "user": {
            "name": "string",
            "id": "string",
            "platform": "string" // Ex: "Telegram"
        },
        "status": "string", // "pending", "responded", "resolved"
        "messages": [
            {
                "messageId": "string",
                "sender": "user" | "alfred",
                "timestamp": "string",
                "content": "string"
            }
            // ... todas as mensagens da conversa
        ]
    }
    ```

## Requisitos de Backend/Endpoints para o Gerenciamento de Usuários [x]

### 1. Listar Usuários

Este endpoint será o responsável por fornecer a lista de usuários exibida no painel.

  * **Endpoint:** `/api/users`
  * **Método:** `GET`
  * **Objetivo:** Retornar uma lista de usuários que interagiram com o bot, incluindo seus detalhes e status de banimento.
  * **Parâmetros de Requisição (Query Parameters - Opcionais para filtragem/paginação):**
      * `searchTerm`: **String**. Opcional. Termo de busca para filtrar usuários por nome, username ou ID (ex: `?searchTerm=joao`).
      * `status`: **String**. Opcional. Filtra usuários por status (ex: `?status=banned`). Valores possíveis: `active`, `banned`.
      * `limit`: **Número** (inteiro). Opcional. O número máximo de usuários a serem retornados.
      * `offset`: **Número** (inteiro). Opcional. Usado para paginação, indicando o número de usuários a pular.
  * **Resposta (JSON):**
    ```json
    [
        {
            "id": "string",         // ID interno do usuário no seu sistema
            "name": "string",       // Nome completo do usuário
            "username": "string",   // Username do Telegram/plataforma
            "userId": "string",     // ID exclusivo do usuário na plataforma (Telegram User ID)
            "status": "string",     // "active" ou "banned"
            "lastSeen": "string",   // Data e hora do último acesso/interação (formato ISO 8601)
            "messageCount": number  // Número de mensagens/interações com o bot
        }
        // ... outros usuários
    ]
    ```
  * **Códigos de Status:**
      * `200 OK`: Lista de usuários retornada com sucesso.
      * `400 Bad Request`: Parâmetros de query inválidos.
      * `500 Internal Server Error`: Erro no servidor ao buscar os usuários.

-----

### 2. Banir Usuário

Este endpoint será usado para aplicar um banimento a um usuário específico.

  * **Endpoint:** `/api/users/{userId}/ban`
  * **Método:** `POST`
  * **Objetivo:** Marcar um usuário como banido no seu sistema e, idealmente, instruir o bot a bani-lo na plataforma (Telegram, Discord).
  * **Parâmetros de URL:**
      * `userId`: **String**. O ID exclusivo do usuário na plataforma (Telegram User ID) a ser banido.
  * **Corpo da Requisição (JSON - Opcional, para detalhes do banimento):**
    ```json
    {
        "reason": "string", // Opcional: Motivo do banimento
        "duration": "string" // Opcional: Duração do banimento (ex: "permanent", "24h", "7d")
    }
    ```
  * **Resposta (JSON):**
    ```json
    {
        "message": "Usuário banido com sucesso.",
        "userId": "string",
        "status": "banned"
    }
    ```
  * **Códigos de Status:**
      * `200 OK`: Usuário banido com sucesso.
      * `400 Bad Request`: ID de usuário inválido ou já banido.
      * `404 Not Found`: Usuário não encontrado.
      * `500 Internal Server Error`: Erro no servidor ou na comunicação com a API da plataforma (Telegram/Discord).

-----

### 3. Desbanir Usuário

Este endpoint será usado para remover o banimento de um usuário.

  * **Endpoint:** `/api/users/{userId}/unban`
  * **Método:** `POST`
  * **Objetivo:** Remover a marcação de banimento de um usuário no seu sistema e instruir o bot a desbani-lo na plataforma.
  * **Parâmetros de URL:**
      * `userId`: **String**. O ID exclusivo do usuário na plataforma a ser desbanido.
  * **Corpo da Requisição:** Nenhum.
  * **Resposta (JSON):**
    ```json
    {
        "message": "Usuário desbanido com sucesso.",
        "userId": "string",
        "status": "active"
    }
    ```
  * **Códigos de Status:**
      * `200 OK`: Usuário desbanido com sucesso.
      * `400 Bad Request`: ID de usuário inválido ou não estava banido.
      * `404 Not Found`: Usuário não encontrado.
      * `500 Internal Server Error`: Erro no servidor ou na comunicação com a API da plataforma.

-----

### Considerações Importantes para o Backend:

  * **Fonte de Dados de Usuários:** Você precisará de um banco de dados para armazenar as informações dos usuários que interagem com o bot (ID da plataforma, nome, username, status, contagem de mensagens, etc.). Este banco será a fonte de verdade para a lista de usuários e seus status de banimento.
  * **Integração com a Plataforma do Bot:** Ao banir/desbanir um usuário, o backend precisará usar a API do Telegram (ou Discord, dependendo da plataforma) para executar a ação real de banimento/desbanimento no canal/grupo. Isso deve ser feito de forma assíncrona para não atrasar a resposta da API ao frontend. O método `context.bot.ban_chat_member` e `context.bot.unban_chat_member` que você já tem no código do Telegram seriam invocados pelo backend.
  * **Autenticação e Autorização:** Assim como os outros painéis, todos esses endpoints de gerenciamento de usuários devem ser **protegidos**. Apenas administradores ou usuários autorizados devem ter permissão para banir/desbanir.
  * **Logs e Auditoria:** Registre todas as ações de banimento e desbanimento, incluindo quem executou a ação e o motivo, para fins de auditoria e conformidade.
  * **Sincronização:** Se as ações de banimento também puderem ocorrer por meio de moderação automática (definida no `ConfigPanel`), o sistema deve garantir que o status do usuário no banco de dados seja atualizado consistentemente e refletido no `UserManagement` frontend.

## Requisitos de Backend/Endpoints para o Monitor de Atividades [x]

### 1. Obter Métricas em Tempo Real (Real-time Stats)

Este endpoint agregará os principais KPIs para exibir nos cards de "Real-time Stats".

  * **Endpoint:** `/api/metrics/realtime`
  * **Método:** `GET`
  * **Objetivo:** Fornecer dados agregados e em tempo real sobre a atividade do bot, como mensagens por hora, usuários online e tempo de resposta médio.
  * **Parâmetros de Requisição:** Nenhum. (Poderíamos adicionar `interval` para especificar a janela de tempo, mas para "tempo real" um padrão fixo, como a última hora, é comum).
  * **Resposta (JSON):**
    ```json
    {
        "messagesPerHour": number,    // Número total de mensagens processadas na última hora (ou período definido)
        "onlineUsers": number,        // Número de usuários atualmente ativos/online
        "averageResponseTime": number // Tempo de resposta médio do bot em segundos (ex: 1.2)
    }
    ```
      * **Observações:** "Usuários Online" pode ser complexo. Pode significar usuários que interagiram nos últimos X minutos, ou que estão em uma conversa ativa. A definição deve ser clara no backend.
  * **Códigos de Status:**
      * `200 OK`: Métricas retornadas com sucesso.
      * `500 Internal Server Error`: Erro no servidor ao calcular ou buscar as métricas.

-----

### 2. Listar Log de Atividades (Activity Log)

Este endpoint será o responsável por fornecer os dados para a seção de "Log de Atividades".

  * **Endpoint:** `/api/activities`
  * **Método:** `GET`
  * **Objetivo:** Retornar uma lista paginada e filtrável de todas as atividades registradas pelo sistema do bot (mensagens, banimentos, uploads, respostas, erros, etc.).
  * **Parâmetros de Requisição (Query Parameters):**
      * `limit`: **Número** (inteiro). Opcional. Número máximo de atividades a serem retornadas (ex: `?limit=20`).
      * `offset`: **Número** (inteiro). Opcional. Usado para paginação, indica o número de atividades a pular (ex: `?offset=20`).
      * `type`: **String**. Opcional. Filtra por tipo de atividade (ex: `?type=error`). Valores possíveis: `message`, `ban`, `file`, `response`, `error`, etc.
      * `status`: **String**. Opcional. Filtra por status da atividade (ex: `?status=error`). Valores possíveis: `success`, `warning`, `info`, `error`.
      * `startDate`: **String** (ISO 8601). Opcional. Data de início para o filtro de período.
      * `endDate`: **String** (ISO 8601). Opcional. Data de fim para o filtro de período.
      * `searchTerm`: **String**. Opcional. Termo para buscar nos campos `user`, `action` ou `details`.
  * **Resposta (JSON):**
    ```json
    {
        "total": number, // Total de atividades correspondentes aos filtros (para paginação)
        "activities": [
            {
                "id": "string",          // ID único da atividade
                "type": "string",        // Tipo da atividade (e.g., "message", "ban", "file", "response", "error")
                "user": "string",        // Usuário ou entidade que realizou/envolveu-se na ação (e.g., "João Silva", "Sistema", "Alfred (Bot)", "Administrador")
                "action": "string",      // Descrição breve da ação (e.g., "Enviou mensagem", "Usuário banido")
                "details": "string",     // Detalhes adicionais sobre a atividade
                "timestamp": "string",   // Data e hora exata da ocorrência (ISO 8601)
                "status": "string"       // "success", "warning", "info", "error"
            }
            // ... outras atividades
        ]
    }
    ```
  * **Códigos de Status:**
      * `200 OK`: Log de atividades retornado com sucesso.
      * `400 Bad Request`: Parâmetros de query inválidos.
      * `500 Internal Server Error`: Erro no servidor ao buscar o log.

-----

### 3. Limpar Log de Atividades (Clear Log)

Se o botão "Limpar Log" tiver a intenção de realmente remover entradas do banco de dados, você precisará de um endpoint. Se for apenas para limpar a visualização no frontend, nenhum endpoint é necessário.

  * **Endpoint:** `/api/activities`
  * **Método:** `DELETE`
  * **Objetivo:** Excluir todas ou um subconjunto de atividades do log. (Geralmente, não se apaga logs de produção, mas se arquiva).
  * **Parâmetros de Requisição (Query Parameters - para filtragem de exclusão):**
      * `beforeDate`: **String** (ISO 8601). Opcional. Excluir atividades anteriores a esta data.
      * `status`: **String**. Opcional. Excluir atividades com um status específico (ex: `?status=success`).
  * **Resposta (JSON):**
    ```json
    {
        "message": "Log de atividades limpo com sucesso.",
        "deletedCount": number // Número de registros excluídos
    }
    ```
  * **Códigos de Status:**
      * `200 OK`: Log limpo com sucesso.
      * `400 Bad Request`: Parâmetros de query inválidos.
      * `403 Forbidden`: Usuário não autorizado a limpar o log.
      * `500 Internal Server Error`: Erro no servidor.

-----

### Considerações Importantes para o Backend:

  * **Fonte de Dados de Atividades:** Todas as ações do bot (mensagens recebidas/enviadas, banimentos, uploads, erros internos) devem ser registradas em um sistema de logs persistente. Isso pode ser um banco de dados (ideal para consultas e filtros) ou um serviço de logging dedicado (como ELK Stack, Splunk, Datadog).
  * **Coleta de Métricas:** As métricas em tempo real (`messagesPerHour`, `onlineUsers`, `averageResponseTime`) precisariam ser calculadas dinamicamente a partir dos dados de log ou de contadores dedicados no backend. Isso pode envolver:
      * Consultas otimizadas no banco de dados.
      * Caches de dados para acesso rápido.
      * Serviços de mensageria (como Kafka ou RabbitMQ) para processamento de eventos assíncronos e agregação.
  * **Autenticação e Autorização:** Assim como os outros painéis, todos esses endpoints devem ser protegidos. O acesso ao monitor de atividades e, especialmente, a capacidade de limpar logs, deve ser restrito a administradores.
  * **Escalabilidade do Log:** Se o seu bot tiver muitos usuários ou alta atividade, o volume de logs pode ser enorme. Garanta que a sua solução de armazenamento de logs e os endpoints sejam escaláveis para lidar com isso.
  * **Atualizações em Tempo Real (Opcional, mas Altamente Recomendado):** Para um "monitoramento em tempo real", considere o uso de **WebSockets** ou **Server-Sent Events (SSE)**. Isso permitiria que o backend enviasse novas atividades e atualizações de métricas diretamente para o frontend sem a necessidade de o frontend ficar "perguntando" (polling) constantemente, tornando a dashboard mais responsiva e eficiente.

## Requisitos de Backend/Endpoints para o Painel de Controle Principal (`Index`) [x]

O componente `Index` precisa de endpoints para:

1.  **Obter as Estatísticas Gerais (Stats Cards):** "Total de Mensagens", "Usuários Ativos", "Respostas do Alfred" e "Arquivos Gerenciados".
2.  **Testar o Status de Conexão do Alfred:** Verificar se o bot está online e funcionando.

### 1. Obter Estatísticas do Dashboard

Este endpoint fornecerá os dados para os cartões de estatísticas no topo da dashboard.

  * **Endpoint:** `/api/dashboard/stats`
  * **Método:** `GET`
  * **Objetivo:** Retornar métricas agregadas e de alto nível que representam a saúde e a atividade geral do agente Alfred.
  * **Parâmetros de Requisição:** Nenhum. (Poderíamos adicionar `period` para filtrar por "desde ontem", mas para simplificar, o backend pode calcular com base em um período padrão ou fornecer dados de sempre).
  * **Resposta (JSON):**
    ```json
    {
        "totalMessages": number,       // Total de mensagens processadas pelo bot
        "activeUsers": number,         // Número de usuários atualmente ativos (definição de "ativo" a ser acordada: ex: interagiram nas últimas 24h)
        "alfredResponses": number,     // Total de respostas geradas pelo Alfred
        "filesManaged": number,        // Total de arquivos de configuração gerenciados
        "totalMessagesChangePercentage": number, // Ex: 12 (para "+12% desde ontem")
        "activeUsersChangePercentage": number,   // Ex: 5 (para "+5% desde ontem")
        "alfredResponsesChangePercentage": number // Ex: 18 (para "+18% desde ontem")
    }
    ```
      * **Observação sobre as porcentagens:** O backend precisaria calcular essas variações comparando os dados atuais com os do dia anterior, por exemplo.
  * **Códigos de Status:**
      * `200 OK`: Estatísticas retornadas com sucesso.
      * `500 Internal Server Error`: Erro no servidor ao calcular as estatísticas.

-----

### 2. Testar Status de Conexão do Alfred

Este endpoint será usado pelo botão "Testar Alfred" para verificar se o bot está respondendo.

  * **Endpoint:** `/api/alfred/status`
  * **Método:** `GET`
  * **Objetivo:** Verificar a conectividade e o status operacional do agente Alfred.
  * **Parâmetros de Requisição:** Nenhum.
  * **Resposta (JSON):**
    ```json
    {
        "status": "online" | "offline" | "degraded", // Status geral do bot
        "message": "string",                          // Mensagem descritiva (ex: "Agente conectado e funcionando.")
        "details": {                                 // Opcional: Detalhes adicionais de saúde
            "telegramApiConnected": boolean,
            "databaseConnected": boolean,
            "lastHeartbeat": "string" // Timestamp da última vez que o bot se reportou
        }
    }
    ```
      * **Implementação:** O backend pode:
          * Fazer um *ping* interno para o serviço do bot.
          * Verificar o status de uma mensagem de *heartbeat* enviada periodicamente pelo bot para o backend.
          * Verificar a conectividade com as APIs externas que o bot utiliza (Telegram, OpenAI, etc.).
  * **Códigos de Status:**
      * `200 OK`: Alfred está online e funcionando.
      * `503 Service Unavailable`: Alfred está offline ou com problemas.
      * `500 Internal Server Error`: Erro no servidor ao tentar verificar o status.

-----

### Considerações Importantes para o Backend:

  * **Agregação de Dados:** As estatísticas da dashboard exigirão que o backend consulte e agregue dados de diferentes fontes:
      * **Mensagens/Respostas:** Do histórico de conversas (o mesmo que alimenta o `MessagePanel`).
      * **Usuários Ativos:** Do sistema de gerenciamento de usuários (o mesmo que alimenta o `UserManagement`).
      * **Arquivos Gerenciados:** Do sistema de arquivos do Alfred (o mesmo que alimenta o `FileManager`).
  * **Monitoramento do Bot:** Para o status de conexão, o seu serviço de backend precisa de um mecanismo para monitorar ativamente o processo do bot. Isso pode ser feito com:
      * **Health Checks:** O bot expõe um endpoint de saúde que o backend pode consultar.
      * **Heartbeat:** O bot envia periodicamente um "sinal de vida" para o backend (ex: atualiza um timestamp em um banco de dados), e o backend verifica se esse sinal é recente.
  * **Autenticação e Autorização:** Assim como todos os outros endpoints, a dashboard e o teste de conexão devem ser protegidos para garantir que apenas usuários autorizados possam acessá-los.
  * **Atualizações em Tempo Real (Opcional):** Para as estatísticas dos cards (e não apenas o status de conexão), você pode considerar o uso de **WebSockets** ou **Server-Sent Events (SSE)**. Isso permitiria que os números nos cartões fossem atualizados em tempo real conforme novas interações acontecem, sem a necessidade de recarregar a página ou fazer polling constante.

Com esses endpoints, o seu componente `Index` será um verdadeiro centro de comando, fornecendo uma visão geral e interativa do desempenho e da saúde do seu agente Alfred!

## Requisitos extras do Projeto de Agentes de suporte de saass com IA [x]
### 1. Funcionalidades de Mensageria e Banco de Dados
* **RF1.1 - Controle de Mensagens do Discord:**
    * O sistema deve capturar todas as interações de mensagens do Discord (recebidas e enviadas).
    * Todas as mensagens e interações devem ser persistidas no banco de dados (Firebase, conforme o código já existente).
    * A funcionalidade de registro de interações e mensagens para o Discord deve ser **equivalente** à que já existe para o Telegram, incluindo a criação/atualização de interações e o armazenamento de mensagens de usuário e respostas do Alfred.

* **RF1.2 - Inicialização de Agentes com Chaves do Banco de Dados:**
    * Os agentes do Discord e Telegram devem ser inicializados utilizando as chaves (tokens, IDs de canal, etc.) que estão salvas no banco de dados (Firebase).
    * O sistema deve consultar o Firebase no momento da inicialização do agente para obter essas credenciais.

---

### 2. Gerenciamento de Agentes e Contêineres (Painel e Endpoints)

* **RF2.1 - Mini Painel de Inicialização de Agentes (Web):**
    * Deve ser desenvolvida uma interface web (mini painel) que permita a inicialização dos agentes do Discord e Telegram.
    * Este painel deve interagir com endpoints do backend para executar as ações de inicialização.

* **RF2.2 - Endpoints para Controle de Contêineres:**
    * O backend deve expor endpoints específicos para gerenciar os contêineres dos serviços do Telegram e Discord.
    * Cada endpoint deve ter a capacidade de:
        * **Inicializar** (start) um contêiner.
        * **Resetar** (restart) um contêiner.
        * **Pausar** (pause) um contêiner.
        * **Deletar** (remove) um contêiner.
    * Esses endpoints devem ser seguros e devidamente autenticados, se necessário.

---

### 3. Orquestração e Implantação (Docker Compose)

* **RF3.1 - Serviço Docker Compose para API (Backend):**
    * Deve ser criado um serviço no arquivo `docker-compose.yml` para a API de backend.
    * Este serviço deve orquestrar a execução do código Python responsável pelos endpoints de gerenciamento de contêineres e pela lógica de comunicação com os agentes.

* **RF3.2 - Serviço Docker Compose para Frontend (Painel Web):**
    * Deve ser criado um serviço no arquivo `docker-compose.yml` para o frontend (mini painel web).
    * Este serviço deve ser configurado para servir a interface web que permitirá a interação do usuário com os agentes e o controle dos contêineres.

---

## Requisitos: Agente de IA Alfred [x]

### 1. Requisitos Funcionais

* **RF1: Inicialização e Configuração do Agente Alfred**
    * **RF1.1:** O agente Alfred deve ser inicializado com uma instância do aplicativo Firebase (`app_1`).
    * **RF1.2:** O agente deve carregar seu nome (`alfredName`), modelo de IA preferido (`alfredModel`) e instruções adicionais (`alfredInstructions`) do Firebase (`configurations` ref).
    * **RF1.3:** O agente deve ter um sistema de instrução base (`system_`) configurável.
* **RF2: Gerenciamento e Utilização da Base de Conhecimento**
    * **RF2.1:** O agente deve ser capaz de recuperar os caminhos locais dos arquivos de conhecimento a partir dos metadados armazenados no Firebase (`alfred_knowledge_metadata` ref).
    * **RF2.2:** O sistema deve verificar a existência física dos arquivos referenciados por `local_path` e alertar se o arquivo não for encontrado.
    * **RF2.3:** O agente deve ser capaz de ler e extrair conteúdo de diferentes tipos de arquivos locais:
        * **RF2.3.1:** Arquivos de texto (`.md`, `.txt`, `.csv`, `.json`).
        * **RF2.3.2:** Arquivos PDF (`.pdf`), extraindo o texto de todas as páginas.
        * **RF2.3.3:** Arquivos DOCX (`.docx`), extraindo o texto de todos os parágrafos.
    * **RF2.4:** O conteúdo extraído dos arquivos de conhecimento deve ser concatenado e incorporado nas instruções do Alfred para o modelo de IA.
* **RF3: Processamento de Mensagens com IA**
    * **RF3.1:** O agente deve utilizar uma instância da classe `Agent` (do módulo `agents`) para processar as mensagens dos usuários.
    * **RF3.2:** A instância do `Agent` deve ser configurada com o nome do Alfred, as instruções combinadas (incluindo o contexto dos arquivos) e o modelo de IA selecionado.
    * **RF3.3:** O agente deve ser capaz de executar o `Runner.run` do `Agent` para obter uma resposta da IA a partir da mensagem do usuário.
    * **RF3.4:** O agente deve retornar a saída final (`final_output`) gerada pela IA.
* **RF4: Integração com Firebase**
    * **RF4.1:** O sistema deve inicializar uma instância do aplicativo Firebase no início da execução.
    * **RF4.2:** O sistema deve interagir com as referências `alfred_knowledge_metadata` e `configurations` no Firebase para carregar e gerenciar dados.

---

### 2. Requisitos Não Funcionais

* **RNF1: Desempenho**
    * **RNF1.1 Tempo de Resposta:** O agente deve fornecer respostas da IA em um tempo razoável para não impactar a experiência do usuário nas plataformas de chat (Discord, Telegram, WhatsApp).
    * **RNF1.2 Eficiência de Leitura:** A leitura e processamento de arquivos de conhecimento devem ser otimizados para evitar gargalos, especialmente com grandes volumes de dados.
* **RNF2: Segurança**
    * **RNF2.1 Gerenciamento de Credenciais:** As chaves de acesso ao Firebase e a outros serviços (implicitamente `HuggingFace` no `main.py` do projeto maior) devem ser carregadas de forma segura (e.g., `.env` ou Firebase), não hardcoded.
    * **RNF2.2 Autorização:** O acesso aos dados no Firebase deve ser controlado por regras de segurança apropriadas.
* **RNF3: Confiabilidade/Disponibilidade**
    * **RNF3.1 Conectividade:** O agente deve manter uma conexão estável com o Firebase e com os serviços de modelo de IA (Hugging Face ou outros).
    * **RNF3.2 Tolerância a Falhas:** O sistema deve lidar graciosamente com erros na leitura de arquivos (permissões, corrupção) ou na comunicação com o Firebase, registrando os erros sem falhar completamente.
* **RNF4: Escalabilidade**
    * **RNF4.1 Concorrência:** O agente deve ser capaz de lidar com múltiplas requisições de mensagens de forma concorrente.
* **RNF5: Manutenibilidade**
    * **RNF5.1 Modularidade:** O código está bem estruturado em uma classe `Alfred`, com métodos dedicados para cada funcionalidade (e.g., `get_alfred_local_file_paths`, `Alfred`).
    * **RNF5.2 Logging:** A implementação de um sistema de log (`logging`) é crucial para monitoramento, depuração e auditoria das operações do agente.
    * **RNF5.3 Extensibilidade:** A arquitetura deve permitir a fácil adição de novos tipos de arquivos de conhecimento ou a integração com diferentes modelos de IA.
* **RNF6: Usabilidade (Interna/Desenvolvedor)**
    * **RNF6.1 Configuração Centralizada:** A configuração do Alfred via Firebase permite que os parâmetros sejam ajustados dinamicamente sem a necessidade de reimplantar o código.

---

### 3. Dependências Externas

* **DE1: Firebase Realtime Database:** Utilizado para armazenamento de metadados de conhecimento e configurações do Alfred.
* **DE2: Módulo `agents`:** Uma biblioteca interna/externa que fornece a estrutura para a criação e execução de agentes de IA (`Agent`, `Runner`).
* **DE3: Hugging Face Hub (InferenceClient/login):** Implícito pelo `import`, sugere o uso de modelos de IA hospedados no Hugging Face para inferência.
* **DE4: `python-dotenv`:** Para carregar variáveis de ambiente.
* **DE5: `PyPDF2`:** Para extração de texto de arquivos PDF.
* **DE6: `python-docx`:** Para extração de texto de arquivos DOCX.

---


## Requisitos: Integração com API oficial do Discord [x]

### 1. Requisitos Funcionais

* **RF1: Inicialização e Conexão com o Discord**
    * **RF1.1:** O sistema deve ser capaz de inicializar o bot do Discord com as permissões de `message_content`.
    * **RF1.2:** O sistema deve estabelecer uma conexão com a API do Discord usando um token de bot fornecido.
* **RF2: Gerenciamento de Status no Firebase**
    * **RF2.1:** O sistema deve registrar seu status como "online" no Firebase Realtime Database ao ser inicializado.
    * **RF2.2:** O registro de status deve incluir a data e hora da última atualização (UTC), o nome da imagem do Docker (`image_name`) e o nome do contêiner (`container_name`).
* **RF3: Processamento de Mensagens Recebidas do Discord**
    * **RF3.1:** O sistema deve escutar e processar mensagens de texto recebidas em qualquer canal onde o bot esteja presente.
    * **RF3.2:** O sistema deve ignorar as mensagens enviadas pelo próprio bot para evitar loops infinitos.
    * **RF3.3:** Ao receber uma mensagem, o sistema deve extrair as informações do usuário remetente (ID do canal, nome de usuário do autor, conteúdo da mensagem).
    * **RF3.4:** O sistema deve extrair as informações do usuário do objeto da mensagem do Discord (ID abreviado, nome completo e nome de usuário).
* **RF4: Gerenciamento de Interações (Conversas) no Firebase**
    * **RF4.1:** O sistema deve verificar se já existe uma interação ativa para o `chat_id` da mensagem recebida.
    * **RF4.2:** Se não houver uma interação ativa, o sistema deve criar uma **nova entrada de interação** no Firebase, registrando o usuário, status "pending" e timestamp da criação.
    * **RF4.3:** O sistema deve salvar todas as mensagens do usuário recebidas na interação correspondente no Firebase.
    * **RF4.4:** O sistema deve salvar as respostas geradas pelo Alfred na interação correspondente no Firebase.
    * **RF4.5:** O sistema deve atualizar o status da interação no Firebase (por exemplo, "pending", "responded") e a data/hora da última atividade.
* **RF5: Integração com o Alfred AI**
    * **RF5.1:** O sistema deve enviar o texto da mensagem do usuário para o módulo de IA "Alfred" para processamento.
    * **RF5.2:** O sistema deve receber e utilizar a resposta gerada pelo Alfred.
* **RF6: Envio de Mensagens e Mídias no Discord**
    * **RF6.1:** O sistema deve enviar a resposta gerada pelo Alfred de volta ao canal de origem da mensagem.
    * **RF6.2:** O sistema deve ser capaz de enviar imagens para um canal específico do Discord (`CHANNEL_ID`), opcionalmente com uma legenda.
* **RF7: Suporte a Comandos do Discord**
    * **RF7.1:** O sistema deve responder ao comando `!ping` com a mensagem "Pong!".
* **RF8: Carregamento de Configurações**
    * **RF8.1:** O sistema deve carregar variáveis de ambiente de um arquivo `.env` para informações sensíveis.
    * **RF8.2:** O sistema deve inicializar uma instância do Firebase.
    * **RF8.3:** O sistema deve recuperar o **ID do Canal** do Discord (`discordChannelId`) e o **TOKEN do Bot** do Discord (`discordBotToken`) das configurações armazenadas no Firebase (`configurations_db_ref`).

---

### 2. Requisitos Não Funcionais

* **RNF1: Desempenho**
    * **RNF1.1 Latência:** O sistema deve processar mensagens e responder no Discord com baixa latência para garantir uma experiência de usuário fluida.
* **RNF2: Segurança**
    * **RNF2.1 Proteção de Credenciais:** O token do Discord e outras informações sensíveis devem ser carregados de variáveis de ambiente ou do Firebase, e nunca diretamente no código.
    * **RNF2.2 Confidencialidade dos Dados:** As mensagens dos usuários e as interações armazenadas no Firebase devem seguir as regras de segurança apropriadas do Firebase.
* **RNF3: Confiabilidade/Disponibilidade**
    * **RNF3.1 Conectividade:** O sistema deve manter uma conexão estável com a API do Discord e com o Firebase Realtime Database.
    * **RNF3.2 Reporte de Status:** A atualização contínua do status no Firebase (`discord_status_ref`) é crucial para monitorar a disponibilidade do agente.
* **RNF4: Escalabilidade**
    * **RNF4.1 Concorrência:** O sistema deve ser capaz de lidar com múltiplas interações simultâneas de usuários no Discord.
* **RNF5: Manutenibilidade**
    * **RNF5.1 Modularidade do Código:** A estrutura em classes e funções (`Discord` class, `_get_user_info`, `_save_message_to_firebase`) promove a modularidade e a fácil manutenção.
    * **RNF5.2 Depuração:** A utilização de `print` statements é implementada para fins de depuração e monitoramento do fluxo de mensagens.
* **RNF6: Usabilidade (Interna/Desenvolvedor)**
    * **RNF6.1 Configuração Facilitada:** A configuração de chaves e IDs através de variáveis de ambiente e Firebase simplifica a implantação e atualização.

---

### 3. Dependências Externas

* **DE1: API do Discord:** O sistema depende da API oficial do Discord para comunicação (envio/recebimento de mensagens).
* **DE2: Firebase Realtime Database:** O sistema utiliza o Firebase para armazenamento de dados de configuração, status e histórico de conversas.
* **DE3: Módulo de IA Alfred:** O sistema depende da classe `Alfred` (assumidamente um módulo de IA externo) para gerar as respostas às mensagens dos usuários.
* **DE4: `discord.py` Library:** A biblioteca `discord.py` é essencial para a interação com a API do Discord.

---

---


## Requisitos: Integração com API oficial do Telegram [x]

### 1. Requisitos Funcionais

* **RF1: Inicialização e Conexão com o Telegram**
    * **RF1.1:** O sistema deve ser capaz de inicializar o bot do Telegram usando um **TOKEN** fornecido.
    * **RF1.2:** O sistema deve configurar uma conexão para escutar mensagens e comandos do Telegram.
* **RF2: Gerenciamento de Status no Firebase**
    * **RF2.1:** O sistema deve registrar seu status como "online" no Firebase Realtime Database ao ser inicializado.
    * **RF2.2:** O registro de status deve incluir a data e hora da última atualização (UTC), o nome da imagem do Docker (`image_name`) e o nome do contêiner (`container_name`).
* **RF3: Processamento de Mensagens Recebidas**
    * **RF3.1:** O sistema deve ser capaz de receber e processar mensagens de texto de chats privados (conversas diretas).
    * **RF3.2:** O sistema deve ser capaz de receber e processar mensagens de texto de um **canal específico** do Telegram (identificado por `CHANNEL_ID`).
    * **RF3.3:** Ao receber uma mensagem, o sistema deve extrair as informações do usuário remetente (ID, nome completo, primeiro nome, nome de usuário e plataforma "Telegram").
* **RF4: Gerenciamento de Interações (Conversas) no Firebase**
    * **RF4.1:** O sistema deve verificar se já existe uma interação ativa para o `chat_id` da mensagem recebida.
    * **RF4.2:** Se não houver uma interação ativa, o sistema deve criar uma **nova entrada de interação** no Firebase, registrando o usuário, status "pending" e timestamp da criação.
    * **RF4.3:** O sistema deve salvar todas as mensagens do usuário recebidas na interação correspondente no Firebase.
    * **RF4.4:** O sistema deve salvar as respostas geradas pelo Alfred na interação correspondente no Firebase.
    * **RF4.5:** O sistema deve atualizar o status da interação no Firebase (por exemplo, "pending", "responded") e a data/hora da última atividade.
* **RF5: Integração com o Alfred AI**
    * **RF5.1:** O sistema deve enviar o texto da mensagem do usuário para o módulo de IA "Alfred" para processamento.
    * **RF5.2:** O sistema deve receber e utilizar a resposta gerada pelo Alfred.
* **RF6: Envio de Mensagens e Mídias no Telegram**
    * **RF6.1:** O sistema deve enviar a resposta gerada pelo Alfred de volta ao chat de origem (privado ou canal).
    * **RF6.2:** O sistema deve ser capaz de enviar imagens para o canal configurado, opcionalmente com uma legenda.
* **RF7: Suporte a Comandos do Telegram**
    * **RF7.1:** O sistema deve responder ao comando `/start` com uma mensagem de boas-vindas ("Olá! Como posso ajudar você hoje?").
* **RF8: Carregamento de Configurações**
    * **RF8.1:** O sistema deve carregar variáveis de ambiente de um arquivo `.env` para informações sensíveis (como tokens).
    * **RF8.2:** O sistema deve inicializar uma instância do Firebase.
    * **RF8.3:** O sistema deve recuperar o **TOKEN** do bot do Telegram (`botToken`) e o **ID do Canal** (`channelId`) das configurações armazenadas no Firebase (`configurations_db_ref`).

---

### 2. Requisitos Não Funcionais

* **RNF1: Desempenho**
    * **RNF1.1 Latência:** O sistema deve processar mensagens e responder no Telegram com baixa latência para garantir uma experiência de usuário fluida.
* **RNF2: Segurança**
    * **RNF2.1 Proteção de Credenciais:** O token do Telegram e outras informações sensíveis devem ser carregados de variáveis de ambiente ou do Firebase, e nunca diretamente no código.
    * **RNF2.2 Confidencialidade dos Dados:** As mensagens dos usuários e as interações armazenadas no Firebase devem seguir as regras de segurança apropriadas do Firebase.
* **RNF3: Confiabilidade/Disponibilidade**
    * **RNF3.1 Conectividade:** O sistema deve manter uma conexão estável com a API do Telegram e com o Firebase Realtime Database.
    * **RNF3.2 Reporte de Status:** A atualização contínua do status no Firebase (`telegram_status_ref`) é crucial para monitorar a disponibilidade do agente.
* **RNF4: Escalabilidade**
    * **RNF4.1 Concorrência:** O sistema deve ser capaz de lidar com múltiplas interações simultâneas de usuários no Telegram.
* **RNF5: Manutenibilidade**
    * **RNF5.1 Modularidade do Código:** A estrutura em classes e funções (`Telegram` class, `_get_user_info`, `_save_message_to_firebase`) promove a modularidade e a fácil manutenção.
    * **RNF5.2 Depuração:** A utilização de `print` statements indica a necessidade de informações para depuração e monitoramento do fluxo de mensagens.
* **RNF6: Usabilidade (Interna/Desenvolvedor)**
    * **RNF6.1 Configuração Facilitada:** A configuração de chaves e IDs através de variáveis de ambiente e Firebase simplifica a implantação e atualização.

---

### 3. Dependências Externas

* **DE1: API do Telegram:** O sistema depende da API oficial do Telegram para comunicação (envio/recebimento de mensagens).
* **DE2: Firebase Realtime Database:** O sistema utiliza o Firebase para armazenamento de dados de configuração, status e histórico de conversas.
* **DE3: Módulo de IA Alfred:** O sistema depende da classe `Alfred` (assumidamente um módulo de IA externo) para gerar as respostas às mensagens dos usuários.
* **DE4: `python-telegram-bot` Library:** A biblioteca `telegram` é essencial para a interação com a API do Telegram.

---

---


## Requisitos: Integração Com API Evolution WhatsApp  [x]

### 1. Requisitos Funcionais

* **RF1: Receber Eventos do Webhook do WhatsApp:** O sistema deve ser capaz de receber eventos de webhook de um servidor WhatsApp Evolution.
    * **RF1.1:** O sistema deve analisar os payloads JSON recebidos dos eventos de webhook do WhatsApp.
    * **RF1.2:** O sistema deve extrair informações relevantes do payload do webhook, incluindo:
        * Tipo de evento (`event`)
        * Nome da instância (`instance`)
        * JID da mensagem (`jid`)
        * Objeto da mensagem (`message_obj`)
        * ID do participante remetente (`sender`)
        * Nome de exibição (`pushName`)
        * Conteúdo da mensagem (texto simples, texto estendido).
* **RF2: Processar Mensagens Recebidas do WhatsApp:** O sistema deve identificar e processar mensagens de texto recebidas de chats individuais do WhatsApp.
    * **RF2.1:** O sistema deve extrair o conteúdo de texto real do objeto da mensagem do WhatsApp.
    * **RF2.2:** O sistema deve obter as informações do usuário (ID, nome, nome de usuário, plataforma) a partir dos dados da mensagem recebida.
* **RF3: Gerenciar Interações do Usuário (Firebase):** O sistema deve gerenciar interações contínuas do usuário (conversas) usando o Firebase Realtime Database.
    * **RF3.1:** O sistema deve identificar interações existentes com base no `chat_id`.
    * **RF3.2:** Se não houver uma interação ativa para um determinado `chat_id`, o sistema deve criar uma nova entrada de interação no Firebase.
    * **RF3.3:** O sistema deve salvar todas as mensagens recebidas do usuário na interação correspondente no Firebase.
    * **RF3.4:** O sistema deve salvar todas as respostas do Alfred na interação correspondente no Firebase.
    * **RF3.5:** O sistema deve atualizar o status de uma interação (por exemplo, "pendente", "respondida") no Firebase.
* **RF4: Integrar com a IA Alfred:** O sistema deve se integrar com o módulo de IA "Alfred" para gerar respostas às mensagens do usuário.
    * **RF4.1:** O sistema deve passar a mensagem do usuário recebida para o Alfred AI para processamento.
    * **RF4.2:** O sistema deve receber e processar a resposta gerada pela IA do Alfred.
* **RF5: Enviar Mensagens do WhatsApp:** O sistema deve enviar mensagens de texto de volta aos usuários do WhatsApp através do servidor WhatsApp Evolution.
    * **RF5.1:** O sistema deve construir um payload para enviar mensagens de texto, incluindo:
        * Número do destinatário (`number`)
        * Opções da mensagem (atraso, presença, pré-visualização de link)
        * Conteúdo da mensagem de texto.
    * **RF5.2:** O sistema deve fazer uma requisição HTTP POST para o endpoint de envio de mensagens do servidor WhatsApp Evolution.
    * **RF5.3:** O sistema deve incluir a Chave da API nos cabeçalhos da requisição para autenticação.
* **RF6: Inicialização e Configuração do Firebase:** O sistema deve inicializar o Firebase e recuperar os dados de configuração.
    * **RF6.1:** O sistema deve inicializar um aplicativo Firebase usando `init_firebase()`.
    * **RF6.2:** O sistema deve recuperar `waServerUrl`, `waInstanceId`, `waApiKey` e `waSupportGroupJid` das configurações do Firebase.
    * **RF6.3:** O sistema deve atualizar o status do serviço WhatsApp Evolution no Firebase (online/offline, última atualização, nome da imagem, nome do contêiner).
* **RF7: Carregamento de Variáveis de Ambiente:** O sistema deve carregar variáveis de ambiente de um arquivo `.env` para informações sensíveis.
* **RF8: Registro (Logging):** O sistema deve implementar um mecanismo de registro para gravar atividades e mensagens do sistema.
    * **RF8.1:** O sistema deve registrar os payloads de webhook recebidos.
    * **RF8.2:** O sistema deve registrar as mensagens de texto extraídas.
    * **RF8.3:** O sistema deve registrar informações de depuração sobre as configurações do Firebase.
    * **RF8.4:** O sistema deve registrar o status das mensagens enviadas ao servidor WhatsApp Evolution.
* **RF9: Endpoint da API:** O sistema deve expor um endpoint POST `/webhook/whatsapp` para receber eventos de webhook.
    * **RF9.1:** O endpoint deve retornar um `JSONResponse` com `{"status": "ok"}` e um código de status `200` após o processamento bem-sucedido.

---

### 2. Requisitos Não Funcionais

* **RNF1: Desempenho:**
    * **RNF1.1 Latência:** O sistema deve processar e responder às mensagens do WhatsApp com latência mínima para garantir uma experiência de usuário fluida.
* **RNF2: Segurança:**
    * **RNF2.1 Proteção da Chave da API:** As chaves da API e outras informações sensíveis devem ser carregadas de variáveis de ambiente e não codificadas diretamente.
    * **RNF2.2 Confidencialidade dos Dados:** As mensagens do usuário e as interações armazenadas no Firebase devem aderir às medidas de segurança apropriadas (regras de segurança internas do Firebase).
* **RNF3: Confiabilidade/Disponibilidade:**
    * **RNF3.1 Conectividade com Firebase:** O sistema deve manter uma conexão confiável com o Firebase Realtime Database.
    * **RNF3.2 Conectividade com o Servidor WhatsApp Evolution:** O sistema deve se conectar de forma confiável ao servidor WhatsApp Evolution para enviar mensagens.
    * **RNF3.3 Relatório de Status:** O sistema deve atualizar continuamente seu status "online" no Firebase para indicar seu estado operacional.
* **RNF4: Escalabilidade:**
    * **RNF4.1 Interações Concorrentes:** O sistema deve ser capaz de lidar com múltiplas interações simultâneas do WhatsApp. (Implicado pela natureza do FastAPI e do Firebase).
* **RNF5: Manutenibilidade:**
    * **RNF5.1 Modularidade do Código:** O código é estruturado com funções para clara separação de responsabilidades (por exemplo, `_get_user_info`, `_save_message_to_firebase`).
    * **RNF5.2 Logging para Depuração:** O registro abrangente deve facilitar a depuração e a solução de problemas.
* **RNF6: Usabilidade (Interna/Desenvolvedor):**
    * **RNF6.1 Fácil Configuração:** Os parâmetros de configuração (por exemplo, `SERVER_URL`, `API_KEY`) devem ser facilmente configuráveis através de variáveis de ambiente e Firebase.

---

### 3. Dependências Externas

* **DE1: Servidor WhatsApp Evolution:** O sistema depende de um servidor WhatsApp Evolution externo para enviar e receber mensagens via webhooks.
* **DE2: Firebase Realtime Database:** O sistema usa o Firebase para armazenar configurações, histórico de interações e atualizações de status.
* **DE3: Módulo de IA Alfred:** O sistema depende do módulo de IA `Alfred` para gerar respostas.


---

## Requisitos de Backend/Endpoint para o controle de Sistema de Agentes [x]

### Gerenciamento do Agente via Interface Web
* **Requisito Principal:** O backend deve expor endpoints para iniciar, redefinir, pausar e deletar os contêineres dos agentes, além de permitir a inicialização com chaves salvas no banco de dados.
* **Endpoints:**
    * `POST /agents/initialize`: Inicializa um novo agente (Discord ou Telegram). O corpo da requisição deve incluir `platform` (telegram/discord), e `agentConfigId` (ID de uma configuração pré-salva no DB contendo as chaves e outros parâmetros). O backend deve então orquestrar a inicialização do contêiner Docker correspondente.
    * `POST /agents/{platform}/reset`: Reinicia o contêiner Docker de um agente específico.
    * `POST /agents/{platform}/pause`: Pausa o contêiner Docker de um agente específico.
    * `DELETE /agents/{platform}/delete`: Deleta o contêiner Docker de um agente específico.
    * `GET /agents/status`: Retorna o status atual de todos os agentes (online, offline, pausado, etc.).


---

# Final do mvp versao 1 (22:00 - 29/06/2025)

**Tempo Gasto Planejamento de requisitos :** 1 a 2,3 horas (27/06/2025 a noite)

**Tempo Gasto de Desenvolvimento Backend (Python) + Integracao com Front end (React):** 4 a 5,3 horas (28/06/2025 de manhã) (endpoints iniciais)
- 16 endpoints desenvolvidos, testados e validados

**Tempo Gasto de Refinamento de Backend (Python) + Refinamento com Front end (React):** 4 a 5,3 horas (29/06/2025 de manhã) 



#
#




- ativar o "Ativa moderação inteligente usando IA" no backend class telegram e discord
- deixar em "Modelo de IA para Moderação" somente omnilatest pois é gratuito
- ativar o "Deletar Spam" no backend class telegram e discord
- ativar o "Limite para Banimento" no backend class telegram e discord

- criar metricas de recursos consumidos pelos servidores de telegram discord e whatsapp

- ativar o "Ferramentas Ativas (Tools_Name_dict)" no backend class Alfred, com sistema para registrar feedback comum dos clientes, sugestões de melhoria do produto e bugs reportados

**Function tool no agente**

- OpenSupportTicketProblem **Criação de Ticket:**
  - a função **OpenSupportTicketProblem** para registra o problema no banco de dados.
  - **Parâmetros necessários:**
      - `user_email`: Email do cliente.
      - `issue_description`: Descrição detalhada do problema.relacionados a problemas 

- GearAssist_Technical_Support **Geração do Boletim Técnico:**
  - a função **GearAssist_Technical_Support** wrapper do agente GearAssist para gerar o boletim técnico associado ao Ticket Que foi Aberto
  - **Parâmetros necessários:**
      - `Ticketid`: ID do ticket registrado.
  - **Retorno:** Caminho para o boletim técnico gerado.
  
- RecordCSAT **Coleta de Satisfação:**
  - Antes de fechar um ticket, utilize a função **RecordCSAT** para coletar a Pontuação de Satisfação do Cliente (CSAT).
  - **Parâmetros necessários:**
  - `ticketid`: ID do ticket em questão.
  - `csat_score`: Nota de satisfação do cliente (de 1 a 5).
  - **Mensagem ao cliente:**  
  "Poderia nos informar uma nota de 1 a 5 para avaliar sua experiência com nosso suporte? Sua opinião é muito importante para nós."


- CloseSupportTicketProblem Fechamento de Tickets:
  - Após a coleta da CSAT, utilize a função **CloseSupportTicketProblem** para fechar o ticket no banco de dados.
  - **Parâmetros necessários:**
  - `ticketid`: ID do ticket a ser fechado.
  - **Mensagem ao cliente:**  
  "Obrigado por sua avaliação. O ticket foi encerrado. Caso precise de mais assistência, estamos à disposição!"











### 2. Endpoints para Gerenciamento de Ferramentas (Opcional, se houver gerenciamento granular)

Se as "Ferramentas Ativas" (`toolsEnabled`) precisarem de um gerenciamento mais granular, onde você pode ativar/desativar ferramentas específicas ou listar as disponíveis dinamicamente, podemos ter endpoints dedicados. No seu frontend, `toolsEnabled` é um switch simples, então o endpoint `/api/config` já seria suficiente.

No entanto, para o futuro, imagine algo assim:

#### 2.1. Listar Ferramentas Disponíveis (GET)

  * **Objetivo:** Obter uma lista de todas as ferramentas que o Alfred pode potencialmente usar.
  * **Método:** `GET`
  * **URL:** `/api/tools`
  * **Resposta (JSON):**
    ```json
    [
        {"id": "OpenSupportTicketProblem", "name": "Abrir Ticket de Suporte", "description": "Registra um ticket no banco de dados."},
        {"id": "GearAssist_Technical_Support", "name": "Gerar Boletim Técnico", "description": "Gera e retorna o caminho para o boletim técnico."},
        {"id": "CloseSupportTicketProblem", "name": "Fechar Ticket de Suporte", "description": "Fecha um ticket existente."},
        {"id": "RecordCSAT", "name": "Registrar Satisfação do Cliente", "description": "Coleta a Pontuação de Satisfação do Cliente."}
    ]
    ```

#### 2.2. Atualizar Status de Ferramenta (PUT/PATCH)

  * **Objetivo:** Ativar ou desativar uma ferramenta específica.
  * **Método:** `PUT` ou `PATCH`
  * **URL:** `/api/tools/{tool_id}/status`
  * **Corpo da Requisição (JSON):**
    ```json
    {
        "enabled": boolean
    }
    ```

-----

  ### Considerações de Backend Adicionais:

    * **Autenticação e Autorização:** Todos os endpoints de configuração devem ser protegidos por autenticação (ex: tokens JWT, sessões) e autorização, garantindo que apenas usuários autorizados possam visualizar ou modificar as configurações.
    * **Validação de Dados:** O backend deve realizar validação rigorosa de todos os dados recebidos para evitar entradas maliciosas ou incorretas (ex: validar formato de `channelId`, garantir que `banThreshold` seja um número).
    * **Armazenamento de Configurações:** As configurações precisarão ser persistidas em um banco de dados (SQL, NoSQL como Firebase/MongoDB, ou até mesmo um arquivo de configuração persistente se a escala for pequena).
    * **Gerenciamento de Erros:** O backend deve ter um tratamento de erro robusto, retornando mensagens de erro claras e códigos de status HTTP apropriados.
    * **Segurança do Token:** O `botToken` é sensível e nunca deve ser exposto no frontend ou em logs. No backend, deve ser armazenado de forma segura (criptografado em repouso e acessado apenas quando estritamente necessário).
    * **Modelos de IA:** O backend precisará ter a lógica para integrar-se com os provedores dos modelos de IA (`ominilatest`, `gpt-4`, `claude-3`, etc.) para a moderação e para o agente Alfred, utilizando as chaves de API desses serviços de forma segura.





- Criar uma nova page de Criacao de novos agentes com foto, nome e area de atuacao (Suporte ou Atendimento)
