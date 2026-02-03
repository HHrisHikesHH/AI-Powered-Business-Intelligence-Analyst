import jsPDF from 'jspdf';
import * as XLSX from 'xlsx';
import type { QueryResponse } from '@/types/api';
import { formatCurrency, formatDuration } from './utils';

export const exportToCSV = (response: QueryResponse) => {
  if (!response.results || response.results.length === 0) {
    alert('No data to export');
    return;
  }

  // Get headers from first row
  const headers = Object.keys(response.results[0]);
  const csvRows = [headers.join(',')];

  // Add data rows
  response.results.forEach((row) => {
    const values = headers.map((header) => {
      const value = row[header];
      // Escape commas and quotes in CSV
      if (typeof value === 'string') {
        return `"${value.replace(/"/g, '""')}"`;
      }
      return value ?? '';
    });
    csvRows.push(values.join(','));
  });

  // Create blob and download
  const csvContent = csvRows.join('\n');
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  link.setAttribute('href', url);
  link.setAttribute('download', `query_${response.query_id}.csv`);
  link.style.visibility = 'hidden';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

export const exportToExcel = (response: QueryResponse) => {
  if (!response.results || response.results.length === 0) {
    alert('No data to export');
    return;
  }

  // Create workbook
  const wb = XLSX.utils.book_new();

  // Convert results to worksheet
  const ws = XLSX.utils.json_to_sheet(response.results);

  // Add metadata sheet
  const metadata = [
    ['Query', response.natural_language_query],
    ['Generated SQL', response.generated_sql || 'N/A'],
    ['Execution Time', response.execution_time_ms ? formatDuration(response.execution_time_ms) : 'N/A'],
    ['Total Rows', response.results.length],
    ['Cost', response.cost_breakdown?.cost ? formatCurrency(response.cost_breakdown.cost) : 'N/A'],
  ];
  const metadataWs = XLSX.utils.aoa_to_sheet(metadata);

  XLSX.utils.book_append_sheet(wb, metadataWs, 'Metadata');
  XLSX.utils.book_append_sheet(wb, ws, 'Results');

  // Download
  XLSX.writeFile(wb, `query_${response.query_id}.xlsx`);
};

export const exportToPDF = (response: QueryResponse) => {
  const doc: any = new jsPDF();
  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();
  const margin = 20;
  let yPos = margin;

  // Title
  doc.setFontSize(18);
  doc.text('AI-Powered Business Intelligence Analyst', margin, yPos);
  yPos += 10;

  // Query information
  doc.setFontSize(12);
  doc.setFont(undefined, 'bold');
  doc.text('Query:', margin, yPos);
  yPos += 7;
  doc.setFont(undefined, 'normal');
  const queryLines = doc.splitTextToSize(response.natural_language_query, pageWidth - 2 * margin);
  doc.text(queryLines, margin, yPos);
  yPos += queryLines.length * 7 + 5;

  // SQL
  if (response.generated_sql) {
    doc.setFont(undefined, 'bold');
    doc.text('Generated SQL:', margin, yPos);
    yPos += 7;
    doc.setFont(undefined, 'normal');
    doc.setFontSize(10);
    const sqlLines = doc.splitTextToSize(response.generated_sql, pageWidth - 2 * margin);
    doc.text(sqlLines, margin, yPos);
    yPos += sqlLines.length * 5 + 5;
    doc.setFontSize(12);
  }

  // Metadata
  const metadata: [string, string][] = [
    ['Execution Time', response.execution_time_ms ? formatDuration(response.execution_time_ms) : 'N/A'],
    ['Total Rows', String(response.results?.length ?? 0)],
    ['Cost', response.cost_breakdown?.cost ? formatCurrency(response.cost_breakdown.cost) : 'N/A'],
  ];

  metadata.forEach(([label, value]) => {
    doc.setFont(undefined, 'bold');
    doc.text(`${label}:`, margin, yPos);
    doc.setFont(undefined, 'normal');
    doc.text(value, margin + 60, yPos);
    yPos += 7;
  });

  yPos += 5;

  // Results table
  if (response.results && response.results.length > 0) {
    doc.setFont(undefined, 'bold');
    doc.text('Results:', margin, yPos);
    yPos += 7;

    const headers = Object.keys(response.results[0]);
    const colWidth = (pageWidth - 2 * margin) / headers.length;

    // Table headers
    doc.setFontSize(10);
    headers.forEach((header, i) => {
      doc.text(header.substring(0, 15), margin + i * colWidth, yPos);
    });
    yPos += 7;

    // Table rows (limit to fit on page)
    const maxRows = Math.floor((pageHeight - yPos - margin) / 7);
    response.results.slice(0, maxRows).forEach((row) => {
      headers.forEach((header, i) => {
        const value = String(row[header] ?? '').substring(0, 15);
        doc.text(value, margin + i * colWidth, yPos);
      });
      yPos += 7;

      if (yPos > pageHeight - margin) {
        doc.addPage();
        yPos = margin;
      }
    });

    if (response.results.length > maxRows) {
      doc.text(`... and ${response.results.length - maxRows} more rows`, margin, yPos);
    }
  }

  // Save
  doc.save(`query_${response.query_id}.pdf`);
};

