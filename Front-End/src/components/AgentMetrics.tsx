import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { 
  Bot, 
  Activity, 
  Clock, 
  Zap,
  TrendingUp,
  Users,
  Settings,
  ExternalLink,
  Loader2,
  AlertCircle,
  CheckCircle,
  XCircle,
  Image,
  Calendar,
  CheckSquare
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface AgentMetrics {
  totalAgents: number;
  onlineAgents: number;
  offlineAgents: number;
  degradedAgents: number;
  alfredResponses24h: number;
  alfredResponsesChangePercentage: number;
  avgResponseTime: string;
  uptimePercentage: number;
  platformStats: Array<{
    platform: string;
    messageCount: number;
  }>;
  mostActiveAgents: Array<{
    platform: string;
    status: string;
    lastUpdate: string | null;
    containerName: string;
    imageName: string;
  }>;
}

interface Agent {
  id: number;
  platform: string;
  status: string;
  lastUpdate: string | null;
  containerName: string;
  imageName: string;
  name: string;
  area: string;
  photo: string;
  workingHours: string;
  tasks: string[];
}

const AgentMetrics = () => {
  const [metrics, setMetrics] = useState<AgentMetrics>({
    totalAgents: 0,
    onlineAgents: 0,
    offlineAgents: 0,
    degradedAgents: 0,
    alfredResponses24h: 0,
    alfredResponsesChangePercentage: 0,
    avgResponseTime: "0s",
    uptimePercentage: 0,
    platformStats: [],
    mostActiveAgents: []
  });

  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingAgents, setLoadingAgents] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);

  const { toast } = useToast();
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api';
  const userId = localStorage.getItem('user_email') || '';

  const fetchAgentMetrics = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/agents/metrics?user_id=${encodeURIComponent(userId)}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setMetrics(data);
    } catch (err: any) {
      console.error('Erro ao buscar métricas de agentes:', err);
      setError('Erro ao carregar métricas de agentes');
      toast({
        title: "Erro de Conexão",
        description: "Não foi possível carregar as métricas de agentes.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchAgentsList = async () => {
    try {
      setLoadingAgents(true);
      const response = await fetch(`${API_BASE_URL}/agents/list?user_id=${encodeURIComponent(userId)}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setAgents(data.agents);
    } catch (err: any) {
      console.error('Erro ao buscar lista de agentes:', err);
      toast({
        title: "Erro",
        description: "Não foi possível carregar a lista de agentes.",
        variant: "destructive",
      });
    } finally {
      setLoadingAgents(false);
    }
  };

  useEffect(() => {
    fetchAgentMetrics();
    fetchAgentsList();
  }, []);

  const getStatusBadge = (status: string) => {
    const configs = {
      online: { variant: "default", text: "Online", icon: CheckCircle, color: "text-green-600" },
      offline: { variant: "secondary", text: "Offline", icon: XCircle, color: "text-gray-600" },
      degraded: { variant: "destructive", text: "Degradado", icon: AlertCircle, color: "text-red-600" }
    };
    
    const config = configs[status as keyof typeof configs] || configs.offline;
    const Icon = config.icon;
    
    return (
      <Badge variant={config.variant as any} className="flex items-center gap-1">
        <Icon className="w-3 h-3" />
        {config.text}
      </Badge>
    );
  };

  const formatPercentage = (value: number) => {
    if (value > 0) return `+${value}%`;
    if (value < 0) return `${value}%`;
    return "0%";
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "Nunca";
    return new Date(dateString).toLocaleString('pt-BR');
  };

  if (error) {
    return (
      <div className="flex justify-center items-center h-48 text-red-500">
        <AlertCircle className="h-6 w-6 mr-2" />
        <span>{error}</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Métricas dos Agentes */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total de Agentes</p>
                {loading ? (
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                ) : (
                  <p className="text-2xl font-bold">{metrics.totalAgents}</p>
                )}
              </div>
              <Bot className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Agentes Online</p>
                {loading ? (
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                ) : (
                  <div>
                    <p className="text-2xl font-bold text-green-600">{metrics.onlineAgents}</p>
                    <p className="text-xs text-muted-foreground">
                      {metrics.uptimePercentage}% uptime
                    </p>
                  </div>
                )}
              </div>
              <CheckCircle className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Respostas 24h</p>
                {loading ? (
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                ) : (
                  <div>
                    <p className="text-2xl font-bold">{metrics.alfredResponses24h}</p>
                    <p className="text-xs text-muted-foreground">
                      {formatPercentage(metrics.alfredResponsesChangePercentage)} desde ontem
                    </p>
                  </div>
                )}
              </div>
              <Activity className="h-8 w-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Tempo Médio</p>
                {loading ? (
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                ) : (
                  <p className="text-2xl font-bold">{metrics.avgResponseTime}</p>
                )}
                <p className="text-xs text-muted-foreground">Resposta</p>
              </div>
              <Clock className="h-8 w-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Lista de Agentes */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="w-5 h-5" />
            Controle de Agentes
          </CardTitle>
          <CardDescription>
            Gerencie e monitore todos os agentes em operação
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {loadingAgents ? (
              <div className="flex justify-center items-center h-32">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                <span className="ml-2 text-muted-foreground">Carregando agentes...</span>
              </div>
            ) : agents.length === 0 ? (
              <div className="flex justify-center items-center h-32 text-muted-foreground">
                <span>Nenhum agente encontrado.</span>
              </div>
            ) : (
              agents.map((agent) => (
                <div key={agent.id} className="p-4 border rounded-lg hover:bg-gray-50 transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                        <Bot className="w-6 h-6 text-white" />
                      </div>
                      <div>
                        <div className="flex items-center gap-3 mb-1">
                          <span className="font-semibold">{agent.name}</span>
                          {getStatusBadge(agent.status)}
                        </div>
                        <div className="flex items-center gap-3 text-sm text-muted-foreground">
                          <span>Área: {agent.area}</span>
                          <span>•</span>
                          <span>Plataforma: {agent.platform}</span>
                        </div>
                      </div>
                    </div>
                    
                    <Dialog>
                      <DialogTrigger asChild>
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => setSelectedAgent(agent)}
                        >
                          <Settings className="w-4 h-4 mr-2" />
                          Detalhes
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="sm:max-w-[500px]">
                        <DialogHeader>
                          <DialogTitle className="flex items-center gap-3">
                            <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                              <Bot className="w-8 h-8 text-white" />
                            </div>
                            {selectedAgent?.name}
                          </DialogTitle>
                          <DialogDescription>
                            Informações detalhadas e configurações do agente
                          </DialogDescription>
                        </DialogHeader>
                        
                        {selectedAgent && (
                          <div className="space-y-6">
                            {/* Status e Info Básica */}
                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <label className="text-sm font-medium text-muted-foreground">Status</label>
                                <div className="mt-1">
                                  {getStatusBadge(selectedAgent.status)}
                                </div>
                              </div>
                              <div>
                                <label className="text-sm font-medium text-muted-foreground">Área de Atuação</label>
                                <p className="text-sm mt-1">{selectedAgent.area}</p>
                              </div>
                            </div>

                            {/* Horários de Trabalho */}
                            <div>
                              <label className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                                <Calendar className="w-4 h-4" />
                                Horários de Trabalho
                              </label>
                              <p className="text-sm mt-1 p-2 bg-gray-50 rounded">{selectedAgent.workingHours}</p>
                            </div>

                            {/* Tarefas */}
                            <div>
                              <label className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                                <CheckSquare className="w-4 h-4" />
                                Tarefas Principais
                              </label>
                              <div className="mt-2 space-y-2">
                                {selectedAgent.tasks.map((task, index) => (
                                  <div key={index} className="flex items-start gap-2 text-sm">
                                    <CheckSquare className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                                    <span>{task}</span>
                                  </div>
                                ))}
                              </div>
                            </div>

                            {/* Informações Técnicas */}
                            <div className="border-t pt-4">
                              <label className="text-sm font-medium text-muted-foreground">Informações Técnicas</label>
                              <div className="mt-2 space-y-2 text-xs text-muted-foreground">
                                <div>Container: {selectedAgent.containerName}</div>
                                <div>Imagem: {selectedAgent.imageName}</div>
                                <div>Última Atualização: {formatDate(selectedAgent.lastUpdate)}</div>
                                <div>Plataforma: {selectedAgent.platform}</div>
                              </div>
                            </div>
                          </div>
                        )}

                        <DialogFooter>
                          <Button variant="outline">
                            <Settings className="w-4 h-4 mr-2" />
                            Configurar
                          </Button>
                          <Button>
                            <Activity className="w-4 h-4 mr-2" />
                            Ver Logs
                          </Button>
                        </DialogFooter>
                      </DialogContent>
                    </Dialog>
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>

      {/* Atividade por Plataforma */}
      {metrics.platformStats.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5" />
              Atividade por Plataforma (24h)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {metrics.platformStats.map((platform, index) => (
                <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                      <Bot className="w-4 h-4 text-blue-600" />
                    </div>
                    <span className="font-medium capitalize">{platform.platform}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-lg font-bold">{platform.messageCount}</span>
                    <span className="text-sm text-muted-foreground">mensagens</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default AgentMetrics;