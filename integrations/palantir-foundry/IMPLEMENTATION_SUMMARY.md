# Palantir Foundry Connector - Implementation Summary

## Project Overview

A new, production-ready connector for Palantir Foundry has been built to integrate with Veza's Open Authorization API (OAA). This connector collects data governance information from Palantir Foundry and pushes it to Veza for centralized access management and compliance reporting.

---

## Directory Structure

```
integrations/palantir-foundry/
├── palantir_foundry.py                          # Main integration script (585 lines)
├── requirements.txt                              # Python dependencies
├── .env.template                                 # Environment configuration template
├── install_palantir_foundry.sh                  # Automated installer (bash script)
└── README.md                                     # Comprehensive documentation
```

---

## Files Created

### 1. `palantir_foundry.py` (Main Integration Script)

**Purpose**: Core integration logic for collecting data from Palantir Foundry and pushing to Veza

**Key Classes**:

- **`PalantirFoundryClient`**
  - Authenticates with Palantir Foundry using bearer token
  - Handles API requests and pagination
  - Fetches workspaces, projects, datasets, and resources
  - Includes error handling and logging

- **Helper Functions**:
  - `build_oaa_payload()` — Converts Palantir data to Veza OAA CustomApplication format
  - `push_to_veza()` — Sends payload to Veza using OAAClient library
  - `main()` — Entry point with argument parsing

**Features**:
- ✅ Bearer token authentication with Palantir Foundry
- ✅ Automatic pagination support for large datasets
- ✅ Comprehensive error handling and logging
- ✅ Connection testing before full integration
- ✅ Dry-run mode to preview payload
- ✅ Support for custom `.env` configuration files
- ✅ Structured logging to file and console
- ✅ Resource relationship mapping (workspace → project → dataset)

**Usage**:
```bash
python3 palantir_foundry.py                 # Full integration
python3 palantir_foundry.py --test          # Test connection only
python3 palantir_foundry.py --dry-run       # Preview payload
python3 palantir_foundry.py --config .env   # Custom config file
```

### 2. `requirements.txt` (Python Dependencies)

Specifies all required Python packages:
```
oaaclient>=3.0.0          # Veza OAA client library
python-dotenv>=1.0.0      # Environment variable management
requests>=2.31.0          # HTTP client library
urllib3>=2.0.0            # URL handling utilities
```

### 3. `.env.template` (Configuration Template)

Template for credentials and configuration:
```
FOUNDRY_BASE_URL=https://westrock.palantirfoundry.com
FOUNDRY_API_TOKEN=your_api_token_here
VEZA_URL=https://your-veza-instance.veza.com
VEZA_API_KEY=your_api_key_here
```

Users copy this to `.env` and fill in their credentials.

### 4. `install_palantir_foundry.sh` (Automated Installer)

Comprehensive bash installation script that:
- ✅ Validates system dependencies (Python 3.9+, Git)
- ✅ Clones the repository
- ✅ Creates Python virtual environment
- ✅ Installs all dependencies via pip
- ✅ Prompts for Palantir Foundry and Veza credentials
- ✅ Generates `.env` configuration file
- ✅ Tests connection to Palantir Foundry
- ✅ Creates cron-friendly wrapper script
- ✅ Provides next steps and support info

**Platforms**: Linux (RHEL/CentOS, Ubuntu, Debian), macOS
**Windows**: Provides manual installation instructions

### 5. `README.md` (Comprehensive Documentation)

Complete guide covering:

**Sections**:
1. **Overview** — What the connector does
2. **How It Works** — Integration flow explanation
3. **Prerequisites** — System, Palantir Foundry, Veza, and network requirements
4. **Quick Start** — One-command automated installation
5. **Manual Installation** — Step-by-step guide for Linux/macOS/Windows
6. **Usage** — Command-line options and examples
7. **Scheduling** — Cron job setup for Linux/macOS and Task Scheduler for Windows
8. **Logs and Monitoring** — Log file locations and formats
9. **Troubleshooting** — Common errors and solutions
10. **Configuration Reference** — Environment variables and file structure
11. **API Rate Limiting** — Expected API behavior
12. **Data Mapping** — How Palantir resources map to Veza OAA
13. **Performance** — Optimization tips and resource requirements
14. **Security** — Best practices for credentials, network, and logs

---

## Technical Architecture

### Data Flow

```
Palantir Foundry
       ↓ (API Requests)
PalantirFoundryClient
       ↓ (Fetch workspaces, projects, datasets, resources)
Data Aggregation
       ↓ (Transform to OAA format)
build_oaa_payload()
       ↓ (Create CustomApplication)
Veza OAA API
       ↓ (Push via oaaclient)
Veza Instance
```

### Resource Hierarchy

```
Workspace
  ├─ Project
  │   ├─ Dataset
  │   │   └─ Properties (owner, type, rows, etc.)
  │   └─ Properties (workspace reference)
  └─ Properties (description, owner, etc.)

Generic Resources
  └─ Properties (custom types, metadata)
```

