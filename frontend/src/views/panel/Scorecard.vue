<template>
	<div v-if="loaded && needsConflictConfirmation" class="max-w-2xl rounded-xl border border-gray-200 p-6">
		<h1 class="text-xl font-bold text-ink">Before you continue</h1>
		<p class="mt-2 text-sm text-body">
			Confirm you have no conflict of interest (family, personal/financial relationship, or prior dealings) with this
			candidate before viewing their details or scoring them.
		</p>
		<p v-if="conflictError" class="mt-2 text-sm text-red-600">{{ conflictError }}</p>
		<div class="mt-4 flex gap-2">
			<button
				type="button"
				:disabled="confirmingConflict"
				class="rounded-md bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
				@click="confirmConflict(false)"
			>
				I have no conflict of interest
			</button>
			<button
				type="button"
				:disabled="confirmingConflict"
				class="rounded-md border border-gray-200 px-4 py-2 text-sm font-medium text-ink hover:bg-gray-50"
				@click="confirmConflict(true)"
			>
				I have a conflict of interest
			</button>
		</div>
	</div>

	<div v-else-if="loaded && hasConflictOfInterest" class="max-w-2xl rounded-xl border border-gray-200 p-6">
		<h1 class="text-xl font-bold text-ink">Not available</h1>
		<p class="mt-2 text-sm text-body">
			You declared a conflict of interest with this candidate. HR has been notified to reassign scoring.
		</p>
	</div>

	<div v-else-if="loaded && data" class="max-w-2xl">
		<router-link :to="backLink" class="text-sm text-body hover:text-brand-700">← Back to candidates</router-link>

		<h1 class="mt-3 text-2xl font-bold text-ink">{{ data.applicant_name }}</h1>
		<p v-if="data.locked" class="mt-1 text-sm text-body">
			{{ data.is_submitted ? "You have submitted your scores. They are locked and can no longer be edited." : "This session has been completed. Your scores are locked and can no longer be edited." }}
		</p>

		<Tabs v-model="activeTab" :tabs="['Overview', 'Documents', 'Test Results', 'Scorecard']" class="mt-4">
			<div v-if="activeTab === 'Overview'" class="rounded-xl border border-gray-200 p-4 text-sm text-body">
				<p>Use the tabs above to review the candidate's documents and test result before scoring them.</p>
				<p class="mt-2 font-medium text-ink">Total so far: {{ total }} / {{ maxTotal }}</p>
				<p v-if="data.venue_or_link" class="mt-2 text-body">Where: {{ data.venue_or_link }}</p>
				<a
					v-if="data.location_map_link"
					:href="data.location_map_link"
					target="_blank"
					class="mt-1 inline-block text-sm font-medium text-brand-700 hover:underline"
				>
					Get directions
				</a>
				<a
					v-if="data.terms_of_reference"
					:href="data.terms_of_reference.file_url"
					target="_blank"
					class="mt-3 block text-sm font-medium text-brand-700 hover:underline"
				>
					Terms of Reference ({{ data.terms_of_reference.filename }})
				</a>
			</div>

			<CandidateDocumentsCard v-else-if="activeTab === 'Documents'" :documents="data.documents" />

			<template v-else-if="activeTab === 'Test Results'">
				<ExamResultCard
					v-if="data.panel_can_view_exam_result"
					:result="examResult"
					:checked="examResultChecked"
					:session="props.session"
					:panel-editable="true"
				/>
				<p v-else class="text-sm text-body">Test result is not shared for this interview.</p>
			</template>

			<form v-else-if="activeTab === 'Scorecard'" class="space-y-4" @submit.prevent="save(false)">
				<div v-for="row in rows" :key="row.criterion" class="rounded-xl border border-gray-200 p-4">
					<div class="flex items-center justify-between gap-3">
						<div>
							<span class="text-sm font-medium text-ink">{{ row.criterion_label }}</span>
							<p v-if="row.description" class="mt-0.5 text-xs text-body">{{ row.description }}</p>
						</div>
						<div class="flex items-center gap-2">
							<input
								v-model.number="row.score_given"
								type="number"
								min="0"
								:max="row.max_score"
								:disabled="data.locked"
								class="w-20 rounded-md border border-gray-200 px-2 py-1 text-sm disabled:bg-gray-50"
							/>
							<span class="text-xs text-body">/ {{ row.max_score }}</span>
						</div>
					</div>
					<textarea
						v-model="row.comments"
						:disabled="data.locked"
						rows="2"
						placeholder="Comments (optional)"
						class="mt-2 w-full rounded-md border border-gray-200 px-3 py-2 text-sm disabled:bg-gray-50"
					></textarea>
				</div>

				<div class="rounded-xl border border-gray-200 p-4">
					<label class="mb-1 block text-sm font-medium text-ink">Overall comments</label>
					<textarea
						v-model="overallComments"
						:disabled="data.locked"
						rows="2"
						placeholder="Any overall remarks about the candidate (optional)"
						class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm disabled:bg-gray-50"
					></textarea>
				</div>

				<div class="flex items-center justify-between rounded-xl border border-gray-200 p-4">
					<span class="text-sm font-medium text-ink">Total: {{ total }} / {{ maxTotal }}</span>
					<div v-if="!data.locked" class="flex gap-2">
						<button
							type="submit"
							:disabled="saving"
							class="rounded-md border border-gray-200 px-4 py-2 text-sm font-semibold text-ink hover:bg-gray-50 disabled:opacity-60"
						>
							{{ saving ? "Saving..." : "Save draft" }}
						</button>
						<button
							type="button"
							:disabled="saving"
							class="rounded-md bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
							@click="save(true)"
						>
							Submit score
						</button>
					</div>
				</div>
				<p v-if="error" class="text-sm text-red-600">{{ error }}</p>
				<p v-if="message" class="text-sm text-brand-700">{{ message }}</p>
			</form>
		</Tabs>
	</div>

	<p v-else-if="loaded" class="text-sm text-red-600">{{ loadError }}</p>

	<div v-else class="max-w-2xl space-y-4">
		<div class="h-6 w-48 animate-pulse rounded bg-gray-100"></div>
		<div class="h-40 animate-pulse rounded-xl bg-gray-100"></div>
	</div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useRoute } from "vue-router";
