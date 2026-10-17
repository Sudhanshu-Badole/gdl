<template>
	<form class="space-y-3" @submit.prevent="save">
		<div class="grid gap-3 sm:grid-cols-2">
			<div>
				<label class="mb-1 block text-sm font-medium text-ink">Question type</label>
				<select v-model="form.question_type" class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm">
					<option value="Multiple Choice">Multiple Choice</option>
					<option value="True or False">True or False</option>
					<option value="Short Answer">Short Answer</option>
				</select>
			</div>
			<div>
				<label class="mb-1 block text-sm font-medium text-ink">Marks</label>
				<input
					v-model.number="form.marks"
					type="number"
					min="0"
					step="0.5"
					class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm"
				/>
			</div>
		</div>

		<div>
			<label class="mb-1 block text-sm font-medium text-ink">Question</label>
			<textarea v-model="form.question_text" rows="2" class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm"></textarea>
		</div>

		<div class="grid gap-3 sm:grid-cols-2">
			<div>
				<label class="mb-1 block text-sm font-medium text-ink">Vacancy category (optional)</label>
				<select v-model="form.category" class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm">
					<option value="">None</option>
					<option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
				</select>
			</div>
			<div>
				<label class="mb-1 block text-sm font-medium text-ink">Tags (optional)</label>
				<input v-model="form.tags" type="text" placeholder="comma, separated, tags" class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm" />
			</div>
		</div>

		<div v-if="form.question_type === 'Multiple Choice'" class="grid gap-3 sm:grid-cols-2">
			<div v-for="opt in ['a', 'b', 'c', 'd']" :key="opt">
				<label class="mb-1 block text-sm font-medium text-ink">Option {{ opt.toUpperCase() }}</label>
				<input v-model="form[`option_${opt}`]" type="text" class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm" />
			</div>
		</div>

		<div v-if="form.question_type !== 'Short Answer'">
			<label class="mb-1 block text-sm font-medium text-ink">Correct option</label>
			<select v-model="form.correct_option" class="w-full max-w-[10rem] rounded-md border border-gray-200 px-3 py-2 text-sm">
				<option value="">Select...</option>
				<template v-if="form.question_type === 'True or False'">
					<option value="A">True</option>
					<option value="B">False</option>
				</template>
				<template v-else>
					<option v-for="opt in ['A', 'B', 'C', 'D']" :key="opt" :value="opt">{{ opt }}</option>
				</template>
			</select>
		</div>

		<p v-if="error" class="text-sm text-red-600">{{ error }}</p>

		<div class="flex gap-2">
			<button
				type="submit"
				:disabled="saving"
				class="rounded-md bg-brand-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
			>
				{{ existing ? "Save question" : "Add question" }}
			</button>
			<button type="button" class="rounded-md border border-gray-200 px-3 py-1.5 text-sm font-medium text-ink hover:bg-white" @click="$emit('cancel')">
				Cancel
			</button>
		</div>
	</form>
</template>

<script setup>
import { ref } from "vue";
import call from "../../lib/call";

const props = defineProps({
	existing: { type: Object, default: null },
	categories: { type: Array, default: () => [] },
});
const emit = defineEmits(["saved", "cancel"]);

function initialForm() {
	if (props.existing) {
		return {
			question_type: props.existing.question_type,
			question_text: props.existing.question_text,
			marks: props.existing.marks,
			category: props.existing.category || "",
			tags: props.existing.tags || "",
			option_a: props.existing.option_a || "",
			option_b: props.existing.option_b || "",
			option_c: props.existing.option_c || "",
			option_d: props.existing.option_d || "",
			correct_option: props.existing.correct_option || "",
		};
	}
	return {
		question_type: "Multiple Choice",
		question_text: "",
		marks: 1,
		category: "",
		tags: "",
		option_a: "",
		option_b: "",
		option_c: "",
		option_d: "",
		correct_option: "",
	};
}

const form = ref(initialForm());
const saving = ref(false);
const error = ref("");

async function save() {
	saving.value = true;
	error.value = "";
	try {
		const method = props.existing
			? "gdl.api.hr_question_bank.update_bank_question"
			: "gdl.api.hr_question_bank.create_bank_question";
		const args = props.existing ? { name: props.existing.name, ...form.value } : { ...form.value };
		const res = await call(method, args);
		if (res.success) {
			emit("saved");
		} else {
			error.value = res.message || "Could not save question.";
		}
	} catch (err) {
		error.value = err.messages?.[0] || "Could not save question.";
	} finally {
		saving.value = false;
	}
}
</script>
