import QueryInterface from './components/QueryInterface';

function App() {
  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card">
        <div className="container mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold">AI-Powered Business Intelligence Analyst</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Ask questions in natural language and get instant insights
          </p>
        </div>
      </header>
      <QueryInterface />
    </div>
  );
}

export default App;

