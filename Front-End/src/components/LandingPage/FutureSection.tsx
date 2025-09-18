import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { 
  Sparkles, 
  Users, 
  BarChart, 
  Link, 
  ArrowRight,
  Calendar,
  Target
} from "lucide-react";
import { CONTACTS } from "@/constants/contacts";

// pega só o link do GitHub
const github = CONTACTS.find((c) => c.name === "GitHub Repository");


const roadmapItems = [
  {
    phase: "Fase 2",
    timeline: "Próximos 3 meses",
    icon: Users,
    color: "text-primary",
    title: "Criação de Agentes Personalizados",
    description: "Interface para criar novos agentes com fotos, nomes e áreas de atuação específicas (Suporte, Vendas, Atendimento).",
    features: [
      "Designer de agentes drag-and-drop",
      "Personalização de personalidade e tom",
      "Especialização por área de negócio",
      "Templates pré-configurados"
    ]
  },
  {
    phase: "Fase 3", 
    timeline: "6 meses",
    icon: BarChart,
    color: "text-tech-blue",
    title: "Dashboards de Performance Avançados",
    description: "Métricas detalhadas de consumo de recursos (CPU, memória) e analytics comportamentais dos usuários.",
    features: [
      "Monitoramento de recursos em tempo real",
      "Analytics de conversação avançados",
      "Relatórios de satisfação do cliente",
      "Previsão de demanda com IA"
    ]
  },
  {
    phase: "Fase 4",
    timeline: "9 meses", 
    icon: Link,
    color: "text-accent",
    title: "Integrações Empresariais",
    description: "Expansão das ferramentas para integrar com CRMs, ERPs e outras plataformas empresariais.",
    features: [
      "Integração com Salesforce, HubSpot",
      "Conectores para Slack, Microsoft Teams",
      "APIs para sistemas legados",
      "Webhooks customizáveis"
    ]
  }
];

const marketImpact = [
  {
    metric: "90%",
    label: "Redução no tempo de resposta",
    icon: Target,
    color: "text-success-green"
  },
  {
    metric: "24/7",
    label: "Disponibilidade contínua", 
    icon: Calendar,
    color: "text-primary"
  },
  {
    metric: "∞",
    label: "Escalabilidade ilimitada",
    icon: BarChart,
    color: "text-accent"
  }
];

const FutureSection = () => {
  return (
    <section id="futuro" className="py-20 lg:py-32">
      <div className="container max-w-screen-xl">
        <div className="text-center space-y-4 mb-16">
          <Badge className="bg-accent/10 text-accent border-accent/20">
            <Sparkles className="mr-2 h-3 w-3" />
            Roadmap & Visão
          </Badge>
          <h2 className="text-3xl lg:text-5xl font-bold">
            O <span className="bg-gradient-primary bg-clip-text text-transparent">Futuro</span> do Suporte IA
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            Expandindo as capacidades do MVP para criar a plataforma definitiva de suporte automatizado.
          </p>
        </div>

        {/* Impact Metrics */}
        <div className="grid gap-6 md:grid-cols-3 mb-16">
          {marketImpact.map((impact, index) => {
            const IconComponent = impact.icon;
            return (
              <Card key={index} className="text-center group hover:shadow-ai transition-all duration-300 border-border/50 hover:border-primary/20">
                <CardContent className="pt-8 pb-6">
                  <div className="space-y-4">
                    <div className="flex justify-center">
                      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gradient-card border border-border/50">
                        <IconComponent className={`h-6 w-6 ${impact.color}`} />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className={`text-4xl font-bold ${impact.color}`}>
                        {impact.metric}
                      </div>
                      <p className="text-sm text-muted-foreground font-medium">
                        {impact.label}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Roadmap */}
        <div className="space-y-8 mb-16">
          {roadmapItems.map((item, index) => {
            const IconComponent = item.icon;
            return (
              <Card key={index} className="group hover:shadow-ai transition-all duration-300 border-border/50 hover:border-primary/20">
                <CardHeader>
                  <div className="flex items-start gap-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-gradient-card border border-border/50">
                      <IconComponent className={`h-6 w-6 ${item.color}`} />
                    </div>
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center gap-3">
                        <Badge className="bg-primary/10 text-primary border-primary/20">
                          {item.phase}
                        </Badge>
                        <span className="text-sm text-muted-foreground">
                          {item.timeline}
                        </span>
                      </div>
                      <CardTitle className="text-xl group-hover:text-primary transition-colors">
                        {item.title}
                      </CardTitle>
                      <p className="text-muted-foreground">
                        {item.description}
                      </p>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                    {item.features.map((feature, featureIndex) => (
                      <div key={featureIndex} className="flex items-center gap-2 text-sm">
                        <div className="h-1.5 w-1.5 rounded-full bg-primary flex-shrink-0" />
                        <span className="text-muted-foreground">{feature}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Call to Action */}
        <Card className="bg-gradient-hero border-0 text-white">
          <CardContent className="p-8 lg:p-12 text-center">
            <div className="space-y-6">
              <div className="space-y-4">
                <h3 className="text-2xl lg:text-3xl font-bold">
                  Interessado em Colaborar?
                </h3>
                <p className="text-lg opacity-90 max-w-2xl mx-auto">
                  Este MVP demonstra capacidades técnicas sólidas e visão estratégica. 
                  Vamos conversar sobre oportunidades de desenvolvimento.
                </p>
              </div>
                
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                {github && (
                  <Button
                    asChild
                    variant="secondary"
                    size="lg"
                    className="group bg-white/10 text-white border-white/20 hover:bg-white/20"
                  >
                    <a
                      href={github.href}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      Ver Código no GitHub
                      <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
                    </a>
                  </Button>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </section>
  );
};

export default FutureSection;