<template>
	<div class="mx-auto max-w-md px-6 py-16">
		<h1 class="text-3xl font-extrabold text-ink">Sign in</h1>
		<p class="mt-2 text-sm text-body">Sign in to track your applications and continue your profile.</p>

		<form @submit.prevent="submit" class="mt-8 space-y-5">
			<div>
				<label for="email" class="mb-1 block text-sm font-medium text-ink">Email</label>
				<input
					id="email"
					v-model.trim="email"
					type="text"
					autocapitalize="none"
					required
					class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
				/>
			</div>
			<div>
				<label for="password" class="mb-1 block text-sm font-medium text-ink">Password</label>
				<input
					id="password"
					v-model="password"
					type="password"
					required
					class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
				/>
			</div>

			<p v-if="error" class="text-sm text-red-600">{{ error }}</p>

			<button
				type="submit"
				:disabled="submitting"
				class="w-full rounded-md bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
			>
				{{ submitting ? "Signing in..." : "Sign in" }}
			</button>

			<p class="text-center text-sm text-body">
				New here?
				<router-link to="/register" class="font-semibold text-brand-700 hover:text-brand-800">
					Create an applicant account
				</router-link>
			</p>
		</form>
	</div>
</template>

<script setup>
import { inject, ref } from "vue";
import { useRoute } from "vue-router";

const auth = inject("$auth");
const route = useRoute();

const email = ref("");
const password = ref("");
const submitting = ref(false);
const error = ref("");

async function submit() {
	submitting.value = true;
	error.value = "";
	try {
		const res = await auth.login(email.value, password.value);
		if (res) {
			// Real browser navigation (not router.push) so Frappe's own
			// server-side get_home_page() resolves the user's real role
			// dashboard (HR/Panel/Applicant) - see hooks.py's home_page note.
			const redirectTo = route.query["redirect-to"] || route.query.redirect;
			window.location.href = redirectTo || "/";
		} else {
			error.value = "Invalid email or password.";
		}
	} catch (e) {
		error.value = e.messages?.[0] || e.message || "Invalid email or password.";
	} finally {
		submitting.value = false;
	}
}
</script>
