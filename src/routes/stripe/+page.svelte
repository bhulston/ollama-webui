<script src = "https://js.stripe.com/v3/">
	import { goto } from '$app/navigation';
	import { getSubscriptionStatus, createStripeCheckout, sendPaymentConfirmation } from '$lib/apis/stripe';
	import { WEBUI_API_BASE_URL } from '$lib/constants';
	import { config, user } from '$lib/stores';
	import { onMount } from 'svelte';
    import { getBackendConfig } from '$lib/apis';
	import { getSessionUser } from '$lib/apis/auths';

	import toast from 'svelte-french-toast';
    import stripe from 'stripe';
    

	let loaded = false;

    onMount(async () => {
		// Check Backend Status
		const backendConfig = await getBackendConfig();

		if (backendConfig) {
			// Save Backend Status to Store
			await config.set(backendConfig);
			console.log(backendConfig);

			if ($config) {
				if (localStorage.token) {
					// Get Session User Info
					const sessionUser = await getSessionUser(localStorage.token).catch((error) => {
						toast.error(error);
						return null;
					});

					if (sessionUser) {
						// Save Session User to Store
						await user.set(sessionUser);
					} else {
						// Redirect Invalid Session User to /auth Page
						localStorage.removeItem('token');
						await goto('/auth');
					}
				} else {
					await goto('/auth');
				}
			}
		} else {
			// Redirect to /error when Backend Not Detected
			await goto(`/error`);
		}

		loaded = true;

        // Load Stripe library
        const stripe = await loadStripe('pk_test_51OZMBRKy06mdLefoAi42rCd8NENBZciBj2fMVjW2WxH1zaxpLk6d1Czn4mTuBMLADrBo5V38RoFX4WBTGYHhls7S00ejspmQOY'); // Replace with your actual public key

        // Fetch Checkout Session and retrieve the client secret
        async function initialize() {
            try {
                const response = await createStripeCheckout(); // API call to get client secret for checkout session

                if (response) {
                    const checkout = await stripe.initEmbeddedCheckout({
                        clientSecret: response["clientSecret"],
                    });

                    // Mount Checkout
                    checkout.mount('#checkout');
                } else {
                    console.error('Client secret not received');
                }
            } catch (error) {
                console.error('Error initializing checkout:', error);
            }
        }

        initialize();
    });

	// Load Stripe as a module
    async function loadStripe(publicKey) {
        if (!window.Stripe) {
            const script = document.createElement('script');
            script.src = 'https://js.stripe.com/v3/';
            document.head.appendChild(script);
            await new Promise((resolve) => (script.onload = resolve));
        }
        return Stripe(publicKey);
    }
</script>

{#if loaded}
	<div class="fixed m-10 z-50">
		<div class="flex space-x-2">
			<div class="self-center">
                <a href="/">
                    <img src="/ollama.png" class="w-8" />
                </a>
            </div>
		</div>
	</div>

    <div id="checkout">
        <!-- Checkout will insert the payment form here -->
    </div>


	{/if}

<style>
	.font-mona {
		font-family: 'Mona Sans';
	}
</style>
