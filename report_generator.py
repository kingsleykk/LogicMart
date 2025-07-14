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
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor("#2c3e50"),
            spaceAfter=20,
            alignment=1  
        )
        self.header_style = ParagraphStyle(
            'CustomHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor("#34495e"),
            spaceAfter=15,
            borderPadding=5
        )
        self.normal_style = self.styles['Normal']

    def create_chart(self, df, chart_type, title, x_col=None, y_col=None, figsize=(8, 4)):
        plt.style.use('seaborn-v0_8-whitegrid')
        fig, ax = plt.subplots(figsize=figsize)
        
        try:
            if chart_type == 'line' and x_col and y_col:
                ax.plot(df[x_col], df[y_col], marker='o', linewidth=2, markersize=5, color='#3498db')
            elif chart_type == 'bar' and x_col and y_col:
                sns.barplot(x=x_col, y=y_col, data=df, ax=ax, palette='viridis')
            elif chart_type == 'pie':
                labels = df.iloc[:, 0]
                values = df.iloc[:, 1]
                ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=140, colors=sns.color_palette("husl", len(labels)))
                ax.axis('equal')

            ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
            ax.set_xlabel(x_col.replace('_', ' ').title() if x_col else '', fontsize=10)
            ax.set_ylabel(y_col.replace('_', ' ').title() if y_col else '', fontsize=10)
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            buffer = io.BytesIO()
            fig.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
        finally:
            plt.close(fig)
        
        return buffer

    def generate_pdf_report(self, title, data_sections, charts=None, filename=None):
        if not filename:
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                title="Save PDF Report"
            )
        if not filename: return False
            
        try:
            doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=inch/2, leftMargin=inch/2, topMargin=inch/2, bottomMargin=inch/2)
            story = []
            
            story.append(Paragraph(title, self.title_style))
            story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", self.normal_style))
            story.append(Spacer(1, 20))
            
            if charts:
                for chart_title, chart_buffer in charts.items():
                    story.append(Paragraph(chart_title, self.header_style))
                    chart_buffer.seek(0)
                    img = Image(chart_buffer, width=7*inch, height=3.5*inch, hAlign='CENTER')
                    story.append(img)
                    story.append(Spacer(1, 20))

            for section_title, df in data_sections.items():
                if df.empty: continue
                story.append(Paragraph(section_title, self.header_style))
                
                df_display = df.copy()
                for col in df_display.select_dtypes(include=['datetime64[ns]']).columns:
                    df_display[col] = df_display[col].dt.strftime('%Y-%m-%d')

                data = [df_display.columns.tolist()] + df_display.values.tolist()
                
                table = Table(data, hAlign='CENTER')
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#34495e")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#ecf0f1")),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#95a5a6"))
                ]))
                story.append(table)
                story.append(Spacer(1, 20))
            
            doc.build(story)
            messagebox.showinfo("Success", f"PDF report saved successfully to {filename}")
            return True
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate PDF report: {e}")
            return False
    
    def generate_excel_report(self, title, data_sections, filename=None):
        if not filename:
            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")],
                title="Save Excel Report"
            )
        if not filename: return False
            
        try:
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                summary_data = {'Report Title': [title], 'Generated On': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')], 'Sections': [', '.join(data_sections.keys())]}
                pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
                
                for section_title, df in data_sections.items():
                    if not df.empty:
                        sheet_name = section_title.replace('/', '_').replace('\\', '_')[:31]
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            messagebox.showinfo("Success", f"Excel report saved successfully to {filename}")
            return True
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate Excel report: {e}")
            return False

class ManagerReportGenerator(ReportGenerator):
    def _create_traffic_analysis_chart(self, df):
        if df.empty: return None
        plt.style.use('seaborn-v0_8-whitegrid')
        fig, axes = plt.subplots(2, 2, figsize=(12, 8), facecolor='white')
        fig.suptitle('Customer Traffic Analysis', fontsize=16, fontweight='bold')

        plot_details = [
            (axes[0, 0], 'transaction_count', 'Transaction Volume'),
            (axes[0, 1], 'items_sold', 'Items Sold'),
            (axes[1, 0], 'total_revenue', 'Revenue Performance'),
            (axes[1, 1], 'avg_transaction_value', 'Avg Transaction Value')
        ]

        for ax, y_col, title in plot_details:
            ax.plot(df['period_label'], df[y_col], marker='o', linestyle='-', color='#3498db')
            ax.set_title(title, fontsize=12)
            ax.tick_params(axis='x', rotation=45, labelsize=8)
            ax.grid(True, linestyle='--', alpha=0.6)

        plt.tight_layout(rect=[0, 0, 1, 0.96])
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=300)
        buffer.seek(0)
        plt.close(fig)
        return buffer

    def _create_promotion_effectiveness_chart(self, df):
        if df.empty: return None
        plt.style.use('seaborn-v0_8-whitegrid')
        fig, axes = plt.subplots(1, 2, figsize=(12, 5), facecolor='white')
        fig.suptitle('Promotion Effectiveness', fontsize=16, fontweight='bold')

        top_promos = df.nlargest(8, 'total_revenue')
        sns.barplot(x='promotion_name', y='total_revenue', data=top_promos, ax=axes[0], palette='mako')
        axes[0].set_title('Revenue by Promotion', fontsize=12)
        axes[0].tick_params(axis='x', rotation=45, ha='right')

        promo_types = df['promotion_type'].value_counts()
        axes[1].pie(promo_types.values, labels=promo_types.index, autopct='%1.1f%%', startangle=140, colors=sns.color_palette("husl", len(promo_types)))
        axes[1].set_title('Promotion Types Distribution', fontsize=12)

        plt.tight_layout(rect=[0, 0, 1, 0.95])
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=300)
        buffer.seek(0)
        plt.close(fig)
        return buffer

    def generate_comprehensive_report(self, analytics_data, format_type='pdf'):
        title = "Manager Analytics Report"
        data_sections, charts = {}, {}
        
        if 'sales_trend' in analytics_data and not analytics_data['sales_trend'].empty:
            df = analytics_data['sales_trend']
            data_sections['Sales Trend Analysis'] = df
            charts['Sales Trend Chart'] = self.create_chart(df, 'line', 'Daily Revenue Trend', 'date', 'daily_revenue')
        
        if 'top_products' in analytics_data and not analytics_data['top_products'].empty:
            df = analytics_data['top_products']
            data_sections['Top Selling Products'] = df
            charts['Top Products Chart'] = self.create_chart(df.head(10), 'bar', 'Top 10 Products by Quantity Sold', 'product_name', 'total_quantity_sold')
        
        if 'customer_traffic' in analytics_data and not analytics_data['customer_traffic'].empty:
            df = analytics_data['customer_traffic']
            data_sections['Customer Traffic Analysis'] = df
            charts['Customer Traffic Chart'] = self._create_traffic_analysis_chart(df)
        
        if 'inventory' in analytics_data and not analytics_data['inventory'].empty:
            data_sections['Inventory Usage Insights'] = analytics_data['inventory']
        
        if 'promotions' in analytics_data and not analytics_data['promotions'].empty:
            df = analytics_data['promotions']
            data_sections['Promotion Effectiveness'] = df
            charts['Promotion Effectiveness Chart'] = self._create_promotion_effectiveness_chart(df)

        if 'product_trends' in analytics_data and not analytics_data['product_trends'].empty:
            df = analytics_data['product_trends']
            data_sections['Product Sales Trends'] = df.drop(columns=['total_quantity', 'avg_daily_quantity', 'days_with_sales']).drop_duplicates()

            products = df['product_name'].unique()[:5]

            fig_qty, ax_qty = plt.subplots(figsize=(10, 5))
            for product in products:
                product_data = df[df['product_name'] == product]
                ax_qty.plot(product_data['sale_date'], product_data['daily_quantity'], marker='o', label=product)
            ax_qty.set_title('Daily Quantity Sold - Top 5 Products')
            ax_qty.legend()
            ax_qty.grid(True)
            plt.xticks(rotation=45)
            plt.tight_layout()
            qty_buffer = io.BytesIO()
            fig_qty.savefig(qty_buffer, format='png')
            plt.close(fig_qty)
            charts['Daily Quantity Trends'] = qty_buffer

            fig_rev, ax_rev = plt.subplots(figsize=(10, 5))
            for product in products:
                product_data = df[df['product_name'] == product]
                ax_rev.plot(product_data['sale_date'], product_data['daily_revenue'], marker='s', label=product)
            ax_rev.set_title('Daily Revenue - Top 5 Products')
            ax_rev.legend()
            ax_rev.grid(True)
            plt.xticks(rotation=45)
            plt.tight_layout()
            rev_buffer = io.BytesIO()
            fig_rev.savefig(rev_buffer, format='png')
            plt.close(fig_rev)
            charts['Daily Revenue Trends'] = rev_buffer

        if format_type == 'pdf':
            return self.generate_pdf_report(title, data_sections, charts)
        else:
            return self.generate_excel_report(title, data_sections)