import call from "../../lib/call";
import ExamResultCard from "../../components/shared/ExamResultCard.vue";
import CandidateDocumentsCard from "../../components/shared/CandidateDocumentsCard.vue";
import Tabs from "../../components/shared/Tabs.vue";

const props = defineProps({
	session: { type: String, required: true },
});
const route = useRoute();

const activeTab = ref("Overview");
const data = ref(null);
const rows = ref([]);
const overallComments = ref("");
const loaded = ref(false);
const loadError = ref("");
const saving = ref(false);
const error = ref("");
const message = ref("");
const examResult = ref(null);
const examResultChecked = ref(false);
const needsConflictConfirmation = ref(false);
const hasConflictOfInterest = ref(false);
const confirmingConflict = ref(false);
const conflictError = ref("");

const backLink = computed(() => (route.query.interview ? `/panel/interviews/${route.query.interview}` : "/panel/past"));

const total = computed(() => rows.value.reduce((sum, r) => sum + (Number(r.score_given) || 0), 0));
const maxTotal = computed(() => rows.value.reduce((sum, r) => sum + (Number(r.max_score) || 0), 0));

async function loadScorecard() {
	try {
		const res = await call("gdl.api.panel.get_scorecard", { session: props.session });
		if (res.success) {
			if (res.data.needs_conflict_confirmation) {
				needsConflictConfirmation.value = true;
				return;
			}
			if (res.data.has_conflict_of_interest) {
				hasConflictOfInterest.value = true;
				return;
			}
			data.value = res.data;
			overallComments.value = res.data.existing_overall_comments || "";
			const existingByCriterion = {};
			for (const s of data.value.existing_scores) existingByCriterion[s.criterion] = s;
			rows.value = data.value.criteria.map((c) => {
				const existing = existingByCriterion[c.name];
				return {
					criterion: c.name,
					criterion_label: c.criterion_label,
					description: c.description,
					max_score: c.max_score,
					score_given: existing?.score_given ?? 0,
					comments: existing?.comments ?? "",
				};
			});

			if (data.value.panel_can_view_exam_result) {
				try {
					const examRes = await call("gdl.api.panel.get_candidate_exam_result", { session: props.session });
					examResult.value = examRes?.data || null;
				} catch {
					// non-critical - just skip showing the exam result if this fails
				} finally {
					examResultChecked.value = true;
				}
			}
		} else {
			loadError.value = res.message || "Could not load this scorecard.";
		}
	} catch (err) {
		loadError.value = err.messages?.[0] || "Could not load this scorecard.";
	} finally {
		loaded.value = true;
	}
}

async function confirmConflict(hasConflict) {
	confirmingConflict.value = true;
	conflictError.value = "";
	try {
		const res = await call("gdl.api.panel.confirm_no_conflict", { session: props.session, has_conflict: hasConflict ? 1 : 0 });
		if (res.success) {
			needsConflictConfirmation.value = false;
			if (hasConflict) {
				hasConflictOfInterest.value = true;
			} else {
				await loadScorecard();
			}
		} else {
			conflictError.value = res.message || "Could not record your response.";
		}
	} catch (err) {
		conflictError.value = err.messages?.[0] || "Could not record your response.";
	} finally {
		confirmingConflict.value = false;
	}
}

onMounted(async () => {
	await loadScorecard();
});

async function save(submit) {
	if (submit && !window.confirm("Submit your scores? Once submitted you will not be able to change them.")) return;
	saving.value = true;
	error.value = "";
	message.value = "";
	try {
		const res = await call("gdl.api.panel.save_scorecard", {
			session: props.session,
			criterion_scores: rows.value,
			overall_comments: overallComments.value,
			submit: submit ? 1 : 0,
		});
		if (res.success) {
			message.value = res.message;
			if (submit) { data.value.locked = true; data.value.is_submitted = true; }
		} else {
			error.value = res.message || "Could not save score.";
		}
	} catch (err) {
		error.value = err.messages?.[0] || "Could not save score.";
	} finally {
		saving.value = false;
	}
}
</script>
