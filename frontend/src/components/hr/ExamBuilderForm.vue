<template>
	<form class="space-y-4" @submit.prevent="save">
		<div>
			<label class="mb-1 block text-sm font-medium text-ink">Title</label>
			<input v-model="form.title" type="text" class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm" />
		</div>
		<div>
			<label class="mb-1 block text-sm font-medium text-ink">Instructions</label>
			<textarea v-model="form.instructions" rows="3" class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm"></textarea>
		</div>
		<div class="grid gap-4 sm:grid-cols-3">
			<div>
				<label class="mb-1 block text-sm font-medium text-ink">Duration (minutes)</label>
				<input v-model.number="form.duration_minutes" type="number" min="1" class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm" />
			</div>
			<div>
				<label class="mb-1 block text-sm font-medium text-ink">Opens on</label>
				<input v-model="form.opens_on" type="datetime-local" class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm" />
			</div>
			<div>
				<label class="mb-1 block text-sm font-medium text-ink">Closes on</label>
				<input v-model="form.closes_on" type="datetime-local" class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm" />
			</div>
		</div>
		<div>
			<label class="mb-1 block text-sm font-medium text-ink">Pass marks</label>
			<input v-model.number="form.pass_marks" type="number" min="0" step="0.5" class="w-full max-w-[10rem] rounded-md border border-gray-200 px-3 py-2 text-sm" />
		</div>

		<p v-if="error" class="text-sm text-red-600">{{ error }}</p>
		<p v-if="message" class="text-sm text-brand-700">{{ message }}</p>

		<button
			type="submit"
			:disabled="saving"
			class="rounded-md bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
		>
			{{ existing ? "Save exam details" : "Create exam" }}
		</button>
	</form>
</template>

<script setup>
import { ref } from "vue";
import call from "../../lib/call";

const props = defineProps({
	jobOpening: { type: String, default: "" },
	existing: { type: Object, default: null },
});
const emit = defineEmits(["saved"]);

function toLocalInput(value) {
	if (!value) return "";
	return value.slice(0, 16).replace(" ", "T");
}

function toBackend(value) {
	if (!value) return null;
	return value.length === 16 ? `${value.replace("T", " ")}:00` : value.replace("T", " ");
}

function initialForm() {
	if (props.existing) {
		return {
			title: props.existing.title,
			instructions: props.existing.instructions || "",
			duration_minutes: props.existing.duration_minutes,
			opens_on: toLocalInput(props.existing.opens_on),
			closes_on: toLocalInput(props.existing.closes_on),
			pass_marks: props.existing.pass_marks,
		};
	}
	return { title: "", instructions: "", duration_minutes: 60, opens_on: "", closes_on: "", pass_marks: 0 };
}

const form = ref(initialForm());
const saving = ref(false);
const error = ref("");
const message = ref("");

async function save() {
	saving.value = true;
	error.value = "";
	message.value = "";
	try {
		const payload = { ...form.value, opens_on: toBackend(form.value.opens_on), closes_on: toBackend(form.value.closes_on) };
		const method = props.existing ? "gdl.api.hr_exam.update_exam" : "gdl.api.hr_exam.create_exam";
		const args = props.existing ? { name: props.existing.name, ...payload } : { job_opening: props.jobOpening, ...payload };
		const res = await call(method, args);
		if (res.success) {
			message.value = res.message;
			emit("saved");
		} else {
			error.value = res.message || "Could not save exam.";
		}
	} catch (err) {
		error.value = err.messages?.[0] || "Could not save exam.";
	} finally {
		saving.value = false;
	}
}
</script>
