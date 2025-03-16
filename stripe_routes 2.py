import stripe
import os
from flask import Blueprint, request, jsonify, redirect, url_for, render_template, session, flash, current_app
from flask_login import current_user, login_required
from models import db, User, Subscription
from datetime import datetime
import stripe_config
from functools import wraps

# Initialize Stripe with the API keys
stripe.api_key = stripe_config.STRIPE_SECRET_KEY

# Create Blueprint
stripe_bp = Blueprint('stripe', __name__, url_prefix='/stripe')

# Ensure user is logged in for routes that require it
def login_required_ajax(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({"error": "Login required"}), 401
        return f(*args, **kwargs)
    return decorated_function

@stripe_bp.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    """Create a Stripe checkout session for subscription."""
    try:
        price_id = request.form.get('price_id')
        
        # Validate price ID
        if not price_id:
            flash('Invalid price selected', 'danger')
            return redirect(url_for('pricing'))
            
        # Create checkout session with Stripe
        checkout_session = stripe.checkout.Session.create(
            customer_email=current_user.email,
            payment_method_types=['card'],
            line_items=[
                {
                    'price': price_id,
                    'quantity': 1,
                },
            ],
            mode='subscription',  # Changed from 'payment' to 'subscription'
            subscription_data={
                'trial_period_days': stripe_config.TRIAL_DAYS,
            },
            success_url=stripe_config.DOMAIN + url_for('stripe.checkout_success') + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=stripe_config.DOMAIN + url_for('stripe.checkout_cancel'),
            metadata={
                'user_id': current_user.id
            }
        )
        
        # Create a subscription record in our database
        subscription = Subscription.query.filter_by(user_id=current_user.id).first()
        if not subscription:
            subscription = Subscription(
                user_id=current_user.id,
                stripe_checkout_session_id=checkout_session.id,
                stripe_price_id=price_id,
                status='pending'
            )
            db.session.add(subscription)
        else:
            subscription.stripe_checkout_session_id = checkout_session.id
            subscription.stripe_price_id = price_id
            subscription.status = 'pending'
            
        db.session.commit()
        
        # Redirect to Stripe Checkout
        return redirect(checkout_session.url)
    
    except Exception as e:
        current_app.logger.error(f"Error creating checkout session: {str(e)}")
        flash(f"An error occurred: {str(e)}", 'danger')
        return redirect(url_for('pricing'))

@stripe_bp.route('/checkout-success')
@login_required
def checkout_success():
    """Handle successful checkout."""
    session_id = request.args.get('session_id')
    
    if not session_id:
        flash('No checkout session found', 'warning')
        return redirect(url_for('dashboard'))
    
    try:
        # Retrieve the checkout session from Stripe
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        customer_id = checkout_session.customer
        
        # Update local record
        subscription = Subscription.query.filter_by(user_id=current_user.id).first()
        if subscription:
            subscription.stripe_customer_id = customer_id
            subscription.status = 'active'  # Active means lifetime access in our case
            subscription.current_period_start = datetime.utcnow()  # Purchase date
            
            # Set the user as premium
            user = User.query.get(current_user.id)
            user.is_premium = True
            
            db.session.commit()
            
            flash('Thank you for your purchase! Your premium features are now active.', 'success')
        else:
            flash('Payment processed, but no local record found. Please contact support.', 'warning')
        
        return redirect(url_for('dashboard'))
    
    except Exception as e:
        current_app.logger.error(f"Error processing successful checkout: {str(e)}")
        flash(f"An error occurred while processing your payment: {str(e)}", 'danger')
        return redirect(url_for('dashboard'))

@stripe_bp.route('/checkout-cancel')
@login_required
def checkout_cancel():
    """Handle cancelled checkout."""
    flash('Your payment process was cancelled. You can try again anytime!', 'info')
    return redirect(url_for('pricing'))

@stripe_bp.route('/webhook', methods=['POST'])
def webhook():
    """Handle Stripe webhook events."""
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    
    # Verify webhook signature
    if not sig_header or not stripe_config.STRIPE_WEBHOOK_SECRET:
        current_app.logger.warning("Webhook signature verification not configured")
        return jsonify(success=True)
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, stripe_config.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        current_app.logger.error(f"Invalid payload: {str(e)}")
        return jsonify(error=str(e)), 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        current_app.logger.error(f"Invalid signature: {str(e)}")
        return jsonify(error=str(e)), 400
    
    # Handle different event types
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        _handle_checkout_session_completed(session)
    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        _handle_subscription_updated(subscription)
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        _handle_subscription_deleted(subscription)
    
    return jsonify(success=True)

def _handle_checkout_session_completed(session):
    """Handle checkout.session.completed event."""
    try:
        # Get user_id from session metadata
        user_id = session.get('metadata', {}).get('user_id')
        
        if not user_id:
            current_app.logger.error(f"No user_id in session metadata: {session.id}")
            return
        
        # Get subscription ID from the session
        subscription_id = session.get('subscription')
        
        if subscription_id:
            # Retrieve the subscription details from Stripe
            stripe_subscription = stripe.Subscription.retrieve(subscription_id)
            
            # Update our local record
            subscription = Subscription.query.filter_by(
                stripe_checkout_session_id=session.id
            ).first()
            
            if subscription:
                subscription.stripe_customer_id = session.customer
                subscription.stripe_subscription_id = subscription_id
                subscription.status = stripe_subscription.status
                subscription.current_period_start = datetime.fromtimestamp(stripe_subscription.current_period_start)
                subscription.current_period_end = datetime.fromtimestamp(stripe_subscription.current_period_end)
                
                # Set user as premium
                user = User.query.get(subscription.user_id)
                if user:
                    user.is_premium = True
                    
                db.session.commit()
                current_app.logger.info(f"Activated premium for user {user_id}")
            else:
                current_app.logger.error(f"No record found for session: {session.id}")
        else:
            current_app.logger.error(f"No subscription ID in session: {session.id}")
    
    except Exception as e:
        current_app.logger.error(f"Error handling checkout.session.completed: {str(e)}")

def _handle_subscription_updated(stripe_subscription):
    """Handle subscription updates from Stripe."""
    try:
        # Find the subscription in our database
        subscription = Subscription.query.filter_by(
            stripe_subscription_id=stripe_subscription.id
        ).first()
        
        if subscription:
            # Update status and period info
            subscription.status = stripe_subscription.status
            subscription.current_period_start = datetime.fromtimestamp(stripe_subscription.current_period_start)
            subscription.current_period_end = datetime.fromtimestamp(stripe_subscription.current_period_end)
            
            # Handle status changes
            user = User.query.get(subscription.user_id)
            if user:
                if subscription.status in ['active', 'trialing']:
                    user.is_premium = True
                else:
                    user.is_premium = False
            
            db.session.commit()
            current_app.logger.info(f"Updated subscription {stripe_subscription.id} status to {stripe_subscription.status}")
    except Exception as e:
        current_app.logger.error(f"Error handling subscription update: {str(e)}")

def _handle_subscription_deleted(stripe_subscription):
    """Handle subscription deletion from Stripe."""
    try:
        # Find the subscription in our database
        subscription = Subscription.query.filter_by(
            stripe_subscription_id=stripe_subscription.id
        ).first()
        
        if subscription:
            # Update status
            subscription.status = 'canceled'
            
            # Remove premium status
            user = User.query.get(subscription.user_id)
            if user:
                user.is_premium = False
            
            db.session.commit()
            current_app.logger.info(f"Subscription {stripe_subscription.id} was canceled")
    except Exception as e:
        current_app.logger.error(f"Error handling subscription deletion: {str(e)}")

@stripe_bp.route('/manage-subscription')
@login_required
def manage_subscription():
    """Create a Stripe customer portal session to manage subscription."""
    try:
        # Get the user's subscription
        subscription = Subscription.query.filter_by(user_id=current_user.id).first()
        
        if not subscription or not subscription.stripe_customer_id:
            flash('No active subscription found', 'warning')
            return redirect(url_for('subscription'))
            
        # Create a portal session
        session = stripe.billing_portal.Session.create(
            customer=subscription.stripe_customer_id,
            return_url=stripe_config.DOMAIN + url_for('subscription')
        )
        
        # Redirect to the customer portal
        return redirect(session.url)
        
    except Exception as e:
        current_app.logger.error(f"Error creating customer portal session: {str(e)}")
        flash(f"An error occurred: {str(e)}", 'danger')
        return redirect(url_for('subscription')) 