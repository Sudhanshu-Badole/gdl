<template>
	<form class="space-y-3 rounded-md border border-gray-200 bg-gray-50 p-4" @submit.prevent="save">
		<div class="grid gap-3 sm:grid-cols-[1fr_auto]">
			<div>
				<label class="mb-1 block text-sm font-medium text-ink">Criterion</label>
				<input v-model="form.criterion_label" type="text" class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm" />
			</div>
			<div>
				<label class="mb-1 block text-sm font-medium text-ink">Max score</label>
				<input
					v-model.number="form.max_score"
					type="number"
					min="0"
					step="0.5"
					class="w-24 rounded-md border border-gray-200 px-3 py-2 text-sm"
				/>
			</div>
		</div>

		<div>
			<label class="mb-1 block text-sm font-medium text-ink">Description (optional)</label>
			<textarea
				v-model="form.description"
				rows="2"
				placeholder="Guidance shown to panel members while scoring this criterion"
				class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm"
			></textarea>
		</div>

		<p v-if="error" class="text-sm text-red-600">{{ error }}</p>

		<div class="flex gap-2">
			<button
				type="submit"
				:disabled="saving"
				class="rounded-md bg-brand-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
			>
				{{ existing ? "Save criterion" : "Add criterion" }}
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
	interview: { type: String, required: true },
	existing: { type: Object, default: null },
});
const emit = defineEmits(["saved", "cancel"]);

const form = ref(
	props.existing
		? {
				criterion_label: props.existing.criterion_label,
				description: props.existing.description,
				max_score: props.existing.max_score,
			}
		: { criterion_label: "", description: "", max_score: 10 }
);
const saving = ref(false);
const error = ref("");

async function save() {
	saving.value = true;
	error.value = "";
	try {
		const method = props.existing ? "gdl.api.hr_interview.update_criterion" : "gdl.api.hr_interview.add_criterion";
		const args = props.existing
			? { name: props.existing.name, ...form.value }
			: { interview: props.interview, ...form.value };
		const res = await call(method, args);
		if (res.success) {
			emit("saved");
		} else {
			error.value = res.message || "Could not save criterion.";
		}
	} catch (err) {
		error.value = err.messages?.[0] || "Could not save criterion.";
	} finally {
		saving.value = false;
	}
}
</script>
