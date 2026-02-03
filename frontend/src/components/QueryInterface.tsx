import { useState, useRef, useEffect } from 'react';
import { useSubmitQuery } from '@/hooks/useQuery';
import { useQueryHistory } from '@/hooks/useQueryHistory';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { ScrollArea } from './ui/scroll-area';
import { Badge } from './ui/badge';
import { Send, Clock, Trash2, History } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import QueryResults from './QueryResults';
import { cn } from '@/lib/utils';

export default function QueryInterface() {
  const [query, setQuery] = useState('');
  const [selectedHistoryId, setSelectedHistoryId] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { history, clearHistory } = useQueryHistory();
  const submitQuery = useSubmitQuery();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || submitQuery.isPending) return;

    submitQuery.mutate({
      query: query.trim(),
      page: 1,
      page_size: 100,
    });
    setSelectedHistoryId(null);
  };

  const handleHistoryClick = (historyItem: typeof history[0]) => {
    setQuery(historyItem.query);
    setSelectedHistoryId(historyItem.id);
    if (historyItem.response) {
      // The QueryResults component will show the cached response
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [query]);

  const currentResponse = selectedHistoryId
    ? history.find((h) => h.id === selectedHistoryId)?.response
    : submitQuery.data;

  return (
    <div className="flex h-screen">
      {/* Left Sidebar - Query History */}
      <div className="w-80 border-r bg-muted/50 p-4 flex flex-col">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <History className="h-5 w-5" />
            Query History
          </h2>
          {history.length > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={clearHistory}
              className="text-xs"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          )}
        </div>

        <ScrollArea className="flex-1">
          {history.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">
              No query history yet
            </p>
          ) : (
            <div className="space-y-2">
              {history.map((item) => (
                <Card
                  key={item.id}
                  className={cn(
                    "cursor-pointer transition-colors hover:bg-accent",
                    selectedHistoryId === item.id && "bg-accent border-primary"
                  )}
                  onClick={() => handleHistoryClick(item)}
                >
                  <CardContent className="p-3">
                    <p className="text-sm font-medium line-clamp-2 mb-2">
                      {item.query}
                    </p>
                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {formatDistanceToNow(item.timestamp, { addSuffix: true })}
                      </span>
                      {item.response?.error ? (
                        <Badge variant="destructive" className="text-xs">Error</Badge>
                      ) : (
                        <Badge variant="secondary" className="text-xs">Success</Badge>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </ScrollArea>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Query Input */}
        <Card className="m-4 mb-0">
          <CardHeader>
            <CardTitle>Ask a Question</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <Textarea
                ref={textareaRef}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter your question in natural language, e.g., 'Show me total revenue by month'"
                className="min-h-[100px] resize-none"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                    handleSubmit(e);
                  }
                }}
              />
              <div className="flex items-center justify-between">
                <p className="text-xs text-muted-foreground">
                  Press Cmd/Ctrl + Enter to submit
                </p>
                <Button
                  type="submit"
                  disabled={!query.trim() || submitQuery.isPending}
                >
                  {submitQuery.isPending ? (
                    <>Processing...</>
                  ) : (
                    <>
                      <Send className="h-4 w-4 mr-2" />
                      Submit Query
                    </>
                  )}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Results */}
        <div className="flex-1 overflow-auto p-4">
          {submitQuery.isError && (
            <Card className="border-destructive">
              <CardContent className="p-4">
                <p className="text-destructive">
                  Error: {submitQuery.error instanceof Error ? submitQuery.error.message : 'Unknown error'}
                </p>
              </CardContent>
            </Card>
          )}

          {currentResponse && (
            <QueryResults response={currentResponse} />
          )}

          {!currentResponse && !submitQuery.isPending && !submitQuery.isError && (
            <Card>
              <CardContent className="p-8 text-center text-muted-foreground">
                <p>Submit a query to see results</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

