import React, { useState, useEffect, useCallback } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import {
    MessageCircle,
    Users,
    Upload,
    FileText,
    Activity,
    Settings,
    Bot,
    GitFork // Adicionado GitFork para consistência, se necessário no futuro
} from "lucide-react";
import MessagePanel from "@/components/MessagePanel";
import FileManager from "@/components/FileManager";
import ActivityMonitor from "@/components/ActivityMonitor";
import ConfigPanel from "@/components/ConfigPanel";
import AlfredControlPanel from "@/components/AlfredControlPanel"; // Importe o novo componente

const Index = () => {
    const [stats, setStats] = useState({
        totalMessages: 0,
        activeUsers: 0,
        alfredResponses: 0,
        filesManaged: 0,
        totalMessagesChangePercentage: 0,
        activeUsersChangePercentage: 0,
        alfredResponsesChangePercentage: 0,
    });

    const [isConnected, setIsConnected] = useState(false);
    const [alfredStatusMessage, setAlfredStatusMessage] = useState("Conectando...");
    const { toast } = useToast();
    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api';

    // Função para buscar as estatísticas do dashboard
    const fetchDashboardStats = useCallback(async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/dashboard/stats`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            setStats(data);
        } catch (error) {
            console.error("Erro ao buscar estatísticas do dashboard:", error);
            toast({
                title: "Erro de Conexão",
                description: "Não foi possível carregar as estatísticas do dashboard.",
                variant: "destructive",
            });
        }
    }, [toast]);

    // Função para verificar o status do Alfred
    const checkAlfredStatus = useCallback(async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/alfred/status`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            setIsConnected(data.status === "online");
            setAlfredStatusMessage(data.message);
        } catch (error) {
            console.error("Erro ao verificar status do Alfred:", error);
            setIsConnected(false);
            setAlfredStatusMessage("Erro ao conectar com o Alfred.");
            toast({
                title: "Erro de Conexão",
                description: "Não foi possível verificar o status do Alfred.",
                variant: "destructive",
            });
        }
    }, [toast]);

    useEffect(() => {
        // Busca inicial das estatísticas e status do Alfred
        fetchDashboardStats();
        checkAlfredStatus();

        // Configura intervalos para atualização periódica (a cada 30 segundos)
        const statsInterval = setInterval(fetchDashboardStats, 30000); // Atualiza a cada 30 segundos
        const statusInterval = setInterval(checkAlfredStatus, 30000); // Atualiza a cada 30 segundos

        // Limpeza dos intervalos ao desmontar o componente
        return () => {
            clearInterval(statsInterval);
            clearInterval(statusInterval);
        };
    }, [fetchDashboardStats, checkAlfredStatus]); // Dependências do useEffect

    const handleConnectionTest = async () => {
        toast({
            title: "Testando conexão...",
            description: "Verificando status do agente Alfred",
        });

        await checkAlfredStatus(); // Chama a função que verifica o status do Alfred via API
        toast({
            title: isConnected ? "Alfred está online!" : "Alfred está offline!",
            description: alfredStatusMessage,
        });
    };

    // Helper para formatar a mudança percentual
    const formatPercentage = (value: number) => {
        if (value > 0) {
            return `+${value}% desde ontem`;
        } else if (value < 0) {
            return `${value}% desde ontem`;
        }
        return "Sem mudanças desde ontem";
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
            <div className="max-w-7xl mx-auto space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between bg-white rounded-lg shadow-sm p-6">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900">Dashboard do Agente Alfred</h1>
                        <p className="text-gray-600 mt-1">Controle completo do agente de suporte inteligente</p>
                    </div>
                    <div className="flex items-center gap-4">
                        <Badge variant={isConnected ? "default" : "destructive"} className="px-3 py-1">
                            {alfredStatusMessage}
                        </Badge>
                        <Button onClick={handleConnectionTest} variant="outline">
                            <Bot className="w-4 h-4 mr-2" />
                            Testar Alfred
                        </Button>
                    </div>
                </div>

                {/* Stats Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Total de Mensagens</CardTitle>
                            <MessageCircle className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">{stats.totalMessages.toLocaleString()}</div>
                            <p className="text-xs text-muted-foreground">
                                {formatPercentage(stats.totalMessagesChangePercentage)}
                            </p>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Usuários Ativos</CardTitle>
                            <Users className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">{stats.activeUsers}</div>
                            <p className="text-xs text-muted-foreground">
                                {formatPercentage(stats.activeUsersChangePercentage)}
                            </p>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Respostas do Alfred</CardTitle>
                            <Bot className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">{stats.alfredResponses.toLocaleString()}</div>
                            <p className="text-xs text-muted-foreground">
                                {formatPercentage(stats.alfredResponsesChangePercentage)}
                            </p>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Arquivos Gerenciados</CardTitle>
                            <FileText className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">{stats.filesManaged}</div>
                            <p className="text-xs text-muted-foreground">Arquivos do Alfred</p>
                        </CardContent>
                    </Card>
                </div>

                {/* Main Dashboard */}
                <Card className="shadow-lg">
                    <CardContent className="p-6">
                        <Tabs defaultValue="messages" className="w-full">
                            <TabsList className="grid w-full grid-cols-5"> {/* Alterado para 5 colunas */}
                                <TabsTrigger value="messages" className="flex items-center gap-2">
                                    <MessageCircle className="w-4 h-4" />
                                    Mensagens
                                </TabsTrigger>
                                <TabsTrigger value="files" className="flex items-center gap-2">
                                    <Upload className="w-4 h-4" />
                                    Arquivos Alfred
                                </TabsTrigger>
                                {/* Nova aba para o AlfredControlPanel */}
                                <TabsTrigger value="alfred-control" className="flex items-center gap-2">
                                    <Bot className="w-4 h-4" />
                                    Controle Alfred
                                </TabsTrigger>
                                <TabsTrigger value="activity" className="flex items-center gap-2">
                                    <Activity className="w-4 h-4" />
                                    Atividade
                                </TabsTrigger>
                                <TabsTrigger value="config" className="flex items-center gap-2">
                                    <Settings className="w-4 h-4" />
                                    Configurações
                                </TabsTrigger>
                            </TabsList>

                            <TabsContent value="messages" className="mt-6">
                                <MessagePanel />
                            </TabsContent>

                            <TabsContent value="files" className="mt-6">
                                <FileManager />
                            </TabsContent>

                            {/* Conteúdo para o AlfredControlPanel */}
                            <TabsContent value="alfred-control" className="mt-6">
                                <AlfredControlPanel API_BASE_URL={API_BASE_URL} />
                            </TabsContent>

                            <TabsContent value="activity" className="mt-6">
                                <ActivityMonitor />
                            </TabsContent>

                            <TabsContent value="config" className="mt-6">
                                <ConfigPanel />
                            </TabsContent>
                        </Tabs>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
};

export default Index;