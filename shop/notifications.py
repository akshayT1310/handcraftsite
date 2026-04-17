"""
Notification Service - Email and SMS notifications
"""
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)


def send_order_confirmation_email(order):
    """Send order confirmation email to customer"""
    try:
        subject = f'✅ Order Confirmed - #{order.id} | HANDCRAFT Artisan Creations'
        
        # Email content
        context = {
            'order': order,
            'order_id': order.id,
            'customer_name': order.full_name,
            'total_amount': order.total_amount,
            'delivery_address': f"{order.address}, {order.city} - {order.pincode}",
        }
        
        # HTML email template
        html_content = render_to_string('shop/emails/order_confirmation.html', context)
        text_content = strip_tags(html_content)
        
        # Create email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[order.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(f"✅ Order confirmation email sent to {order.email} for Order #{order.id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send email for Order #{order.id}: {str(e)}")
        return False


def send_order_status_update_email(order):
    """Send email when order status changes"""
    try:
        subject = f'📦 Order Update - #{order.id} | HANDCRAFT'
        
        context = {
            'order': order,
            'customer_name': order.full_name,
            'new_status': order.status,
        }
        
        html_content = render_to_string('shop/emails/order_status_update.html', context)
        text_content = strip_tags(html_content)
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[order.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(f"✅ Status update email sent to {order.email} for Order #{order.id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send status email for Order #{order.id}: {str(e)}")
        return False


def send_sms_notification(phone_number, message):
    """Send SMS notification using MSG91 API"""
    if not getattr(settings, 'SMS_ENABLED', False):
        logger.info("SMS notifications disabled")
        return False
    
    try:
        import requests
        
        # Clean phone number (remove +, -, spaces)
        clean_phone = phone_number.replace('+', '').replace('-', '').replace(' ', '')
        
        # Ensure it has country code (default to India +91)
        if not clean_phone.startswith('91'):
            clean_phone = '91' + clean_phone
        
        # MSG91 API Configuration
        authkey = getattr(settings, 'SMS_API_KEY', '')
        sender_id = getattr(settings, 'SMS_SENDER_ID', 'HNDCFT')
        route = '4'  # Transactional route
        country = '91'  # India
        
        # MSG91 SMS API URL
        url = "https://control.msg91.com/api/v5/flow/"
        
        headers = {
            'authkey': authkey,
            'Content-Type': 'application/json'
        }
        
        # Prepare message payload
        payload = {
            "template_id": getattr(settings, 'SMS_TEMPLATE_ID', ''),  # Your MSG91 template ID
            "short_url": "0",
            "recipients": [
                {
                    "mobiles": clean_phone,
                    "VAR1": message[:150]  # MSG91 variable
                }
            ]
        }
        
        # Send request
        response = requests.post(url, json=payload, headers=headers)
        response_data = response.json()
        
        if response.status_code == 200 and response_data.get('type') == 'success':
            logger.info(f"✅ SMS sent successfully to {phone_number}: {message}")
            return True
        else:
            logger.error(f"❌ MSG91 API Error: {response_data}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to send SMS to {phone_number}: {str(e)}")
        return False


def send_order_confirmation_sms(order):
    """Send order confirmation SMS using MSG91"""
    if not order.phone:
        logger.info("No phone number provided for order")
        return False
    
    message = f"Order #{order.id} confirmed! Total: ₹{order.total_amount}. Track at handcraft.com. Thank you!"
    
    return send_sms_notification(order.phone, message)


def send_order_status_sms(order):
    """Send order status update SMS"""
    if not order.phone:
        return False
    
    message = f"Order #{order.id} status: {order.status}. Track updates at handcraft.com"
    
    return send_sms_notification(order.phone, message)


def send_order_cancelled_email(order, reason=None):
    """Send email when order is cancelled"""
    try:
        subject = f'❌ Order Cancelled - #{order.id} | HANDCRAFT'
        
        context = {
            'order': order,
            'customer_name': order.full_name,
            'cancellation_reason': reason or 'No reason provided',
            'show_refund_info': order.payment_status,  # Show refund info if paid
        }
        
        html_content = render_to_string('shop/emails/order_cancelled.html', context)
        text_content = strip_tags(html_content)
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[order.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(f"✅ Cancellation email sent to {order.email} for Order #{order.id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send cancellation email for Order #{order.id}: {str(e)}")
        return False


def send_order_cancelled_sms(order, reason=None):
    """Send SMS notification when order is cancelled"""
    if not order.phone:
        return False
    
    refund_text = " A refund will be initiated soon." if order.payment_status else ""
    message = f"Order #{order.id} cancelled.{refund_text} Contact us for details. HANDCRAFT"
    
    return send_sms_notification(order.phone, message)


def send_admin_cancellation_alert(order, cancelled_by, reason=None):
    """Send alert to admin when order is cancelled"""
    try:
        subject = f'⚠️ Order Cancelled - #{order.id} by {cancelled_by}'
        
        context = {
            'order': order,
            'cancelled_by': cancelled_by,
            'cancellation_reason': reason or 'No reason provided',
            'refund_needed': order.payment_status,
        }
        
        html_content = render_to_string('shop/emails/admin_cancellation_alert.html', context)
        text_content = strip_tags(html_content)
        
        # Send to admin email
        admin_email = settings.ADMIN_EMAIL if hasattr(settings, 'ADMIN_EMAIL') else settings.DEFAULT_FROM_EMAIL
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[admin_email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(f"✅ Admin alert sent for Order #{order.id} cancelled by {cancelled_by}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send admin alert for Order #{order.id}: {str(e)}")
        return False

