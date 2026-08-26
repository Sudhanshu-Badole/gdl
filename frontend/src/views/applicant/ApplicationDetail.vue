<template>
	<div v-if="loaded && detail">
		<h1 class="text-2xl font-bold text-ink">{{ detail.job_opening.job_title }}</h1>
		<p class="text-sm text-body">{{ detail.application.name }}</p>
		<div class="mt-2">
			<StatusPill :status="detail.application.status" />
		</div>

		<div class="mt-6 grid gap-6 lg:grid-cols-3">
			<div class="space-y-6 lg:col-span-2">
				<div class="rounded-xl border border-gray-200 p-6">
					<h2 class="mb-2 font-semibold text-ink">Examination</h2>
					<p class="text-sm text-body">Not scheduled yet.</p>
				</div>
				<div class="rounded-xl border border-gray-200 p-6">
					<h2 class="mb-2 font-semibold text-ink">Interview</h2>
					<p class="text-sm text-body">Not scheduled yet.</p>
				</div>
				<div class="rounded-xl border border-gray-200 p-6">
					<h2 class="mb-2 font-semibold text-ink">Offer &amp; Appointment</h2>
					<p class="text-sm text-body">No offer issued yet.</p>
				</div>
			</div>

			<div class="space-y-6">
				<div class="rounded-xl border border-gray-200 p-6">
					<h2 class="mb-2 font-semibold text-ink">Cover Letter</h2>
					<p class="text-sm text-body">{{ detail.application.cover_letter || "(none provided)" }}</p>
				</div>
				<router-link to="/applications" class="inline-block text-sm font-medium text-brand-700 hover:underline">
					← Back to My Applications
				</router-link>
			</div>
		</div>
	</div>

	<p v-else-if="loaded" class="text-sm text-body">{{ error || "Application not found." }}</p>

	<div v-else class="space-y-4">
		<div class="h-8 w-64 animate-pulse rounded bg-gray-100"></div>
		<div class="h-32 animate-pulse rounded-xl bg-gray-100"></div>
	</div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import call from "@doppio/controllers/call";
import StatusPill from "../../components/applicant/StatusPill.vue";

const props = defineProps({
	name: { type: String, required: true },
});

const detail = ref(null);
const loaded = ref(false);
const error = ref("");

onMounted(async () => {
	try {
		const res = await call("gdl.api.applicant.get_application_detail", { name: props.name });
		if (res.success) {
			detail.value = res.data;
		} else {
			error.value = res.message;
		}
	} catch (err) {
		error.value = err.messages?.[0] || "Application not found.";
	} finally {
		loaded.value = true;
	}
});
</script>