class SalesManagerReportGenerator(ReportGenerator):
    def generate_sales_report(self, analytics_data, format_type='pdf'):
        title = "Sales Manager Analytics Report"
        data_sections, charts = {}, {}
        
        if 'dashboard' in analytics_data and not analytics_data['dashboard'].empty:
            data_sections['Today\'s Sales Dashboard'] = analytics_data['dashboard']
        
        if 'promotional_comparison' in analytics_data and not analytics_data['promotional_comparison'].empty:
            df = analytics_data['promotional_comparison']
            data_sections['Promotional Comparison'] = df

        if 'customer_behavior' in analytics_data and not analytics_data['customer_behavior'].empty:
            df = analytics_data['customer_behavior']
            data_sections['Customer Buying Behavior'] = df
            charts['Customer Behavior Chart'] = self.create_chart(df, 'pie', 'Revenue by Customer Type')
        
        if 'popular_products' in analytics_data and not analytics_data['popular_products'].empty:
            data_sections['Popular Products for Promotion'] = analytics_data['popular_products']
        
        if 'seasonal' in analytics_data and not analytics_data['seasonal'].empty:
            df = analytics_data['seasonal']
            data_sections['Seasonal Sales Trends'] = df
            charts['Seasonal Trends Chart'] = self.create_chart(df, 'line', 'Monthly Revenue Trends', 'month', 'monthly_revenue')
        
        if format_type == 'pdf':
            return self.generate_pdf_report(title, data_sections, charts)
        else:
            return self.generate_excel_report(title, data_sections)

class RestockerReportGenerator(ReportGenerator):
    def generate_inventory_report(self, analytics_data, format_type='pdf'):
        title = "Inventory Management Report"
        data_sections, charts = {}, {}
        
        if 'low_stock' in analytics_data and not analytics_data['low_stock'].empty:
            data_sections['Low Stock Products'] = analytics_data['low_stock']
        
        if 'high_demand' in analytics_data and not analytics_data['high_demand'].empty:
            data_sections['Predicted High Demand Products'] = analytics_data['high_demand']
        
        if 'movement_trends' in analytics_data and not analytics_data['movement_trends'].empty:
            df = analytics_data['movement_trends']
            data_sections['Inventory Movement by Category'] = df
            charts['Movement Trends Chart'] = self.create_chart(df, 'bar', 'Inventory Outbound by Category', 'category', 'total_outbound')
        
        if format_type == 'pdf':
            return self.generate_pdf_report(title, data_sections, charts)
        else:
            return self.generate_excel_report(title, data_sections)
