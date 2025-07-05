# LogicMart Analytics System

A comprehensive retail analytics dashboard built with Python and Tkinter.

## Features

### Manager Dashboard
- **Sales Trend Analysis**: Track revenue, transactions, and growth over time
- **Customer Traffic Reports**: Monitor peak shopping hours and patterns  
- **Top Selling Products**: Identify best-performing products by category
- **Inventory Usage**: Track stock levels and restock insights
- **Promotion Effectiveness**: Analyze promotional campaign performance
- **Sales Forecast**: Predict future sales using various forecasting methods

### Sales Manager Dashboard
- **Sales Trend Analysis**: Detailed sales performance metrics
- **Real Time Sales Dashboard**: Live sales monitoring
- **Popular Product Data**: Product performance analytics
- **Promotion Sales Comparison**: Compare promotional effectiveness

### Restocker Dashboard
- **Inventory Management**: Stock level monitoring and alerts
- **Restock Recommendations**: AI-driven restocking suggestions
- **Product Usage Analytics**: Track product movement patterns

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

2. Configure database connection in `database_config.py`

3. Run the application:
```bash
python main.py
```

Or use the launcher script:
```bash
python run_app.py
```

## Technical Stack

- **Frontend**: Python Tkinter
- **Data Processing**: Pandas, NumPy
- **Visualization**: Matplotlib, Seaborn
- **Database**: PostgreSQL (via psycopg2)
- **Reports**: ReportLab (PDF), OpenPyXL (Excel)
- **Date Selection**: tkcalendar

## File Structure

```
LogicMart/
├── main.py                 # Application entry point
├── login_page.py           # User authentication
├── manager_page.py         # Manager dashboard
├── sales_manager_page.py   # Sales manager dashboard
├── restocker_page.py       # Restocker dashboard
├── analytics_engine.py     # Data analytics backend
├── report_generator.py     # PDF/Excel report generation
├── database_config.py      # Database configuration
├── database_schema.py      # Database schema definitions
├── user_credentials.txt    # User credentials storage
├── user_settings.json      # Application settings
├── requirements.txt        # Python dependencies
└── run_app.py             # Application launcher script
```

## Database Configuration

Update `database_config.py` with your PostgreSQL connection details:

```python
DATABASE_CONFIG = {
    'host': 'your_host',
    'port': 'your_port', 
    'database': 'your_database',
    'user': 'your_username',
    'password': 'your_password'
}
```

## Usage

1. **Login**: Use credentials from `user_credentials.txt`
2. **Navigation**: Use the sidebar menu to access different analytics
3. **Filtering**: Most analytics support date range and category filtering
4. **Export**: Generate PDF or Excel reports from any analytics view
5. **Refresh**: Update data in real-time using the refresh button

## User Roles

- **Manager**: Full access to all analytics and reports
- **Sales Manager**: Access to sales-focused analytics
- **Restocker**: Access to inventory and restocking tools

## Optimizations Applied

- Removed all test and development files
- Cleaned up unused imports and dependencies
- Removed customer buying behavior analytics (as requested)
- Streamlined file structure
- Optimized requirements.txt
- Added proper error handling
- Improved code organization

## License

This project is for educational/demonstration purposes.
