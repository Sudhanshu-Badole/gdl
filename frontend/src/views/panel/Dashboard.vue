<template>
	<div>
		<h1 class="text-2xl font-bold text-ink">Your interview assignments</h1>
		<p class="mt-1 text-sm text-body">Upcoming interviews you're assigned to review.</p>

		<div v-if="loaded && !error" class="mt-6">
			<EmptyState
				v-if="!assignments.length"
				:icon="ClockIcon"
				title="No assignments yet"
				subtitle="You'll see interviews here once HR assigns you as a panel member."
			/>
			<div v-else class="space-y-3">
				<router-link
					v-for="a in assignments"
					:key="a.interview"
					:to="`/panel/interviews/${a.interview}`"
					class="block rounded-xl border border-gray-200 p-5 hover:border-brand-200"
				>
					<div class="flex items-start justify-between gap-4">
						<div>
							<p class="font-semibold text-ink">{{ a.job_title }}</p>
							<p class="text-sm text-body">{{ a.title }}</p>
							<p class="mt-2 text-sm text-body">
								{{ formatDateTime(a.scheduled_on) }}
								<template v-if="a.venue_or_link"> &middot; {{ a.venue_or_link }}</template>
							</p>
						</div>
						<span class="shrink-0 rounded-full bg-brand-50 px-3 py-1 text-xs font-semibold text-brand-700">
							{{ a.open_count }} of {{ a.candidate_count }} pending
						</span>
					</div>
				</router-link>
			</div>
		</div>

		<p v-else-if="loaded" class="mt-6 text-sm text-red-600">{{ error }}</p>

		<div v-else class="mt-6 space-y-3">
			<div v-for="i in 3" :key="i" class="h-20 animate-pulse rounded-xl bg-gray-100"></div>
		</div>
	</div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import call from "../../lib/call";
import EmptyState from "../../components/applicant/EmptyState.vue";
import ClockIcon from "../../components/icons/ClockIcon.vue";

const assignments = ref([]);
const loaded = ref(false);
const error = ref("");

onMounted(async () => {
	try {
		const res = await call("gdl.api.panel.get_dashboard");
		assignments.value = res?.data || [];
	} catch (err) {
		error.value = err.messages?.[0] || "Could not load your assignments.";
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
