import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Code, Database, Cloud, Cpu } from "lucide-react";
import techStackImage from "@/assets/tech-stack-illustration.jpg";

const technologies = [
  {
    category: "Backend",
    icon: Code,
    color: "text-primary",
    items: [
      { name: "Python", description: "Core backend development" },
      { name: "FastAPI", description: "RESTful API framework" },
      { name: "Pydantic", description: "Data validation" }
    ]
  },
  {
    category: "Frontend", 
    icon: Cpu,
    color: "text-tech-blue",
    items: [
      { name: "React", description: "Interface de usuário" },
      { name: "TypeScript", description: "Tipagem estática" },
      { name: "Tailwind CSS", description: "Estilização moderna" }
    ]
  },
  {
    category: "Infraestrutura",
    icon: Cloud,
    color: "text-accent",
    items: [
      { name: "Docker", description: "Containerização" },
      { name: "Docker Compose", description: "Orquestração" },
      { name: "PostgreSQL", description: "Banco de dados" }
    ]
  },
  {
    category: "Inteligência Artificial",
    icon: Database,
    color: "text-success-green",
    items: [
      { name: "OpenAI GPT-5-Nano", description: "IA conversacional" },
      { name: "Agents SDK", description: "SDK Oficial de Agentes da OpenAI" },
      { name: "Omini Latest", description: "Modelo avançado de moderação de conteudo" }
    ]
  }
];

const architectureFeatures = [
  "Arquitetura modular e escalável",
  "Microserviços containerizados",
  "Base de dados persistente",
  "APIs RESTful padronizadas",
  "Integração multi-modelo de IA",
  "Monitoramento em tempo real"
];

const TechStackSection = () => {
  return (
    <section id="tecnologias" className="py-20 lg:py-32 bg-secondary/30">
      <div className="container max-w-screen-xl">
        <div className="text-center space-y-4 mb-16">
          <Badge className="bg-tech-blue/10 text-tech-blue border-tech-blue/20">
            Stack Tecnológico
          </Badge>
          <h2 className="text-3xl lg:text-5xl font-bold">
            Tecnologias <span className="bg-gradient-primary bg-clip-text text-transparent">Modernas</span> e Escaláveis
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            Arquitetura robusta construída com as melhores práticas de desenvolvimento e tecnologias cutting-edge.
          </p>
        </div>

        <div className="grid gap-12 lg:grid-cols-2 items-center mb-16">
          <div className="space-y-8">
            <div className="grid gap-6 sm:grid-cols-2">
              {technologies.map((tech, index) => {
                const IconComponent = tech.icon;
                return (
                  <Card key={index} className="group hover:shadow-card-custom transition-all duration-300 border-border/50 hover:border-primary/20">
                    <CardHeader className="space-y-3">
                      <div className="flex items-center gap-3">
                        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-card border border-border/50">
                          <IconComponent className={`h-4 w-4 ${tech.color}`} />
                        </div>
                        <CardTitle className="text-base group-hover:text-primary transition-colors">
                          {tech.category}
                        </CardTitle>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      {tech.items.map((item, itemIndex) => (
                        <div key={itemIndex} className="space-y-1">
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-medium text-foreground">
                              {item.name}
                            </span>
                          </div>
                          <p className="text-xs text-muted-foreground">
                            {item.description}
                          </p>
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                );
              })}
            </div>

            <Card className="border-border/50">
              <CardHeader>
                <CardTitle className="text-lg">Arquitetura e Práticas</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-2 sm:grid-cols-2">
                  {architectureFeatures.map((feature, index) => (
                    <div key={index} className="flex items-center gap-2 text-sm">
                      <div className="h-1.5 w-1.5 rounded-full bg-success-green flex-shrink-0" />
                      <span className="text-muted-foreground">{feature}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="relative">
            <img 
              src={techStackImage} 
              alt="Ilustração da stack tecnológica com IA, React, Python e Docker"
              className="w-full h-auto rounded-xl shadow-ai border border-border/50"
            />
            
            {/* Floating tech badges */}
            <div className="absolute -top-4 -left-4 bg-primary/10 text-primary rounded-full px-3 py-1 border border-primary/20">
              <span className="text-xs font-medium">Python</span>
            </div>
            <div className="absolute top-1/2 -right-4 bg-tech-blue/10 text-tech-blue rounded-full px-3 py-1 border border-tech-blue/20">
              <span className="text-xs font-medium">React</span>
            </div>
            <div className="absolute -bottom-4 left-1/2 transform -translate-x-1/2 bg-success-green/10 text-success-green rounded-full px-3 py-1 border border-success-green/20">
              <span className="text-xs font-medium">Docker</span>
            </div>
          </div>
        </div>

        {/* Architecture Diagram */}
        <Card className="border-border/50 bg-gradient-card">
          <CardHeader className="text-center">
            <CardTitle className="text-xl">Arquitetura de Microserviços</CardTitle>
            <p className="text-muted-foreground">
              Sistema distribuído com containers Docker e orquestração via Docker Compose
            </p>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-4 text-center">
              <div className="space-y-2 p-4 rounded-lg bg-background/50 border border-border/30">
                <Code className="h-6 w-6 text-primary mx-auto" />
                <h4 className="font-medium text-sm">Backend API</h4>
                <p className="text-xs text-muted-foreground">Python + FastAPI</p>
              </div>
              <div className="space-y-2 p-4 rounded-lg bg-background/50 border border-border/30">
                <Cpu className="h-6 w-6 text-tech-blue mx-auto" />
                <h4 className="font-medium text-sm">Frontend UI</h4>
                <p className="text-xs text-muted-foreground">React + TypeScript</p>
              </div>
              <div className="space-y-2 p-4 rounded-lg bg-background/50 border border-border/30">
                <Database className="h-6 w-6 text-success-green mx-auto" />
                <h4 className="font-medium text-sm">Database</h4>
                <p className="text-xs text-muted-foreground">PostgreSQL</p>
              </div>
              <div className="space-y-2 p-4 rounded-lg bg-background/50 border border-border/30">
                <Cloud className="h-6 w-6 text-accent mx-auto" />
                <h4 className="font-medium text-sm">AI Agents</h4>
                <p className="text-xs text-muted-foreground">Multi-platform Bots</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </section>
  );
};

export default TechStackSection;