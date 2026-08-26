<template>
	<div class="rounded-xl border border-gray-200 p-6">
		<div class="flex items-center justify-between">
			<div>
				<h2 class="font-semibold text-ink">CID / National ID</h2>
				<p class="mt-1 text-sm text-body">Upload one PDF with the front and back of your CID clearly visible.</p>
			</div>
			<span
				class="rounded-full px-3 py-1 text-xs font-semibold"
				:class="fileUrl ? 'bg-brand-100 text-brand-700' : 'bg-gray-100 text-body'"
			>
				{{ fileUrl ? "Uploaded" : "Not uploaded" }}
			</span>
		</div>

		<div v-if="fileUrl" class="mt-4 flex items-center justify-between rounded-md bg-gray-50 px-4 py-2 text-sm">
			<span class="text-ink">{{ fileName }}</span>
			<a :href="fileUrl" target="_blank" class="font-medium text-brand-700 hover:underline">View</a>
		</div>

		<label class="mt-4 inline-block cursor-pointer rounded-md border border-gray-200 px-4 py-2 text-sm font-medium text-ink hover:bg-gray-50">
			{{ fileUrl ? "Replace CID (PDF)" : "Upload CID (PDF)" }}
			<input type="file" accept="application/pdf" class="hidden" @change="onChange" />
		</label>
		<p class="mt-1 text-xs text-body">PDF only</p>
		<p v-if="error" class="mt-2 text-xs text-red-600">{{ error }}</p>
	</div>
</template>

<script setup>
import { computed, ref } from "vue";
import upload from "../../lib/upload";

const props = defineProps({
	fileUrl: { type: String, default: null },
});
const emit = defineEmits(["uploaded"]);

const error = ref("");
const fileName = computed(() => props.fileUrl?.split("/").pop() || "");

async function onChange(e) {
	const file = e.target.files[0];
	if (!file) return;
	error.value = "";
	try {
		const res = await upload("gdl.api.applicant.upload_national_id", file);
		if (res.success) {
			emit("uploaded");
		} else {
			error.value = res.message || "Could not upload document.";
		}
	} catch (err) {
		error.value = err.messages?.[0] || "Could not upload document.";
	} finally {
		e.target.value = "";
	}
}
</script>
