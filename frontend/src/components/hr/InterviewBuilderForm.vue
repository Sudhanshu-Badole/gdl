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
		<div class="grid gap-4 sm:grid-cols-2">
			<div>
				<label class="mb-1 block text-sm font-medium text-ink">Venue or meeting link</label>
				<input v-model="form.venue_or_link" type="text" class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm" />
			</div>
			<div>
				<label class="mb-1 block text-sm font-medium text-ink">Scheduled on</label>
				<input v-model="form.scheduled_on" type="datetime-local" class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm" />
			</div>
			<div>
				<label class="mb-1 block text-sm font-medium text-ink">Location map link (Google Maps)</label>
				<input v-model="form.gdl_location_map_link" type="url" placeholder="https://maps.google.com/..." class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm" />
			</div>
		</div>
		<label class="flex items-center gap-2 text-sm text-ink">
			<input v-model="form.panel_can_view_documents" type="checkbox" />
			Panel members can view candidate documents
		</label>
		<label class="flex items-center gap-2 text-sm text-ink">
			<input v-model="form.panel_can_view_exam_result" type="checkbox" />
			Panel members can view the candidate's test result
		</label>
		<div>
			<label class="mb-1 block text-sm font-medium text-ink">Score entry mode</label>
			<select v-model="form.score_entry_mode" class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm">
				<option value="Panel Self Entry">Panel Self Entry - panelists score via the Panel Portal</option>
				<option value="HR Proxy Entry">HR Proxy Entry - HR enters scores on a panelist's behalf</option>
				<option value="Compiled Scores">Compiled Scores - HR enters one aggregate number, no panel</option>
			</select>
		</div>

		<p v-if="error" class="text-sm text-red-600">{{ error }}</p>
		<p v-if="message" class="text-sm text-brand-700">{{ message }}</p>

		<button
			type="submit"
			:disabled="saving"
			class="rounded-md bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
		>
			{{ existing ? "Save interview details" : "Create interview" }}
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
			venue_or_link: props.existing.venue_or_link || "",
			gdl_location_map_link: props.existing.gdl_location_map_link || "",
			scheduled_on: toLocalInput(props.existing.scheduled_on),
			panel_can_view_documents: !!props.existing.panel_can_view_documents,
			panel_can_view_exam_result: !!props.existing.panel_can_view_exam_result,
			score_entry_mode: props.existing.score_entry_mode || "Panel Self Entry",
		};
	}
	return {
		title: "",
		instructions: "",
		venue_or_link: "",
		gdl_location_map_link: "",
		scheduled_on: "",
		panel_can_view_documents: false,
		panel_can_view_exam_result: false,
		score_entry_mode: "Panel Self Entry",
	};
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
		const payload = {
			...form.value,
			scheduled_on: toBackend(form.value.scheduled_on),
			panel_can_view_documents: form.value.panel_can_view_documents ? 1 : 0,
			panel_can_view_exam_result: form.value.panel_can_view_exam_result ? 1 : 0,
		};
		const method = props.existing ? "gdl.api.hr_interview.update_interview" : "gdl.api.hr_interview.create_interview";
		const args = props.existing ? { name: props.existing.name, ...payload } : { job_opening: props.jobOpening, ...payload };
		const res = await call(method, args);
		if (res.success) {
			message.value = res.message;
			emit("saved");
		} else {
			error.value = res.message || "Could not save interview.";
		}
	} catch (err) {
		error.value = err.messages?.[0] || "Could not save interview.";
	} finally {
		saving.value = false;
	}
}
</script>
