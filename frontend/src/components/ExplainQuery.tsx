import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { ScrollArea } from './ui/scroll-area';
import { X } from 'lucide-react';
import { Button } from './ui/button';
import type { QueryResponse } from '@/types/api';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface ExplainQueryProps {
  response: QueryResponse;
  onClose: () => void;
}

export default function ExplainQuery({ response, onClose }: ExplainQueryProps) {
  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh]">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <DialogTitle>Query Explanation</DialogTitle>
            <Button variant="ghost" size="icon" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        </DialogHeader>

        <ScrollArea className="max-h-[calc(90vh-100px)]">
          <div className="space-y-4 pr-4">
            {/* Natural Language Query */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Your Question</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm">{response.natural_language_query}</p>
              </CardContent>
            </Card>

            {/* Generated SQL */}
            {response.generated_sql && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Generated SQL</CardTitle>
                </CardHeader>
                <CardContent>
                  <SyntaxHighlighter
                    language="sql"
                    style={oneDark}
                    customStyle={{
                      borderRadius: '0.5rem',
                      fontSize: '0.875rem',
                      padding: '1rem',
                    }}
                  >
                    {response.generated_sql}
                  </SyntaxHighlighter>
                </CardContent>
              </Card>
            )}

            {/* Execution Details */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Execution Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {response.execution_time_ms && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Execution Time:</span>
                    <Badge variant="secondary">
                      {(response.execution_time_ms / 1000).toFixed(2)}s
                    </Badge>
                  </div>
                )}
                {response.cost_breakdown && (
                  <>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Total Tokens:</span>
                      <Badge variant="secondary">
                        {response.cost_breakdown.tokens?.total || 0}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Input Tokens:</span>
                      <Badge variant="secondary">
                        {response.cost_breakdown.tokens?.input || 0}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Output Tokens:</span>
                      <Badge variant="secondary">
                        {response.cost_breakdown.tokens?.output || 0}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Estimated Cost:</span>
                      <Badge variant="secondary">
                        ${response.cost_breakdown.cost?.toFixed(6) || '0.000000'}
                      </Badge>
                    </div>
                  </>
                )}
                {response.results && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Rows Returned:</span>
                    <Badge variant="secondary">
                      {response.results.length}
                    </Badge>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Agent Pipeline Explanation */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">How It Works</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div>
                  <h4 className="font-semibold mb-1">1. Query Understanding Agent</h4>
                  <p className="text-muted-foreground">
                    Analyzed your natural language question to extract intent, identify required
                    tables and columns, and understand filters and aggregations.
                  </p>
                </div>
                <div>
                  <h4 className="font-semibold mb-1">2. SQL Generation Agent</h4>
                  <p className="text-muted-foreground">
                    Used RAG (Retrieval-Augmented Generation) to retrieve similar past queries
                    and schema context, then generated the SQL query using few-shot learning.
                  </p>
                </div>
                <div>
                  <h4 className="font-semibold mb-1">3. SQL Validation</h4>
                  <p className="text-muted-foreground">
                    Validated the SQL syntax, checked table/column existence, and ensured
                    no dangerous operations were included.
                  </p>
                </div>
                <div>
                  <h4 className="font-semibold mb-1">4. Query Execution</h4>
                  <p className="text-muted-foreground">
                    Executed the validated SQL query against the database with timeout and
                    row limit protections.
                  </p>
                </div>
                {response.analysis && (
                  <div>
                    <h4 className="font-semibold mb-1">5. Analysis Agent</h4>
                    <p className="text-muted-foreground">
                      Analyzed the results to identify insights, trends, and provide
                      actionable recommendations.
                    </p>
                  </div>
                )}
                {response.visualization && (
                  <div>
                    <h4 className="font-semibold mb-1">6. Visualization Agent</h4>
                    <p className="text-muted-foreground">
                      Determined the optimal chart type based on data characteristics and
                      generated the visualization configuration.
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Error Information */}
            {response.error && (
              <Card className="border-destructive">
                <CardHeader>
                  <CardTitle className="text-base text-destructive">Error</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-destructive">{response.error}</p>
                </CardContent>
              </Card>
            )}
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}

