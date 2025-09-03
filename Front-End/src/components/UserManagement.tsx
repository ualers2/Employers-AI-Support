
import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { useToast } from "@/hooks/use-toast";
import { Users, Ban, UserCheck, Search, AlertTriangle } from "lucide-react";

const UserManagement = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [userIdToBan, setUserIdToBan] = useState('');
  const { toast } = useToast();

  const [users] = useState([
    {
      id: 1,
      name: "João Silva",
      username: "@joaosilva",
      userId: "123456789",
      status: "active",
      lastSeen: "2024-01-15 14:30",
      messageCount: 45
    },
    {
      id: 2,
      name: "Maria Santos",
      username: "@mariasantos",
      userId: "987654321",
      status: "banned",
      lastSeen: "2024-01-14 10:15",
      messageCount: 12
    },
    {
      id: 3,
      name: "Carlos Oliveira",
      username: "@carlosoliveira",
      userId: "456789123",
      status: "active",
      lastSeen: "2024-01-15 15:45",
      messageCount: 78
    }
  ]);

  const handleBanUser = async () => {
    if (!userIdToBan.trim()) {
      toast({
        title: "Erro",
        description: "Digite o ID do usuário para banir",
        variant: "destructive"
      });
      return;
    }

    console.log('Banindo usuário:', userIdToBan);
    
    toast({
      title: "Usuário banido!",
      description: `Usuário ${userIdToBan} foi banido do canal`,
    });

    setUserIdToBan('');
  };

  const handleUnbanUser = (userId: string) => {
    console.log('Removendo ban do usuário:', userId);
    
    toast({
      title: "Ban removido!",
      description: `Ban do usuário ${userId} foi removido`,
    });
  };

  const filteredUsers = users.filter(user => 
    user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.userId.includes(searchTerm)
  );

  const getStatusBadge = (status: string) => {
    return status === 'active' 
      ? <Badge variant="default">Ativo</Badge>
      : <Badge variant="destructive">Banido</Badge>;
  };

  return (
    <div className="space-y-6">
      {/* Ban User Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Ban className="w-5 h-5" />
            Gerenciar Banimentos
          </CardTitle>
          <CardDescription>
            Banir ou desbanir usuários do canal
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              placeholder="ID do usuário (ex: 123456789)"
              value={userIdToBan}
              onChange={(e) => setUserIdToBan(e.target.value)}
              className="flex-1"
            />
            <Button onClick={handleBanUser} variant="destructive">
              <Ban className="w-4 h-4 mr-2" />
              Banir
            </Button>
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <AlertTriangle className="w-4 h-4" />
            Use com cuidado. Usuários banidos não poderão mais interagir no canal.
          </div>
        </CardContent>
      </Card>

      {/* User List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="w-5 h-5" />
            Lista de Usuários
          </CardTitle>
          <CardDescription>
            Visualize e gerencie todos os usuários do canal
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
              <Input
                placeholder="Buscar usuários..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>

            {/* User List */}
            <div className="space-y-4">
              {filteredUsers.map((user, index) => (
                <div key={user.id}>
                  <div className="flex items-center justify-between space-x-4">
                    <div className="flex-1 space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{user.name}</span>
                        <span className="text-sm text-muted-foreground">{user.username}</span>
                        {getStatusBadge(user.status)}
                      </div>
                      <div className="flex items-center gap-4 text-xs text-muted-foreground">
                        <span>ID: {user.userId}</span>
                        <span>Mensagens: {user.messageCount}</span>
                        <span>Último acesso: {user.lastSeen}</span>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      {user.status === 'banned' ? (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleUnbanUser(user.userId)}
                        >
                          <UserCheck className="w-4 h-4 mr-1" />
                          Desbanir
                        </Button>
                      ) : (
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => handleBanUser()}
                        >
                          <Ban className="w-4 h-4 mr-1" />
                          Banir
                        </Button>
                      )}
                    </div>
                  </div>
                  {index < filteredUsers.length - 1 && <Separator className="mt-4" />}
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default UserManagement;
