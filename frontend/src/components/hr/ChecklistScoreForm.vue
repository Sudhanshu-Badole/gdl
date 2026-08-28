<template>
	<form class="mt-3 space-y-3 rounded-md border border-gray-200 bg-gray-50 p-4" @submit.prevent="save">
		<div v-for="(row, i) in rows" :key="row.criterion_label" class="flex items-center justify-between gap-3">
			<span class="text-sm text-ink">{{ row.criterion_label }}</span>
			<div class="flex items-center gap-2">
				<input
					v-model.number="row.score_given"
					type="number"
					min="0"
					:max="row.max_score"
					class="w-20 rounded-md border border-gray-200 px-2 py-1 text-sm"
				/>
				<span class="text-xs text-body">/ {{ row.max_score }}</span>
			</div>
		</div>
		<div class="flex items-center justify-between border-t border-gray-200 pt-3">
			<span class="text-sm font-medium text-ink">Total: {{ total }} / {{ maxTotal }}</span>
			<div class="flex gap-2">
				<button type="submit" :disabled="saving" class="rounded-md bg-brand-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60">
					Save score
				</button>
				<button type="button" class="rounded-md border border-gray-200 px-3 py-1.5 text-sm font-medium text-ink hover:bg-white" @click="$emit('cancel')">
					Cancel
				</button>
			</div>
		</div>
		<p v-if="error" class="text-sm text-red-600">{{ error }}</p>
	</form>
</template>

<script setup>
import { ref, computed } from "vue";
import call from "../../lib/call";

const props = defineProps({
	jobApplication: { type: String, required: true },
	criteria: { type: Array, required: true },
	existingScores: { type: Array, default: () => [] },
});
const emit = defineEmits(["saved", "cancel"]);

function initialRows() {
	return props.criteria.map((c) => {
		const existing = props.existingScores.find((s) => s.criterion_label === c.criterion_label);
		return { criterion_label: c.criterion_label, max_score: c.max_score, score_given: existing?.score_given ?? 0 };
	});
}

const rows = ref(initialRows());
const saving = ref(false);
const error = ref("");

const total = computed(() => rows.value.reduce((sum, r) => sum + (Number(r.score_given) || 0), 0));
const maxTotal = computed(() => rows.value.reduce((sum, r) => sum + (Number(r.max_score) || 0), 0));

async function save() {
	saving.value = true;
	error.value = "";
	try {
		const res = await call("gdl.api.hr_shortlisting.save_shortlisting_score", {
			job_application: props.jobApplication,
			criterion_scores: rows.value,
		});
		if (res.success) {
			emit("saved", res.data.total_score);
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
