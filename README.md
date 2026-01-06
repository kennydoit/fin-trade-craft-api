# Financial Trade Craft API

API service for distributing financial market data files. This service pulls data from Snowflake, exports it to flat files (JSON or CSV) on S3, and provides an API for accessing and distributing those files.

## Features

- **Data Extraction**: Connect to Snowflake and execute queries or extract tables
- **File Export**: Export data to S3 as JSON or CSV files
- **API Service**: REST API for listing and downloading exported files
- **Flexible Queries**: Support for custom SQL queries and table exports with filtering
- **Timestamped Files**: Automatic timestamp generation for file versioning

## Architecture

```
Snowflake → Data Pipeline → S3 Storage → API Service → End Users
```

The system consists of:
1. **Snowflake Client**: Connects to Snowflake and executes queries
2. **S3 Writer**: Writes data to S3 as JSON or CSV files
3. **Data Pipeline**: Orchestrates data extraction and export
4. **FastAPI Service**: Provides REST endpoints for file access

## Installation

1. Clone the repository:
```bash
git clone https://github.com/kennydoit/fin-trade-craft-api.git
cd fin-trade-craft-api
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your actual credentials
```

## Configuration

Create a `.env` file with the following variables:

```env
# Snowflake Configuration
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USER=your_user
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_DATABASE=your_database
SNOWFLAKE_SCHEMA=your_schema
SNOWFLAKE_ROLE=your_role  # Optional

# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your_bucket_name

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

## Usage

### Running the API Server

Start the API server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

API documentation is automatically available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Using the Data Pipeline Programmatically

See `examples.py` for usage examples:

```python
from src.data_pipeline import DataPipeline

pipeline = DataPipeline()

# Export a query to JSON
s3_uri = pipeline.export_query_to_json(
    query="SELECT * FROM trades WHERE trade_date >= CURRENT_DATE - 7",
    output_key="exports/recent_trades.json"
)

# Export a table to CSV
s3_uri = pipeline.export_table_to_csv(
    table_name="market_data",
    output_key="exports/market_data.csv",
    where_clause="trade_date = CURRENT_DATE"
)
```

## API Endpoints

### Health Check
```
GET /health
```

### List Files
```
GET /files?prefix=exports/
```
List all available files in S3 with optional prefix filter.

### Get Download URL
```
GET /files/{file_key}/download?expiration=3600
```
Get a presigned download URL for a specific file.

### Get File Content
```
GET /files/{file_key}/content
```
Retrieve the file content directly.

### Export Query Results
```
POST /export/query
```
Execute a Snowflake query and export results to S3.

Request body:
```json
{
  "query": "SELECT * FROM trades LIMIT 100",
  "output_key": "exports/trades.json",
  "format": "json",
  "include_timestamp": true,
  "orient": "records"
}
```

### Export Table
```
POST /export/table
```
Export a Snowflake table to S3.

Request body:
```json
{
  "table_name": "market_data",
  "output_key": "exports/market_data.csv",
  "format": "csv",
  "columns": ["symbol", "price", "volume"],
  "where_clause": "trade_date = CURRENT_DATE",
  "limit": 1000,
  "include_timestamp": true
}
```

## Project Structure

```
fin-trade-craft-api/
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   └── app.py              # FastAPI application
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py         # Configuration management
│   ├── data_pipeline/
│   │   ├── __init__.py
│   │   ├── snowflake_client.py # Snowflake connection and queries
│   │   ├── s3_writer.py        # S3 file writing
│   │   └── pipeline.py         # Pipeline orchestration
│   └── __init__.py
├── tests/                      # Test directory
├── examples.py                 # Usage examples
├── main.py                     # Application entry point
├── requirements.txt            # Python dependencies
├── .env.example               # Example environment variables
├── .gitignore
└── README.md
```

## Security Considerations

- Store credentials securely in environment variables or secrets management systems
- Use IAM roles instead of access keys when running on AWS infrastructure
- Implement rate limiting and authentication for production API deployments
- Regularly rotate Snowflake and AWS credentials
- Use presigned URLs with appropriate expiration times for file access

## Development

### Adding New Features

1. **New data sources**: Extend the data pipeline to support additional sources
2. **New export formats**: Add writers for other file formats (Parquet, Avro, etc.)
3. **Scheduled exports**: Integrate with job schedulers (Airflow, AWS Step Functions)
4. **Data transformation**: Add transformation logic between extraction and export

### Testing

Run tests (when test suite is implemented):
```bash
pytest tests/
```

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! Please submit pull requests or open issues for any improvements or bug fixes.
