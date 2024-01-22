import { WEBUI_API_BASE_URL } from '$lib/constants';

export const getSubscriptionStatus = async (email: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/stripepay/verify?email=${email}`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json'
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err.detail;
			return null;
		});
	
		if (error) {
			throw error;
		}

		return res;

};

export const stripeSignUp = async (id: string, email: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/stripepay/signup`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({
			id: id,
			email: email
		})
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log("Hey error:", err);
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const sendPaymentConfirmation = async (token: string, sessionId: string) => {
    let error = null;

    const res = await fetch(`${WEBUI_API_BASE_URL}/stripepay/confirm-payment`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
			sessionId: sessionId
		})
    })
        .then(async (res) => {
            if (!res.ok) throw await res;
            return res.json();
        })
        .catch((err) => {
            console.log(err);
            error = err.detail;
            return null
        });

        if (error) {
            throw error;
        }

        return res;
}

export const createStripeCheckout = async () => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/stripepay/create-checkout-session`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		}
	})
		.then(async (res) => {
            console.log("Response in Index function here:", res);
			if (!res.ok) throw await res;
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err.detail;
			return null;
		});
	
		if (error) {
			throw error;
		}

		return res;
};

export const getSubscription = async (token: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/stripepay/`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err.detail;
			return null;
		});
	
		if (error) {
			throw error;
		}

		return res;

};


export const cancelStripeSubscription = async (token: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/stripepay/cancel`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err.detail;
			return null;
		});
	
		if (error) {
			throw error;
		}

		return res;

}