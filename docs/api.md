# VisionIQ API Documentation

## Health Check
- **Endpoint**: `GET /api/health`
- **Description**: Verifies backend server health and readiness.
- **Response**:
  ```json
  {
    "status": "ok"
  }
  ```

## Upcoming Endpoints
- `POST /api/agent/query`: Execute an agent run with user prompt and optional media URL.
- `POST /api/vision/analyze`: Analyze an image and retrieve visual descriptions / tags.
- `POST /api/products/identify`: Detect products and query knowledge base.
- `POST /api/video/search`: Temporal search within video content for specific events or queries.
