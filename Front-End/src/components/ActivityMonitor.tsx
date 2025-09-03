// src/components/ActivityMonitor.tsx (or wherever your component is located)

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Activity, Clock, MessageCircle, Users, Ban, Upload, AlertCircle, Loader2 } from "lucide-react"; // Added Loader2 for loading state
import { fetchRealtimeMetrics, fetchActivityLog, clearActivityLog, Activity as ActivityType } from "@/lib/api"; // Import from your new api.ts

const ActivityMonitor = () => {
    const [realtimeMetrics, setRealtimeMetrics] = useState({
        messagesPerHour: 0,
        onlineUsers: 0,
        averageResponseTime: 0
    });
    const [activities, setActivities] = useState<ActivityType[]>([]);
    const [loadingMetrics, setLoadingMetrics] = useState(true);
    const [loadingActivities, setLoadingActivities] = useState(true);
    const [clearingLog, setClearingLog] = useState(false);
    const [errorMetrics, setErrorMetrics] = useState<string | null>(null);
    const [errorActivities, setErrorActivities] = useState<string | null>(null);

    // Fetch Real-time Metrics
    useEffect(() => {
        const getMetrics = async () => {
            setLoadingMetrics(true);
            setErrorMetrics(null);
            try {
                const data = await fetchRealtimeMetrics();
                setRealtimeMetrics(data);
            } catch (error) {
                console.error("Failed to fetch real-time metrics:", error);
                setErrorMetrics("Failed to load real-time metrics.");
            } finally {
                setLoadingMetrics(false);
            }
        };
        getMetrics();

        // Optional: Polling for real-time metrics (e.g., every 15 seconds)
        const intervalId = setInterval(getMetrics, 15000); 
        return () => clearInterval(intervalId); // Cleanup on unmount
    }, []);

    // Fetch Activity Log
    useEffect(() => {
        const getActivities = async () => {
            setLoadingActivities(true);
            setErrorActivities(null);
            try {
                // Fetching the first 20 recent activities for the log
                const data = await fetchActivityLog(20); 
                setActivities(data.activities);
            } catch (error) {
                console.error("Failed to fetch activity log:", error);
                setErrorActivities("Failed to load activity log.");
            } finally {
                setLoadingActivities(false);
            }
        };
        getActivities();

        // Optional: Polling for activity log updates (e.g., every 30 seconds)
        const intervalId = setInterval(getActivities, 30000); 
        return () => clearInterval(intervalId); // Cleanup on unmount
    }, []);

    const handleClearLog = async () => {
        if (!window.confirm("Tem certeza que deseja limpar o log de atividades mais antigas? Esta ação é irreversível.")) {
            return;
        }

        setClearingLog(true);
        try {
            // Clear activities older than, for example, 30 days
            const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString();
            const result = await clearActivityLog(thirtyDaysAgo);
            console.log("Log cleared:", result);
            alert(`Log limpo com sucesso! ${result.deletedCount} registros excluídos.`);
            // After clearing, refetch the activities to update the display
            const data = await fetchActivityLog(20);
            setActivities(data.activities);
        } catch (error: any) {
            console.error("Failed to clear activity log:", error);
            alert(`Erro ao limpar o log: ${error.message || "Tente novamente mais tarde."}`);
        } finally {
            setClearingLog(false);
        }
    };

    const getActivityIcon = (type: string) => {
        const icons = {
            message: MessageCircle,
            ban: Ban,
            file: Upload,
            response: MessageCircle, // Alfred's responses are also messages
            error: AlertCircle,
            info: Activity, // Default for 'info' type if any
            unban: Users, // Assuming unban is related to user management
        };
        const Icon = icons[type as keyof typeof icons] || Activity;
        return <Icon className="w-4 h-4" />;
    };

    const getStatusBadge = (status: string) => {
        const variants = {
            success: { variant: "default", text: "Sucesso" },
            warning: { variant: "secondary", text: "Aviso" },
            info: { variant: "outline", text: "Info" },
            error: { variant: "destructive", text: "Erro" }
        };
        
        const config = variants[status as keyof typeof variants] || variants.info;
        return <Badge variant={config.variant as any}>{config.text}</Badge>;
    };

    const getActivityColor = (type: string) => {
        const colors = {
            message: "text-blue-600",
            ban: "text-red-600",
            file: "text-green-600",
            response: "text-purple-600",
            error: "text-red-600",
            info: "text-gray-600",
            unban: "text-yellow-600",
        };
        return colors[type as keyof typeof colors] || "text-gray-600";
    };

    return (
        <div className="space-y-6">
            {/* Real-time Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm font-medium text-muted-foreground">Mensagens/hora</p>
                                {loadingMetrics ? (
                                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                                ) : errorMetrics ? (
                                    <p className="text-red-500 text-sm">{errorMetrics}</p>
                                ) : (
                                    <p className="text-2xl font-bold">{realtimeMetrics.messagesPerHour}</p>
                                )}
                            </div>
                            <MessageCircle className="h-8 w-8 text-muted-foreground" />
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm font-medium text-muted-foreground">Usuários Online</p>
                                {loadingMetrics ? (
                                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                                ) : errorMetrics ? (
                                    <p className="text-red-500 text-sm">{errorMetrics}</p>
                                ) : (
                                    <p className="text-2xl font-bold">{realtimeMetrics.onlineUsers}</p>
                                )}
                            </div>
                            <Users className="h-8 w-8 text-muted-foreground" />
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm font-medium text-muted-foreground">Tempo de Resposta</p>
                                {loadingMetrics ? (
                                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                                ) : errorMetrics ? (
                                    <p className="text-red-500 text-sm">{errorMetrics}</p>
                                ) : (
                                    <p className="text-2xl font-bold">{realtimeMetrics.averageResponseTime?.toFixed(2)}s</p>
                                )}
                            </div>
                            <Clock className="h-8 w-8 text-muted-foreground" />
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Activity Log */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Activity className="w-5 h-5" />
                        Log de Atividades
                    </CardTitle>
                    <CardDescription>
                        Monitoramento em tempo real de todas as atividades do bot
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                        <div className="flex justify-between items-center">
                            <h3 className="text-sm font-medium">Atividades Recentes</h3>
                            <Button 
                                variant="outline" 
                                size="sm" 
                                onClick={handleClearLog} 
                                disabled={clearingLog}
                            >
                                {clearingLog ? (
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                ) : (
                                    "Limpar Log"
                                )}
                            </Button>
                        </div>
                        
                        <div className="space-y-4 max-h-96 overflow-y-auto pr-2"> {/* Added pr-2 for scrollbar spacing */}
                            {loadingActivities ? (
                                <div className="flex justify-center items-center h-48">
                                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                                    <span className="ml-2 text-muted-foreground">Carregando atividades...</span>
                                </div>
                            ) : errorActivities ? (
                                <div className="flex justify-center items-center h-48 text-red-500">
                                    <AlertCircle className="h-6 w-6 mr-2" />
                                    <span>{errorActivities}</span>
                                </div>
                            ) : activities.length === 0 ? (
                                <div className="flex justify-center items-center h-48 text-muted-foreground">
                                    <span>Nenhuma atividade encontrada.</span>
                                </div>
                            ) : (
                                activities.map((activity, index) => (
                                    <div key={activity.id}>
                                        <div className="flex items-start space-x-4">
                                            <div className={`${getActivityColor(activity.type)} mt-1`}>
                                                {getActivityIcon(activity.type)}
                                            </div>
                                            <div className="flex-1 space-y-1">
                                                <div className="flex items-center justify-between">
                                                    <div className="flex items-center gap-2">
                                                        <span className="font-medium">{activity.action}</span>
                                                        {getStatusBadge(activity.status)}
                                                    </div>
                                                    <div className="flex items-center gap-1 text-xs text-muted-foreground">
                                                        <Clock className="w-3 h-3" />
                                                        {new Date(activity.timestamp).toLocaleString()}
                                                    </div>
                                                </div>
                                                <p className="text-sm text-muted-foreground">
                                                    <span className="font-medium">{activity.user}</span> - {activity.details}
                                                </p>
                                            </div>
                                        </div>
                                        {index < activities.length - 1 && <Separator className="mt-4" />}
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

export default ActivityMonitor;