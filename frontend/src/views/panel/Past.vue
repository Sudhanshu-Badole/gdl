<template>
	<div>
		<h1 class="text-2xl font-bold text-ink">Past interviews</h1>
		<p class="mt-1 text-sm text-body">Completed sessions you've scored.</p>

		<div v-if="loaded && !error" class="mt-6">
			<EmptyState
				v-if="!sessions.length"
				:icon="ClockIcon"
				title="No completed sessions yet"
				subtitle="Sessions you've scored will show up here once HR marks them completed."
			/>
			<div v-else class="overflow-x-auto rounded-xl border border-gray-200">
				<table class="w-full text-left text-sm">
					<thead class="border-b border-gray-200 text-xs uppercase tracking-wide text-body">
						<tr>
							<th class="px-4 py-3 font-medium">Candidate</th>
							<th class="px-4 py-3 font-medium">Vacancy</th>
							<th class="px-4 py-3 font-medium">Application</th>
							<th class="px-4 py-3 font-medium">Your score</th>
							<th class="px-4 py-3 font-medium">Submitted</th>
						</tr>
					</thead>
					<tbody class="divide-y divide-gray-100">
						<tr v-for="s in sessions" :key="s.session">
							<td class="px-4 py-3 font-medium text-ink">
								<router-link :to="`/panel/sessions/${s.session}`" class="text-brand-700 hover:underline">{{ s.applicant_name }}</router-link>
							</td>
							<td class="px-4 py-3 text-body">{{ s.job_title }}</td>
							<td class="px-4 py-3 text-body">{{ s.job_application }}</td>
							<td class="px-4 py-3 text-body">{{ s.score }}</td>
							<td class="px-4 py-3 text-body">{{ formatDate(s.submitted_on) }}</td>
						</tr>
					</tbody>
				</table>
			</div>
		</div>

		<p v-else-if="loaded" class="mt-6 text-sm text-red-600">{{ error }}</p>

		<div v-else class="mt-6 space-y-3">
			<div v-for="i in 3" :key="i" class="h-10 animate-pulse rounded-md bg-gray-100"></div>
		</div>
	</div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import call from "../../lib/call";
import EmptyState from "../../components/applicant/EmptyState.vue";
import ClockIcon from "../../components/icons/ClockIcon.vue";

const sessions = ref([]);
const loaded = ref(false);
const error = ref("");

onMounted(async () => {
	try {
		const res = await call("gdl.api.panel.get_past_sessions");
		sessions.value = res?.data || [];
	} catch (err) {
		error.value = err.messages?.[0] || "Could not load past interviews.";
	} finally {
		loaded.value = true;
	}
});

function formatDate(value) {
	if (!value) return "—";
	return new Date(value.replace(" ", "T")).toLocaleDateString("en-GB", {
		day: "numeric",
		month: "short",
		year: "numeric",
	});
}
</script>
