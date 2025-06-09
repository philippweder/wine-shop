import Link from "next/link";

export default function LandingPage() {
  return (
    <main className="min-h-screen flex flex-col items-center p-4 md:p-8 lg:p-12 bg-background text-foreground">
      <header className="w-full max-w-6xl mb-6 text-center">
        <h1 className="text-5xl lg:text-6xl font-bold font-serif text-primary tracking-tight">
          Welcome to Sentio
        </h1>
        <p className="mt-4 text-xl text-secondary font-sans">
          Experience a new era of wine appreciation, curated for the modern connoisseur.
        </p>
      </header>

      <section className="w-full max-w-4xl mt-12 text-center">
        <h2 className="text-3xl font-semibold font-serif text-accent mb-6">
          Going on a Date?
        </h2>
        <p className="text-lg text-secondary-foreground mb-4">
          Find the perfect wine for any occasion with our AI-powered sommelier. Whether you're impressing a date or bringing a gift to your in-laws, we have the ideal selection for you.
        </p>
        <Link
          href="/browse-wines"
          className="inline-block bg-primary text-primary-foreground font-medium py-3 px-8 rounded-lg shadow-md hover:bg-primary/90 transition-colors text-lg"
        >
          Start Browsing Wines
        </Link>
      </section>

      <section className="w-full max-w-4xl mt-16">
        <h3 className="text-2xl font-semibold font-serif text-accent mb-4 text-center">Why Choose Sentio?</h3>
        <div className="grid md:grid-cols-3 gap-8 text-center">
          <div className="bg-card p-6 rounded-lg shadow">
            <h4 className="text-xl font-bold text-card-foreground mb-2">Curated Selection</h4>
            <p className="text-sm text-muted-foreground">Only the best, hand-picked for quality and character.</p>
          </div>
          <div className="bg-card p-6 rounded-lg shadow">
            <h4 className="text-xl font-bold text-card-foreground mb-2">AI-Powered Guidance</h4>
            <p className="text-sm text-muted-foreground">Personalized recommendations from our smart sommelier.</p>
          </div>
          <div className="bg-card p-6 rounded-lg shadow">
            <h4 className="text-xl font-bold text-card-foreground mb-2">Sleek & Modern</h4>
            <p className="text-sm text-muted-foreground">A user-friendly experience designed for today's wine lover.</p>
          </div>
        </div>
      </section>

      <footer className="w-full max-w-6xl mt-16 pt-8 border-t border-border-color text-center">
        <p className="text-sm text-secondary">
          &copy; {new Date().getFullYear()} Sentio. All rights reserved.
        </p>
      </footer>
    </main>
  );
}
