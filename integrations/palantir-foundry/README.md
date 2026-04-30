# Palantir Foundry to Veza OAA Integration

## Overview

This integration script collects data governance and access control information from **Palantir Foundry** and pushes it to **Veza** via the Open Authorization API (OAA). The connector provides read-only visibility into:

- **Workspaces** — Logical groupings for collaborative work within Foundry
- **Projects** — Organizational units and containers within workspaces
- **Datasets** — Data assets with complete metadata and lineage information
- **Resources** — Generic resources and custom objects within Foundry
- **Access Policies** — Fine-grained permissions and role-based access controls

All data flows through Veza's OAA model, enabling centralized visibility into data governance, lineage, and access management across your Palantir Foundry deployment at Westrock.

---

## How It Works

The integration follows this flow:

1. **Authenticate** — Validates credentials with Palantir Foundry API using bearer token authentication
2. **Fetch Resources** — Retrieves workspaces, projects, datasets, and resources from Foundry APIs
3. **Build Payload** — Constructs a Veza CustomApplication object with:
   - Workspaces as container resources
   - Projects as organizational resources
   - Datasets as data assets with metadata
   - Generic resources and access policy information
4. **Push to Veza** — Sends the complete OAA payload to Veza for indexing, analysis, and visualization
5. **Log Results** — Tracks metrics (resources discovered, permissions mapped, warnings)

---

## Prerequisites

### System Requirements
- **OS**: Linux (RHEL/CentOS, Ubuntu, Debian), macOS, or Windows with Python
- **Python**: 3.9 or higher
- **Internet Access**: HTTPS connectivity to Palantir Foundry and Veza instances
- **Disk Space**: ≥ 500 MB (for virtual environment and logs)
- **Network Firewall**: Outbound HTTPS (port 443) allowed

### Palantir Foundry Prerequisites
- **Active Palantir Foundry instance** at `https://westrock.palantirfoundry.com/`
- **API Token** with read access to resources (obtained from Foundry admin console)
- **Required API Endpoints**: 
  - `GET /api/foundry/core/v1/user` — authentication and user info
  - `GET /api/foundry/core/v1/healthcheck` — health check
  - `GET /api/foundry/datasets/v1/datasets` — list datasets
  - `GET /api/foundry/projects/v1/projects` — list projects
  - `GET /api/foundry/workspaces/v1/workspaces` — list workspaces
  - `GET /api/foundry/resources/v1/resources` — list resources
  - `GET /api/foundry/resources/v1/resources/{id}/access-policies` — access policies

### Veza Prerequisites
- **Active Veza instance** with API access enabled
- **Valid API key** with permissions to push OAA data
- **Network connectivity** from integration server to Veza instance
- **Supported Veza version**: 6.0 or higher

### Network Requirements
```
Outbound HTTPS (port 443) to:
  - Palantir Foundry: westrock.palantirfoundry.com
  - Veza instance: your-veza-domain.veza.com
  - PyPI (for package installation): pypi.org, pypi.python.org

Optional:
  - Firewall rules limiting access to service account IP
  - Proxy configuration if environment requires
```

---

## Quick Start

### One-Command Installation (Interactive - Linux/macOS)

```bash
curl -fsSL https://raw.githubusercontent.com/andrewmusto-git/OAA_Veza/main/integrations/palantir-foundry/install_palantir_foundry.sh | bash
```

The installer will:
1. Check system dependencies (Python 3.9+, Git)
2. Clone the integration repository
3. Create a Python virtual environment
4. Prompt for Palantir Foundry and Veza credentials
5. Generate a `.env` file with configuration
6. Test the connection to Palantir Foundry
7. Create a wrapper script for cron scheduling

---

## Manual Installation

### Step 1: Clone the Repository

```bash
# Clone the OAA Veza repository
git clone https://github.com/andrewmusto-git/OAA_Veza.git
cd OAA_Veza/integrations/palantir-foundry
```

### Step 2: Create Python Virtual Environment

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies

```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### Step 4: Configure Credentials

Copy the template configuration file:
```bash
cp .env.template .env
```

Edit `.env` with your credentials:
```bash
# Palantir Foundry Configuration
FOUNDRY_BASE_URL=https://westrock.palantirfoundry.com
FOUNDRY_API_TOKEN=your_api_token_here

# Veza Configuration
VEZA_URL=https://your-veza-instance.veza.com
VEZA_API_KEY=your_api_key_here
```

### Step 5: Test Connection

```bash
python3 palantir_foundry.py --test
```

Expected output:
```
2024-04-27 10:15:23,456 - __main__ - INFO - Initializing Palantir Foundry client...
2024-04-27 10:15:24,123 - __main__ - INFO - Successfully authenticated with Palantir Foundry as: Service Account
...
2024-04-27 10:15:24,567 - __main__ - INFO - Test mode: connection successful
```

### Step 6: Run Integration

```bash
# Full integration (test connection, fetch data, push to Veza)
python3 palantir_foundry.py

