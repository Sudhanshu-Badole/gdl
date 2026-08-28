<template>
	<div class="mt-3 rounded-md border border-gray-200 bg-gray-50 p-4">
		<div v-if="!loaded" class="space-y-2">
			<div v-for="i in 2" :key="i" class="h-16 animate-pulse rounded-md bg-gray-100"></div>
		</div>

		<template v-else>
			<p v-if="!shortAnswerRows.length" class="text-sm text-body">No Short Answer questions to grade for this attempt.</p>

			<form v-else class="space-y-4" @submit.prevent="save">
				<div v-for="row in shortAnswerRows" :key="row.question" class="rounded-md border border-gray-200 bg-white p-3">
					<p class="text-sm font-medium text-ink">{{ row.question_text }}</p>
					<p class="mt-1 whitespace-pre-wrap text-sm text-body">{{ row.short_answer_text || "(no answer given)" }}</p>
					<div class="mt-2 flex items-center gap-2">
						<input
							v-model.number="scores[row.answer_name]"
							type="number"
							min="0"
							:max="row.marks"
							class="w-20 rounded-md border border-gray-200 px-2 py-1 text-sm"
						/>
						<span class="text-xs text-body">/ {{ row.marks }}</span>
					</div>
				</div>

				<p v-if="error" class="text-sm text-red-600">{{ error }}</p>

				<div class="flex gap-2">
					<button
						type="submit"
						:disabled="saving"
						class="rounded-md bg-brand-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
					>
						Save scores
					</button>
					<button type="button" class="rounded-md border border-gray-200 px-3 py-1.5 text-sm font-medium text-ink hover:bg-white" @click="$emit('cancel')">
						Cancel
					</button>
				</div>
			</form>
		</template>
	</div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import call from "../../lib/call";

const props = defineProps({
	attempt: { type: String, required: true },
});
const emit = defineEmits(["saved", "cancel"]);

const loaded = ref(false);
const questions = ref([]);
const scores = ref({});
const saving = ref(false);
const error = ref("");

const shortAnswerRows = computed(() => questions.value.filter((q) => q.question_type === "Short Answer" && q.answer_name));

onMounted(async () => {
	try {
		const res = await call("gdl.api.hr_exam.get_attempt_detail", { attempt: props.attempt });
		questions.value = res?.data?.questions || [];
		for (const row of shortAnswerRows.value) {
			scores.value[row.answer_name] = row.score_given ?? 0;
		}
	} finally {
		loaded.value = true;
	}
});

async function save() {
	saving.value = true;
	error.value = "";
	try {
		const res = await call("gdl.api.hr_exam.grade_answers", { attempt: props.attempt, scores: scores.value });
		if (res.success) {
			emit("saved");
		} else {
			error.value = res.message || "Could not save scores.";
		}
	} catch (err) {
		error.value = err.messages?.[0] || "Could not save scores.";
	} finally {
		saving.value = false;
	}
}
</script>
