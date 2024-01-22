from fastapi import Depends, APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Optional
from datetime import datetime
import stripe

from apps.web.models.stripepay import StripeUser, SubscribeForm, Stripes, SubscriptionResponse, SignupForm
from apps.web.models.users import Users
from apps.web.models.auths import (
    SigninResponse
)

from utils.utils import get_current_user, create_token
from constants import ERROR_MESSAGES

from config import STRIPE_API_KEY, STRIPE_PROD_KEY, APP_BASE_URL

router = APIRouter()


############################
# GetStripe
############################

@router.get("/", response_model=Optional[dict])
async def get_stripe_info(user=Depends(get_current_user)):
    
    if user == None:
        return None
    else:
      stripe.api_key = STRIPE_API_KEY
      try:
        stripe_user = Stripes.get_stripe_by_id(user.id)
        customer = stripe.Customer.retrieve(
          id=stripe_user.customerId,
          expand=['subscriptions']
        )
        subscription = customer['subscriptions']['data'][0]
        return {
           'subscriptionId': subscription.get('id'),
           'currentPeriodEnd': subscription.get('current_period_end'),
           'customerId': stripe_user.customerId,
           'active': subscription.get('status'),
           'email': customer['email'],
           'amount': ('$' + str(subscription['plan'].get('amount')/100) + ' ' + subscription['plan'].get('currency'))[:3]
        }
      except Exception as e:
        print("Error in getting live stripe info", e)
        stripe_user =  Stripes.get_stripe_by_id(user.id)
        if stripe_user:
            return {
                'subscriptionId': stripe_user.subscriptionId,
                'currentPeriodEnd': stripe_user.currentPeriodEnd,
                'customerId': stripe_user.customerId,
                'active': False,
                'email': stripe_user.email,
                'amount': "None"
            }
        return None

############################
# StripeSignUp
############################


@router.post("/signup", response_model=Optional[StripeUser])
async def create_subscription(form_data: SignupForm):
    try:
        if not Stripes.get_stripe_by_id(form_data.id):
            try:
                stripe_user = Stripes.create_new_stripe(form_data.id, form_data.email)
                print("Stripe User created:", stripe_user)
                if stripe_user:
                    return stripe_user
                else:
                    raise HTTPException(
                        500, detail=ERROR_MESSAGES.CREATE_USER_ERROR)
            except Exception as err:
                raise HTTPException(500,
                    detail=ERROR_MESSAGES.DEFAULT(err))
        else:
            raise HTTPException(400, detail=ERROR_MESSAGES.EMAIL_TAKEN)
    except Exception as e:
       print("Error in singup for stripe:", e)


############################
# CreateStripeCheckout
############################


@router.post("/create-checkout-session")
async def create_stripe_checkout():
    try:
        stripe.api_key = STRIPE_API_KEY
        checkout_session = stripe.checkout.Session.create(
            line_items = [{
                "price": STRIPE_PROD_KEY,
                "quantity": 1,
            }],
            mode="subscription",
            ui_mode = "embedded",
            return_url = APP_BASE_URL + "/stripe/return?session_id={CHECKOUT_SESSION_ID}"
        )

    except Exception as e:
        print("ERROR CHECKOUT", e)
        return str(e)
    
    print("Checkout session info", checkout_session)
    return JSONResponse({"clientSecret": checkout_session.client_secret})

############################
# GetStripeStatus - on login and signup
############################

@router.get("/verify", response_model=Optional[SigninResponse])
async def verify_stripe_status(email: str):
    user = Users.get_user_by_email(email)
    if not user:
        # User not found
        raise HTTPException(status_code=404, detail="User not found or invalid email address")

    if user.role in ['admin', 'trial']: # Allow access without Stripe verification
        print("user role is admin/trial")
        token = create_token(data={"email": user.email})

        return {
            "token": token,
            "token_type": "Bearer",
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "profile_image_url": user.profile_image_url,
        }

    stripe.api_key = STRIPE_API_KEY
    stripe_user = Stripes.get_stripe_by_id(user.id)

    if not stripe_user:
        stripe_user = Stripes.create_new_stripe(user.id, email)

    has_active_subscription = Stripes.authenticate_stripe(stripe_user.ollamaId)
    if not has_active_subscription:
        try:
            # Where date is before today, double check Stripe API
            customer = stripe.Customer.retrieve(
                id=stripe_user.customerId,
                expand=['subscriptions']
            )
            
            has_active_subscription = any(
                sub.get('status') == 'active' for sub in customer['subscriptions']['data']
                ) if 'subscriptions' in customer and 'data' in customer['subscriptions'] else False
            
            stripe_user = Stripes.update_stripe_by_id(user.id, {"active": has_active_subscription, 
                                                "currentPeriodEnd": customer['subscriptions']['data'][0].get('current_period_end'),
                                                })
        except:
            print("Could not find Stripe customer and subscription")
    new_role = "user" if has_active_subscription else "pending"
           
        
    
    user = Users.update_user_role_by_id(user.id, new_role)
    token = create_token(data={"email": user.email})

    return {
        "token": token,
        "token_type": "Bearer",
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "profile_image_url": user.profile_image_url,
    }

