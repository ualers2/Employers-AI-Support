import { Button } from "@/components/ui/button";
import { Bot, Github, Linkedin, Mail, ExternalLink } from "lucide-react";
import { CONTACTS } from "@/constants/contacts";

const Footer = () => {
  return (
    <footer className="border-t border-border/40 bg-secondary/30 py-12">
      <div className="container max-w-screen-xl">
        <div className="grid gap-8 md:grid-cols-4">
          {/* Brand */}
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-primary">
                <Bot className="h-5 w-5 text-white" />
              </div>
              <span className="text-lg font-bold bg-gradient-primary bg-clip-text text-transparent">
                Employers AI
              </span>
            </div>
            <p className="text-sm text-muted-foreground max-w-sm">
              MVP inovador de agentes de IA para suporte SaaS multi-canal. 
              Demonstrando expertise técnica e visão estratégica.
            </p>
          </div>

          {/* MVP Features */}
          <div className="space-y-4">
            <h4 className="font-semibold">MVP</h4>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li>Suporte 24/7 Multi-canal</li>
              <li>Dashboard de Métricas</li>
              <li>Base de Conhecimento IA</li>
              <li>API RESTful Completa</li>
            </ul>
          </div>

          {/* Technologies */}
          <div className="space-y-4">
            <h4 className="font-semibold">Tecnologias</h4>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li>Python + FastAPI</li>
              <li>React + TypeScript</li>
              <li>Docker + PostgreSQL</li>
              <li>OpenAI + Agents SDK</li>
            </ul>
          </div>

          {/* Contact */}
          <div className="space-y-4">
            <h4 className="font-semibold">Contato</h4>
            <div className="space-y-3">
              {CONTACTS.map((item) => {
                const Icon = item.icon;
                return (
                  <a
                    key={item.name}
                    href={item.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center text-sm p-0 h-auto hover:bg-transparent"
                  >
                    <Icon className="h-4 w-4 mr-2" />
                    {item.name}
                    <ExternalLink className="h-3 w-3 ml-1 opacity-50" />
                  </a>
                );
              })}
            </div>
          </div>



        </div>

        <div className="mt-8 pt-8 border-t border-border/40 flex flex-col sm:flex-row justify-between items-center gap-4">
          <p className="text-sm text-muted-foreground">
            © 2025 Employers AI . Desenvolvido por ualerson.
          </p>
          <div className="flex items-center gap-4">
            <span className="text-xs text-muted-foreground">Construído com</span>
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-primary animate-pulse" />
              <span className="text-xs font-medium">React + Python</span>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;