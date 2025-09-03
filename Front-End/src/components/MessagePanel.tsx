import React, { useState, useEffect } from 'react'; // Import useEffect
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { MessageCircle, Clock, User, Loader2 } from "lucide-react"; // Import Loader2
import { useToast } from "@/hooks/use-toast"; // Import useToast

import { fetchRecentMessages, RecentMessage } from '@/lib/api'; // Import the new function and interface

const MessagePanel = () => {
    // Initialize with an empty array, data will be fetched
    const [recentMessages, setRecentMessages] = useState<RecentMessage[]>([]);
    const [loading, setLoading] = useState(true); // Add loading state
    const [error, setError] = useState<string | null>(null); // Add error state
    const { toast } = useToast();

    // Fetch messages on component mount
    useEffect(() => {
        const loadRecentMessages = async () => {
            setLoading(true);
            setError(null);
            try {
                const messages = await fetchRecentMessages();
                setRecentMessages(messages);
            } catch (err: any) {
                setError(err.message || "Failed to load recent messages.");
                toast({
                    title: "Erro ao carregar mensagens",
                    description: err.message || "Não foi possível carregar as mensagens recentes.",
                    variant: "destructive"
                });
            } finally {
                setLoading(false);
            }
        };

        loadRecentMessages();
        // You might want to set up an interval for refreshing data periodically
        // const intervalId = setInterval(loadRecentMessages, 30000); // Refresh every 30 seconds
        // return () => clearInterval(intervalId); // Cleanup on unmount
    }, []); // Empty dependency array means this runs once on mount

    const getStatusBadge = (status: string) => {
        const variants = {
            pending: { variant: "destructive", text: "Pendente" },
            responded: { variant: "secondary", text: "Respondido" },
            resolved: { variant: "default", text: "Resolvido" }
        };

        const config = variants[status as keyof typeof variants] || variants.pending;
        return <Badge variant={config.variant as any}>{config.text}</Badge>;
    };

    return (
        <div className="space-y-6">
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <MessageCircle className="w-5 h-5" />
                        Mensagens Recentes
                    </CardTitle>
                    <CardDescription>
                        Últimas interações do agente Alfred com os usuários
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    {loading ? (
                        <div className="flex items-center justify-center h-24">
                            <Loader2 className="mr-2 h-6 w-6 animate-spin" /> Carregando mensagens...
                        </div>
                    ) : error ? (
                        <div className="text-red-500 text-center py-4">{error}</div>
                    ) : recentMessages.length === 0 ? (
                        <p className="text-center text-muted-foreground py-4">Nenhuma mensagem recente encontrada.</p>
                    ) : (
                        <div className="space-y-4">
                            {recentMessages.map((msg, index) => (
                                <div key={msg.id}>
                                    <div className="flex items-start justify-between space-x-4">
                                        <div className="flex-1 space-y-2">
                                            <div className="flex items-center gap-2">
                                                <User className="w-4 h-4 text-muted-foreground" />
                                                <span className="font-medium">{msg.user}</span>
                                                <span className="text-sm text-muted-foreground">{msg.userId}</span>
                                                {getStatusBadge(msg.status)}
                                            </div>
                                            <p className="text-sm text-gray-600">{msg.message}</p>
                                            <div className="flex items-center gap-1 text-xs text-muted-foreground">
                                                <Clock className="w-3 h-3" />
                                                {new Date(msg.timestamp).toLocaleString()} {/* Format timestamp for display */}
                                            </div>
                                        </div>
                                    </div>
                                    {index < recentMessages.length - 1 && <Separator className="mt-4" />}
                                </div>
                            ))}
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
};

export default MessagePanel;