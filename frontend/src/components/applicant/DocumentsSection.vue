<template>
	<div id="documents-section" class="rounded-xl border border-gray-200 p-6">
		<h2 class="font-semibold text-ink">Documents</h2>
		<p class="mt-1 text-sm text-body">Upload your CV and any other supporting files. CID and certificates are uploaded in Personal and Education sections.</p>

		<p v-if="!applicant.resume_attachment" class="mt-4 rounded-md bg-amber-50 px-4 py-2 text-sm text-amber-800">
			Upload your <strong>CV / Résumé</strong> to apply.
		</p>

		<div class="mt-4 space-y-3">
			<div v-for="doc in fixedDocs" :key="doc.method" class="flex items-center justify-between border-b border-gray-100 pb-3">
				<div>
					<p class="text-sm font-medium text-ink">
						{{ doc.label }} <span v-if="doc.required" class="text-red-600">*</span>
					</p>
					<a v-if="applicant[doc.field]" :href="applicant[doc.field]" target="_blank" class="text-xs font-medium text-brand-700 hover:underline">
						View uploaded file
					</a>
					<span v-else class="text-xs text-body">Not uploaded</span>
				</div>
				<label class="cursor-pointer rounded-md border border-gray-200 px-3 py-1.5 text-sm font-medium text-ink hover:bg-gray-50">
					{{ applicant[doc.field] ? "Replace" : "Upload" }}
					<input type="file" accept=".pdf,.jpg,.jpeg,.png,.docx" class="hidden" @change="(e) => uploadFixed(e, doc.method)" />
				</label>
			</div>
		</div>
		<p v-if="fixedError" class="mt-2 text-xs text-red-600">{{ fixedError }}</p>
		<p class="mt-3 text-xs text-body">PDF, JPG, PNG, or DOCX - max 5MB each.</p>

		<h3 class="mb-3 mt-6 font-medium text-ink">Other Supporting Documents</h3>
		<p v-if="!applicant.gdl_other_documents?.length" class="text-sm text-body">No documents uploaded yet.</p>
		<div v-else class="mb-4 space-y-2">
			<div v-for="row in applicant.gdl_other_documents" :key="row.name" class="flex items-center justify-between border-b border-gray-100 pb-2">
				<a :href="row.attachment" target="_blank" class="text-sm font-medium text-brand-700 hover:underline">{{ row.document_type }}</a>
				<button type="button" class="text-xs font-medium text-red-600 hover:underline" @click="removeOther(row.name)">Delete</button>
			</div>
		</div>

		<form class="flex flex-wrap items-end gap-3" @submit.prevent="addOther">
			<div>
				<label class="mb-1 block text-xs text-body">Document type</label>
				<select v-model="otherType" class="rounded-md border border-gray-200 px-3 py-2 text-sm">
					<option v-for="t in OTHER_TYPE_PRESETS" :key="t" :value="t">{{ t }}</option>
				</select>
				<input
					v-if="otherType === 'Other'"
					v-model="otherTypeCustom"
					type="text"
					placeholder="Specify type"
					class="mt-2 block rounded-md border border-gray-200 px-3 py-2 text-sm"
				/>
			</div>
			<div>
				<label class="mb-1 block text-xs text-body">File (PDF, DOCX)</label>
				<input ref="otherFileInput" type="file" accept=".pdf,.jpg,.jpeg,.png,.docx" class="text-sm" required />
			</div>
			<button type="submit" :disabled="addingOther" class="rounded-md bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60">
				Upload
			</button>
		</form>
		<p v-if="otherError" class="mt-2 text-xs text-red-600">{{ otherError }}</p>
	</div>
</template>

<script setup>
import { ref } from "vue";
import call from "@doppio/controllers/call";
import upload from "../../lib/upload";

const props = defineProps({
	applicant: { type: Object, required: true },
});
const emit = defineEmits(["changed"]);

const OTHER_TYPE_PRESETS = ["Cover Letter", "Reference Letter", "Certificate", "Other"];

const fixedDocs = [
	{ label: "Curriculum Vitae (CV)", field: "resume_attachment", method: "gdl.api.applicant.upload_cv", required: true },
	{
		label: "Academic Certificate",
		field: "gdl_academic_certificate",
		method: "gdl.api.applicant.upload_academic_certificate",
		required: true,
	},
	{
		label: "Experience Letter (optional)",
		field: "gdl_experience_letter",
		method: "gdl.api.applicant.upload_experience_letter",
		required: false,
	},
];

const fixedError = ref("");
const otherType = ref(OTHER_TYPE_PRESETS[0]);
const otherTypeCustom = ref("");
const otherFileInput = ref(null);
const addingOther = ref(false);
const otherError = ref("");

async function uploadFixed(e, method) {
	const file = e.target.files[0];
	if (!file) return;
	fixedError.value = "";
	try {
		const res = await upload(method, file);
		if (res.success) {
			emit("changed");
		} else {
			fixedError.value = res.message || "Upload failed.";
		}
	} catch (err) {
		fixedError.value = err.messages?.[0] || "Upload failed.";
	} finally {
		e.target.value = "";
	}
}

async function addOther() {
	const file = otherFileInput.value?.files[0];
	if (!file) return;
	const documentType = otherType.value === "Other" ? otherTypeCustom.value.trim() || "Other" : otherType.value;

	addingOther.value = true;
	otherError.value = "";
	try {
		const res = await upload("gdl.api.applicant.add_other_document", file, { document_type: documentType });
		if (res.success) {
			otherFileInput.value.value = "";
			otherTypeCustom.value = "";
			emit("changed");
		} else {
			otherError.value = res.message || "Upload failed.";
		}
	} catch (err) {
		otherError.value = err.messages?.[0] || "Upload failed.";
	} finally {
		addingOther.value = false;
	}
}

async function removeOther(rowName) {
	const res = await call("gdl.api.applicant.delete_other_document", { row_name: rowName });
	if (res.success) emit("changed");
}
</script>
