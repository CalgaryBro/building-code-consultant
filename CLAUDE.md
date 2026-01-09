# Claude Project Notes

## Important Guidelines

### Port Management
- **NEVER try to free/stop services on ports** - If a port is in use, use an alternative free port instead
- For PostgreSQL, if port 5432 is busy, use 5433 or another available port
- Modify docker-compose.yml to use different ports rather than stopping system services

### Web Search & Data Fetching
When searching for information or downloading data from the internet:

1. **Use realistic browser headers** when making HTTP requests:
   ```bash
   curl -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
        -H "Accept: application/json" \
        "https://api.example.com/data"
   ```

2. **Implement delays between requests** to avoid rate limiting:
   ```bash
   sleep 2  # Wait 2 seconds between requests
   ```

3. **Check API documentation first** - Use WebSearch to find official API endpoints
4. **Prefer official data portals** - Calgary Open Data (data.calgary.ca), Open Alberta, NRC, etc.
5. **Save downloaded data** with descriptive filenames in the `/data/` directory
6. **Verify downloads** - Check file sizes and record counts after download

### Open Data Sources for This Project
- **Calgary Open Data**: https://data.calgary.ca/
- **Open Alberta**: https://open.alberta.ca/
- **NRC Publications**: https://nrc-publications.canada.ca/
- **Socrata API**: Use `resource/{dataset-id}.json` pattern with `$limit` parameter

### Database Configuration
- Primary database: PostgreSQL via Docker (pgvector image)
- Default port: 5432 (or next available if occupied)
- Connection string in `.env` file

### Resume Commands
See `Calgary_Code_Expert_System_Plan.md` section "Implementation Progress Log" for latest status and commands.
