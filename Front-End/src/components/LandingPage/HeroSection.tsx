import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ArrowRight, Zap, MessageSquare, Bot } from "lucide-react";
import heroImage from "@/assets/Screenshot_2.png";

import { CONTACTS } from "@/constants/contacts";

const apiDocs = CONTACTS.find(contact => contact.name === "Documentação API");

const HeroSection = () => {
  return (
    <section className="relative overflow-hidden bg-gradient-to-br from-background via-background to-primary/5 py-20 lg:py-32">
      <div className="container relative max-w-screen-xl">
        <div className="grid gap-8 lg:grid-cols-2 lg:gap-16 items-center">
          <div className="space-y-8">
            <div className="space-y-4">
              <Badge className="bg-accent/10 text-accent border-accent/20 hover:bg-accent/20">
                <Bot className="mr-2 h-3 w-3" />
                MVP Inovador • Agentes de IA
              </Badge>
              
              <h1 className="text-4xl font-bold tracking-tight lg:text-6xl">
                <span className="bg-gradient-hero bg-clip-text text-transparent">
                  Employers AI
                </span>
                <br />
                <span className="text-foreground">
                  Revoluciona o Suporte SaaS
                </span>
              </h1>
              
              <p className="text-xl text-muted-foreground max-w-lg">
                Agentes inteligentes que automatizam o atendimento em múltiplos canais, 
                reduzindo tempo de resposta e otimizando recursos humanos.
              </p>
            </div>

            <div className="flex flex-wrap gap-4">
              <Button 
                variant="hero" 
                size="lg" 
                className="group"
                onClick={() => window.location.href = "/login"}
              >
                Teste Gratis
                <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Button>

              <Button 
                variant="outline" 
                size="lg"
                onClick={() => window.location.href = apiDocs.href}
              >
                Documentação Técnica
              </Button>
            </div>


            <div className="flex items-center gap-8 pt-4">
              <div className="flex items-center gap-2">
                <Zap className="h-5 w-5 text-success-green" />
                <span className="text-sm font-medium">24/7 Disponível</span>
              </div>
              <div className="flex items-center gap-2">
                <MessageSquare className="h-5 w-5 text-tech-blue" />
                <span className="text-sm font-medium">Multi-canal</span>
              </div>
              <div className="flex items-center gap-2">
                <Bot className="h-5 w-5 text-accent" />
                <span className="text-sm font-medium">IA Avançada</span>
              </div>
            </div>
          </div>

          <div className="relative">
            <div className="relative overflow-hidden rounded-xl shadow-ai border border-border/50">
              <img 
                src={heroImage} 
                alt="Dashboard AI do Employers AI mostrando métricas e conversas"
                className="w-full h-auto object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/20 via-transparent to-transparent" />
            </div>
            
            {/* Floating elements */}
            <div className="absolute -top-4 -right-4 bg-success-green/10 text-success-green rounded-full p-4 border border-success-green/20">
              <Zap className="h-6 w-6" />
            </div>
            <div className="absolute -bottom-4 -left-4 bg-accent/10 text-accent rounded-full p-4 border border-accent/20">
              <Bot className="h-6 w-6" />
            </div>
          </div>
        </div>
      </div>
      
      {/* Background decoration */}
      <div className="absolute top-0 right-0 -z-10 h-full w-full opacity-20">
        <div className="absolute top-20 right-20 h-32 w-32 rounded-full bg-gradient-primary blur-3xl" />
        <div className="absolute bottom-20 left-20 h-40 w-40 rounded-full bg-gradient-to-r from-accent to-tech-blue blur-3xl" />
      </div>
    </section>
  );
};

export default HeroSection;