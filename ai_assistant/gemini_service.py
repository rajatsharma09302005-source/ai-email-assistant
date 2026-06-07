from google import genai
from decouple import config
import logging
import time

logger = logging.getLogger(__name__)

# ✅ NEW: Using updated google-genai package
GEMINI_MODEL = 'gemini-3.1-flash-lite'

def get_gemini_client():
    """
    Initialize and return Gemini client.
    """
    try:
        client = genai.Client(api_key=config('GEMINI_API_KEY', default=''))
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Gemini client: {str(e)}")
        return None


def get_tone_instruction(tone):
    """
    Returns tone-specific writing instructions for Gemini.
    """
    tone_map = {
        'formal': (
            "Write in a formal, professional tone. "
            "Use proper salutations and closings. "
            "Avoid contractions and casual language. "
            "Be respectful and courteous."
        ),
        'friendly': (
            "Write in a warm, friendly tone. "
            "Be approachable and personable. "
            "You can use light contractions. "
            "Sound genuine and caring."
        ),
        'concise': (
            "Write in a concise, to-the-point tone. "
            "Keep it brief and clear. "
            "Avoid unnecessary words or filler phrases. "
            "Get straight to the point."
        ),
        'assertive': (
            "Write in a confident, assertive tone. "
            "Be direct and clear about expectations. "
            "Show confidence without being rude. "
            "Use active voice throughout."
        ),
        'professional': (
            "Write in a professional business tone. "
            "Be clear, respectful, and competent. "
            "Use appropriate business language. "
            "Maintain a neutral, objective voice."
        ),
    }
    return tone_map.get(tone, tone_map['professional'])


def compose_email(description, tone='professional', recipient_name=''):
    """
    Generate a complete email from a brief description.
    """
    client = get_gemini_client()
    if not client:
        return None

    tone_instruction = get_tone_instruction(tone)
    recipient_part = f"addressed to {recipient_name}" if recipient_name else ""

    prompt = f"""
You are a professional email writing assistant.

Task: Write a complete email {recipient_part} based on this description:
"{description}"

Tone Instructions: {tone_instruction}

Requirements:
- Write a clear, appropriate subject line
- Write a complete email body with greeting, main content, and closing
- Format the response EXACTLY as shown below (no extra text):

SUBJECT: [subject line here]

BODY:
[email body here]

Important: Only output the subject and body in the format above. Nothing else.
"""

    try:
        start_time = time.time()
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )
        processing_time = time.time() - start_time

        if not response or not response.text:
            logger.error("Gemini returned empty response for compose")
            return None

        result = parse_email_response(response.text)
        result['processing_time'] = processing_time
        logger.info(f"Email composed successfully in {processing_time:.2f}s")
        return result

    except Exception as e:
        logger.error(f"Gemini compose error: {str(e)}")
        return None


def improve_email(draft, tone='professional'):
    """
    Improve and polish an existing email draft.
    """
    client = get_gemini_client()
    if not client:
        return None

    tone_instruction = get_tone_instruction(tone)

    prompt = f"""
You are a professional email editor.

Task: Improve and polish this email draft:

--- ORIGINAL EMAIL ---
{draft}
--- END OF EMAIL ---

Tone Instructions: {tone_instruction}

Instructions:
- Fix grammar, spelling, and punctuation errors
- Improve clarity and flow
- Make it more professional and effective
- Keep the original meaning and intent
- Improve the subject line if needed

Format your response EXACTLY as shown below:

SUBJECT: [improved subject line]

BODY:
[improved email body]

Important: Only output the improved subject and body. Nothing else.
"""

    try:
        start_time = time.time()
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )
        processing_time = time.time() - start_time

        if not response or not response.text:
            logger.error("Gemini returned empty response for improve")
            return None

        result = parse_email_response(response.text)
        result['processing_time'] = processing_time
        logger.info(f"Email improved successfully in {processing_time:.2f}s")
        return result

    except Exception as e:
        logger.error(f"Gemini improve error: {str(e)}")
        return None


def generate_reply(received_email, tone='professional', additional_context=''):
    """
    Generate a smart reply to a received email.
    """
    client = get_gemini_client()
    if not client:
        return None

    tone_instruction = get_tone_instruction(tone)
    context_part = f"\nAdditional context: {additional_context}" if additional_context else ""

    prompt = f"""
You are a professional email assistant helping to write a reply.

Task: Write a professional reply to this email:

--- RECEIVED EMAIL ---
{received_email}
--- END OF EMAIL ---
{context_part}

Tone Instructions: {tone_instruction}

Instructions:
- Acknowledge the sender's message appropriately
- Address all points raised in the original email
- Be helpful and constructive
- Keep the reply focused and relevant

Format your response EXACTLY as shown below:

SUBJECT: [reply subject line starting with Re:]

BODY:
[reply email body]

Important: Only output the subject and body. Nothing else.
"""

    try:
        start_time = time.time()
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )
        processing_time = time.time() - start_time

        if not response or not response.text:
            logger.error("Gemini returned empty response for reply")
            return None

        result = parse_email_response(response.text)
        result['processing_time'] = processing_time
        logger.info(f"Reply generated successfully in {processing_time:.2f}s")
        return result

    except Exception as e:
        logger.error(f"Gemini reply error: {str(e)}")
        return None


