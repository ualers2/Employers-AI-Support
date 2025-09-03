
class MemeinApplicationContext:
    """
    Com essa classe Alfred é capaz de Criar e enviar memes que refletem o Contexto do aplicativo NordVPN Auto Rotate para o grupo do discord e telegram 
    """
    def __init__(self,
                appfb,
                client,
                nameApp,
                descriptionApp,
                watermark,
                Debug=True,
                lang="pt"


            ):
        self.Debug = Debug
        self.lang = lang
        self.appfb = appfb
        self.client = client
        self.user_threads = {}
        self.key = "AI_MemeinApplicationContext"
        self.nameassistant = "MemeinApplicationContext"
        self.model_select = "gpt-4o-mini-2024-07-18"
        self.nameApp = nameApp
        self.watermark = watermark 
        self.Upload_1_file_in_thread = None
        self.Upload_1_file_in_message = None
        self.Upload_1_image_for_vision_in_thread = None
        self.codeinterpreter = None
        self.vectorstore = None
        self.vectorstore_in_agent = None
        self.instruction = """
        com base no mini dataset de prompt atual crie outro prompt para memes diarios para  os canais de comunicacao do aplicativo adicione uma marca da agua {self.watermark} 
        responda semprem em ingles
        """
        self.descriptionApp = descriptionApp 
        hugfacetoken = hugKeys.hug_1_keys()
        login(hugfacetoken)
        self.InferenceClientMeme  = InferenceClient("prithivMLmods/Flux-Meme-Xd-LoRA", token=hugfacetoken)

    def main(self):

        AI, instructionsassistant, nameassistant, model_select = AutenticateAgent.create_or_auth_AI(
            self.appfb,
            self.client,
            self.key,
            self.instruction,
            self.nameassistant,
            self.model_select,
            response_format="json_object"
        )

        if self.Debug:
            if self.lang == "pt":
                cprint(f"🔐 Autenticação concluída. Assistente: {nameassistant}, Modelo: {model_select}", 'cyan')
            else:
                cprint(f"🔐 Authentication completed. Assistant: {nameassistant}, Model: {model_select}", 'cyan')

        prompt = f"""
        com base no mini dataset de prompt atual crie outro prompt para memes diarios para  os canais de comunicacao do aplicativo adicione uma marca da agua {self.watermark} 
        responda semprem em ingles

        aplicativo:
        {self.descriptionApp}

        

        mini dataset:

        meme, A cartoon drawing of a brown cat and a white sheep. The sheep is facing each other and the cat is facing towards the left side of the image. The brown cat has a black nose and a black mouth. The white sheep has a white body and black legs. The background is a light peach color. There is a text bubble above the brown cat that says "If you feel sad I can eat you".

        meme, A medium-sized painting of a white T-rex in the middle of a dark, stormy night. The t-rex is facing towards the left side of the frame, its head turned towards the right. Its mouth is open, revealing its sharp teeth. A rooster is standing in the foreground of the painting, with a red cap on its head. The roosters head is turned to the right, and the word "Remember who you are" is written in white text above it. The background is a deep blue, with dark gray clouds and a crescent moon in the upper left corner of the image. There are mountains in the background, and a few other animals can be seen in the lower right corner.


        meme, A cartoon drawing of two zebras facing each other. The zebra on the left is facing the right. The horse on the right is facing to the left. The zebrab is facing towards the right and has a black mane on its head. The mane is black and white. The sky is light blue and there are birds flying in the sky. There is a text bubble above the zebras head that says "UPGRADE MAN!"

        meme, A cartoon-style illustration showing a hooded hacker sitting in front of a computer with the message "VPN expired" flashing on the screen. In the corner of the image, a stylized safe with the NordVPN logo is being closed automatically. The hacker has a frustrated expression with a speech bubble saying, "No chance today!" At the bottom, the text: "Nord Auto Rotate – Changing servers, keeping you safe."
                    
        """

        if self.Debug:
            if self.lang == "pt":
                cprint(f"📝 Prompt criado : {prompt}", 'cyan')
            else:
                cprint(f"📝 Prompt created : {prompt}", 'cyan')

        # Instrução adicional para resposta em JSON
        self.adxitional_instructions = 'Responda no formato JSON Exemplo: {"newprompt": "..."}'

        # Chamada para gerar a resposta do assistente
        response, total_tokens, prompt_tokens, completion_tokens = ResponseAgent.ResponseAgent_message_with_assistants(
            mensagem=prompt,
            agent_id=AI,
            key=self.key,
            app1=self.appfb,
            client=self.client,
            model_select=model_select,
            aditional_instructions=self.adxitional_instructions
        )

        if self.Debug:
            if self.lang == "pt":
                cprint(f"📨 Resposta recebida do assistente: {response}", 'cyan')
            else:
                cprint(f"📨 Response received from assistant: {response}", 'cyan')

        try:
            response_dictload = json.loads(response)
            response_dict = response_dictload['newprompt']

            if self.Debug:
                if self.lang == "pt":
                    cprint("✅ Resposta convertida para dicionário JSON.", 'green')
                else:
                    cprint("✅ Response converted to JSON dictionary.", 'green')
        except Exception as e:
            response_dict = response
            if self.Debug:
                if self.lang == "pt":
                    cprint(f"⚠️ Falha ao converter resposta para JSON: {str(e)}", 'red')
                else:
                    cprint(f"⚠️ Failed to convert response to JSON: {str(e)}", 'red')

        full_hash = hashlib.sha256(response_dict.encode('utf-8')).hexdigest()
        MemeHash = full_hash[:13]

        tentativas = 15
        espera = 60
        for tentativa in range(tentativas):
            try:
                if self.lang == "pt":
                    cprint(" Gerando Meme", 'green')
                else:
                    cprint(" Generating meme.", 'green')
                image = self.InferenceClientMeme.text_to_image(response_dict)
                os.makedirs(os.path.join(os.path.dirname(__file__), f"Meme_{self.nameApp}"), exist_ok=True)
                image_path = os.path.join(os.path.dirname(__file__), f"Meme_{self.nameApp}", f"{MemeHash}.png")
                image.save(image_path)
                return image_path
            except Exception as e:
                print(f"Erro na tentativa {tentativa + 1}: {e}")
                if tentativa < tentativas - 1:
                    print(f"Tentando novamente em {espera} segundos...")
                    time.sleep(espera)
                else:
                    print("Falha após múltiplas tentativas. Tente mais tarde.")

    def meme(self):
        nameApp = "Nord Auto Rotate"
        DescriptionApp = """
        Nord Auto Rotate is a robust and secure application designed to automate the rotation of NordVPN's VPN servers. With an intuitive interface and advanced features, the app ensures its users maintain privacy and security online by automatically switching between different VPN servers at set intervals.

        https://www.youtube.com/watch?v=E4fbZUVMMEI

        AI-Supported Group:
        https://t.me/+dpGofyMuGUszY2Rh

        Requirements
        NordVPN Subscription: To use Nord Auto Rotate, you must have an active NordVPN subscription. The application only works when the subscription is active, whether for 1 month or 1 year.


        Main Features:

        Automatic Server Rotation: Automatically switch between different NordVPN VPN servers to ensure online security and privacy.
        Custom Configuration: Set custom time intervals for server rotation.
        Monitoring and Reporting: Track VPN performance and view detailed usage reports.
        Integration with NordVPN: You must have an active subscription to NordVPN, either monthly or annually.

        Device Limitation: The Nord Auto Rotate license allows installation and use on up to 2 different computers. This limit is imposed to prevent misuse and unauthorized resale of the application.
        License Validity: The license is linked to the order serial. This serial is generated automatically after purchase.

        Security and Authentication:

        Unique Serial: Each license generates a unique serial that is checked against the CPU and disk serial number of the devices. This serial must be used to register the application on up to two computers.
        Serial Validity: The generated serial is valid for 30 days from the initial registration date. After this period, a license renewal will be required to continue using the application.
        Nord Auto Rotate is the ideal solution for those who want to keep their connection secure and anonymous with NordVPN, ensuring automatic and efficient rotation of VPN servers for continuous protection.


        """
        watemark = "@https://t.me/NVAR_suport"

        MemeinApplicationContext_class = Alfred.MemeinApplicationContext(
                                                                        self.appfb, 
                                                                        self.client,
                                                                        nameApp,
                                                                        DescriptionApp,
                                                                        watemark
                                                                        )
        image_path = MemeinApplicationContext_class.main()
        caption=None
        async def main():
            await self.handle_task(image_path, caption)

        asyncio.run(main())
