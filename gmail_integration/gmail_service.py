import base64
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


def get_gmail_service(user_profile):
    """
    Build and return Gmail API service client using user's stored tokens.
    
    Args:
        user_profile: UserProfile instance with Gmail tokens
        
    Returns:
        Gmail API service object or None if failed
    """
    try:
        # Build credentials from stored tokens
        credentials = Credentials(
            token=user_profile.gmail_access_token,
            refresh_token=user_profile.gmail_refresh_token,
            token_uri='https://oauth2.googleapis.com/token',
            client_id='',
            client_secret='',
        )

        # Build Gmail service
        service = build('gmail', 'v1', credentials=credentials)
        return service

    except Exception as e:
        logger.error(f"Failed to build Gmail service: {str(e)}")
        return None


def parse_email_message(message):
    """
    Parse raw Gmail message into a clean dictionary.
    
    Args:
        message: Raw Gmail API message object
        
    Returns:
        Dictionary with parsed email fields
    """
    headers = message.get('payload', {}).get('headers', [])

    # Extract headers
    header_dict = {}
    for header in headers:
        header_dict[header['name'].lower()] = header['value']

    # Extract body
    body = ''
    html_body = ''
    payload = message.get('payload', {})

    # Handle different email formats
    if 'parts' in payload:
        for part in payload['parts']:
            mime_type = part.get('mimeType', '')
            data = part.get('body', {}).get('data', '')
            if data:
                decoded = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                if mime_type == 'text/plain':
                    body = decoded
                elif mime_type == 'text/html':
                    html_body = decoded
    else:
        # Single part email
        data = payload.get('body', {}).get('data', '')
        if data:
            body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')

    return {
        'gmail_message_id': message.get('id', ''),
        'thread_id': message.get('threadId', ''),
        'sender': header_dict.get('from', ''),
        'recipient': header_dict.get('to', ''),
        'cc': header_dict.get('cc', ''),
        'subject': header_dict.get('subject', '(No Subject)'),
        'body': body,
        'html_body': html_body,
        'is_read': 'UNREAD' not in message.get('labelIds', []),
        'is_sent': 'SENT' in message.get('labelIds', []),
    }


def fetch_inbox_emails(service, max_results=20):
    """
    Fetch emails from Gmail inbox.
    
    Args:
        service: Gmail API service object
        max_results: Number of emails to fetch (default 20)
        
    Returns:
        List of parsed email dictionaries
    """
    try:
        # Get list of messages from inbox
        results = service.users().messages().list(
            userId='me',
            labelIds=['INBOX'],
            maxResults=max_results
        ).execute()

        messages = results.get('messages', [])
        emails = []

        for msg in messages:
            # Fetch full message details
            message = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='full'
            ).execute()

            parsed = parse_email_message(message)
            emails.append(parsed)

        return emails

    except HttpError as e:
        logger.error(f"Gmail API error fetching inbox: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Error fetching inbox: {str(e)}")
        return []


def fetch_sent_emails(service, max_results=20):
    """
    Fetch sent emails from Gmail.
    
    Args:
        service: Gmail API service object
        max_results: Number of emails to fetch
        
    Returns:
        List of parsed email dictionaries
    """
    try:
        results = service.users().messages().list(
            userId='me',
            labelIds=['SENT'],
            maxResults=max_results
        ).execute()

        messages = results.get('messages', [])
        emails = []

        for msg in messages:
            message = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='full'
            ).execute()

            parsed = parse_email_message(message)
            parsed['is_sent'] = True
            emails.append(parsed)

        return emails

    except HttpError as e:
        logger.error(f"Gmail API error fetching sent: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Error fetching sent emails: {str(e)}")
        return []


def send_email_via_gmail(service, to, subject, body, cc='', bcc=''):
    """
    Send an email via Gmail API.
    
    Args:
        service: Gmail API service object
        to: Recipient email address
        subject: Email subject
        body: Email body text
        cc: CC recipients (optional)
        bcc: BCC recipients (optional)
        
    Returns:
        Dictionary with sent message info or None if failed
    """
    try:
        # Create email message
        message = MIMEMultipart()
        message['to'] = to
        message['subject'] = subject

        if cc:
            message['cc'] = cc
        if bcc:
            message['bcc'] = bcc

        # Attach body
        message.attach(MIMEText(body, 'plain'))

        # Encode message
        raw_message = base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode('utf-8')

        # Send via Gmail API
        sent_message = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()

        logger.info(f"Email sent successfully: {sent_message.get('id')}")
        return sent_message

    except HttpError as e:
        logger.error(f"Gmail API error sending email: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return None


def reply_to_email(service, thread_id, message_id, to, subject, body):
    """
    Reply to an existing email thread.
    
    Args:
        service: Gmail API service object
        thread_id: Gmail thread ID
        message_id: Original message ID to reply to
        to: Recipient email
        subject: Reply subject (usually Re: original subject)
        body: Reply body text
        
    Returns:
        Dictionary with sent reply info or None if failed
    """
    try:
        # Create reply message
        message = MIMEMultipart()
        message['to'] = to
        message['subject'] = f"Re: {subject}" if not subject.startswith('Re:') else subject
        message['In-Reply-To'] = message_id
        message['References'] = message_id

        # Attach body
        message.attach(MIMEText(body, 'plain'))

        # Encode message
        raw_message = base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode('utf-8')

        # Send reply in same thread
        sent_reply = service.users().messages().send(
            userId='me',
            body={
                'raw': raw_message,
                'threadId': thread_id
            }
        ).execute()

        logger.info(f"Reply sent successfully: {sent_reply.get('id')}")
        return sent_reply

    except HttpError as e:
        logger.error(f"Gmail API error replying: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error replying to email: {str(e)}")
        return None


def get_email_thread(service, thread_id):
    """
    Get full email thread/conversation.
    
    Args:
        service: Gmail API service object
        thread_id: Gmail thread ID
        
    Returns:
        List of parsed emails in the thread
    """
    try:
        thread = service.users().threads().get(
            userId='me',
            id=thread_id,
            format='full'
        ).execute()

        messages = thread.get('messages', [])
        emails = [parse_email_message(msg) for msg in messages]
        return emails

    except HttpError as e:
        logger.error(f"Gmail API error getting thread: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Error getting thread: {str(e)}")
        return []