def generate_subject(email_body, tone='professional'):
    """
    Generate multiple subject line suggestions for an email.
    """
    client = get_gemini_client()
    if not client:
        return None

    tone_instruction = get_tone_instruction(tone)

    prompt = f"""
You are a professional email subject line writer.

Task: Generate 5 subject line suggestions for this email:

--- EMAIL BODY ---
{email_body}
--- END OF EMAIL ---

Tone Instructions: {tone_instruction}

Requirements:
- Each subject should be clear and compelling
- Keep subjects under 60 characters
- Make them relevant to the email content
- Vary the style and approach for each suggestion

Format your response EXACTLY as shown below (numbered list only):

1. [first subject line]
2. [second subject line]
3. [third subject line]
4. [fourth subject line]
5. [fifth subject line]

Important: Only output the numbered list. Nothing else.
"""

    try:
        start_time = time.time()
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )
        processing_time = time.time() - start_time

        if not response or not response.text:
            logger.error("Gemini returned empty response for subject")
            return None

        lines = response.text.strip().split('\n')
        subjects = []
        for line in lines:
            line = line.strip()
            if line and line[0].isdigit():
                subject = line.split('.', 1)[-1].strip()
                if subject:
                    subjects.append(subject)

        logger.info(f"Subjects generated: {len(subjects)} suggestions")
        return {
            'subjects': subjects[:5],
            'processing_time': processing_time
        }

    except Exception as e:
        logger.error(f"Gemini subject error: {str(e)}")
        return None


def summarize_email(email_body):
    """
    Summarize a long email into key points.
    """
    client = get_gemini_client()
    if not client:
        return None

    prompt = f"""
You are a professional email summarizer.

Task: Summarize this email clearly and concisely:

--- EMAIL ---
{email_body}
--- END OF EMAIL ---

Requirements:
- Write a 2-3 sentence summary
- Extract the 3 most important key points
- Identify any action items required

Format your response EXACTLY as shown below:

SUMMARY:
[2-3 sentence summary here]

KEY POINTS:
- [key point 1]
- [key point 2]
- [key point 3]

ACTION ITEMS:
- [action item 1, or "None" if no actions needed]

Important: Only output in the format above. Nothing else.
"""

    try:
        start_time = time.time()
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )
        processing_time = time.time() - start_time

        if not response or not response.text:
            logger.error("Gemini returned empty response for summarize")
            return None

        result = parse_summary_response(response.text)
        result['processing_time'] = processing_time
        logger.info(f"Email summarized successfully in {processing_time:.2f}s")
        return result

    except Exception as e:
        logger.error(f"Gemini summarize error: {str(e)}")
        return None


def parse_email_response(text):
    """
    Parse Gemini response into subject and body.
    """
    subject = ''
    body = ''

    try:
        lines = text.strip().split('\n')
        body_start = False
        body_lines = []

        for line in lines:
            if line.startswith('SUBJECT:'):
                subject = line.replace('SUBJECT:', '').strip()
            elif line.strip() == 'BODY:':
                body_start = True
            elif body_start:
                body_lines.append(line)

        body = '\n'.join(body_lines).strip()

        if not subject and not body:
            subject = 'Email'
            body = text.strip()

    except Exception as e:
        logger.error(f"Error parsing email response: {str(e)}")
        subject = 'Email'
        body = text.strip()

    return {'subject': subject, 'body': body}


def parse_summary_response(text):
    """
    Parse Gemini summary response.
    """
    summary = ''
    key_points = []
    action_items = []

    try:
        current_section = None

        for line in text.strip().split('\n'):
            line = line.strip()
            if line.startswith('SUMMARY:'):
                current_section = 'summary'
                val = line.replace('SUMMARY:', '').strip()
                if val:
                    summary = val
            elif line.startswith('KEY POINTS:'):
                current_section = 'key_points'
            elif line.startswith('ACTION ITEMS:'):
                current_section = 'action_items'
            elif line.startswith('- ') and current_section == 'key_points':
                key_points.append(line[2:].strip())
            elif line.startswith('- ') and current_section == 'action_items':
                action_items.append(line[2:].strip())
            elif current_section == 'summary' and line and not line.startswith('KEY'):
                summary = (summary + ' ' + line).strip()

    except Exception as e:
        logger.error(f"Error parsing summary response: {str(e)}")
        summary = text.strip()

    return {
        'summary': summary,
        'key_points': key_points,
        'action_items': action_items,
    }