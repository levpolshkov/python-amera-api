from app.clients.twilio import BaseTwilioClient
from twilio.base.exceptions import TwilioRestException
import os
import time
from datetime import datetime
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.twofactor.totp import TOTP
from cryptography.hazmat.primitives.twofactor import InvalidToken
from cryptography.hazmat.primitives.hashes import SHA1
from app.config import settings
from app.util.db import source
import app.util.email as sendmail
from app.exceptions.data import DuplicateKeyError, DataMissingError, RelationshipReferenceError
import logging
logger = logging.getLogger(__name__)

class VerificationDA(object):
    source = source

    @classmethod
    def get_twilio_client(cls):
        client = BaseTwilioClient()
        return client.client

    @classmethod
    def get_totp(cls):
        key = os.urandom(20)
        timeout = 30
        token_time = time.time()
        totp_length = settings.get("services.twilio.totp_length")
        totp = TOTP(key, totp_length, SHA1(), timeout,
                    backend=default_backend())
        token = totp.generate(token_time).decode('utf8')
        return (token, token_time)

    @classmethod
    def verify_contact(cls, contact_type, value, user_token):
        verification_entry = cls.get_verification_entry(contact_type, value)
        logger.debug(verification_entry)

        if verification_entry:

            # Check if has expired
            totp_lifetime_seconds = int(settings.get(
                "services.twilio.totp_lifetime_seconds"))
            token_age_seconds = int(
                (datetime.now() - verification_entry["token_time"]).seconds)

            if verification_entry["token"] != user_token:
                return 'mismatch'
            elif (verification_entry["token"] == user_token) and (token_age_seconds > totp_lifetime_seconds):
                cls.delete_verification_entry(
                    contact_type, verification_entry["entry_id"])
                return 'expired'
            else:
                cls.delete_verification_entry(
                    contact_type, verification_entry["entry_id"])
                return 'match'
        return 'no_entry'

    @classmethod
    def create_verification_entry(cls, contact_type, value):
        try:
            if contact_type == 'cell':
                (message_sid, token, token_time) = cls.sendSMS(value)
                ISOtimestamp = datetime.fromtimestamp(token_time).isoformat()

                if message_sid:
                    query = ("""
                        INSERT INTO cell_token
                        (cell_phone, token, time, sms_sid)
                        VALUES (%s, %s, TIMESTAMP %s, %s)
                    """)
                    params = (value, token, ISOtimestamp, message_sid)
                    cls.source.execute(query, params)
                    cls.source.commit()
                    return True
            elif contact_type == 'email':
                # Send email here
                (token, token_time) = cls.sendMail(value)
                ISOtimestamp = datetime.fromtimestamp(token_time).isoformat()
                query = ("""
                    INSERT INTO email_token
                    (email, token, time)
                    VALUES (%s, %s, TIMESTAMP %s)
                """)
                params = (value, token, ISOtimestamp)
                cls.source.execute(query, params)
                cls.source.commit()
                return True
        except Exception as e:
            logger.exception(e)

    @classmethod
    def delete_verification_entry(cls, contact_type, id):
        try:
            query = None
            if contact_type == 'cell':
                query = ("""
                    DELETE FROM cell_token
                    WHERE id = %s
                """)
            elif contact_type == 'email':
                query = ("""
                    DELETE FROM email_token
                    WHERE id = %s
                """)
            params = (id,)
            cls.source.execute(query, params)
            cls.source.commit()
        except Exception as e:
            logger.exception(e)

    @classmethod
    def get_verification_entry(cls, contact_type, value):
        if contact_type == 'cell':
            try:
                query = ("""SELECT
                        id as entry_id,
                        token,
                        time
                    FROM cell_token
                    WHERE cell_phone = %s AND time = (SELECT MAX(time) FROM cell_token)""")
                params = (value,)
                cls.source.execute(query, params)
                if cls.source.has_results():
                    for (
                        entry_id,
                        token,
                        time
                    ) in cls.source.cursor:
                        verification_entry = {
                            "entry_id": entry_id,
                            "token": token,
                            "token_time": time
                        }
                        return verification_entry
                return None
            except Exception as e:
                logger.exception(e)
        elif contact_type == 'email':
            try:
                query = ("""SELECT
                        id as entry_id,
                        token,
                        time
                    FROM email_token
                    WHERE email = %s AND time = (SELECT MAX(time) FROM email_token)""")
                params = (value,)
                cls.source.execute(query, params)
                if cls.source.has_results():
                    for (
                        entry_id,
                        token,
                        time
                    ) in cls.source.cursor:
                        verification_entry = {
                            "entry_id": entry_id,
                            "token": token,
                            "token_time": time
                        }
                        return verification_entry
                return None
            except Exception as e:
                logger.exception(e)

    @classmethod
    def sendSMS(cls, cell):
        client = cls.get_twilio_client()
        (token, token_time) = cls.get_totp()
        try:
            message = client.messages.create(
                to=f"+{cell}",
                from_=settings.get('services.twilio.sender_number'),
                body="Your AMERA Share verification code is: " + token)
            return (message.sid, token, token_time)
        except TwilioRestException as e:
            logger.exception(e)

    @classmethod
    def sendMail(cls, email):
        (token, token_time) = cls.get_totp()
        try:
            sendmail.send_mail(
                to_email=email,
                subject="AMERA Share E-mail confirmation",
                template="confirmation",
                data={
                    "token": token
                }
            )
            return (token, token_time)
        except sendmail.EmailAuthError:
            logger.exception('Deleting invite due to unable \
                             to auth to email system')

    @classmethod
    def add_outgoing_caller(cls, member_id, username, contact_id, phone_number, callback_url):
        try:
            client = cls.get_twilio_client()
            # phone_number = "+15005550006"
            validation_request = client.validation_requests.create(
                    friendly_name=f"{member_id}_{username}",
                    phone_number=phone_number,
                    status_callback=callback_url
                )
            return validation_request
        except TwilioRestException as e:
            logger.exception(e)
            raise e

    @classmethod
    def update_outgoing_caller(cls, contact_id, verification_status):
        try:
            query = ("""
                UPDATE member_contact_2
                SET
                    outgoing_caller_verified = %s
                WHERE id = %s;
            """)
            
            cls.source.execute(query, (verification_status, contact_id ))
            cls.source.commit()
        except Exception as e:
            raise e

    @classmethod
    def create_twilio_verification(cls, session_id, member_id, contact_id):
        try:
            query = ("""
                INSERT INTO twilio_verification
                    (session_id, member_id, member_contact_id)
                VALUES (%s, %s, %s)
                RETURNING id;
            """)
            
            cls.source.execute(query, (session_id, member_id, contact_id ))
            twilio_verify_id = cls.source.get_last_row_id()
            cls.source.commit()

            return twilio_verify_id
        except Exception as e:
            raise e

    @classmethod
    def get_twilio_verification(cls, twilio_verify_id):
        
        query = ("""
            SELECT
                session_id,
                member_id,
                member_contact_id
            FROM twilio_verification
            WHERE id = %s
        """)
        cls.source.execute(query, (twilio_verify_id, ))
        if cls.source.has_results():
            (
                session_id,
                member_id,
                contact_id
            ) = cls.source.cursor.fetchone()

            session = {
                "session_id": session_id,
                "member_id": member_id,
                "contact_id": contact_id
            }

            return session

        return None
