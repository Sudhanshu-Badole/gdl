<template>
	<div id="employment-section" class="rounded-xl border border-gray-200 p-6">
		<div class="flex items-center justify-between">
			<h2 class="font-semibold text-ink">Work experience</h2>
			<button
				v-if="!showForm"
				type="button"
				class="rounded-md bg-brand-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-brand-700"
				@click="startAdd"
			>
				+ Add experience
			</button>
		</div>
		<p class="mt-1 text-sm text-body">Required for experienced vacancies (with an experience letter).</p>

		<EmptyState
			v-if="!rows.length && !showForm"
			:icon="BriefcaseIcon"
			title="No experience added"
			subtitle="Required for experienced vacancies. Upload a certificate or experience letter (PDF) for each role."
		/>

		<div v-else-if="rows.length" class="mt-4 space-y-3">
			<div v-for="row in rows" :key="row.name" class="flex items-center justify-between border-b border-gray-100 pb-3">
				<div>
					<p class="font-medium text-ink">
						<template v-if="row.job_title">{{ row.job_title }} at </template>{{ row.company_name }}
					</p>
					<p class="text-xs text-body">
						{{ row.start_date || "" }} - {{ row.currently_working ? "Present" : row.end_date || "" }}
					</p>
				</div>
				<div class="flex shrink-0 gap-3 text-xs">
					<button type="button" class="font-medium text-brand-700 hover:underline" @click="startEdit(row)">Edit</button>
					<button type="button" class="font-medium text-red-600 hover:underline" @click="remove(row.name)">Delete</button>
				</div>
			</div>
			<p v-if="deleteError" class="text-sm text-red-600">{{ deleteError }}</p>
		</div>

		<form v-if="showForm" class="mt-4 space-y-3 border-t border-gray-100 pt-4" @submit.prevent="save">
			<div class="grid gap-3 sm:grid-cols-2">
				<input v-model="form.company_name" required placeholder="Company Name" class="rounded-md border border-gray-200 px-3 py-2 text-sm" />
				<input v-model="form.job_title" placeholder="Job Title" class="rounded-md border border-gray-200 px-3 py-2 text-sm" />
			</div>
			<div class="grid gap-3 sm:grid-cols-3">
				<div>
					<label class="mb-1 block text-xs text-body">Start Date</label>
					<input v-model="form.start_date" type="date" class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm" />
				</div>
				<div>
					<label class="mb-1 block text-xs text-body">End Date</label>
					<input v-model="form.end_date" type="date" :disabled="form.currently_working" class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm disabled:bg-gray-100" />
				</div>
				<label class="flex items-center gap-2 self-end pb-2 text-sm text-ink">
					<input v-model="form.currently_working" type="checkbox" />
					Currently working here
				</label>
			</div>
			<textarea v-model="form.responsibilities" rows="2" placeholder="Responsibilities (optional)" class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm"></textarea>
			<p v-if="error" class="text-sm text-red-600">{{ error }}</p>
			<div class="flex gap-2">
				<button type="submit" :disabled="saving" class="rounded-md bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60">
					{{ editingRowName ? "Save changes" : "Add experience" }}
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
import call from "../../lib/call";
import EmptyState from "./EmptyState.vue";
import BriefcaseIcon from "../icons/BriefcaseIcon.vue";

defineProps({
	rows: { type: Array, required: true },
});
const emit = defineEmits(["changed"]);

const FIELDS = ["company_name", "job_title", "start_date", "end_date", "currently_working", "responsibilities"];
const EMPTY_FORM = () => ({
	company_name: "",
	job_title: "",
	start_date: "",
	end_date: "",
	currently_working: false,
	responsibilities: "",
});

const showForm = ref(false);
const editingRowName = ref(null);
const form = ref(EMPTY_FORM());
const saving = ref(false);
const error = ref("");
const deleteError = ref("");

function startAdd() {
	editingRowName.value = null;
	form.value = EMPTY_FORM();
	showForm.value = true;
}

function startEdit(row) {
	editingRowName.value = row.name;
	form.value = { ...EMPTY_FORM(), ...row, currently_working: !!row.currently_working };
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
		for (const f of FIELDS) {
			args[f] = f === "currently_working" ? (form.value[f] ? 1 : 0) : form.value[f] || "";
		}
		const method = editingRowName.value ? "gdl.api.applicant.update_employment" : "gdl.api.applicant.add_employment";
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
	deleteError.value = "";
	try {
		const res = await call("gdl.api.applicant.delete_employment", { row_name: rowName });
		if (res.success) {
			emit("changed");
		} else {
			deleteError.value = res.message || "Could not delete this record.";
		}
	} catch (err) {
		deleteError.value = err.messages?.[0] || "Could not delete this record.";
	}
}
</script>
