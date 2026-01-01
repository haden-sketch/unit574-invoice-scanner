# Gmail Mechanic Invoice Scanner - Unit 574

Automatically scans Gmail for mechanic invoices related to truck Unit 574.

**VIN:** `3AKJHHDR7KSKE1598`

## Search Terms
- Full VIN: `3AKJHHDR7KSKE1598`
- Last 8: `KSKE1598`
- Last 6: `SE1598`
- Last 4: `1598`
- Unit: `574`, `Unit 574`, `Truck 574`

## What It Finds ✅
- Repair invoices
- Mechanic service records
- Towing bills
- Oil change receipts
- Parts invoices
- Maintenance records
- Shop invoices (Freightliner, TA Petro, Loves, Speedco, etc.)

## What It Skips ❌
- Rate confirmations
- Load tenders
- BOLs / PODs
- Fuel receipts
- Settlements
- Insurance documents

---

## Deployment Options

### Option 1: Railway (Easiest - $5/month)

1. Go to [railway.app](https://railway.app)
2. Create new project → Deploy from GitHub
3. Add your `credentials.json` as a secret file
4. Add environment variables:
   ```
   DOWNLOAD_DIR=/var/invoices/unit_574
   ```
5. Deploy!

### Option 2: DigitalOcean Droplet ($6/month)

```bash
# SSH into your droplet
ssh root@your-droplet-ip

# Install Docker
curl -fsSL https://get.docker.com | sh

# Clone this repo
git clone https://github.com/YOUR_USERNAME/gmail-invoice-scanner.git
cd gmail-invoice-scanner

# Add your credentials.json to ./credentials/
mkdir credentials
# Upload your credentials.json here

# Build and run
docker-compose up -d

# View logs
docker-compose logs -f
```

### Option 3: Render (Free tier available)

1. Go to [render.com](https://render.com)
2. Create new Web Service
3. Connect GitHub repo
4. Set environment variables
5. Add secret file for credentials.json

### Option 4: Google Cloud Run (Pay per use)

```bash
# Install gcloud CLI
# Build and push to Container Registry
gcloud builds submit --tag gcr.io/YOUR_PROJECT/invoice-scanner

# Deploy to Cloud Run
gcloud run deploy invoice-scanner \
  --image gcr.io/YOUR_PROJECT/invoice-scanner \
  --platform managed \
  --region us-central1
```

---

## Setup Instructions

### 1. Get Gmail API Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project (or use existing)
3. Enable the **Gmail API**
4. Go to **Credentials** → Create Credentials → **OAuth 2.0 Client ID**
5. Choose "Desktop Application"
6. Download the JSON file
7. Rename it to `credentials.json`

### 2. First-Time Authentication

The first time you run the scanner, it will open a browser for OAuth:

```bash
python scanner.py
```

This creates `token.json` which is reused for future runs.

### 3. Run the Scanner

```bash
# Local run
python scanner.py

# Or with Docker
docker-compose up
```

### 4. Schedule Regular Scans (Cron)

On your server, add to crontab:

```bash
crontab -e

# Run every 6 hours
0 */6 * * * cd /path/to/scanner && python scanner.py >> /var/log/invoice-scanner.log 2>&1
```

---

## Configuration

Edit `config.py` to customize:

- `SEARCH_DAYS_BACK` - How far back to search (default: 365 days)
- `MECHANIC_KEYWORDS` - Keywords to look for
- `EXCLUDE_KEYWORDS` - Keywords to skip
- `DOWNLOAD_DIR` - Where to save files

---

## Output Structure

```
/var/invoices/unit_574/
├── 2025-01/
│   ├── 20250115_Repair_Invoice_abc123_invoice.pdf
│   └── 20250120_Oil_Change_def456_receipt.pdf
├── 2025-02/
│   └── ...
├── processed_emails.json      # Track what's been scanned
└── scan_summary_20250101.json # Scan results
```

---

## Smart Filtering Logic

The scanner uses a confidence-based classification:

| Signal | Confidence Boost |
|--------|-----------------|
| Full VIN match | +40% |
| Last 8 VIN match | +35% |
| Last 6 VIN match | +25% |
| Last 4 VIN match | +15% |
| "Unit 574" match | +20% |
| Mechanic keywords | +10% each (max 40%) |
| Has PDF attachment | +10% |
| "Invoice" in subject | +15% |

**Minimum 30% confidence required to classify as mechanic invoice.**

Rate confirmations are **immediately excluded** regardless of other signals.

---

## Troubleshooting

### "Credentials file not found"
Make sure `credentials.json` is in the right location.

### "Token expired"
Delete `token.json` and re-authenticate.

### "No emails found"
- Check your search date range in `config.py`
- Verify the VIN/unit number is correct
- Make sure emails actually exist in Gmail

---

## Support

For Rajo Transportation internal use.

