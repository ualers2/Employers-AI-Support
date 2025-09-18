import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { 
  Clock, 
  Users, 
  MessageCircle, 
  TrendingUp, 
  Brain, 
  Database 
} from "lucide-react";

const problems = [
  {
    icon: Clock,
    title: "Redução do Tempo de Resposta",
    description: "Respostas instantâneas e consistentes, eliminando gargalos e filas de espera, mesmo em picos de demanda.",
    highlight: "Resposta Instantânea",
    color: "text-success-green"
  },
  {
    icon: Users,
    title: "Padronização e Qualidade do Atendimento",
    description: "Respostas padronizadas e de alta qualidade com base em uma base de conhecimento centralizada.",
    highlight: "Qualidade Garantida",
    color: "text-tech-blue"
  },
  {
    icon: MessageCircle,
    title: "Disponibilidade em Múltiplos Canais",
    description: "Atendimento unificado em Telegram, Discord e WhatsApp, eliminando equipes separadas para cada canal.",
    highlight: "Multi-canal",
    color: "text-accent"
  },
  {
    icon: TrendingUp,
    title: "Escalabilidade Ilimitada",
    description: "Lida com número virtualmente ilimitado de usuários simultaneamente, escalando sem aumentar custos.",
    highlight: "Escalabilidade Infinita",
    color: "text-primary"
  },
  {
    icon: Brain,
    title: "Otimização de Recursos Humanos",
    description: "IA assume tarefas repetitivas, liberando profissionais para problemas complexos e estratégicos.",
    highlight: "Eficiência Humana",
    color: "text-success-green"
  },
  {
    icon: Database,
    title: "Base de Conhecimento Viva",
    description: "Centraliza informações e resolve a dispersão de dados com base atualizável e acessível.",
    highlight: "Conhecimento Centralizado",
    color: "text-tech-blue"
  }
];

const ProblemsSection = () => {
  return (
    <section id="problemas" className="py-20 lg:py-32 bg-secondary/30">
      <div className="container max-w-screen-xl">
        <div className="text-center space-y-4 mb-16">
          <Badge className="bg-primary/10 text-primary border-primary/20">
            Problemas Resolvidos
          </Badge>
          <h2 className="text-3xl lg:text-5xl font-bold">
            Desafios que o <span className="bg-gradient-primary bg-clip-text text-transparent">Employers AI</span> Supera
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            Desenvolvido para resolver desafios reais no atendimento ao cliente, 
            proporcionando eficiência e consistência sem precedentes.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {problems.map((problem, index) => {
            const IconComponent = problem.icon;
            return (
              <Card key={index} className="group hover:shadow-ai transition-all duration-300 border-border/50 hover:border-primary/20">
                <CardHeader className="space-y-4">
                  <div className="flex items-center gap-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-gradient-card border border-border/50">
                      <IconComponent className={`h-6 w-6 ${problem.color}`} />
                    </div>
                    <Badge variant="outline" className="text-xs">
                      {problem.highlight}
                    </Badge>
                  </div>
                  <CardTitle className="text-lg group-hover:text-primary transition-colors">
                    {problem.title}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground leading-relaxed">
                    {problem.description}
                  </p>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>
    </section>
  );
};

export default ProblemsSection;