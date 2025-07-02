# Analytics Feature Documentation

## Overview
This document describes the comprehensive analytics feature implemented for the CCS Info administration panel. The analytics dashboard provides detailed insights into system usage, user activity, and performance metrics.

## Features Implemented

### 1. Analytics Dashboard (`/admin/analytics`)
- **Location**: `templates/admin/analytics_robust.html`
- **Route**: `/admin/analytics` in `app/routes.py`
- **Access**: Admin and Super Admin only

### 2. Key Metrics
The dashboard displays the following primary metrics:

#### Homepage Views
- Tracks visits to the main homepage
- Shows percentage change compared to previous period
- Data source: `page_views` table

#### Active Users
- Count of unique users accessing rooms
- Based on room access logs
- Shows trend over selected time period

#### Room Accesses
- Total number of room access events
- Includes both successful and attempted accesses
- Percentage change indicator

#### Temporary Key Usage
- Count of temporary keys created and used
- Tracks temporary access patterns
- Change indicator compared to previous period

### 3. Interactive Charts

#### Daily Visitors Chart
- Line chart showing daily visitor trends
- Configurable time periods (7, 30, 90 days)
- Auto-updates every 5 minutes

#### Room Usage Chart
- Doughnut chart showing relative room usage
- Displays top 5 most accessed rooms
- Color-coded for easy identification

### 4. System Performance Monitoring
- **CPU Usage**: Real-time system CPU utilization
- **Memory Usage**: Current memory consumption
- Visual progress bars with percentage indicators

### 5. Activity Logs
- Recent system activity logs
- Categorized by type (auth, room, admin, system)
- Timestamps and user information
- Searchable and filterable

### 6. Data Export
- **Export Route**: `/admin/analytics/export`
- **Format**: CSV file with analytics summary
- **Contents**: Key metrics, trends, and date ranges
- **Filename**: `analytics_report_YYYYMMDD.csv`

### 7. API Endpoints

#### `/admin/analytics/data`
- **Method**: GET
- **Parameters**: `range` (7, 30, 90 days)
- **Returns**: JSON with updated analytics data
- **Usage**: AJAX refresh functionality

#### `/admin/analytics/chart`
- **Method**: GET
- **Parameters**: `type` (visitors, rooms), `view` (daily, weekly, monthly)
- **Returns**: JSON with chart data
- **Usage**: Dynamic chart updates

## Database Tables

### page_views
```sql
CREATE TABLE page_views (
    id INT AUTO_INCREMENT PRIMARY KEY,
    page_path VARCHAR(255) NOT NULL,
    user_ip VARCHAR(45),
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX(page_path),
    INDEX(timestamp)
);
```

### system_logs
```sql
CREATE TABLE system_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    level ENUM('info', 'warning', 'error') DEFAULT 'info',
    category VARCHAR(50) NOT NULL,
    user_id INT,
    user_name VARCHAR(255),
    action VARCHAR(255) NOT NULL,
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX(level),
    INDEX(category),
    INDEX(timestamp)
);
```

## Analytics Functions

### Core Functions
- `get_analytics_data(days=30)`: Main function to retrieve all analytics data
- `get_homepage_views(cursor, start_date, end_date)`: Homepage visit counts
- `get_active_users_count(cursor, start_date, end_date)`: Unique active users
- `get_room_accesses_count(cursor, start_date, end_date)`: Room access totals
- `get_temp_key_usage(cursor, start_date, end_date)`: Temporary key statistics

### Chart Data Functions
- `get_visitors_chart_data(cursor, days)`: Daily visitor trends
- `get_room_usage_chart_data(cursor, days)`: Room usage distribution
- `get_activity_pattern_data(cursor, days)`: Hourly activity patterns

### Utility Functions
- `log_page_view(page_path, user_ip, user_agent)`: Track page visits
- `log_system_action(level, category, action, details, user_id, user_name)`: Log system events
- `create_analytics_tables(cursor)`: Initialize required database tables

## Features and Capabilities

### Real-time Updates
- Auto-refresh every 5 minutes
- Manual refresh button
- AJAX-based data updates without page reload

### Responsive Design
- Mobile-friendly interface
- Adaptive grid layout
- Collapsible sidebar for smaller screens

### Data Visualization
- Chart.js integration for interactive charts
- Color-coded metrics with trend indicators
- Progress bars for system performance

### Error Handling
- Graceful fallback to simulated data when database is unavailable
- Silent failure for missing analytics tables
- User-friendly error messages

### Security
- Admin authentication required for all analytics routes
- Session validation on every request
- Input sanitization for all parameters

## Usage Instructions

### Accessing Analytics
1. Log in to the admin panel
2. Navigate to "Analytics" in the sidebar
3. View real-time metrics and charts

### Changing Time Ranges
1. Use the dropdown in the top-right to select 7, 30, or 90 days
2. Data automatically updates when selection changes

### Exporting Reports
1. Click the "Export Report" button
2. CSV file downloads with current analytics data
3. File includes metrics, trends, and time period information

### Refreshing Data
1. Manual refresh: Click the "Refresh" button
2. Automatic refresh: Every 5 minutes
3. Real-time updates: Charts and metrics update without page reload

## Technical Implementation

### Backend (Flask/Python)
- Route handlers in `app/routes.py`
- Database queries using MySQL Connector
- JSON API endpoints for AJAX requests
- CSV export functionality

### Frontend (HTML/CSS/JavaScript)
- Responsive template with Bootstrap-like styling
- Chart.js for data visualization
- AJAX for real-time updates
- Mobile-responsive sidebar navigation

### Database Integration
- MySQL database with proper indexing
- Fallback to simulated data for development
- Automatic table creation if missing

## Future Enhancements

### Potential Additions
1. **User Behavior Analytics**: Track user navigation patterns
2. **Predictive Analytics**: Forecast usage trends
3. **Alert System**: Notifications for unusual activity
4. **Custom Dashboards**: User-configurable analytics views
5. **Advanced Filtering**: Date ranges, user types, room categories
6. **Performance Optimization**: Caching for large datasets

### Scalability Considerations
- Database query optimization for large datasets
- Caching strategies for frequently accessed data
- API rate limiting for heavy usage
- Background processing for complex analytics

## Troubleshooting

### Common Issues
1. **Empty Data**: Check database connection and table creation
2. **Chart Not Loading**: Verify Chart.js CDN and JavaScript errors
3. **Export Not Working**: Check file permissions and Flask configuration
4. **Performance Issues**: Review database indexes and query optimization

### Debug Mode
- Enable Flask debug mode for detailed error messages
- Check browser console for JavaScript errors
- Monitor database queries for performance issues

## Security Considerations
- All analytics data is protected by admin authentication
- No sensitive user data is exposed in charts or exports
- SQL injection protection through parameterized queries
- XSS protection through proper template escaping

---

*This analytics feature provides comprehensive insights into system usage and helps administrators make data-driven decisions about resource allocation and system optimization.*