# Dry-run mode (test and build payload without pushing)
python3 palantir_foundry.py --dry-run

# Using custom config file
python3 palantir_foundry.py --config /path/to/.env
```

---

## Usage

### Command-Line Options

```bash
python3 palantir_foundry.py [OPTIONS]

Options:
  --config PATH    Path to .env configuration file (default: .env)
  --test           Test connection without pushing to Veza
  --dry-run        Build payload without pushing to Veza
  --help           Show help message and exit
```

### Example: Dry-Run Mode

```bash
python3 palantir_foundry.py --dry-run 2>&1 | head -100
```

This will output the JSON payload that would be sent to Veza without actually pushing it.

### Example: Test Connection Only

```bash
python3 palantir_foundry.py --test
```

### Example: Full Integration

```bash
python3 palantir_foundry.py
```

---

## Scheduling with Cron

### Linux/macOS Cron

To run the integration automatically, add a cron job:

```bash
# Open crontab editor
crontab -e

# Add entry to run daily at 2 AM
0 2 * * * cd /home/user/palantir-foundry-veza/integrations/palantir-foundry && source venv/bin/activate && python3 palantir_foundry.py >> integration.log 2>&1

# Run every 6 hours
0 */6 * * * cd /home/user/palantir-foundry-veza/integrations/palantir-foundry && source venv/bin/activate && python3 palantir_foundry.py >> integration.log 2>&1

# Run hourly
0 * * * * cd /home/user/palantir-foundry-veza/integrations/palantir-foundry && source venv/bin/activate && python3 palantir_foundry.py >> integration.log 2>&1
```

### Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (Daily at 2 AM, etc.)
4. Set action:
   - Program: `C:\path\to\venv\Scripts\python.exe`
   - Arguments: `C:\path\to\palantir_foundry.py`
   - Start in: `C:\path\to\integration\directory`
5. Configure credentials to run as service account

---

## Logs and Monitoring

### Log Files

The integration generates detailed logs in two locations:

```
# Console output
STDOUT / STDERR

# File logs (in integration directory)
palantir_foundry_veza_integration.log
```

### Log Levels

Logs are set to `INFO` level by default. To view DEBUG logs:

```bash
# Edit palantir_foundry.py and change logging level to DEBUG
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    ...
)
```

### Log Format

```
2024-04-27 10:15:23,456 - palantir_foundry.py - INFO - Successfully authenticated with Palantir Foundry as: Service Account
2024-04-27 10:15:24,123 - palantir_foundry.py - INFO - Fetching workspaces from Palantir Foundry...
2024-04-27 10:15:25,789 - palantir_foundry.py - INFO - Retrieved 5 workspaces
...
2024-04-27 10:15:30,456 - palantir_foundry.py - INFO - Successfully pushed data to Veza
```

---

## Troubleshooting

### Authentication Errors

**Error**: `Failed to authenticate with Palantir Foundry`

**Solutions**:
1. Verify `FOUNDRY_API_TOKEN` is valid and hasn't expired
2. Check token permissions in Palantir Foundry admin console
3. Verify `FOUNDRY_BASE_URL` is correct: `https://westrock.palantirfoundry.com`
4. Test connectivity: `curl -H "Authorization: Bearer YOUR_TOKEN" https://westrock.palantirfoundry.com/api/foundry/core/v1/user`

### Network Errors

**Error**: `Connection timeout`, `Failed to connect to Palantir Foundry`

**Solutions**:
1. Verify internet connectivity: `ping westrock.palantirfoundry.com`
2. Check firewall rules allow HTTPS (port 443) outbound
3. If using proxy, configure environment variables:
   ```bash
   export HTTP_PROXY=http://proxy.company.com:8080
   export HTTPS_PROXY=https://proxy.company.com:8080
   ```
4. Test with curl: `curl -v https://westrock.palantirfoundry.com/api/foundry/core/v1/healthcheck`

### Veza Push Errors

**Error**: `Failed to push to Veza`

**Solutions**:
1. Verify `VEZA_API_KEY` is valid
2. Check Veza instance URL in `.env` file
3. Ensure Veza API endpoint is accessible: `curl -H "Authorization: Bearer YOUR_KEY" https://your-veza.veza.com/api/v2/health`
4. Check Veza API logs for detailed error messages
5. Verify `oaaclient` library version: `pip show oaaclient`

### Missing Data

**Issue**: Fewer resources than expected appear in Veza

**Solutions**:
1. Check Palantir Foundry API token has read access to all resources
2. Run with `--dry-run` to inspect fetched data: `python3 palantir_foundry.py --dry-run`
3. Review logs for warnings and errors
4. Verify user permissions in Palantir Foundry for accessing datasets/projects
5. Check API response limits and pagination

