#!/usr/bin/env python3
"""
Gmail Mechanic Invoice Scanner for Unit 574
Truck VIN: 3AKJHHDR7KSKE1598

This script scans Gmail for mechanic invoices related to truck Unit 574,
filtering out rate confirmations and other irrelevant documents.

Author: Auto-generated for Rajo Transportation
"""

import os
import sys
import base64
import re
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Tuple
import logging

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import (
    UNIT_NUMBER, FULL_VIN, VIN_LAST_4, VIN_LAST_6, VIN_LAST_8,
    SEARCH_TERMS, MECHANIC_KEYWORDS, EXCLUDE_KEYWORDS, EXCLUDE_SENDERS,
    DOWNLOAD_DIR, CREDENTIALS_PATH, TOKEN_PATH, SCOPES,
    BATCH_SIZE, SEARCH_DAYS_BACK
)

# =============================================================================
# LOGGING SETUP
# =============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('scanner.log')
    ]
)
logger = logging.getLogger(__name__)


# =============================================================================
# GMAIL AUTHENTICATION
# =============================================================================
def authenticate_gmail():
    """Authenticate with Gmail API and return service object."""
    creds = None
    
    # Check for existing token
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    
    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing expired token...")
            creds.refresh(Request())
        else:
            logger.info("Starting OAuth flow...")
            if not os.path.exists(CREDENTIALS_PATH):
                logger.error(f"Credentials file not found: {CREDENTIALS_PATH}")
                logger.error("Please download credentials.json from Google Cloud Console")
                sys.exit(1)
            
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials for next run
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
            logger.info(f"Token saved to {TOKEN_PATH}")
    
    return build('gmail', 'v1', credentials=creds)


# =============================================================================
# SMART FILTERING LOGIC
# =============================================================================
class InvoiceClassifier:
    """
    Smart classifier to determine if an email is a mechanic invoice.
    Uses multiple signals to make intelligent decisions.
    """
    
    def __init__(self):
        self.mechanic_keywords = [kw.lower() for kw in MECHANIC_KEYWORDS]
        self.exclude_keywords = [kw.lower() for kw in EXCLUDE_KEYWORDS]
        self.search_terms = [term.lower() for term in SEARCH_TERMS]
        self.exclude_senders = [s.lower() for s in EXCLUDE_SENDERS]
    
    def contains_truck_identifier(self, text: str) -> Tuple[bool, List[str]]:
        """Check if text contains any truck identifier."""
        text_lower = text.lower()
        found_terms = []
        
        for term in self.search_terms:
            if term.lower() in text_lower:
                found_terms.append(term)
        
        return len(found_terms) > 0, found_terms
    
    def is_mechanic_related(self, text: str) -> Tuple[bool, List[str]]:
        """Check if text contains mechanic-related keywords."""
        text_lower = text.lower()
        found_keywords = []
        
        for keyword in self.mechanic_keywords:
            if keyword in text_lower:
                found_keywords.append(keyword)
        
        return len(found_keywords) > 0, found_keywords
    
    def should_exclude(self, text: str, sender: str) -> Tuple[bool, str]:
        """Check if email should be excluded."""
        text_lower = text.lower()
        sender_lower = sender.lower()
        
        # Check excluded senders
        for excluded_sender in self.exclude_senders:
            if excluded_sender in sender_lower:
                return True, f"Excluded sender: {excluded_sender}"
        
        # Check excluded keywords
        for keyword in self.exclude_keywords:
            if keyword in text_lower:
                # Special case: "rate confirmation" is a strong signal to exclude
                if "rate" in keyword and "confirm" in keyword:
                    return True, f"Rate confirmation detected"
                # For other keywords, need multiple signals
                exclude_count = sum(1 for kw in self.exclude_keywords if kw in text_lower)
                mechanic_count = sum(1 for kw in self.mechanic_keywords if kw in text_lower)
                
                # If more exclude signals than mechanic signals, exclude
                if exclude_count > mechanic_count:
                    return True, f"More exclusion signals ({exclude_count}) than mechanic signals ({mechanic_count})"
        
        return False, ""
    
    def classify(self, subject: str, body: str, sender: str, 
                 attachment_names: List[str]) -> Dict:
        """
        Classify an email as mechanic invoice or not.
        
        Returns a dict with:
        - is_mechanic_invoice: bool
        - confidence: float (0-1)
        - reason: str
        - found_identifiers: list
        - found_keywords: list
        """
        full_text = f"{subject} {body} {' '.join(attachment_names)}"
        
        result = {
            "is_mechanic_invoice": False,
            "confidence": 0.0,
            "reason": "",
            "found_identifiers": [],
            "found_keywords": []
        }
        
        # Step 1: Check for exclusions FIRST
        should_exclude, exclude_reason = self.should_exclude(full_text, sender)
        if should_exclude:
            result["reason"] = f"EXCLUDED: {exclude_reason}"
            return result
        
        # Step 2: Check for truck identifiers
        has_truck_id, found_ids = self.contains_truck_identifier(full_text)
        result["found_identifiers"] = found_ids
        
        if not has_truck_id:
            result["reason"] = "No truck identifier found (574, VIN, etc.)"
            return result
        
        # Step 3: Check for mechanic-related content
        is_mechanic, found_keywords = self.is_mechanic_related(full_text)
        result["found_keywords"] = found_keywords
        
        if not is_mechanic:
            result["reason"] = f"Found truck ID ({found_ids}) but no mechanic keywords"
            return result
        
        # Step 4: Calculate confidence score
        confidence = 0.0
        
        # VIN matches are strongest signals
        if FULL_VIN.lower() in full_text.lower():
            confidence += 0.4
        elif VIN_LAST_8.lower() in full_text.lower():
            confidence += 0.35
        elif VIN_LAST_6.lower() in full_text.lower():
            confidence += 0.25
        elif VIN_LAST_4.lower() in full_text.lower():
            confidence += 0.15
        
        # Unit number match
        if f"unit {UNIT_NUMBER}".lower() in full_text.lower():
            confidence += 0.2
        elif UNIT_NUMBER in full_text:
            confidence += 0.1
        
        # Mechanic keyword matches
        keyword_score = min(len(found_keywords) * 0.1, 0.4)
        confidence += keyword_score
        
        # Attachment bonus (invoices usually have PDFs)
        has_pdf = any(name.lower().endswith('.pdf') for name in attachment_names)
        if has_pdf:
            confidence += 0.1
        
        # Invoice in subject is strong signal
        if "invoice" in subject.lower():
            confidence += 0.15
        
        confidence = min(confidence, 1.0)
        
        # Need at least 0.3 confidence to classify as invoice
        if confidence >= 0.3:
            result["is_mechanic_invoice"] = True
            result["confidence"] = confidence
            result["reason"] = f"Mechanic invoice detected (confidence: {confidence:.0%})"
        else:
            result["reason"] = f"Low confidence ({confidence:.0%}) - not enough signals"
        
        return result


