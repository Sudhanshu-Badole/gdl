<template>
	<div id="education-section" class="rounded-xl border border-gray-200 p-6">
		<div class="flex items-center justify-between">
			<h2 class="font-semibold text-ink">Education</h2>
			<button
				v-if="!showForm"
				type="button"
				class="rounded-md bg-brand-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-brand-700"
				@click="startAdd"
			>
				+ Add education
			</button>
		</div>

		<EmptyState
			v-if="!rows.length && !showForm"
			:icon="GraduationCapIcon"
			title="No education added"
			subtitle="Add your qualifications with your score (GPA or percentage) and upload the certificate (PDF) for each."
		/>

		<div v-else-if="rows.length" class="mt-4 space-y-3">
			<div v-for="row in rows" :key="row.name" class="flex items-center justify-between border-b border-gray-100 pb-3">
				<div>
					<p class="font-medium text-ink">{{ row.qualification }} - {{ row.institution_name }}</p>
					<p class="text-xs text-body">
						{{ row.start_date || "" }}<template v-if="row.completion_date"> - {{ row.completion_date }}</template>
						<template v-if="row.grade_or_result"> · {{ row.grade_or_result }}</template>
					</p>
				</div>
				<div class="flex shrink-0 gap-3 text-xs">
					<button type="button" class="font-medium text-brand-700 hover:underline" @click="startEdit(row)">Edit</button>
					<button type="button" class="font-medium text-red-600 hover:underline" @click="remove(row.name)">Delete</button>
				</div>
			</div>
		</div>

		<form v-if="showForm" class="mt-4 space-y-3 border-t border-gray-100 pt-4" @submit.prevent="save">
			<div class="grid gap-3 sm:grid-cols-2">
				<input v-model="form.qualification" required placeholder="Qualification" class="rounded-md border border-gray-200 px-3 py-2 text-sm" />
				<input v-model="form.institution_name" required placeholder="Institution Name" class="rounded-md border border-gray-200 px-3 py-2 text-sm" />
			</div>
			<div class="grid gap-3 sm:grid-cols-3">
				<div>
					<label class="mb-1 block text-xs text-body">Start Date</label>
					<input v-model="form.start_date" type="date" class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm" />
				</div>
				<div>
					<label class="mb-1 block text-xs text-body">Completion Date</label>
					<input v-model="form.completion_date" type="date" class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm" />
				</div>
				<input v-model="form.grade_or_result" placeholder="Grade or Result" class="self-end rounded-md border border-gray-200 px-3 py-2 text-sm" />
			</div>
			<p v-if="error" class="text-sm text-red-600">{{ error }}</p>
			<div class="flex gap-2">
				<button type="submit" :disabled="saving" class="rounded-md bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60">
					{{ editingRowName ? "Save changes" : "Add education" }}
				</button>
				<button type="button" class="rounded-md border border-gray-200 px-4 py-2 text-sm font-medium text-ink hover:bg-gray-50" @click="cancel">
					Cancel
				</button>
			</div>
		</form>
	</div>
</template>

<script setup>
import { ref } from "vue";
import call from "@doppio/controllers/call";
import EmptyState from "./EmptyState.vue";
import GraduationCapIcon from "../icons/GraduationCapIcon.vue";

defineProps({
	rows: { type: Array, required: true },
});
const emit = defineEmits(["changed"]);

const FIELDS = ["qualification", "institution_name", "start_date", "completion_date", "grade_or_result"];
const EMPTY_FORM = () => ({ qualification: "", institution_name: "", start_date: "", completion_date: "", grade_or_result: "" });

const showForm = ref(false);
const editingRowName = ref(null);
const form = ref(EMPTY_FORM());
const saving = ref(false);
const error = ref("");

function startAdd() {
	editingRowName.value = null;
	form.value = EMPTY_FORM();
	showForm.value = true;
}

function startEdit(row) {
	editingRowName.value = row.name;
	form.value = { ...EMPTY_FORM(), ...row };
	showForm.value = true;
}

function cancel() {
	showForm.value = false;
	editingRowName.value = null;
	error.value = "";
}

async function save() {
	saving.value = true;
	error.value = "";
	try {
		const args = {};
		for (const f of FIELDS) args[f] = form.value[f] || "";
		const method = editingRowName.value ? "gdl.api.applicant.update_education" : "gdl.api.applicant.add_education";
		if (editingRowName.value) args.row_name = editingRowName.value;
		const res = await call(method, args);
		if (res.success) {
			showForm.value = false;
			editingRowName.value = null;
			emit("changed");
		} else {
			error.value = res.message || "Could not save.";
		}
	} catch (err) {
		error.value = err.messages?.[0] || "Could not save.";
	} finally {
		saving.value = false;
	}
}

async function remove(rowName) {
	const res = await call("gdl.api.applicant.delete_education", { row_name: rowName });
	if (res.success) emit("changed");
}
</script>