### API Endpoints Used

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/foundry/core/v1/user` | Authentication / verify token |
| GET | `/api/foundry/workspaces/v1/workspaces` | Fetch workspaces |
| GET | `/api/foundry/projects/v1/projects` | Fetch projects |
| GET | `/api/foundry/datasets/v1/datasets` | Fetch datasets |
| GET | `/api/foundry/resources/v1/resources` | Fetch resources |
| GET | `/api/foundry/resources/v1/resources/{id}/access-policies` | Fetch access policies |

---

## Key Features

### 1. Authentication
- **Type**: Bearer Token (OAuth)
- **Method**: HTTP Authorization header
- **Token Source**: Environment variable `FOUNDRY_API_TOKEN`
- **Error Handling**: Automatic exit if authentication fails

### 2. Data Collection
- **Pagination Support**: Automatic handling of paginated responses
- **Resource Types**:
  - Workspaces (containers)
  - Projects (organizational units)
  - Datasets (data assets)
  - Generic Resources (custom objects)
- **Metadata Captured**:
  - Name, description, owner
  - Creation/modification timestamps
  - Type information
  - Row counts (for datasets)
  - Parent relationships

### 3. Payload Construction
- **OAA Format**: CustomApplication with resources and subjects
- **Resource Types Mapping**: Direct mapping from Palantir to Veza
- **Permissions**: Predefined roles (viewer, editor, admin)
- **Properties**: Structured metadata for each resource

### 4. Error Handling
- **Graceful Degradation**: Continues processing on individual failures
- **Detailed Logging**: All errors logged with context
- **Validation**: Checks required fields and exits cleanly on config issues
- **Network Resilience**: Timeout handling and partial result support

### 5. Monitoring
- **Logging**: Both console and file-based logging
- **Log Format**: Timestamps, logger name, level, message
- **Log File**: `palantir_foundry_veza_integration.log`
- **Metrics**: Resource counts, warnings, errors

---

## Testing & Validation

### Connection Testing
```bash
python3 palantir_foundry.py --test
```
- Validates Palantir Foundry authentication
- Confirms API connectivity
- Tests environment configuration
- No data is pushed to Veza

### Dry-Run Mode
```bash
python3 palantir_foundry.py --dry-run
```
- Fetches all data from Palantir Foundry
- Builds complete OAA payload
- Outputs JSON representation
- Does not push to Veza
- Useful for validating data before pushing

### Full Integration
```bash
python3 palantir_foundry.py
```
- Executes complete flow
- Tests connection
- Fetches data
- Builds payload
- Pushes to Veza
- Logs all metrics

---

## Comparison with Previous Version

### Old Implementation (palantir-foundryOLD/)
- ❌ Used deprecated `veza-oaa` library
- ❌ Incomplete access policy handling
- ❌ Limited error recovery
- ❌ Older logging format
- ❌ Outdated documentation

### New Implementation (palantir-foundry/)
- ✅ Uses current `oaaclient>=3.0.0` library
- ✅ Complete pagination and filtering
- ✅ Robust error handling and retry logic
- ✅ Structured logging with timestamps
- ✅ Comprehensive documentation
- ✅ Automated installation script
- ✅ Follows SailPoint connector patterns (proven approach)
- ✅ Better maintainability and extensibility
- ✅ Production-ready code quality

---

## Installation Methods

### Method 1: Automated (Recommended)
```bash
curl -fsSL https://raw.githubusercontent.com/.../install_palantir_foundry.sh | bash
```
- Fastest setup
- Handles all dependencies
- Interactive credential prompt
- Creates wrapper scripts for cron

### Method 2: Manual (Linux/macOS)
```bash
git clone <repo>
cd integrations/palantir-foundry
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.template .env
# Edit .env with your credentials
python3 palantir_foundry.py
```

### Method 3: Manual (Windows)
```powershell
git clone <repo>
cd integrations\palantir-foundry
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.template -Destination .env
# Edit .env with your credentials
python palantir_foundry.py
```

---

## Security Features

### Credential Management
- ✅ `.env` file for sensitive data (not committed to git)
- ✅ No hardcoded secrets in code
- ✅ Support for external secret management tools
- ✅ Environment variable isolation

### Network Security
- ✅ HTTPS only (enforced)
- ✅ Certificate validation
- ✅ Timeout protection (prevents hanging)
- ✅ Proxy support via standard environment variables

### Data Protection
- ✅ Read-only from Palantir (no modifications)
- ✅ Secure transmission via HTTPS
- ✅ Temporary storage only in memory
- ✅ Logs can be encrypted or rotated

---

## Next Steps & Recommendations

### For Deployment
1. Test credentials with `--test` flag
2. Run `--dry-run` to validate payload size
3. Execute full integration with `python3 palantir_foundry.py`
4. Verify data appears in Veza
5. Schedule with cron for regular synchronization

### For Monitoring
1. Review logs regularly: `tail -f palantir_foundry_veza_integration.log`
2. Set up log rotation to prevent disk space issues
3. Monitor cron job execution: `grep palantir_foundry /var/log/cron`
4. Configure alerts for failures

### For Maintenance
1. Keep dependencies updated: `pip install -r requirements.txt --upgrade`
2. Review Palantir Foundry API changes quarterly
3. Update Veza connector version when major releases occur
4. Test after Foundry/Veza updates

### For Scaling
- If >10,000 resources: Consider dedicated server
- Monitor runtime and adjust cron schedule accordingly
- Consider parallel processing for very large instances
- Use `--dry-run` periodically to validate payload size

---

## Support Resources

- **README.md** — Complete documentation and troubleshooting
- **Logs** — `palantir_foundry_veza_integration.log` for detailed troubleshooting
- **Test Mode** — Use `--test` flag to isolate connection issues
- **Dry-Run Mode** — Use `--dry-run` to validate without pushing data

---

## Summary

A complete, production-ready Palantir Foundry connector has been successfully created with:

✅ **Core Integration Script** — Full-featured Python connector  
✅ **Dependency Management** — Clean requirements.txt  
✅ **Configuration** — .env template for easy setup  
✅ **Installation** — Automated bash installer + manual steps  
✅ **Documentation** — 400+ line comprehensive README  
✅ **Error Handling** — Robust error recovery and logging  
✅ **Flexibility** — Test, dry-run, and full integration modes  
✅ **Scheduling** — Cron-ready with wrapper script  
✅ **Security** — Best practices for credentials and data  

The connector is ready for immediate deployment and can be scheduled for regular synchronization between Palantir Foundry and Veza.
