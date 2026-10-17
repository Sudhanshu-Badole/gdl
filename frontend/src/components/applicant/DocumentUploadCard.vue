<template>
	<div class="rounded-xl border border-gray-200 p-6">
		<div class="flex items-center justify-between">
			<div>
				<h2 class="font-semibold text-ink">
					{{ title }} <span v-if="required" class="text-red-600">*</span>
				</h2>
				<p class="mt-1 text-sm text-body">{{ description }}</p>
			</div>
			<span class="rounded-full px-3 py-1 text-xs font-semibold" :class="statusBadgeClass">
				{{ statusLabel }}
			</span>
		</div>

		<p v-if="status === 'Sent Back' && remark" class="mt-3 rounded-md bg-red-50 px-3 py-2 text-xs text-red-700">
			HR sent this back: {{ remark }}
		</p>

		<div v-if="fileUrl" class="mt-4 flex items-center justify-between rounded-md bg-gray-50 px-4 py-2 text-sm">
			<span class="text-ink">{{ fileName }}</span>
			<a :href="fileUrl" target="_blank" class="font-medium text-brand-700 hover:underline">View</a>
		</div>

		<label
			class="mt-4 inline-block cursor-pointer rounded-md border border-gray-200 px-4 py-2 text-sm font-medium text-ink hover:bg-gray-50"
		>
			{{ fileUrl ? "Replace" : "Upload" }}
			<input type="file" :accept="accept" class="hidden" @change="onChange" />
		</label>
		<p class="mt-1 text-xs text-body">{{ hint }}</p>
		<p v-if="error" class="mt-2 text-xs text-red-600">{{ error }}</p>
	</div>
</template>

<script setup>
import { computed, ref } from "vue";
import upload from "../../lib/upload";

const props = defineProps({
	title: { type: String, required: true },
	description: { type: String, default: "" },
	fileUrl: { type: String, default: null },
	uploadMethod: { type: String, required: true },
	accept: { type: String, default: ".pdf,.jpg,.jpeg,.png,.docx" },
	hint: { type: String, default: "PDF, JPG, PNG, or DOCX - max 5MB." },
	required: { type: Boolean, default: false },
	status: { type: String, default: "Submitted" },
	remark: { type: String, default: null },
});
const emit = defineEmits(["uploaded"]);

const error = ref("");
const fileName = computed(() => props.fileUrl?.split("/").pop() || "");

const statusLabel = computed(() => (props.fileUrl ? props.status : "Not uploaded"));
const statusBadgeClass = computed(() => {
	if (!props.fileUrl) return "bg-gray-100 text-body";
	return (
		{
			Verified: "bg-green-100 text-green-700",
			"Sent Back": "bg-red-100 text-red-700",
			Submitted: "bg-brand-100 text-brand-700",
		}[props.status] || "bg-gray-100 text-body"
	);
});

async function onChange(e) {
	const file = e.target.files[0];
	if (!file) return;
	error.value = "";
	try {
		const res = await upload(props.uploadMethod, file);
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