### Python Version Issues

**Error**: `ModuleNotFoundError: No module named 'oaaclient'`

**Solutions**:
1. Ensure virtual environment is activated: `source venv/bin/activate`
2. Reinstall dependencies: `pip install -r requirements.txt`
3. Check Python version: `python3 --version` (must be 3.9+)
4. Clear pip cache: `pip cache purge`

---

## Configuration Reference

### Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `FOUNDRY_BASE_URL` | Yes | Base URL of Palantir Foundry instance | `https://westrock.palantirfoundry.com` |
| `FOUNDRY_API_TOKEN` | Yes | API token for Palantir Foundry authentication | `eyJhbGciOi...` |
| `VEZA_URL` | Yes | Base URL of Veza instance | `https://your-instance.veza.com` |
| `VEZA_API_KEY` | Yes | API key for Veza OAA authentication | `veza_api_...` |

### File Structure

```
palantir-foundry/
├── palantir_foundry.py              # Main integration script
├── requirements.txt                 # Python dependencies
├── .env.template                    # Template for .env file
├── .env                             # Configuration file (created during install)
├── install_palantir_foundry.sh      # Automated installer
├── run_integration.sh               # Wrapper script for cron
├── README.md                        # This file
├── venv/                            # Python virtual environment
└── palantir_foundry_veza_integration.log  # Integration logs
```

---

## API Rate Limiting

Palantir Foundry and Veza both enforce API rate limits:

- **Palantir Foundry**: 
  - Read endpoints: typically 100-1000 requests per minute
  - Pagination: up to 1000 items per page

- **Veza OAA**: 
  - Push endpoint: depends on data size and instance

The integration includes automatic pagination handling and retry logic for transient failures.

---

## Data Mapping

### Resource Types Mapped

| Palantir Foundry | Veza OAA | Properties |
|-----------------|----------|-----------|
| Workspace | Workspace | name, description, owner, createdAt |
| Project | Project | name, description, owner, workspace, createdAt |
| Dataset | Dataset | name, description, owner, project, type, rowCount, createdAt, modifiedAt |
| Resource | Resource | name, description, owner, type, createdAt |

### Permission Types

Custom permissions are created for common Foundry roles:

- `viewer` — Read-only access (DataRead)
- `editor` — Read and write access (DataRead, DataWrite)
- `admin` — Full access (DataRead, DataWrite, MetadataRead, MetadataWrite)

---

## Performance Considerations

### Data Fetching

The integration uses pagination to efficiently fetch large datasets:

- Default page size: Palantir Foundry default (typically 100-1000 items)
- Timeout: 30 seconds per request, 60 seconds for large fetches
- Retry: Automatic retry on transient network failures

### Resource Limits

- **Memory**: ~500 MB for typical instances with 1000+ resources
- **Network**: Bandwidth scales with data volume (~100 MB per 10,000 resources)
- **Time**: Integration typically completes in 2-10 minutes depending on Foundry size

### Optimization Tips

1. Use `--dry-run` to test payload size before pushing to Veza
2. Schedule integration during low-traffic periods
3. Monitor logs for performance metrics
4. Consider running on dedicated server for large instances (>10,000 resources)

---

## Support and Contributing

### Getting Help

- **Issues**: Open an issue on GitHub with:
  - Error message and logs (remove sensitive data)
  - Python version and OS
  - Steps to reproduce
  
- **Documentation**: Check README, logs, and error messages first

### Updating

To update to the latest version:

```bash
cd /path/to/integration
git pull
source venv/bin/activate
pip install -r requirements.txt --upgrade
```

---

## Security Considerations

### Credentials

- **Never commit `.env` file** to version control
- Use service accounts with minimal required permissions
- Rotate API tokens regularly
- Store credentials securely (e.g., in secret management system)

### Network

- Use HTTPS only (enforced by default)
- Consider IP whitelisting on Veza and Palantir Foundry
- Run integration on trusted network segments

### Data

- Integration is read-only from Palantir Foundry
- Only sends data to Veza OAA endpoint
- No data is stored locally except in logs (which should be rotated)

### Log Files

- Review logs regularly for sensitive data exposure
- Implement log rotation to prevent disk space issues
- Consider encrypting log files if stored long-term

---

## Changelog

### Version 1.0.0 (2024-04-27)

- Initial release
- Support for Palantir Foundry workspaces, projects, and datasets
- Integration with Veza OAA API
- Automated installation script
- Comprehensive documentation

---

## License

This integration is part of the OAA_Veza project. See LICENSE file for details.

---

## Contact

For questions or issues related to this integration, please contact:
- **Westrock IT Team**: [contact info]
- **Veza Support**: [support portal]
- **Palantir Support**: [support portal]
