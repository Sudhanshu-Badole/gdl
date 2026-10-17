<template>
	<div v-if="loaded">
		<p v-if="!data.template" class="mb-4 rounded-md border border-dashed border-gray-300 p-4 text-sm text-body">
			No checklist template configured for this vacancy's category yet — set one up in Desk
			(Shortlisting Checklist Template) to enable scoring. Bulk Shortlist/Reject/Hold and advancing
			candidates still work without one.
		</p>

		<EmptyState
			v-if="!data.applications.length"
			:icon="UsersIcon"
			title="No applications to review"
			subtitle="Applications will appear here once candidates apply to this vacancy."
		/>

		<template v-else>
			<div v-if="selected.length" class="mb-3 flex items-center gap-2 rounded-md bg-gray-50 px-4 py-2">
				<span class="text-sm text-body">{{ selected.length }} selected</span>
				<button
					v-for="s in ['Shortlisted', 'Not Shortlisted', 'Review on Hold']"
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
							<th class="px-4 py-3 font-medium">Applicant</th>
							<th class="px-4 py-3 font-medium">Status</th>
							<th class="px-4 py-3 font-medium">Score</th>
							<th class="px-4 py-3 text-right font-medium">Action</th>
						</tr>
					</thead>
					<tbody class="divide-y divide-gray-100">
						<template v-for="app in data.applications" :key="app.name">
							<tr>
								<td class="px-4 py-3">
									<input v-model="selected" type="checkbox" :value="app.name" />
								</td>
								<td class="px-4 py-3">
									<p class="font-medium text-ink">{{ app.applicant_name }}</p>
									<p class="text-xs text-body">{{ app.email_id }}</p>
								</td>
								<td class="px-4 py-3">
									<StatusPill :status="app.status" />
								</td>
								<td class="px-4 py-3 text-body">
									{{ app.total_score ?? "—" }}
								</td>
								<td class="px-4 py-3 text-right">
									<button
										v-if="data.template"
										type="button"
										class="text-xs font-medium text-brand-700 hover:underline"
										@click="toggleScoring(app.name)"
									>
										{{ app.total_score != null ? "Edit score" : "Score" }}
									</button>
								</td>
							</tr>
							<tr v-if="scoringFor === app.name">
								<td colspan="5" class="px-4 pb-4">
									<ChecklistScoreForm
										:job-application="app.name"
										:criteria="data.template.criteria"
										:existing-scores="app.criterion_scores"
										@saved="(total) => onScoreSaved(app, total)"
										@cancel="scoringFor = null"
									/>
								</td>
							</tr>
						</template>
					</tbody>
				</table>
			</div>

			<div class="mt-6 flex flex-wrap items-center gap-3 rounded-xl border border-gray-200 p-4">
				<span class="text-sm font-medium text-ink">Advance top</span>
				<input v-model.number="cutoff" type="number" min="1" class="w-20 rounded-md border border-gray-200 px-2 py-1.5 text-sm" />
				<span class="text-sm text-body">shortlisted candidate(s) by score to</span>
				<span class="text-sm font-medium text-ink">{{ data.exam_required ? "Test" : "Interview" }}</span>
				<button
					type="button"
					:disabled="advancing"
					class="ml-auto rounded-md bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
					@click="advance"
				>
					Advance
				</button>
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
import ChecklistScoreForm from "./ChecklistScoreForm.vue";
import UsersIcon from "../icons/UsersIcon.vue";

const props = defineProps({
	jobOpening: { type: String, required: true },
});

const data = ref({ template: null, applications: [], exam_required: false });
const loaded = ref(false);
const selected = ref([]);
const scoringFor = ref(null);
const cutoff = ref(1);
const advancing = ref(false);
const actionMessage = ref("");
const actionError = ref("");

async function load() {
	const res = await call("gdl.api.hr_shortlisting.get_shortlisting_queue", { job_opening: props.jobOpening });
	data.value = res?.data || { template: null, applications: [], exam_required: false };
	selected.value = [];
}

onMounted(async () => {
	try {
		await load();
	} finally {
		loaded.value = true;
	}
});

function toggleScoring(name) {
	scoringFor.value = scoringFor.value === name ? null : name;
}

async function onScoreSaved(app, total) {
	scoringFor.value = null;
	actionMessage.value = "";
	actionError.value = "";
	await load();
}

async function bulkUpdate(status) {
	actionMessage.value = "";
	actionError.value = "";
	try {
		const res = await call("gdl.api.hr_shortlisting.bulk_set_shortlist_status", {
			job_applications: selected.value,
			status,
		});
		actionMessage.value = res.message;
		await load();
	} catch (err) {
		actionError.value = err.messages?.[0] || "Could not update.";
	}
}

async function advance() {
	advancing.value = true;
	actionMessage.value = "";
	actionError.value = "";
	try {
		const res = await call("gdl.api.hr_shortlisting.advance_shortlisted", {
			job_opening: props.jobOpening,
			cutoff: cutoff.value,
		});
		if (res.success) {
			actionMessage.value = res.message;
			await load();
		} else {
			actionError.value = res.message || "Could not advance candidates.";
		}
	} catch (err) {
		actionError.value = err.messages?.[0] || "Could not advance candidates.";
	} finally {
		advancing.value = false;
	}
}
</script>
