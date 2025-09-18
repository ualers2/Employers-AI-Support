import { Button } from "@/components/ui/button";
import { Bot, Github, Linkedin } from "lucide-react";
import { CONTACTS } from "@/constants/contacts";

const Header = () => {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 max-w-screen-xl items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-primary">
            <Bot className="h-5 w-5 text-white" />
          </div>
          <span className="text-xl font-bold bg-gradient-primary bg-clip-text text-transparent">
            Employers AI
          </span>
        </div>
        
        <nav className="hidden md:flex items-center gap-8">
          <a href="#problemas" className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors">
            Problemas Resolvidos
          </a>
          <a href="#mvp" className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors">
            MVP
          </a>
          <a href="#tecnologias" className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors">
            Tecnologias
          </a>
          <a href="#futuro" className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors">
            Futuro
          </a>
        </nav>

        <div className="flex items-center gap-4">
          {CONTACTS.map((item) => {
            const Icon = item.icon;

            if (item.type === "icon") {
              return (
                <Button
                  key={item.name}
                  asChild
                  variant="ghost"
                  size="icon"
                  className="hover:bg-accent"
                >
                  <a
                    href={item.href}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <Icon className="h-4 w-4" />
                  </a>
                </Button>
              );
            }

            if (item.type === "cta") {
              return (
                <Button
                  key={item.name}
                  asChild
                  variant="cta"
                  className="hidden md:inline-flex"
                >
                  <a
                    href={item.href}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {item.name}
                  </a>
                </Button>
              );
            }

            return null;
          })}
        </div>
      </div>
    </header>
  );
};

export default Header;