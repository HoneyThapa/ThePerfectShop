# PostgreSQL Local Setup Guide

## Quick Installation

### macOS (using Homebrew)
```bash
# Install PostgreSQL
brew install postgresql

# Start PostgreSQL service
brew services start postgresql

# Create a postgres user (if needed)
createuser -s postgres

# Set password for postgres user
psql -U postgres -c "ALTER USER postgres PASSWORD 'postgres';"
```

### Ubuntu/Debian
```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Set password for postgres user
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';"
```

### Windows
1. Download PostgreSQL from: https://www.postgresql.org/download/windows/
2. Run the installer
3. Set password as `postgres` during installation
4. Make sure it starts on port 5432

## Verify Installation

```bash
# Test connection
psql -U postgres -h localhost -p 5432 -c "SELECT version();"
```

## Run the Setup Script

Once PostgreSQL is installed and running:

```bash
cd backend
python setup_local_db.py
```

This will:
- Create the `ThePerfectShop` database
- Create all required tables
- Insert realistic dummy data for a grocery store
- Set up 3 stores with 15 products and 60 days of sales history

## Troubleshooting

### Connection Issues
- Make sure PostgreSQL is running: `brew services list | grep postgresql` (macOS)
- Check if port 5432 is available: `lsof -i :5432`
- Verify credentials: username=`postgres`, password=`postgres`

### Permission Issues
- On Linux, you might need to configure PostgreSQL authentication
- Edit `/etc/postgresql/*/main/pg_hba.conf` and set local connections to `trust` or `md5`

### Database Already Exists
- The script will skip database creation if it already exists
- To start fresh: `dropdb -U postgres ThePerfectShop` then run the script again