import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime
import io
import matplotlib.pyplot as plt
import seaborn as sns
from tkinter import filedialog, messagebox
import os

class ReportGenerator:
    """Generate PDF and Excel reports from analytics data"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.darkblue,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
    def create_chart(self, df, chart_type, title, x_col=None, y_col=None, figsize=(10, 6)):
        """Create a chart from DataFrame and return as image buffer"""
        try:
            plt.style.use('seaborn-v0_8')
        except:
            # Fallback to default style if seaborn style not available
            plt.style.use('default')
        
        fig, ax = plt.subplots(figsize=figsize)
        
        if chart_type == 'line' and x_col and y_col:
            ax.plot(df[x_col], df[y_col], marker='o', linewidth=2, markersize=6)
            ax.set_xlabel(x_col.replace('_', ' ').title())
            ax.set_ylabel(y_col.replace('_', ' ').title())
            
        elif chart_type == 'bar' and x_col and y_col:
            bars = ax.bar(df[x_col], df[y_col], color='steelblue', alpha=0.7)
            ax.set_xlabel(x_col.replace('_', ' ').title())
            ax.set_ylabel(y_col.replace('_', ' ').title())
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.1f}', ha='center', va='bottom')
                       
        elif chart_type == 'pie':
            # Assume first column is labels, second is values
            labels = df.iloc[:, 0]
            values = df.iloc[:, 1]
            wedges, texts, autotexts = ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
            
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Save to buffer
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        plt.close(fig)
        
        return buffer
    
    def generate_pdf_report(self, title, data_sections, charts=None, filename=None):
        """Generate a comprehensive PDF report"""
        if not filename:
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                title="Save PDF Report"
            )
        
        if not filename:
            return False
            
        try:
            doc = SimpleDocTemplate(filename, pagesize=A4)
            story = []
            
            # Title
            title_para = Paragraph(title, self.title_style)
            story.append(title_para)
            story.append(Spacer(1, 20))
            
            # Date
            date_para = Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                                 self.styles['Normal'])
            story.append(date_para)
            story.append(Spacer(1, 30))
            
            # Add data sections
            for section_title, df in data_sections.items():
                if df.empty:
                    continue
                    
                # Section title
                section_para = Paragraph(section_title, self.styles['Heading2'])
                story.append(section_para)
                story.append(Spacer(1, 10))
                
                # Convert DataFrame to table
                data = [df.columns.tolist()] + df.values.tolist()
                
                # Limit columns and rows for PDF
                if len(data[0]) > 6:
                    data = [row[:6] for row in data]
                    
                if len(data) > 21:  # Including header
                    data = data[:21]
                    
                table = Table(data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(table)
                story.append(Spacer(1, 20))
            
            # Add charts if provided
            if charts:
                for chart_title, chart_buffer in charts.items():
                    chart_para = Paragraph(chart_title, self.styles['Heading2'])
                    story.append(chart_para)
                    story.append(Spacer(1, 10))
                    
                    # Add chart image
                    chart_buffer.seek(0)
                    img = Image(chart_buffer, width=6*inch, height=3.6*inch)
                    story.append(img)
                    story.append(Spacer(1, 20))
            
            doc.build(story)
            messagebox.showinfo("Success", f"PDF report saved successfully to {filename}")
            return True
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate PDF report: {e}")
            return False
    
    def generate_excel_report(self, title, data_sections, filename=None):
        """Generate Excel report with multiple sheets"""
        if not filename:
            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")],
                title="Save Excel Report"
            )
        
        if not filename:
            return False
            
        try:
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Summary sheet
                summary_data = {
                    'Report Title': [title],
                    'Generated On': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
                    'Sections': [', '.join(data_sections.keys())]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Data sheets
                for section_title, df in data_sections.items():
                    if not df.empty:
                        # Clean sheet name (Excel has restrictions)
                        sheet_name = section_title.replace('/', '_').replace('\\', '_')[:31]
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            messagebox.showinfo("Success", f"Excel report saved successfully to {filename}")
            return True
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate Excel report: {e}")
            return False

class ManagerReportGenerator(ReportGenerator):
    """Specialized report generator for Manager analytics"""
    
    def generate_comprehensive_report(self, analytics_data, format_type='pdf'):
        """Generate comprehensive manager report"""
        title = "Manager Analytics Report"
        
        data_sections = {}
        charts = {}
        
        # Sales Trend Analysis
        if 'sales_trend' in analytics_data and not analytics_data['sales_trend'].empty:
            data_sections['Sales Trend Analysis'] = analytics_data['sales_trend']
            
            # Create sales trend chart
            chart_buffer = self.create_chart(
                analytics_data['sales_trend'], 
                'line', 
                'Daily Revenue Trend',
                'date', 
                'daily_revenue'
            )
            charts['Sales Trend Chart'] = chart_buffer
        
        # Top Selling Products
        if 'top_products' in analytics_data and not analytics_data['top_products'].empty:
            data_sections['Top Selling Products'] = analytics_data['top_products']
            
            # Create top products chart
            top_10 = analytics_data['top_products'].head(10)
            chart_buffer = self.create_chart(
                top_10, 
                'bar', 
                'Top 10 Products by Quantity Sold',
                'product_name', 
                'total_quantity_sold'
            )
            charts['Top Products Chart'] = chart_buffer
        
        # Peak Shopping Hours (Customer Traffic)
        if 'peak_hours' in analytics_data and not analytics_data['peak_hours'].empty:
            data_sections['Peak Shopping Hours'] = analytics_data['peak_hours']
            
            # Create peak hours chart - handle different period types
            df = analytics_data['peak_hours']
            x_col = None
            y_col = None
            chart_title = 'Customer Traffic Analysis'
            
            # Determine appropriate columns based on data structure
            if 'hour' in df.columns and 'transaction_count' in df.columns:
                x_col, y_col = 'hour', 'transaction_count'
                chart_title = 'Customer Traffic by Hour'
            elif 'date' in df.columns and 'transaction_count' in df.columns:
                x_col, y_col = 'date', 'transaction_count'
                chart_title = 'Customer Traffic by Date'
            elif 'week' in df.columns and 'transaction_count' in df.columns:
                x_col, y_col = 'week', 'transaction_count'
                chart_title = 'Customer Traffic by Week'
            elif 'month' in df.columns and 'transaction_count' in df.columns:
                x_col, y_col = 'month', 'transaction_count' 
                chart_title = 'Customer Traffic by Month'
            elif len(df.columns) >= 2:
                # Fallback to first two columns
                x_col, y_col = df.columns[0], df.columns[1]
                
            if x_col and y_col:
                chart_buffer = self.create_chart(
                    df, 
                    'line', 
                    chart_title,
                    x_col, 
                    y_col
                )
                charts['Customer Traffic Chart'] = chart_buffer
        
        # Inventory Insights
        if 'inventory' in analytics_data and not analytics_data['inventory'].empty:
            data_sections['Inventory Usage Insights'] = analytics_data['inventory']
        
        # Promotion Effectiveness
        if 'promotions' in analytics_data and not analytics_data['promotions'].empty:
            data_sections['Promotion Effectiveness'] = analytics_data['promotions']
            
            # Create promotion effectiveness chart if possible
            df = analytics_data['promotions']
            if 'promotion_name' in df.columns and 'effectiveness_score' in df.columns:
                chart_buffer = self.create_chart(
                    df.head(10), 
                    'bar', 
                    'Top 10 Promotion Effectiveness',
                    'promotion_name', 
                    'effectiveness_score'
                )
                charts['Promotion Effectiveness Chart'] = chart_buffer
        
        # Generic handling for any other data types
        for key, df in analytics_data.items():
            if key not in ['sales_trend', 'top_products', 'peak_hours', 'inventory', 'promotions']:
                if not df.empty:
                    # Clean up the section name
                    section_name = key.replace('_', ' ').title()
                    data_sections[section_name] = df

        if format_type == 'pdf':
            return self.generate_pdf_report(title, data_sections, charts)
        else:
            return self.generate_excel_report(title, data_sections)

class SalesManagerReportGenerator(ReportGenerator):
    """Specialized report generator for Sales Manager analytics"""
    
    def generate_sales_report(self, analytics_data, format_type='pdf'):
        """Generate sales manager report"""
        title = "Sales Manager Analytics Report"
        
        data_sections = {}
        charts = {}
        
        # Real-time Dashboard
        if 'dashboard' in analytics_data and not analytics_data['dashboard'].empty:
            data_sections['Today\'s Sales Dashboard'] = analytics_data['dashboard']
        
        # Customer Behavior
        if 'customer_behavior' in analytics_data and not analytics_data['customer_behavior'].empty:
            data_sections['Customer Buying Behavior'] = analytics_data['customer_behavior']
            
            # Create customer behavior chart
            chart_buffer = self.create_chart(
                analytics_data['customer_behavior'], 
                'pie', 
                'Revenue by Customer Type'
            )
            charts['Customer Behavior Chart'] = chart_buffer
        
        # Popular Products
        if 'popular_products' in analytics_data and not analytics_data['popular_products'].empty:
            data_sections['Popular Products for Promotion'] = analytics_data['popular_products']
        
        # Seasonal Trends
        if 'seasonal' in analytics_data and not analytics_data['seasonal'].empty:
            data_sections['Seasonal Sales Trends'] = analytics_data['seasonal']
            
            # Create seasonal chart
            chart_buffer = self.create_chart(
                analytics_data['seasonal'], 
                'line', 
                'Monthly Revenue Trends',
                'month', 
                'monthly_revenue'
            )
            charts['Seasonal Trends Chart'] = chart_buffer
        
        if format_type == 'pdf':
            return self.generate_pdf_report(title, data_sections, charts)
        else:
            return self.generate_excel_report(title, data_sections)

class RestockerReportGenerator(ReportGenerator):
    """Specialized report generator for Restocker analytics"""
    
    def generate_inventory_report(self, analytics_data, format_type='pdf'):
        """Generate restocker inventory report"""
        title = "Inventory Management Report"
        
        data_sections = {}
        charts = {}
        
        # Low Stock Products
        if 'low_stock' in analytics_data and not analytics_data['low_stock'].empty:
            data_sections['Low Stock Products'] = analytics_data['low_stock']
        
        # High Demand Predictions
        if 'high_demand' in analytics_data and not analytics_data['high_demand'].empty:
            data_sections['Predicted High Demand Products'] = analytics_data['high_demand']
        
        # Inventory Movement Trends
        if 'movement_trends' in analytics_data and not analytics_data['movement_trends'].empty:
            data_sections['Inventory Movement by Category'] = analytics_data['movement_trends']
            
            # Create movement trends chart
            chart_buffer = self.create_chart(
                analytics_data['movement_trends'], 
                'bar', 
                'Inventory Outbound by Category',
                'category', 
                'total_outbound'
            )
            charts['Movement Trends Chart'] = chart_buffer
        
        if format_type == 'pdf':
            return self.generate_pdf_report(title, data_sections, charts)
        else:
            return self.generate_excel_report(title, data_sections)