############################
# ConfirmStripePayment - during payment redirect
############################

@router.post("/confirm-payment", response_model=Optional[StripeUser])
async def confirm_stripe_payment(form_data: SubscribeForm, user= Depends(get_current_user)):
    sessionId = form_data.sessionId
    print("SessionId:", sessionId)
    
    try:
        if user:
            stripe.api_key = STRIPE_API_KEY
            checkout = stripe.checkout.Session.retrieve(
               sessionId
            )
            updated = {
               'customerId': checkout.customer,
               'subscriptionId': checkout.subscription,
               'currentPeriodEnd': checkout.expires_at,
               'active': True
            }
            stripe_user = Stripes.update_stripe_by_id(user.id, updated)
            return stripe_user
        else:
            raise HTTPException("User not found or invalid email address")
    except Exception as e:
        print(f"Error occurred while verifying user Stripe status: {str(e)}")
        return None
    

############################
# CancelStripeSubscription
############################

@router.post("/cancel", response_model=str)
async def cancel_stripe_payment(user= Depends(get_current_user)):
    fail_msg = "Stripe Cancellation Failed ... Please reach out your administrator for alternatives!"
    try:
        stripe_user = Stripes.get_stripe_by_id(user.id)
        if stripe_user:
            stripe.api_key = STRIPE_API_KEY
            canceled_subscription = stripe.Subscription.modify(stripe_user.subscriptionId, cancel_at_period_end=True)
            print("Subscription scheduled to cancel:", canceled_subscription)
            if canceled_subscription:
                currentPeriodEnd = canceled_subscription.current_period_end
                end = datetime.utcfromtimestamp(currentPeriodEnd).strftime("%b %d, %Y")
                active = canceled_subscription.status
                stripe_user = Stripes.update_stripe_by_id(user.id, {
                    "currentPeriodEnd": currentPeriodEnd,
                    "active": active
                })
                
                return "Your Stripe subscription will end on " + str(end) + ". You can use the service until that day."
            return fail_msg
        else:
            return fail_msg
    except Exception as e:
        print(f"Error occurred while cancelling : {str(e)}")
        return fail_msg
    


#######################
# Webhook (not in use)
#######################

# @router.post('/webhook')
# def webhook(request: Request):
#     user = get_current_user()
#     stripe.api_key = STRIPE_API_KEY
#     event = None
#     payload = request.data
#     sig_header = request.headers['STRIPE_SIGNATURE']
    
#     endpoint_secret = 'whsec_3dca3b860fa5341b51cae132d3e8cd84b2a972d6d5fe2f7f4134f5851844cfe0'

#     try:
#         event = stripe.Webhook.construct_event(
#             payload, sig_header, endpoint_secret
#         )
#     except ValueError as e:
#         # Invalid payload
#         raise e
#     except stripe.error.SignatureVerificationError as e:
#         # Invalid signature
#         raise e

#     # Handle the event
#     if event['type'] == 'checkout.session.async_payment_failed':
#       session = event['data']['object']
#       print("Async payment failed for",user.email, session)
#     elif event['type'] == 'checkout.session.async_payment_succeeded':
#       session = event['data']['object']
#       print("Async payment succeeded for",user.email, session)
#     elif event['type'] == 'checkout.session.completed':
#       session = event['data']['object']
#       print("Checkout Session Completed for",user.email, session)
#     elif event['type'] == 'checkout.session.expired':
#       session = event['data']['object']
#       print("Checkout Session Expired for",user.email, session)
#     elif event['type'] == 'customer.created':
#       customer = event['data']['object']
#       print("New Stripe customer created for", user.email, customer)
#     elif event['type'] == 'customer.deleted':
#       customer = event['data']['object']
#       print("Stripe customer deleted for", user.email, customer)
#     elif event['type'] == 'customer.updated':
#       customer = event['data']['object']
#       print("Stripe customer updated for", user.email, customer)
#     elif event['type'] == 'customer.subscription.created':
#       subscription = event['data']['object']
#       print("New subscription created for", user.email, subscription)
#     elif event['type'] == 'customer.subscription.deleted':
#       subscription = event['data']['object']
#       print("Deleted subscription for", user.email, subscription)
#     elif event['type'] == 'customer.subscription.paused':
#       subscription = event['data']['object']
#       print("Subscription paused for", user.email, subscription)
#     elif event['type'] == 'customer.subscription.resumed':
#       subscription = event['data']['object']
#       print("Subscription resumed for", user.email, subscription)
#     # ... handle other event types
#     else:
#       print('Unhandled event type {}'.format(event['type']))

#     return JSONResponse(success=True)