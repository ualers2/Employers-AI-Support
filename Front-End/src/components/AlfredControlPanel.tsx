// src/components/AlfredControlPanel.tsx
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
// Importando MessageCircle para o ícone do WhatsApp, além dos existentes
import { Bot, MessageSquare, Send, RotateCcw, Pause, Play, Trash2, MessageCircle } from "lucide-react";
import { Input } from "@/components/ui/input";

interface AlfredControlPanelProps {
    API_BASE_URL: string;
}

const AlfredControlPanel: React.FC<AlfredControlPanelProps> = ({ API_BASE_URL }) => {
    const { toast } = useToast();
    const [loadingDiscord, setLoadingDiscord] = useState(false);
    const [loadingTelegram, setLoadingTelegram] = useState(false);
    // Novo estado para o carregamento do agente WhatsApp
    const [loadingWhatsapp, setLoadingWhatsapp] = useState(false);

    // Estados para armazenar os agentConfigIds.
    const [discordAgentConfigId, setDiscordAgentConfigId] = useState('discord_agent_config_1');
    const [telegramAgentConfigId, setTelegramAgentConfigId] = useState('telegram_agent_config_1');
    // Novo estado para o agentConfigId do WhatsApp
    const [whatsappAgentConfigId, setWhatsappAgentConfigId] = useState('whatsapp_agent_config_1');


    const sendAgentCommand = async (
        platform: 'discord' | 'telegram' | 'whatsapp', // Adicionado 'whatsapp'
        action: 'initialize' | 'reset' | 'pause' | 'delete',
        configId?: string
    ) => {
        const url = `${API_BASE_URL}/agents/${action === 'initialize' ? 'initialize' : platform}/${action === 'initialize' ? '' : action}`;
        const method = action === 'delete' ? 'DELETE' : 'POST';
        const userId = localStorage.getItem('user_email') || '';

        const body = (action === 'initialize' || action === 'reset')
            ? JSON.stringify({ platform, agentConfigId: configId, user_id: userId }) // 🔹 Inclui user_id
            : JSON.stringify({ platform, user_id: userId });

        // Lógica para definir qual estado de carregamento atualizar
        let setLoading: React.Dispatch<React.SetStateAction<boolean>>;
        if (platform === 'discord') {
            setLoading = setLoadingDiscord;
        } else if (platform === 'telegram') {
            setLoading = setLoadingTelegram;
        } else { // 'whatsapp'
            setLoading = setLoadingWhatsapp;
        }

        setLoading(true);
        toast({
            title: `${action.charAt(0).toUpperCase() + action.slice(1)} Alfred no ${platform.charAt(0).toUpperCase() + platform.slice(1)}...`,
            description: `Enviando comando para o backend.`,
        });

        try {
            const response = await fetch(url, {
                method,
                headers: {
                    'Content-Type': 'application/json',
                },
                body,
            });

            const data = await response.json();

            if (response.ok) {
                toast({
                    title: `${action.charAt(0).toUpperCase() + action.slice(1)} Alfred no ${platform.charAt(0).toUpperCase() + platform.slice(1)}!`,
                    description: data.message || `Agente ${action} com sucesso no ${platform}.`,
                });
            } else {
                throw new Error(data.message || `Falha ao ${action} o Alfred no ${platform}.`);
            }
        } catch (error: any) {
            console.error(`Erro ao ${action} Alfred no ${platform}:`, error);
            toast({
                title: `Erro ao ${action} no ${platform.charAt(0).toUpperCase() + platform.slice(1)}`,
                description: error.message || "Não foi possível conectar com o backend.",
                variant: "destructive",
            });
        } finally {
            setLoading(false);
        }
    };

    return (
        <Card className="shadow-lg">
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <Bot className="w-5 h-5" />
                    Controle do Agente Alfred
                </CardTitle>
                <CardDescription>
                    Inicialize, reinicie, pause ou delete os agentes Alfred nas plataformas de comunicação.
                </CardDescription>
            </CardHeader>
            <CardContent className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"> {/* Ajuste o grid para 3 colunas */}
                {/* Painel Discord */}
                <div className="space-y-4 p-4 border rounded-lg">
                    <h3 className="text-lg font-semibold flex items-center gap-2">
                        <MessageSquare className="w-5 h-5" />
                        Agente Discord
                    </h3>

                    <div className="grid grid-cols-2 gap-2">
                        <Button
                            className="flex items-center justify-center gap-2"
                            onClick={() => sendAgentCommand('discord', 'initialize', discordAgentConfigId)}
                            disabled={loadingDiscord}
                        >
                            <Play className="w-4 h-4" />
                            {loadingDiscord ? 'Iniciando...' : 'Iniciar'}
                        </Button>
                        <Button
                            className="flex items-center justify-center gap-2"
                            onClick={() => sendAgentCommand('discord', 'reset', discordAgentConfigId)}
                            disabled={loadingDiscord}
                            variant="outline"
                        >
                            <RotateCcw className="w-4 h-4" />
                            {loadingDiscord ? 'Reiniciando...' : 'Reiniciar'}
                        </Button>
                        <Button
                            className="flex items-center justify-center gap-2"
                            onClick={() => sendAgentCommand('discord', 'pause')}
                            disabled={loadingDiscord}
                            variant="outline"
                        >
                            <Pause className="w-4 h-4" />
                            {loadingDiscord ? 'Processando...' : 'Pausar/Despausar'}
                        </Button>
                        <Button
                            className="flex items-center justify-center gap-2"
                            onClick={() => sendAgentCommand('discord', 'delete')}
                            disabled={loadingDiscord}
                            variant="destructive"
                        >
                            <Trash2 className="w-4 h-4" />
                            {loadingDiscord ? 'Deletando...' : 'Deletar'}
                        </Button>
                    </div>
                </div>

                {/* Painel Telegram */}
                <div className="space-y-4 p-4 border rounded-lg">
                    <h3 className="text-lg font-semibold flex items-center gap-2">
                        <Send className="w-5 h-5" />
                        Agente Telegram
                    </h3>

                    <div className="grid grid-cols-2 gap-2">
                        <Button
                            className="flex items-center justify-center gap-2"
                            onClick={() => sendAgentCommand('telegram', 'initialize', telegramAgentConfigId)}
                            disabled={loadingTelegram}
                        >
                            <Play className="w-4 h-4" />
                            {loadingTelegram ? 'Iniciando...' : 'Iniciar'}
                        </Button>
                        <Button
                            className="flex items-center justify-center gap-2"
                            onClick={() => sendAgentCommand('telegram', 'reset', telegramAgentConfigId)}
                            disabled={loadingTelegram}
                            variant="outline"
                        >
                            <RotateCcw className="w-4 h-4" />
                            {loadingTelegram ? 'Reiniciando...' : 'Reiniciar'}
                        </Button>
                        <Button
                            className="flex items-center justify-center gap-2"
                            onClick={() => sendAgentCommand('telegram', 'pause')}
                            disabled={loadingTelegram}
                            variant="outline"
                        >
                            <Pause className="w-4 h-4" />
                            {loadingTelegram ? 'Processando...' : 'Pausar/Despausar'}
                        </Button>
                        <Button
                            className="flex items-center justify-center gap-2"
                            onClick={() => sendAgentCommand('telegram', 'delete')}
                            disabled={loadingTelegram}
                            variant="destructive"
                        >
                            <Trash2 className="w-4 h-4" />
                            {loadingTelegram ? 'Deletando...' : 'Deletar'}
                        </Button>
                    </div>
                </div>

                {/* Novo Painel WhatsApp */}
                <div className="space-y-4 p-4 border rounded-lg">
                    <h3 className="text-lg font-semibold flex items-center gap-2">
                        <MessageCircle className="w-5 h-5" /> {/* Ícone para WhatsApp */}
                        Agente WhatsApp
                    </h3>

                    <div className="grid grid-cols-2 gap-2">
                        <Button
                            className="flex items-center justify-center gap-2"
                            onClick={() => sendAgentCommand('whatsapp', 'initialize', whatsappAgentConfigId)}
                            disabled={loadingWhatsapp}
                        >
                            <Play className="w-4 h-4" />
                            {loadingWhatsapp ? 'Iniciando...' : 'Iniciar'}
                        </Button>
                        <Button
                            className="flex items-center justify-center gap-2"
                            onClick={() => sendAgentCommand('whatsapp', 'reset', whatsappAgentConfigId)}
                            disabled={loadingWhatsapp}
                            variant="outline"
                        >
                            <RotateCcw className="w-4 h-4" />
                            {loadingWhatsapp ? 'Reiniciando...' : 'Reiniciar'}
                        </Button>
                        <Button
                            className="flex items-center justify-center gap-2"
                            onClick={() => sendAgentCommand('whatsapp', 'pause')}
                            disabled={loadingWhatsapp}
                            variant="outline"
                        >
                            <Pause className="w-4 h-4" />
                            {loadingWhatsapp ? 'Processando...' : 'Pausar/Despausar'}
                        </Button>
                        <Button
                            className="flex items-center justify-center gap-2"
                            onClick={() => sendAgentCommand('whatsapp', 'delete')}
                            disabled={loadingWhatsapp}
                            variant="destructive"
                        >
                            <Trash2 className="w-4 h-4" />
                            {loadingWhatsapp ? 'Deletando...' : 'Deletar'}
                        </Button>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
};

export default AlfredControlPanel;