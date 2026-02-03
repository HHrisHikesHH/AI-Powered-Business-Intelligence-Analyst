import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Download, Info, Code, Table, BarChart3 } from 'lucide-react';
import type { QueryResponse } from '@/types/api';
import { formatDuration, formatCurrency } from '@/lib/utils';
import DataTable from './DataTable';
import Visualization from './Visualization';
import ExplainQuery from './ExplainQuery';
import { exportToCSV, exportToExcel, exportToPDF } from '@/lib/export';

interface QueryResultsProps {
  response: QueryResponse;
}

export default function QueryResults({ response }: QueryResultsProps) {
  const [showExplain, setShowExplain] = useState(false);

  if (response.error) {
    return (
      <Card className="border-destructive" data-testid="query-results">
        <CardHeader>
          <CardTitle className="text-destructive">Error</CardTitle>
        </CardHeader>
        <CardContent>
          <p>{response.error}</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4" data-testid="query-results">
      {/* Header with metadata */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">{response.natural_language_query}</CardTitle>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowExplain(true)}
              >
                <Info className="h-4 w-4 mr-2" />
                Explain Query
              </Button>
              {response.results && response.results.length > 0 && (
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => exportToCSV(response)}
                  >
                    <Download className="h-4 w-4 mr-2" />
                    CSV
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => exportToExcel(response)}
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Excel
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => exportToPDF(response)}
                  >
                    <Download className="h-4 w-4 mr-2" />
                    PDF
                  </Button>
                </div>
              )}
            </div>
          </div>
          <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
            {response.execution_time_ms && (
              <Badge variant="secondary">
                {formatDuration(response.execution_time_ms)}
              </Badge>
            )}
            {response.cost_breakdown?.cost && (
              <Badge variant="secondary">
                Cost: {formatCurrency(response.cost_breakdown.cost)}
              </Badge>
            )}
            {response.results && (
              <Badge variant="secondary">
                {response.results.length} row{response.results.length !== 1 ? 's' : ''}
              </Badge>
            )}
            {response.pagination && (
              <Badge variant="secondary">
                Page {response.pagination.page} of {response.pagination.total_pages}
              </Badge>
            )}
          </div>
        </CardHeader>
      </Card>

      {/* Results Tabs */}
      <Tabs defaultValue="table" className="w-full">
        <TabsList>
          {response.results && response.results.length > 0 && (
            <TabsTrigger value="table">
              <Table className="h-4 w-4 mr-2" />
              Table
            </TabsTrigger>
          )}
          {response.visualization && (
            <TabsTrigger value="visualization">
              <BarChart3 className="h-4 w-4 mr-2" />
              Visualization
            </TabsTrigger>
          )}
          {response.generated_sql && (
            <TabsTrigger value="sql">
              <Code className="h-4 w-4 mr-2" />
              SQL
            </TabsTrigger>
          )}
        </TabsList>

        {response.results && response.results.length > 0 && (
          <TabsContent value="table">
            <DataTable
              data={response.results}
              pagination={response.pagination}
            />
          </TabsContent>
        )}

        {response.visualization && response.results && (
          <TabsContent value="visualization">
            <Visualization
              config={response.visualization}
              results={response.results}
            />
          </TabsContent>
        )}

        {response.generated_sql && (
          <TabsContent value="sql">
            <Card>
              <CardContent className="p-4">
                <pre className="text-sm overflow-x-auto">
                  <code>{response.generated_sql}</code>
                </pre>
              </CardContent>
            </Card>
          </TabsContent>
        )}
      </Tabs>

      {/* Analysis */}
      {response.analysis && (
        <Card>
          <CardHeader>
            <CardTitle>Analysis & Insights</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {response.analysis.summary && (
              <div>
                <h4 className="font-semibold mb-2">Summary</h4>
                <p className="text-sm text-muted-foreground">{response.analysis.summary}</p>
              </div>
            )}
            {response.analysis.insights && response.analysis.insights.length > 0 && (
              <div>
                <h4 className="font-semibold mb-2">Key Insights</h4>
                <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
                  {response.analysis.insights.map((insight, i) => (
                    <li key={i}>{insight}</li>
                  ))}
                </ul>
              </div>
            )}
            {response.analysis.recommendations && response.analysis.recommendations.length > 0 && (
              <div>
                <h4 className="font-semibold mb-2">Recommendations</h4>
                <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
                  {response.analysis.recommendations.map((rec, i) => (
                    <li key={i}>{rec}</li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Explain Query Dialog */}
      {showExplain && (
        <ExplainQuery
          response={response}
          onClose={() => setShowExplain(false)}
        />
      )}
    </div>
  );
}
