import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { 
  Ticket, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  Mail, 
  Copy, 
  ExternalLink,
  Loader2,
  AlertCircle
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface TicketData {
  id: number;
  ticketId: string;
  userEmail: string;
  issueDescription: string;
  status: 'open' | 'closed' | 'escalated';
  csat: string;
  timestampOpen: string;
  timestampClose?: string;
  timestampEscalated?: string;
  escalationReason?: string;
  notes: string[];
}

interface TicketMetrics {
  ticketsOpen: number;
  ticketsClosed: number;
  ticketsEscalated: number;
  totalTickets: number;
  ticketsOpenChangePercentage: number;
  ticketsClosedChangePercentage: number;
  ticketsEscalatedChangePercentage: number;
}

const TicketMetrics = () => {
  const [metrics, setMetrics] = useState<TicketMetrics>({
    ticketsOpen: 0,
    ticketsClosed: 0,
    ticketsEscalated: 0,
    totalTickets: 0,
    ticketsOpenChangePercentage: 0,
    ticketsClosedChangePercentage: 0,
    ticketsEscalatedChangePercentage: 0
  });
  
  const [tickets, setTickets] = useState<TicketData[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingTickets, setLoadingTickets] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTicket, setSelectedTicket] = useState<TicketData | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('all');
    const [emailMessage, setEmailMessage] = useState("");

  const { toast } = useToast();
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api';
  const userId = localStorage.getItem('user_email') || '';

  const fetchTicketMetrics = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/tickets/metrics?user_id=${encodeURIComponent(userId)}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setMetrics(data);
    } catch (err: any) {
      console.error('Erro ao buscar métricas de tickets:', err);
      setError('Erro ao carregar métricas de tickets');
      toast({
        title: "Erro de Conexão",
        description: "Não foi possível carregar as métricas de tickets.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchTickets = async (status?: string) => {
    try {
      setLoadingTickets(true);
      const statusParam = status && status !== 'all' ? `&status=${status}` : '';
      const response = await fetch(`${API_BASE_URL}/tickets?user_id=${encodeURIComponent(userId)}${statusParam}&limit=50`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setTickets(data.tickets);
    } catch (err: any) {
      console.error('Erro ao buscar tickets:', err);
      toast({
        title: "Erro",
        description: "Não foi possível carregar a lista de tickets.",
        variant: "destructive",
      });
    } finally {
      setLoadingTickets(false);
    }
  };

  useEffect(() => {
    fetchTicketMetrics();
    fetchTickets();
  }, []);

  const handleStatusFilterChange = (status: string) => {
    setStatusFilter(status);
    fetchTickets(status);
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      toast({
        title: "Copiado!",
        description: "Email copiado para a área de transferência.",
      });
    } catch (err) {
      console.error('Erro ao copiar:', err);
      toast({
        title: "Erro",
        description: "Não foi possível copiar o email.",
        variant: "destructive",
      });
    }
  };
  const reopenTicket = async (ticketId: number) => {
    try {
        const response = await fetch(`${API_BASE_URL}/tickets/reopen/${ticketId}`, {
        method: 'POST',
        });

        if (!response.ok) throw new Error('Falha ao reabrir o ticket');

        toast({
        title: "Ticket reaberto",
        description: `O ticket #${ticketId} foi reaberto com sucesso.`,
        });

        // Atualiza lista de tickets e métricas
        fetchTicketMetrics();
        fetchTickets(statusFilter);

    } catch (err: any) {
        console.error(err);
        toast({
        title: "Erro",
        description: "Não foi possível reabrir o ticket.",
        variant: "destructive",
        });
    }
    };

  const closeTicket = async (ticketId: number) => {
    try {
        const response = await fetch(`${API_BASE_URL}/tickets/close/${ticketId}`, {
        method: 'POST',
        });

        if (!response.ok) throw new Error('Falha ao fechar o ticket');

        toast({
        title: "Ticket fechado",
        description: `O ticket #${ticketId} foi fechado com sucesso.`,
        });

        // Atualiza lista de tickets e métricas
        fetchTicketMetrics();
        fetchTickets(statusFilter);

    } catch (err: any) {
        console.error(err);
        toast({
        title: "Erro",
        description: "Não foi possível fechar o ticket.",
        variant: "destructive",
        });
    }
    };

    const sendEmail = async (ticketId: number) => {
    try {
        const response = await fetch(`${API_BASE_URL}/tickets/send-email/${ticketId}`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: emailMessage }),
        });

        if (!response.ok) throw new Error("Falha ao enviar email");

        toast({
        title: "Email enviado",
        description: `Mensagem enviada com sucesso para o usuário.`,
        });

        setEmailMessage(""); // limpa input após envio
    } catch (err) {
        console.error(err);
        toast({
        title: "Erro",
        description: "Não foi possível enviar o email.",
        variant: "destructive",
        });
    }
    };


  const getStatusBadge = (status: string) => {
    const configs = {
      open: { variant: "default", text: "Aberto", icon: Clock },
      closed: { variant: "outline", text: "Fechado", icon: CheckCircle },
      escalated: { variant: "destructive", text: "Escalado", icon: AlertTriangle }
    };
    
    const config = configs[status as keyof typeof configs] || configs.open;
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

  const formatDate = (dateString: string) => {
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
      {/* Métricas de Tickets */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Tickets Abertos</p>
                {loading ? (
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                ) : (
                  <div>
                    <p className="text-2xl font-bold text-orange-600">{metrics.ticketsOpen}</p>
                    <p className="text-xs text-muted-foreground">
                      {formatPercentage(metrics.ticketsOpenChangePercentage)} desde ontem
                    </p>
                  </div>
                )}
              </div>
              <Clock className="h-8 w-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Tickets Fechados</p>
                {loading ? (
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                ) : (
                  <div>
                    <p className="text-2xl font-bold text-green-600">{metrics.ticketsClosed}</p>
                    <p className="text-xs text-muted-foreground">
                      {formatPercentage(metrics.ticketsClosedChangePercentage)} desde ontem
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
                <p className="text-sm font-medium text-muted-foreground">Tickets Escalados</p>
                {loading ? (
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                ) : (
                  <div>
                    <p className="text-2xl font-bold text-red-600">{metrics.ticketsEscalated}</p>
                    <p className="text-xs text-muted-foreground">
                      {formatPercentage(metrics.ticketsEscalatedChangePercentage)} desde ontem
                    </p>
                  </div>
                )}
              </div>
              <AlertTriangle className="h-8 w-8 text-red-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total de Tickets</p>
                {loading ? (
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                ) : (
                  <p className="text-2xl font-bold">{metrics.totalTickets}</p>
                )}
              </div>
              <Ticket className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Lista de Tickets */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Ticket className="w-5 h-5" />
            Lista de Tickets
          </CardTitle>
          <CardDescription>
            Gerencie e visualize todos os tickets de suporte
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Filtros */}
            <div className="flex gap-2">
              <Button
                variant={statusFilter === 'all' ? 'default' : 'outline'}
                size="sm"
                onClick={() => handleStatusFilterChange('all')}
              >
                Todos
              </Button>
              <Button
                variant={statusFilter === 'open' ? 'default' : 'outline'}
                size="sm"
                onClick={() => handleStatusFilterChange('open')}
              >
                Abertos
              </Button>
              <Button
                variant={statusFilter === 'closed' ? 'default' : 'outline'}
                size="sm"
                onClick={() => handleStatusFilterChange('closed')}
              >
                Fechados
              </Button>
              <Button
                variant={statusFilter === 'escalated' ? 'default' : 'outline'}
                size="sm"
                onClick={() => handleStatusFilterChange('escalated')}
              >
                Escalados
              </Button>
            </div>

            {/* Lista */}
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {loadingTickets ? (
                <div className="flex justify-center items-center h-32">
                  <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                  <span className="ml-2 text-muted-foreground">Carregando tickets...</span>
                </div>
              ) : tickets.length === 0 ? (
                <div className="flex justify-center items-center h-32 text-muted-foreground">
                  <span>Nenhum ticket encontrado.</span>
                </div>
              ) : (
                tickets.map((ticket) => (
                  <div key={ticket.id} className="p-4 border rounded-lg hover:bg-gray-50 transition-colors">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <span className="font-mono text-sm text-muted-foreground">#{ticket.ticketId}</span>
                          {getStatusBadge(ticket.status)}
                          <span className="text-sm text-muted-foreground">
                            {ticket.userEmail}
                          </span>
                        </div>
                        <p className="text-sm font-medium mb-1">{ticket.issueDescription}</p>
                        <p className="text-xs text-muted-foreground">
                          Criado em: {formatDate(ticket.timestampOpen)}
                        </p>
                      </div>
                      <div className="flex gap-2 ml-4">
                        <Dialog>
                          <DialogTrigger asChild>
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={() => setSelectedTicket(ticket)}
                            >
                              <ExternalLink className="w-4 h-4" />
                            </Button>
                          </DialogTrigger>
                          <DialogContent className="sm:max-w-[425px]">
                            <DialogHeader>
                              <DialogTitle>Ticket #{selectedTicket?.ticketId}</DialogTitle>
                              <DialogDescription>
                                Opções de ação para este ticket
                              </DialogDescription>
                            </DialogHeader>
                            {selectedTicket && (
                              <div className="space-y-4">
                                <div>
                                  <Label className="text-sm font-medium">Email do Usuário</Label>
                                  <div className="flex items-center gap-2 mt-1">
                                    <Input 
                                      value={selectedTicket.userEmail} 
                                      readOnly 
                                      className="text-sm"
                                    />
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      onClick={() => copyToClipboard(selectedTicket.userEmail)}
                                    >
                                      <Copy className="w-4 h-4" />
                                    </Button>
                                  </div>
                                </div>
                                
                                <div>
                                  <Label className="text-sm font-medium">Descrição do Problema</Label>
                                  <Textarea 
                                    value={selectedTicket.issueDescription}
                                    readOnly
                                    className="mt-1 text-sm"
                                    rows={3}
                                  />
                                </div>

                                <div className="flex items-center gap-2">
                                  <Label className="text-sm font-medium">Status:</Label>
                                  {getStatusBadge(selectedTicket.status)}
                                </div>

                                {selectedTicket.escalationReason && (
                                  <div>
                                    <Label className="text-sm font-medium">Motivo da Escalação</Label>
                                    <Textarea 
                                      value={selectedTicket.escalationReason}
                                      readOnly
                                      className="mt-1 text-sm"
                                      rows={2}
                                    />
                                  </div>
                                )}
                              </div>
                            )}

                            <div>
                            <Label className="text-sm font-medium">Mensagem</Label>
                            <Textarea
                                value={emailMessage}
                                onChange={(e) => setEmailMessage(e.target.value)}
                                placeholder="Digite a mensagem para o usuário..."
                                className="mt-1 text-sm"
                                rows={4}
                            />
                            </div>

                            <DialogFooter>
                                {selectedTicket?.status === "closed" && (
                                    <Button
                                        variant="secondary"
                                        onClick={() => selectedTicket && reopenTicket(selectedTicket.id)}
                                    >
                                        <Clock className="w-4 h-4 mr-2" />
                                        Reabrir Ticket
                                    </Button>
                                )}

                                {selectedTicket?.status === "open" && (
                                    <Button
                                    variant="destructive"
                                    onClick={() => selectedTicket && closeTicket(selectedTicket.id)}
                                    >
                                    <CheckCircle className="w-4 h-4 mr-2" />
                                    Fechar Ticket
                                    </Button>
                                )}

                                <Button
                                onClick={() => selectedTicket && sendEmail(selectedTicket.id)}
                                disabled={!emailMessage}
                                >
                                <Mail className="w-4 h-4 mr-2" />
                                Enviar Email
                                </Button>
                            </DialogFooter>
                          </DialogContent>
                        </Dialog>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default TicketMetrics;