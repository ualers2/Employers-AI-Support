import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { 
  BarChart3, 
  Upload, 
  Shield, 
  Ticket, 
  Star,
  ExternalLink
} from "lucide-react";
import multiChannelImage from "@/assets/multi-channel-support.jpg";

import { CONTACTS } from "@/constants/contacts";

const apiDocs = CONTACTS.find(contact => contact.name === "Documentação API");

const features = [
  {
    category: "Gerenciamento e Monitoramento",
    items: [
      "Suporte 24/7 em Telegram, Discord e WhatsApp",
      "Dashboards de performance com métricas importantes", 
      "Gerenciamento centralizado via interface web",
      "Controle de agentes com endpoints Docker",
      "Log e auditoria para monitoramento completo"
    ],
    icon: BarChart3,
    color: "text-tech-blue"
  },
  {
    category: "Base de Conhecimento",
    items: [
      "Upload facilitado com drag-and-drop",
      "Suporte para .md, .txt, .csv, .json",
      "Armazenamento persistente em PostgreSQL",
      "Histórico de interações para auditoria"
    ],
    icon: Upload,
    color: "text-success-green"
  },
  {
    category: "IA e Ferramentas Avançadas",
    items: [
      "Moderação inteligente com IA",
      "Criação automática de tickets de suporte",
      "Geração de boletins técnicos especializados",
      "Coleta de CSAT (satisfação do cliente)",
      "Fechamento automático com feedback"
    ],
    icon: Shield,
    color: "text-accent"
  }
];

const apiEndpoints = [
  { method: "GET", endpoint: "/api/config", description: "Busca configurações do bot" },
  { method: "POST", endpoint: "/api/alfred-files/upload", description: "Upload da base de conhecimento" },
  { method: "GET", endpoint: "/api/messages/recent", description: "Mensagens e interações recentes" },
  { method: "GET", endpoint: "/api/metrics/realtime", description: "Métricas em tempo real" },
  { method: "POST", endpoint: "/api/users/{userId}/ban", description: "Banimento de usuários" }
];

const MVPSection = () => {
  return (
    <section id="mvp" className="py-20 lg:py-32">
      <div className="container max-w-screen-xl">
        <div className="text-center space-y-4 mb-16">
          <Badge className="bg-accent/10 text-accent border-accent/20">
            MVP Características
          </Badge>
          <h2 className="text-3xl lg:text-5xl font-bold">
            <span className="bg-gradient-primary bg-clip-text text-transparent">MVP Robusto</span> e Escalável
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            Base sólida para expansão futura com funcionalidades empresariais completas.
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid gap-8 lg:grid-cols-3 mb-16">
          {features.map((feature, index) => {
            const IconComponent = feature.icon;
            return (
              <Card key={index} className="group hover:shadow-ai transition-all duration-300 border-border/50 hover:border-primary/20">
                <CardHeader className="space-y-4">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-card border border-border/50">
                      <IconComponent className={`h-5 w-5 ${feature.color}`} />
                    </div>
                    <CardTitle className="text-lg group-hover:text-primary transition-colors">
                      {feature.category}
                    </CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-3">
                    {feature.items.map((item, itemIndex) => (
                      <li key={itemIndex} className="flex items-start gap-2 text-sm text-muted-foreground">
                        <div className="h-1.5 w-1.5 rounded-full bg-primary mt-2 flex-shrink-0" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Multi-channel Image */}
        <div className="grid gap-12 lg:grid-cols-2 items-center mb-16">
          <div className="space-y-6">
            <h3 className="text-2xl lg:text-3xl font-bold">
              Integração <span className="text-accent">Multi-canal</span>
            </h3>
            <p className="text-muted-foreground leading-relaxed">
              Centralize o atendimento em uma única plataforma, gerenciando 
              simultaneamente Telegram, Discord e WhatsApp com a mesma eficiência e qualidade.
            </p>
            <div className="flex flex-wrap gap-3">
              <Badge className="bg-primary/10 text-primary">Telegram</Badge>
              <Badge className="bg-accent/10 text-accent">Discord</Badge>
              <Badge className="bg-success-green/10 text-success-green">WhatsApp</Badge>
            </div>
          </div>
          <div className="relative">
            <img 
              src={multiChannelImage} 
              alt="Integração multi-canal mostrando Telegram, Discord e WhatsApp"
              className="w-full h-auto rounded-xl shadow-ai border border-border/50"
            />
          </div>
        </div>

        {/* API Endpoints */}
        <Card className="border-border/50">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Ticket className="h-5 w-5 text-primary" />
                  API RESTful Completa
                </CardTitle>
                <p className="text-muted-foreground mt-2">
                  Backend robusto em Python com endpoints especializados
                </p>
              </div>

              <Button
                as="a"
                href={apiDocs?.href}
                target="_blank"
                rel="noopener noreferrer"
                variant="outline"
                size="sm"
              >
                <ExternalLink className="h-4 w-4 mr-2" />
                Documentação API
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 md:grid-cols-2">
              {apiEndpoints.map((endpoint, index) => (
                <div key={index} className="flex items-center gap-3 p-3 rounded-lg bg-secondary/30 border border-border/30">
                  <Badge 
                    className={`text-xs font-mono ${
                      endpoint.method === 'GET' ? 'bg-tech-blue/10 text-tech-blue' : 'bg-success-green/10 text-success-green'
                    }`}
                  >
                    {endpoint.method}
                  </Badge>
                  <div className="flex-1 min-w-0">
                    <code className="text-xs font-mono text-foreground block truncate">
                      {endpoint.endpoint}
                    </code>
                    <p className="text-xs text-muted-foreground mt-1">
                      {endpoint.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </section>
  );
};

export default MVPSection;