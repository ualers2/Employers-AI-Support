// src/components/ConfigPanel.tsx

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { useToast } from "@/hooks/use-toast";
import { Settings, Bot, Shield, Save, Brain, Loader2, AlertCircle, MessageCircle, GitFork } from "lucide-react"; // Added MessageCircle for WhatsApp, GitFork for Discord

import {
    fetchBotConfiguration,
    updateBotConfiguration,
    FullBotConfiguration,
    BotConfig,
    ModerationConfig,
    AlfredConfig
} from "@/lib/api";

const ConfigPanel = () => {
    const [config, setConfig] = useState<FullBotConfiguration>({
        botConfig: {
            telegramBotToken: '', // Updated field name
            telegramChannelId: '', // Updated field name
            discordBotToken: '', // New field
            discordChannelId: '', // New field
            waServerUrl: '',
            waInstanceId: '',
            waApiKey: '',
            waSupportGroupJid: '',
        },
        moderationConfig: {
            autoModeration: true,
            aiModeration: true,
            aiModerationModel: 'ominilatest',
            deleteSpam: true,
            banThreshold: 3,
        },
        alfredConfig: {
            alfredName: 'Alfred',
            alfredModel: 'gpt-4.1-nano',
            alfredInstructions: `## Objetivo
Oferecer suporte completo aos usuários do **Media Cuts Studio**, garantindo a resolução rápida de problemas, registro organizado de tickets, e coleta de feedback para melhoria contínua.`,
            toolsEnabled: false
        }
    });

    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const { toast } = useToast();

    useEffect(() => {
        const getConfiguration = async () => {
            setLoading(true);
            setError(null);
            try {
                const fetchedConfig = await fetchBotConfiguration();
                setConfig(fetchedConfig);
            } catch (err: any) {
                console.error("Failed to fetch bot configuration:", err);
                setError(err.message || "Failed to load configurations.");
                toast({
                    title: "Erro ao carregar configurações",
                    description: err.message || "Não foi possível carregar as configurações do Alfred.",
                    variant: "destructive",
                });
            } finally {
                setLoading(false);
            }
        };
        getConfiguration();
    }, []);

    const handleSaveConfig = async () => {
        setSaving(true);
        setError(null);
        try {
            const updatedConfig = await updateBotConfiguration(config);
            setConfig(updatedConfig);
            toast({
                title: "Configurações salvas!",
                description: "As configurações foram atualizadas com sucesso.",
            });
        } catch (err: any) {
            console.error('Erro ao salvar configurações:', err);
            setError(err.message || "Erro ao salvar configurações.");
            toast({
                title: "Erro ao salvar configurações",
                description: err.message || "Não foi possível salvar as configurações do Alfred. Verifique o console para mais detalhes.",
                variant: "destructive",
            });
        } finally {
            setSaving(false);
        }
    };

    // Corrected handleNestedConfigChange with conditional types
    const handleNestedConfigChange = <
        TCategory extends keyof FullBotConfiguration,
        TKey extends keyof FullBotConfiguration[TCategory]
    >(
        category: TCategory,
        key: TKey,
        value: FullBotConfiguration[TCategory][TKey] // Type the value to match the property
    ) => {
        setConfig(prev => ({
            ...prev,
            [category]: {
                ...prev[category],
                [key]: value
            }
        }));
    };

    if (loading) {
        return (
            <Card className="flex justify-center items-center h-96">
                <Loader2 className="h-10 w-10 animate-spin text-primary" />
                <span className="ml-4 text-lg text-muted-foreground">Carregando configurações...</span>
            </Card>
        );
    }

    if (error) {
        return (
            <Card className="flex flex-col justify-center items-center h-96 text-destructive">
                <AlertCircle className="h-10 w-10 mb-4" />
                <span className="text-lg text-red-600">Erro: {error}</span>
                <Button onClick={() => window.location.reload()} className="mt-4">Recarregar</Button>
            </Card>
        );
    }

    return (
        <div className="space-y-6">
            {/* Bot Configuration - Telegram */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Bot className="w-5 h-5" />
                        Configuração do Bot (Telegram)
                    </CardTitle>
                    <CardDescription>
                        Configurações de conexão para o bot do Telegram.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div>
                        <Label htmlFor="telegramBotToken">Token do Bot (Telegram)</Label>
                        <Input
                            id="telegramBotToken"
                            type="password"
                            placeholder="123456789:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
                            value={config.botConfig.telegramBotToken}
                            onChange={(e) => handleNestedConfigChange('botConfig', 'telegramBotToken', e.target.value)}
                        />
                    </div>
                    <div>
                        <Label htmlFor="telegramChannelId">ID do Canal (Telegram)</Label>
                        <Input
                            id="telegramChannelId"
                            placeholder="-1001234567890"
                            value={config.botConfig.telegramChannelId}
                            onChange={(e) => handleNestedConfigChange('botConfig', 'telegramChannelId', e.target.value)}
                        />
                    </div>
                </CardContent>
            </Card>

            {/* Bot Configuration - Discord */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <GitFork className="w-5 h-5" />
                        Configuração do Bot (Discord)
                    </CardTitle>
                    <CardDescription>
                        Configurações de conexão para o bot do Discord.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div>
                        <Label htmlFor="discordBotToken">Token do Bot (Discord)</Label>
                        <Input
                            id="discordBotToken"
                            type="password"
                            placeholder="YOUR_DISCORD_BOT_TOKEN"
                            value={config.botConfig.discordBotToken}
                            onChange={(e) => handleNestedConfigChange('botConfig', 'discordBotToken', e.target.value)}
                        />
                    </div>
                    <div>
                        <Label htmlFor="discordChannelId">ID do Canal (Discord)</Label>
                        <Input
                            id="discordChannelId"
                            placeholder="123456789012345678"
                            value={config.botConfig.discordChannelId}
                            onChange={(e) => handleNestedConfigChange('botConfig', 'discordChannelId', e.target.value)}
                        />
                    </div>
                </CardContent>
            </Card>


            {/* Bot Configuration - WhatsApp (Evolution API) */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <MessageCircle className="w-5 h-5" />
                        Configuração do Bot (WhatsApp - Evolution API)
                    </CardTitle>
                    <CardDescription>
                        Configurações para integração com a Evolution API do WhatsApp.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div>
                        <Label htmlFor="waServerUrl">URL do Servidor da Evolution API</Label>
                        <Input
                            id="waServerUrl"
                            placeholder="https://api.evolution-api.com"
                            value={config.botConfig.waServerUrl}
                            onChange={(e) => handleNestedConfigChange('botConfig', 'waServerUrl', e.target.value)}
                        />
                    </div>
                    <div>
                        <Label htmlFor="waInstanceId">ID da Instância (Evolution API)</Label>
                        <Input
                            id="waInstanceId"
                            placeholder="instance_id"
                            value={config.botConfig.waInstanceId}
                            onChange={(e) => handleNestedConfigChange('botConfig', 'waInstanceId', e.target.value)}
                        />
                    </div>
                    <div>
                        <Label htmlFor="waApiKey">Chave da API (Evolution API)</Label>
                        <Input
                            id="waApiKey"
                            type="password"
                            placeholder="your_api_key_here"
                            value={config.botConfig.waApiKey}
                            onChange={(e) => handleNestedConfigChange('botConfig', 'waApiKey', e.target.value)}
                        />
                    </div>
                    <div>
                        <Label htmlFor="waSupportGroupJid">JID do Grupo de Suporte (WhatsApp)</Label>
                        <Input
                            id="waSupportGroupJid"
                            placeholder="1234567890-1234567890@g.us"
                            value={config.botConfig.waSupportGroupJid}
                            onChange={(e) => handleNestedConfigChange('botConfig', 'waSupportGroupJid', e.target.value)}
                        />
                    </div>
                </CardContent>
            </Card>


            {/* Advanced Moderation Settings */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Shield className="w-5 h-5" />
                        Moderação Automática Avançada
                    </CardTitle>
                    <CardDescription>
                        Configure as regras de moderação automática e por IA
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">

                    {/* Note: 'autoModeration' switch was commented out in your original code.
                        If it's managed by backend, uncomment and connect it. */}
                    {/* <div className="flex items-center justify-between">
                        <div className="space-y-0.5">
                            <Label htmlFor="autoModeration">Moderação Automática Geral</Label>
                            <p className="text-sm text-muted-foreground">
                                Ativa/desativa todas as funções de moderação automática.
                            </p>
                        </div>
                        <Switch
                            id="autoModeration"
                            checked={config.moderationConfig.autoModeration}
                            onCheckedChange={(checked) => handleNestedConfigChange('moderationConfig', 'autoModeration', checked)}
                        />
                    </div>
                    <Separator /> */}

                    <div className="flex items-center justify-between">
                        <div className="space-y-0.5">
                            <Label htmlFor="aiModeration">Moderação por IA</Label>
                            <p className="text-sm text-muted-foreground">
                                Ativa moderação inteligente usando IA
                            </p>
                        </div>
                        <Switch
                            id="aiModeration"
                            checked={config.moderationConfig.aiModeration}
                            onCheckedChange={(checked) => handleNestedConfigChange('moderationConfig', 'aiModeration', checked)}
                        />
                    </div>

                    {config.moderationConfig.aiModeration && (
                        <div>
                            <Label htmlFor="aiModerationModel">Modelo de IA para Moderação</Label>
                            <Select
                                value={config.moderationConfig.aiModerationModel}
                                onValueChange={(value) => handleNestedConfigChange('moderationConfig', 'aiModerationModel', value)}
                            >
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="ominilatest">Omini Latest</SelectItem>
                                    <SelectItem value="gpt-4">GPT-4</SelectItem>
                                    <SelectItem value="claude-3">Claude-3</SelectItem>
                                    {/* Add other models if your backend supports them */}
                                </SelectContent>
                            </Select>
                            <p className="text-sm text-muted-foreground mt-1">
                                Modelo de IA especializado para moderação de conteúdo
                            </p>
                        </div>
                    )}

                    <Separator />

                    <div className="flex items-center justify-between">
                        <div className="space-y-0.5">
                            <Label htmlFor="deleteSpam">Deletar Spam</Label>
                            <p className="text-sm text-muted-foreground">
                                Remove automaticamente mensagens identificadas como spam
                            </p>
                        </div>
                        <Switch
                            id="deleteSpam"
                            checked={config.moderationConfig.deleteSpam}
                            onCheckedChange={(checked) => handleNestedConfigChange('moderationConfig', 'deleteSpam', checked)}
                        />
                    </div>

                    <div>
                        <Label htmlFor="banThreshold">Limite para Banimento</Label>
                        <Input
                            id="banThreshold"
                            type="number"
                            min="1"
                            max="10"
                            value={config.moderationConfig.banThreshold}
                            onChange={(e) => handleNestedConfigChange('moderationConfig', 'banThreshold', parseInt(e.target.value))}
                        />
                        <p className="text-sm text-muted-foreground mt-1">
                            Número de infrações antes do banimento automático
                        </p>
                    </div>
                </CardContent>
            </Card>

            {/* Alfred Agent Configuration */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Brain className="w-5 h-5" />
                        Configurações do Agente Alfred
                    </CardTitle>
                    <CardDescription>
                        Configure o comportamento e capacidades do agente Alfred
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                    <div>
                        <Label htmlFor="alfredName">Nome do Agente (nameAlfred)</Label>
                        <Input
                            id="alfredName"
                            value={config.alfredConfig.alfredName}
                            onChange={(e) => handleNestedConfigChange('alfredConfig', 'alfredName', e.target.value)}
                        />
                        <p className="text-sm text-muted-foreground mt-1">
                            Nome de identificação do agente Alfred
                        </p>
                    </div>

                    <div>
                        <Label htmlFor="alfredModel">Modelo do Alfred (model_selectAlfred)</Label>
                        <Select
                            value={config.alfredConfig.alfredModel}
                            onValueChange={(value) => handleNestedConfigChange('alfredConfig', 'alfredModel', value)}
                        >
                            <SelectTrigger>
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="gpt-4.1-nano">GPT-4.1 Nano</SelectItem>
                                <SelectItem value="gpt-4.1">GPT-4.1</SelectItem>
                                <SelectItem value="gpt-4o">GPT-4o</SelectItem>
                                <SelectItem value="claude-3-sonnet">Claude-3 Sonnet</SelectItem>
                                <SelectItem value="claude-3-opus">Claude-3 Opus</SelectItem>
                                {/* Add other models if your backend supports them */}
                            </SelectContent>
                        </Select>
                        <p className="text-sm text-muted-foreground mt-1">
                            Modelo de IA que o Alfred utilizará para processar mensagens
                        </p>
                    </div>

                    <div>
                        <Label htmlFor="alfredInstructions">Instruções do Sistema (instruction)</Label>
                        <Textarea
                            id="alfredInstructions"
                            rows={8}
                            value={config.alfredConfig.alfredInstructions}
                            onChange={(e) => handleNestedConfigChange('alfredConfig', 'alfredInstructions', e.target.value)}
                            className="font-mono text-sm"
                        />
                        <p className="text-sm text-muted-foreground mt-1">
                            Instruções principais que definem o comportamento do agente Alfred
                        </p>
                    </div>

                    <div className="flex items-center justify-between">
                        <div className="space-y-0.5">
                            <Label htmlFor="toolsEnabled">Ferramentas Ativas (Tools_Name_dict)</Label>
                            <p className="text-sm text-muted-foreground">
                                Ativa as ferramentas especializadas do Alfred (em produção)
                            </p>
                        </div>
                        <Switch
                            id="toolsEnabled"
                            checked={config.alfredConfig.toolsEnabled}
                            onCheckedChange={(checked) => handleNestedConfigChange('alfredConfig', 'toolsEnabled', checked)}
                        />
                    </div>
                </CardContent>
            </Card>

            {/* Save Button */}
            <Card>
                <CardContent className="pt-6">
                    <Button onClick={handleSaveConfig} className="w-full" disabled={saving}>
                        {saving ? (
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        ) : (
                            <Save className="w-4 h-4 mr-2" />
                        )}
                        Salvar Configurações do Alfred
                    </Button>
                </CardContent>
            </Card>
        </div>
    );
};

export default ConfigPanel;