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

@payments_bp.route('/pricing')
def pricing():
    """Display subscription pricing plans."""
    # Get pricing details from config
    monthly_price = current_app.config.get('MONTHLY_PRICE', 9.99)
    yearly_price = current_app.config.get('YEARLY_PRICE', 99.99)
    trial_days = current_app.config.get('TRIAL_DAYS', 14)
    stripe_monthly_price_id = current_app.config.get('STRIPE_MONTHLY_PRICE_ID')
    stripe_yearly_price_id = current_app.config.get('STRIPE_YEARLY_PRICE_ID')
    
    return render_template('pricing.html',
                         stripe_public_key=current_app.config.get('STRIPE_PUBLISHABLE_KEY'),
                         monthly_price=monthly_price,
                         yearly_price=yearly_price,
                         trial_days=trial_days,
                         stripe_monthly_price_id=stripe_monthly_price_id,
                         stripe_yearly_price_id=stripe_yearly_price_id)

@payments_bp.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    """Create a Stripe checkout session for subscription."""
    try:
        # Use Stripe API initialized in app.py
        price_id = request.form.get('price_id')
        if not price_id:
            return jsonify({'error': 'Price ID is required'}), 400
        
        # Initialize Stripe if not already done
        stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')
        
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
        current_app.logger.error(f"Error creating checkout session: {str(e)}")
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
    stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')
    webhook_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        current_app.logger.error(f"Invalid payload in webhook: {str(e)}")
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        current_app.logger.error(f"Invalid signature in webhook: {str(e)}")
        return jsonify({'error': 'Invalid signature'}), 400
    
    # Handle the event based on type
    event_type = event['type']
    current_app.logger.info(f"Processing webhook event: {event_type}")
    
    if event_type == 'checkout.session.completed':
        session = event['data']['object']
        
        # Verify session has required fields before accessing
        if 'client_reference_id' in session and session['client_reference_id']:
            user_id = session['client_reference_id']
            user = User.query.get(user_id)
            
            if user:
                # Update user subscription status
                user.subscription_status = 'active'
                
                # Store Stripe identifiers for future reference
                if 'customer' in session:
                    user.stripe_customer_id = session['customer']
                if 'subscription' in session:
                    user.stripe_subscription_id = session['subscription']
                
                db.session.commit()
                current_app.logger.info(f"User {user_id} subscription activated")
    
    elif event_type == 'customer.subscription.deleted':
        subscription_obj = event['data']['object']
        
        # Find user by subscription ID
        if 'id' in subscription_obj:
            user = User.query.filter_by(stripe_subscription_id=subscription_obj['id']).first()
            
            if user:
                user.subscription_status = 'inactive'
                db.session.commit()
                current_app.logger.info(f"User {user.id} subscription deactivated")
    
    return jsonify({'status': 'success'})

@payments_bp.route('/manage-subscription')
@login_required
def manage_subscription():
    """Redirect user to Stripe Customer Portal to manage their subscription."""
    try:
        stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')
        
        if not current_user.stripe_customer_id:
            flash('You do not have an active subscription to manage.', 'warning')
            return redirect(url_for('payments.pricing'))
        
        # Create a Stripe portal session
        session = stripe.billing_portal.Session.create(
            customer=current_user.stripe_customer_id,
            return_url=url_for('payments.subscription', _external=True)
        )
        
        # Redirect to the customer portal
        return redirect(session.url)
    except Exception as e:
        current_app.logger.error(f"Error creating customer portal session: {str(e)}")
        flash('Error accessing subscription management: ' + str(e), 'danger')
        return redirect(url_for('payments.subscription'))

@payments_bp.route('/subscription')
@login_required
def subscription():
    """Display user subscription details."""
    # Get subscription data from Stripe if available
    subscription = None
    if current_user.stripe_subscription_id:
        try:
            stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')
            subscription = stripe.Subscription.retrieve(current_user.stripe_subscription_id)
        except Exception as e:
            current_app.logger.error(f"Error retrieving subscription: {str(e)}")
    
    # Define trial days for display
    trial_days = current_app.config.get('TRIAL_DAYS', 14)
    
    return render_template('subscription.html', 
                          subscription=subscription,
                          trial_days=trial_days) 