<template>
	<div v-if="loaded && data">
		<router-link to="/panel/dashboard" class="text-sm text-body hover:text-brand-700">← Your assignments</router-link>

		<h1 class="mt-3 text-2xl font-bold text-ink">{{ data.interview.job_title }}</h1>
		<p class="text-sm text-body">
			{{ data.interview.title }} &middot; {{ formatDateTime(data.interview.scheduled_on) }}
			<template v-if="data.interview.venue_or_link"> &middot; {{ data.interview.venue_or_link }}</template>
		</p>

		<div class="mt-6 space-y-3">
			<router-link
				v-for="s in data.sessions"
				:key="s.session"
				:to="{ path: `/panel/sessions/${s.session}`, query: { interview: props.interview } }"
				class="flex items-center justify-between rounded-xl border border-gray-200 p-4 hover:border-brand-200"
			>
				<div>
					<p class="font-medium text-ink">{{ s.applicant_name }}</p>
					<p class="text-xs text-body">
						{{ s.status }} &middot; {{ formatDateTime(s.scheduled_on) }} &middot; Attending: {{ s.attendance_response || "Pending" }}
					</p>
				</div>
				<span
					class="rounded-full px-3 py-1 text-xs font-semibold"
					:class="s.submitted ? 'bg-brand-100 text-brand-700' : 'bg-amber-50 text-amber-800'"
				>
					{{ s.submitted ? "Scored" : "Not scored yet" }}
				</span>
			</router-link>
		</div>
	</div>

	<p v-else-if="loaded" class="text-sm text-red-600">{{ error }}</p>

	<div v-else class="space-y-3">
		<div class="h-6 w-48 animate-pulse rounded bg-gray-100"></div>
		<div class="h-16 animate-pulse rounded-xl bg-gray-100"></div>
	</div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import call from "../../lib/call";

const props = defineProps({
	interview: { type: String, required: true },
});

const data = ref(null);
const loaded = ref(false);
const error = ref("");

onMounted(async () => {
	try {
		const res = await call("gdl.api.panel.get_interview_candidates", { interview: props.interview });
		if (res.success) {
			data.value = res.data;
		} else {
			error.value = res.message || "Could not load candidates.";
		}
	} catch (err) {
		error.value = err.messages?.[0] || "Could not load candidates.";
	} finally {
		loaded.value = true;
	}
});

function formatDateTime(value) {
	if (!value) return "—";
	return new Date(value.replace(" ", "T")).toLocaleString("en-GB", {
		day: "numeric",
		month: "short",
		hour: "2-digit",
		minute: "2-digit",
	});
}
</script>
