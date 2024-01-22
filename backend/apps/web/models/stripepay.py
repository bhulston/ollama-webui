from pydantic import BaseModel
from typing import List, Union, Optional, Dict
from playhouse.shortcuts import model_to_dict
import time
from peewee import *
from datetime import datetime

from apps.web.internal.db import DB

####################
# DB MODEL
####################


class Stripe(Model):
    customerId = CharField() 
    ollamaId = CharField(unique = True)
    subscriptionId = CharField()
    description = CharField()
    currentPeriodEnd = DateField()
    active = BooleanField()
    email = CharField()

    class Meta:
        database = DB

class StripeUser(BaseModel):
    customerId: str
    ollamaId: str
    subscriptionId: str
    description: str
    currentPeriodEnd: int #timestamp
    active: bool = False
    email: str


####################
# Forms
####################
class SignupForm(BaseModel):
    id: str
    email: str

class SubscribeForm(BaseModel):
    sessionId: str

class SubscriptionResponse(BaseModel):
    subscriptionId: str
    currentPeriodEnd: int
    customerId: str
    active: bool
    email: str
    amount: str


class StripeTable:
    def __init__(self, db):
        self.db = db
        self.db.create_tables([Stripe])

    def create_new_stripe(
        self, id: str, email: str
    ) -> Optional[StripeUser]:
        print("insert_new_stripe")
        stripe_user = StripeUser(
            **{
                "customerId": "Pending",
                "ollamaId": id,
                "subscriptionId": "Pending",
                "email": email,
                "description": "Pending",
                "currentPeriodEnd": int(time.time()),
                "active": False,
            }
        )
        print("Stripe user created", stripe_user)
        result = Stripe.create(**stripe_user.model_dump())
        if result:
            return stripe_user
        else:
            return None
        
    def get_stripe_by_id(
            self, id:str
    ) -> Optional[StripeUser]:
        try:
            stripe_user = Stripe.get(Stripe.ollamaId == id)
            return StripeUser(**model_to_dict(stripe_user))
        except:
            return None

    def authenticate_stripe(self, id: str) -> Optional[bool]:
        print("authenticate_user stripe", id)
        # Check if expiration date is active, return True or False
        try:
            stripe_user = StripeUser(**model_to_dict(Stripe.get(Stripe.ollamaId == id)))
            if stripe_user:
                if stripe_user.currentPeriodEnd > int(datetime.utcnow().timestamp()):
                    return True
                else:
                    return False
            else:
                return None
        except Exception as e:
            print("Error in stripe Authentication:", e)
            return None

    def update_stripe_by_id(self, id: str, updated: dict) -> Optional[StripeUser]:
        try:
            query = Stripe.update(**updated).where(Stripe.ollamaId == id)
            query.execute()

            stripe_user = Stripe.get(Stripe.ollamaId == id)
            return StripeUser(**model_to_dict(stripe_user))
        except Exception as e:
            print("Error in updating Stripe information", str(e))
            return None
        
    def delete_stripe_by_id(self, id: str) -> Optional[bool]:
        try:
            query = Stripe.delete().where(Stripe.ollamaId == id)
            query.execute()
            return True
        except:
            return False


Stripes = StripeTable(DB)
