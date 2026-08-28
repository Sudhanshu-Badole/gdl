<template>
	<div class="mx-auto max-w-md px-6 py-16">
		<h1 class="text-3xl font-extrabold text-ink">Create your applicant account</h1>
		<p class="mt-2 text-sm text-body">
			Register once, then complete your profile and apply to roles that match your skills.
		</p>

		<div v-if="submitted" class="mt-8 rounded-xl border border-brand-200 bg-brand-50 p-6 text-sm text-brand-800">
			<p class="font-semibold">Registration successful.</p>
			<p class="mt-2">Please check your email to verify your account, then sign in.</p>
			<router-link to="/login" class="mt-4 inline-block font-semibold text-brand-700 hover:text-brand-800">
				Go to sign in
			</router-link>
		</div>

		<form v-else @submit.prevent="submit" class="mt-8 space-y-5">
			<div>
				<label for="full_name" class="mb-1 block text-sm font-medium text-ink">Full name</label>
				<input
					id="full_name"
					v-model.trim="form.full_name"
					type="text"
					required
					class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
				/>
			</div>
			<div>
				<label for="email" class="mb-1 block text-sm font-medium text-ink">Email</label>
				<input
					id="email"
					v-model.trim="form.email"
					type="email"
					required
					class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
				/>
			</div>
			<div>
				<label for="phone" class="mb-1 block text-sm font-medium text-ink">Phone</label>
				<input
					id="phone"
					v-model.trim="form.phone"
					type="tel"
					required
					class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
				/>
			</div>
			<div>
				<label for="password" class="mb-1 block text-sm font-medium text-ink">Password</label>
				<input
					id="password"
					v-model="form.password"
					type="password"
					required
					minlength="8"
					class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
				/>
				<p class="mt-1 text-xs text-body">At least 8 characters, with both uppercase and lowercase letters.</p>
			</div>

			<p v-if="error" class="text-sm text-red-600">{{ error }}</p>

			<button
				type="submit"
				:disabled="submitting"
				class="w-full rounded-md bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
			>
				{{ submitting ? "Creating account..." : "Register" }}
			</button>

			<p class="text-center text-sm text-body">
				Already have an account?
				<router-link to="/login" class="font-semibold text-brand-700 hover:text-brand-800">Sign in</router-link>
			</p>
		</form>
	</div>
</template>

<script setup>
import { reactive, ref } from "vue";
import call from "../lib/call";

const form = reactive({ full_name: "", email: "", phone: "", password: "" });
const submitting = ref(false);
const submitted = ref(false);
const error = ref("");

async function submit() {
	submitting.value = true;
	error.value = "";
	try {
		await call("gdl.api.public.register_applicant", { ...form });
		submitted.value = true;
	} catch (e) {
		error.value = e.messages?.[0] || e.message || "Registration failed. Please try again.";
	} finally {
		submitting.value = false;
	}
}
</script>
