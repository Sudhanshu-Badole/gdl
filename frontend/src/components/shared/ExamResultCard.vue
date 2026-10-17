<template>
	<div v-if="result" class="mt-4 rounded-xl border border-gray-200 p-4">
		<h2 class="mb-2 text-sm font-semibold text-ink">Test result — {{ result.exam_title }}</h2>
		<p class="text-sm text-body">
			Status: {{ result.status }}
			<template v-if="result.is_fully_graded">
				· Score: {{ result.total_score }}
				<span v-if="result.is_pass != null" :class="result.is_pass ? 'text-brand-700' : 'text-red-600'">
					({{ result.is_pass ? "Pass" : "Fail" }})
				</span>
			</template>
			<template v-else> · Grading not yet complete</template>
		</p>

		<div v-if="result.evaluator_comment" class="mt-3 rounded-md bg-gray-50 p-2 text-sm">
			<p class="text-xs font-medium text-body">Evaluator comment</p>
			<p class="mt-0.5 text-ink">{{ result.evaluator_comment }}</p>
		</div>

		<div class="mt-3 space-y-2">
			<div v-for="(q, i) in result.questions" :key="i" class="rounded-md border border-gray-200 p-2 text-sm">
				<p class="text-ink">{{ i + 1 }}. {{ q.question_text }} <span class="text-xs text-body">({{ q.marks }} marks)</span></p>
				<p class="mt-1 text-body">
					Answer: {{ q.selected_option || q.short_answer_text || "—" }}
					<template v-if="q.is_graded"> · Score: {{ q.score_given }}</template>
					<template v-else> · Not graded yet</template>
				</p>
				<p v-if="q.evaluator_comment" class="mt-1 text-xs text-body">Comment: {{ q.evaluator_comment }}</p>
			</div>
		</div>

		<div v-if="panelEditable" class="mt-3 border-t border-gray-100 pt-3">
			<label class="mb-1 block text-xs font-medium text-body">Your comment on this result</label>
			<textarea
				v-model="localPanelComment"
				rows="2"
				placeholder="Comments (optional)"
				class="w-full rounded-md border border-gray-200 px-2 py-1.5 text-sm"
			></textarea>
			<button
				type="button"
				:disabled="savingComment"
				class="mt-1 rounded-md border border-gray-200 px-2 py-1 text-xs font-medium text-ink hover:bg-gray-50 disabled:opacity-60"
				@click="savePanelComment"
			>
				{{ savingComment ? "Saving…" : "Save comment" }}
			</button>
			<p v-if="commentError" class="mt-1 text-xs text-red-600">{{ commentError }}</p>
		</div>
		<div v-else-if="result.panel_comment" class="mt-3 rounded-md bg-gray-50 p-2 text-sm">
			<p class="text-xs font-medium text-body">Panel comment</p>
			<p class="mt-0.5 text-ink">{{ result.panel_comment }}</p>
		</div>
	</div>
	<p v-else-if="checked" class="mt-4 text-sm text-body">No test was required for this candidate.</p>
</template>

<script setup>
import { ref, watch } from "vue";
import call from "../../lib/call";

const props = defineProps({
	result: { type: Object, default: null },
	checked: { type: Boolean, default: false },
	session: { type: String, default: null },
	panelEditable: { type: Boolean, default: false },
});

const localPanelComment = ref(props.result?.panel_comment || "");
watch(
	() => props.result,
	(r) => {
		localPanelComment.value = r?.panel_comment || "";
	}
);

const savingComment = ref(false);
const commentError = ref("");

async function savePanelComment() {
	savingComment.value = true;
	commentError.value = "";
	try {
		const res = await call("gdl.api.panel.save_exam_result_comment", {
			session: props.session,
			comment: localPanelComment.value,
		});
		if (!res.success) {
			commentError.value = res.message || "Could not save comment.";
		}
	} catch (err) {
		commentError.value = err.messages?.[0] || "Could not save comment.";
	} finally {
		savingComment.value = false;
	}
}
</script>
