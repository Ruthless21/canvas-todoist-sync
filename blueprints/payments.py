"""
Payments blueprint.
Handles subscription and payment processing.
"""

from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from blueprints import payments_bp
from models import User, db, Subscription
import stripe
from datetime import datetime, timedelta
from config import Config

# Initialize Stripe with the API key from config
stripe.api_key = Config.STRIPE_SECRET_KEY

@payments_bp.route('/pricing')
def pricing():
    """Display subscription pricing plans."""
    return render_template('pricing.html',
                         stripe_public_key=Config.STRIPE_PUBLISHABLE_KEY)

@payments_bp.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    """Create a Stripe checkout session for subscription."""
    try:
        price_id = request.form.get('price_id')
        if not price_id:
            return jsonify({'error': 'Price ID is required'}), 400
        
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=url_for('payments.success', _external=True),
            cancel_url=url_for('payments.cancel', _external=True),
            customer_email=current_user.email,
            client_reference_id=str(current_user.id),
        )
        
        return jsonify({'sessionId': checkout_session.id})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@payments_bp.route('/success')
@login_required
def success():
    """Handle successful subscription."""
    flash('Thank you for subscribing! Your account has been upgraded.', 'success')
    return redirect(url_for('dashboard.index'))

@payments_bp.route('/cancel')
@login_required
def cancel():
    """Handle cancelled subscription."""
    flash('Subscription was cancelled. No changes were made to your account.', 'info')
    return redirect(url_for('payments.pricing'))

@payments_bp.route('/webhook', methods=['POST'])
def webhook():
    """Handle Stripe webhook events."""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, Config.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        return jsonify({'error': 'Invalid signature'}), 400
    
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        user_id = session['client_reference_id']
        user = User.query.get(user_id)
        
        if user:
            user.subscription_status = 'active'
            user.stripe_customer_id = session['customer']
            user.stripe_subscription_id = session['subscription']
            db.session.commit()
    
    elif event['type'] == 'customer.subscription.deleted':
        session = event['data']['object']
        user = User.query.filter_by(stripe_subscription_id=session['id']).first()
        
        if user:
            user.subscription_status = 'inactive'
            db.session.commit()
    
    return jsonify({'status': 'success'})

@payments_bp.route('/manage-subscription')
@login_required
def manage_subscription():
    """Display subscription management page."""
    if not current_user.stripe_customer_id:
        return redirect(url_for('payments.pricing'))
    
    try:
        portal_session = stripe.billing_portal.Session.create(
            customer=current_user.stripe_customer_id,
            return_url=url_for('dashboard.index', _external=True),
        )
        return redirect(portal_session.url)
    except Exception as e:
        flash('Error accessing subscription management: ' + str(e), 'danger')
        return redirect(url_for('dashboard.index')) 