import Header from "@/components/LandingPage/Header";
import HeroSection from "@/components/LandingPage/HeroSection";
import ProblemsSection from "@/components/LandingPage/ProblemsSection";
import MVPSection from "@/components/LandingPage/MVPSection";
import TechStackSection from "@/components/LandingPage/TechStackSection";
import FutureSection from "@/components/LandingPage/FutureSection";
import Footer from "@/components/LandingPage/Footer";

const Index = () => {
  return (
    <div className="min-h-screen">
      <Header />
      <main>
        <HeroSection />
        <ProblemsSection />
        <MVPSection />
        <TechStackSection />
        <FutureSection />
      </main>
      <Footer />
    </div>
  );
};

export default Index;