# =============================================================================
# EMAIL SCANNING
# =============================================================================
class GmailMechanicScanner:
    """Scanner for mechanic invoices in Gmail."""
    
    def __init__(self, service):
        self.service = service
        self.classifier = InvoiceClassifier()
        self.processed_ids = set()
        self.download_dir = Path(DOWNLOAD_DIR)
        
        # Create download directory
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        # Load previously processed email IDs
        self.processed_file = self.download_dir / "processed_emails.json"
        self._load_processed_ids()
    
    def _load_processed_ids(self):
        """Load previously processed email IDs to avoid duplicates."""
        if self.processed_file.exists():
            with open(self.processed_file, 'r') as f:
                data = json.load(f)
                self.processed_ids = set(data.get("processed_ids", []))
            logger.info(f"Loaded {len(self.processed_ids)} previously processed email IDs")
    
    def _save_processed_ids(self):
        """Save processed email IDs."""
        with open(self.processed_file, 'w') as f:
            json.dump({"processed_ids": list(self.processed_ids)}, f)
    
    def build_search_query(self) -> str:
        """Build Gmail search query for truck 574."""
        # Search for any of our identifiers
        # Gmail uses OR by default when terms are in parentheses with OR
        id_queries = [f'"{term}"' for term in [
            FULL_VIN, VIN_LAST_8, UNIT_NUMBER, f"Unit {UNIT_NUMBER}"
        ]]
        
        # Date filter
        date_after = (datetime.now() - timedelta(days=SEARCH_DAYS_BACK)).strftime('%Y/%m/%d')
        
        # Combine with OR and add date filter
        query = f"({' OR '.join(id_queries)}) after:{date_after}"
        
        logger.info(f"Search query: {query}")
        return query
    
    def get_email_details(self, msg_id: str) -> Optional[Dict]:
        """Get full email details including body and attachments."""
        try:
            message = self.service.users().messages().get(
                userId='me', 
                id=msg_id, 
                format='full'
            ).execute()
            
            headers = message.get('payload', {}).get('headers', [])
            
            # Extract headers
            subject = ""
            sender = ""
            date = ""
            
            for header in headers:
                name = header.get('name', '').lower()
                if name == 'subject':
                    subject = header.get('value', '')
                elif name == 'from':
                    sender = header.get('value', '')
                elif name == 'date':
                    date = header.get('value', '')
            
            # Extract body
            body = self._get_body(message.get('payload', {}))
            
            # Extract attachment info
            attachments = self._get_attachments_info(message.get('payload', {}))
            
            return {
                'id': msg_id,
                'subject': subject,
                'sender': sender,
                'date': date,
                'body': body,
                'attachments': attachments,
                'raw_message': message
            }
            
        except HttpError as e:
            logger.error(f"Error fetching email {msg_id}: {e}")
            return None
    
    def _get_body(self, payload: Dict) -> str:
        """Extract email body from payload."""
        body = ""
        
        if 'body' in payload and payload['body'].get('data'):
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('mimeType') == 'text/plain':
                    if part.get('body', {}).get('data'):
                        body += base64.urlsafe_b64decode(
                            part['body']['data']
                        ).decode('utf-8', errors='ignore')
                elif part.get('mimeType') == 'text/html':
                    if part.get('body', {}).get('data'):
                        html = base64.urlsafe_b64decode(
                            part['body']['data']
                        ).decode('utf-8', errors='ignore')
                        # Simple HTML strip
                        body += re.sub(r'<[^>]+>', ' ', html)
                elif 'parts' in part:
                    # Recursive for nested parts
                    body += self._get_body(part)
        
        return body
    
    def _get_attachments_info(self, payload: Dict) -> List[Dict]:
        """Get list of attachments with their info."""
        attachments = []
        
        def extract_attachments(part):
            filename = part.get('filename', '')
            if filename:
                attachments.append({
                    'filename': filename,
                    'mimeType': part.get('mimeType', ''),
                    'attachmentId': part.get('body', {}).get('attachmentId'),
                    'size': part.get('body', {}).get('size', 0)
                })
            
            if 'parts' in part:
                for subpart in part['parts']:
                    extract_attachments(subpart)
        
        extract_attachments(payload)
        return attachments
    
    def download_attachment(self, msg_id: str, attachment: Dict, 
                           email_date: str, subject: str) -> Optional[str]:
        """Download an attachment and save it."""
        try:
            attachment_id = attachment.get('attachmentId')
            if not attachment_id:
                return None
            
            # Get attachment data
            att_data = self.service.users().messages().attachments().get(
                userId='me',
                messageId=msg_id,
                id=attachment_id
            ).execute()
            
            file_data = base64.urlsafe_b64decode(att_data['data'])
            
            # Create organized folder structure
            # Format: YYYY-MM/
            try:
                # Parse date
                date_obj = datetime.strptime(
                    email_date.split(',')[1].strip().split(' +')[0].split(' -')[0].strip(),
                    '%d %b %Y %H:%M:%S'
                )
            except:
                date_obj = datetime.now()
            
            month_folder = self.download_dir / date_obj.strftime('%Y-%m')
            month_folder.mkdir(parents=True, exist_ok=True)
            
            # Create safe filename
            safe_subject = re.sub(r'[^\w\s-]', '', subject)[:50]
            original_name = attachment['filename']
            
            # Add hash to prevent duplicates
            file_hash = hashlib.md5(file_data).hexdigest()[:8]
            
            filename = f"{date_obj.strftime('%Y%m%d')}_{safe_subject}_{file_hash}_{original_name}"
            filename = re.sub(r'\s+', '_', filename)
            
            filepath = month_folder / filename
            
            # Check if already exists
            if filepath.exists():
                logger.info(f"  Skipping duplicate: {filename}")
                return str(filepath)
            
            # Save file
            with open(filepath, 'wb') as f:
                f.write(file_data)
            
            logger.info(f"  Downloaded: {filename}")
            return str(filepath)
            
        except HttpError as e:
            logger.error(f"Error downloading attachment: {e}")
            return None
    
    def scan(self, max_results: int = 500) -> Dict:
        """
        Scan Gmail for mechanic invoices.
        
        Returns summary of scan results.
        """
        logger.info("=" * 60)
        logger.info(f"Starting Gmail scan for Unit {UNIT_NUMBER} mechanic invoices")
        logger.info(f"VIN: {FULL_VIN}")
        logger.info("=" * 60)
        
        results = {
            "total_scanned": 0,
            "invoices_found": 0,
            "attachments_downloaded": 0,
            "skipped_rate_confirmations": 0,
            "skipped_no_identifier": 0,
            "skipped_not_mechanic": 0,
            "skipped_already_processed": 0,
            "invoices": []
        }
        
        try:
            query = self.build_search_query()
            
            # Get message list
            response = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = response.get('messages', [])
            
            if not messages:
                logger.info("No emails found matching search criteria")
                return results
            
            logger.info(f"Found {len(messages)} emails to analyze")
            
            for i, msg_info in enumerate(messages, 1):
                msg_id = msg_info['id']
                
                # Skip already processed
                if msg_id in self.processed_ids:
                    results["skipped_already_processed"] += 1
                    continue
                
                results["total_scanned"] += 1
                
                # Get full email details
                email = self.get_email_details(msg_id)
                if not email:
                    continue
                
                logger.info(f"\n[{i}/{len(messages)}] Analyzing: {email['subject'][:60]}...")
                
                # Classify the email
                attachment_names = [a['filename'] for a in email['attachments']]
                classification = self.classifier.classify(
                    subject=email['subject'],
                    body=email['body'],
                    sender=email['sender'],
                    attachment_names=attachment_names
                )
                
                if classification['is_mechanic_invoice']:
                    logger.info(f"  ✓ INVOICE FOUND - {classification['reason']}")
                    logger.info(f"    Identifiers: {classification['found_identifiers']}")
                    logger.info(f"    Keywords: {classification['found_keywords'][:5]}")
                    
                    results["invoices_found"] += 1
                    
                    invoice_record = {
                        "id": msg_id,
                        "subject": email['subject'],
                        "sender": email['sender'],
                        "date": email['date'],
                        "confidence": classification['confidence'],
                        "identifiers": classification['found_identifiers'],
                        "keywords": classification['found_keywords'],
                        "attachments_downloaded": []
                    }
                    
                    # Download attachments
                    for attachment in email['attachments']:
                        # Only download PDFs and images
                        mime = attachment.get('mimeType', '').lower()
                        filename = attachment.get('filename', '').lower()
                        
                        if (mime.startswith('application/pdf') or 
                            mime.startswith('image/') or
                            filename.endswith(('.pdf', '.png', '.jpg', '.jpeg', '.tiff'))):
                            
                            filepath = self.download_attachment(
                                msg_id, attachment, 
                                email['date'], email['subject']
                            )
                            if filepath:
                                results["attachments_downloaded"] += 1
                                invoice_record["attachments_downloaded"].append(filepath)
                    
                    results["invoices"].append(invoice_record)
                    
                else:
                    # Log why it was skipped
                    reason = classification['reason']
                    if "EXCLUDED" in reason:
                        results["skipped_rate_confirmations"] += 1
                        logger.info(f"  ✗ Skipped (rate con/excluded): {reason}")
                    elif "No truck identifier" in reason:
                        results["skipped_no_identifier"] += 1
                        logger.info(f"  ✗ Skipped (no ID): {reason}")
                    else:
                        results["skipped_not_mechanic"] += 1
                        logger.info(f"  ✗ Skipped (not mechanic): {reason}")
                
                # Mark as processed
                self.processed_ids.add(msg_id)
            
            # Save processed IDs
            self._save_processed_ids()
            
            # Save results summary
            summary_file = self.download_dir / f"scan_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(summary_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            logger.info("\n" + "=" * 60)
            logger.info("SCAN COMPLETE")
            logger.info("=" * 60)
            logger.info(f"Total emails scanned: {results['total_scanned']}")
            logger.info(f"Mechanic invoices found: {results['invoices_found']}")
            logger.info(f"Attachments downloaded: {results['attachments_downloaded']}")
            logger.info(f"Skipped (rate confirmations): {results['skipped_rate_confirmations']}")
            logger.info(f"Skipped (no truck identifier): {results['skipped_no_identifier']}")
            logger.info(f"Skipped (not mechanic related): {results['skipped_not_mechanic']}")
            logger.info(f"Skipped (already processed): {results['skipped_already_processed']}")
            logger.info(f"\nDownload directory: {self.download_dir}")
            logger.info(f"Summary saved to: {summary_file}")
            
            return results
            
        except HttpError as e:
            logger.error(f"Gmail API error: {e}")
            raise


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================
def main():
    """Main entry point."""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║     GMAIL MECHANIC INVOICE SCANNER - UNIT 574                ║
    ║     VIN: 3AKJHHDR7KSKE1598                                   ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Authenticate
    logger.info("Authenticating with Gmail...")
    service = authenticate_gmail()
    logger.info("Authentication successful!")
    
    # Create scanner and run
    scanner = GmailMechanicScanner(service)
    results = scanner.scan(max_results=500)
    
    return results


if __name__ == "__main__":
    main()

