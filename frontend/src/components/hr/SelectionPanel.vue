<template>
	<div v-if="loaded">
		<EmptyState
			v-if="!rows.length"
			:icon="UsersIcon"
			title="No candidates to rank yet"
			subtitle="Candidates appear here once they reach Interview Completed."
		/>

		<template v-else>
			<p class="mb-4 text-sm text-body">
				Ranking weight: <strong class="text-ink">{{ interviewWeight }}% interview</strong>
				<template v-if="examWeight"> · <strong class="text-ink">{{ examWeight }}% test</strong></template>
			</p>

			<div v-if="selected.length" class="mb-3 flex items-center gap-2 rounded-md bg-gray-50 px-4 py-2">
				<span class="text-sm text-body">{{ selected.length }} selected</span>
				<button
					v-for="s in ['Selected', 'Reserve', 'Rejected']"
					:key="s"
					type="button"
					class="rounded-md border border-gray-200 bg-white px-3 py-1 text-xs font-medium text-ink hover:bg-gray-100"
					@click="bulkUpdate(s)"
				>
					{{ s }}
				</button>
			</div>

			<div class="overflow-x-auto rounded-xl border border-gray-200">
				<table class="w-full text-left text-sm">
					<thead class="border-b border-gray-200 text-xs uppercase tracking-wide text-body">
						<tr>
							<th class="w-8 px-4 py-3"></th>
							<th class="px-4 py-3 font-medium">Rank</th>
							<th class="px-4 py-3 font-medium">Applicant</th>
							<th class="px-4 py-3 font-medium">Status</th>
							<th class="px-4 py-3 font-medium">Test</th>
							<th class="px-4 py-3 font-medium">Interview</th>
							<th class="px-4 py-3 font-medium">Composite</th>
							<th class="px-4 py-3 text-right font-medium">Action</th>
						</tr>
					</thead>
					<tbody class="divide-y divide-gray-100">
						<tr v-for="(row, i) in rows" :key="row.name">
							<td class="px-4 py-3">
								<input v-model="selected" type="checkbox" :value="row.name" />
							</td>
							<td class="px-4 py-3 text-body">{{ i + 1 }}</td>
							<td class="px-4 py-3">
								<p class="font-medium text-ink">{{ row.applicant_name }}</p>
								<p class="text-xs text-body">{{ row.email_id }}</p>
							</td>
							<td class="px-4 py-3"><StatusPill :status="row.status" /></td>
							<td class="px-4 py-3 text-body">{{ row.exam_score ?? "—" }}</td>
							<td class="px-4 py-3 text-body">{{ row.interview_score ?? "—" }}</td>
							<td class="px-4 py-3 font-medium text-ink">{{ row.composite_score }}</td>
							<td class="px-4 py-3 text-right">
								<button
									v-if="row.status === 'Reserve'"
									type="button"
									class="text-xs font-medium text-brand-700 hover:underline"
									@click="promote(row.name)"
								>
									Promote to Selected
								</button>
							</td>
						</tr>
					</tbody>
				</table>
			</div>
			<p v-if="actionMessage" class="mt-2 text-sm text-brand-700">{{ actionMessage }}</p>
			<p v-if="actionError" class="mt-2 text-sm text-red-600">{{ actionError }}</p>
		</template>
	</div>

	<div v-else class="space-y-3">
		<div v-for="i in 3" :key="i" class="h-10 animate-pulse rounded-md bg-gray-100"></div>
	</div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import call from "../../lib/call";
import EmptyState from "../applicant/EmptyState.vue";
import StatusPill from "../applicant/StatusPill.vue";
import UsersIcon from "../icons/UsersIcon.vue";

const props = defineProps({
	jobOpening: { type: String, required: true },
});

const rows = ref([]);
const interviewWeight = ref(100);
const examWeight = ref(0);
const loaded = ref(false);
const selected = ref([]);
const actionMessage = ref("");
const actionError = ref("");

async function load() {
	const res = await call("gdl.api.hr_selection.get_selection_ranking", { job_opening: props.jobOpening });
	const data = res?.data || { rows: [], interview_weight: 100, exam_weight: 0 };
	rows.value = data.rows;
	interviewWeight.value = data.interview_weight;
	examWeight.value = data.exam_weight;
	selected.value = [];
}

onMounted(async () => {
	try {
		await load();
	} finally {
		loaded.value = true;
	}
});

async function bulkUpdate(status) {
	actionMessage.value = "";
	actionError.value = "";
	try {
		const res = await call("gdl.api.hr_selection.bulk_set_selection_status", { job_applications: selected.value, status });
		actionMessage.value = res.message;
		await load();
	} catch (err) {
		actionError.value = err.messages?.[0] || "Could not update.";
	}
}

async function promote(jobApplication) {
	actionMessage.value = "";
	actionError.value = "";
	try {
		const res = await call("gdl.api.hr_selection.promote_reserve", { job_application: jobApplication });
		actionMessage.value = res.message;
		await load();
	} catch (err) {
		actionError.value = err.messages?.[0] || "Could not promote candidate.";
	}
}
</script>
