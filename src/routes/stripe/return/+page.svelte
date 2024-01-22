<script src = "https://js.stripe.com/v3/">
	import { goto } from '$app/navigation';
	import { userSignIn, userSignUp } from '$lib/apis/auths';
	import { getSubscriptionStatus, createStripeCheckout, sendPaymentConfirmation } from '$lib/apis/stripe';
	import { WEBUI_API_BASE_URL } from '$lib/constants';
	import { config, user } from '$lib/stores';
	import { onMount } from 'svelte';
	import toast from 'svelte-french-toast';
    import stripe from 'stripe';

	let loaded = true;
    let sessionId = null;

    const setSessionUser = async (sessionUser) => {
		if (sessionUser) {
			localStorage.token = sessionUser.token;
			toast.success(`You're now logged in.`);
			await user.set(sessionUser);
			goto('/');
		}
	};
	
	onMount(async () => {
        const queryParams = new URLSearchParams(window.location.search);
        sessionId = queryParams.get('session_id');
        
        console.log("Session ID:", sessionId);
        const stripe_user = await sendPaymentConfirmation(localStorage.token, sessionId);
		const user = await getSubscriptionStatus(stripe_user.email);
		console.log(stripe_user);
		if (stripe_user && user) { //aka payment was confirmed in our database
			await setSessionUser(user);
		}
	})
</script>

{#if loaded}
	<div class="fixed m-10 z-50">
		<div class="flex space-x-2">
			<div class=" self-center">
				<img src="/ollama.png" class=" w-8" />
			</div>
		</div>
	</div>
{/if}

<style>
	.font-mona {
		font-family: 'Mona Sans';
	}
</style>
