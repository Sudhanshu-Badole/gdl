<template>
	<div class="rounded-md border border-gray-200 bg-gray-50 p-4">
		<div v-if="!loaded" class="space-y-2">
			<div v-for="i in 3" :key="i" class="h-10 animate-pulse rounded-md bg-gray-100"></div>
		</div>

		<p v-else-if="error" class="text-sm text-red-600">{{ error }}</p>

		<template v-else>
			<div class="space-y-2">
				<div
					v-for="row in [...documents, ...otherDocuments]"
					:key="row.key"
					class="flex flex-wrap items-center justify-between gap-2 rounded-md border border-gray-200 bg-white px-3 py-2"
				>
					<div class="min-w-0">
						<p class="text-sm font-medium text-ink">
							{{ row.label }}
							<span v-if="row.mandatory" class="text-red-500">*</span>
						</p>
						<p v-if="row.status === 'Sent Back' && row.remark" class="mt-0.5 text-xs text-red-600">
							Sent back: {{ row.remark }}
						</p>
					</div>
					<div class="flex shrink-0 items-center gap-2">
						<a
							v-if="row.file_url"
							:href="row.file_url"
							target="_blank"
							class="text-sm font-medium text-brand-700 hover:underline"
						>
							View
						</a>
						<span v-else class="text-sm text-body">Not uploaded</span>
						<span class="rounded-full px-2 py-0.5 text-xs font-semibold" :class="statusBadgeClass(row.status)">
							{{ row.status }}
						</span>
						<template v-if="row.file_url && row.status !== 'Verified'">
							<button
								class="rounded-md border border-brand-200 px-2 py-1 text-xs font-medium text-brand-700 hover:bg-brand-50 disabled:opacity-50"
								:disabled="actionInFlight === row.key"
								@click="setStatus(row, 'Verified')"
							>
								Verify
							</button>
						</template>
						<template v-if="row.file_url && row.status !== 'Sent Back'">
							<button
								class="rounded-md border border-gray-200 px-2 py-1 text-xs font-medium text-ink hover:bg-gray-50 disabled:opacity-50"
								:disabled="actionInFlight === row.key"
								@click="sendBackTarget = sendBackTarget === row.key ? '' : row.key"
							>
								Send back
							</button>
						</template>
					</div>
					<div v-if="sendBackTarget === row.key" class="w-full">
						<textarea
							v-model="sendBackRemark"
							rows="2"
							placeholder="Tell the applicant what needs to be fixed…"
							class="mt-1 w-full rounded-md border border-gray-200 px-2 py-1.5 text-sm focus:border-brand-400 focus:outline-none"
						></textarea>
						<div class="mt-1 flex gap-2">
							<button
								class="rounded-md bg-brand-600 px-2 py-1 text-xs font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
								:disabled="actionInFlight === row.key || !sendBackRemark.trim()"
								@click="setStatus(row, 'Sent Back')"
							>
								Confirm send back
							</button>
							<button
								class="rounded-md border border-gray-200 px-2 py-1 text-xs font-medium text-ink hover:bg-white"
								@click="sendBackTarget = ''"
							>
								Cancel
							</button>
						</div>
					</div>
				</div>
			</div>
			<p v-if="actionError" class="mt-2 text-sm text-red-600">{{ actionError }}</p>
		</template>
	</div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import call from "../../lib/call";

const props = defineProps({
	jobApplicant: { type: String, required: true },
});

const loaded = ref(false);
const error = ref("");
const documents = ref([]);
const otherDocuments = ref([]);
const actionInFlight = ref("");
const actionError = ref("");
const sendBackTarget = ref("");
const sendBackRemark = ref("");

async function load() {
	loaded.value = false;
	error.value = "";
	try {
		const res = await call("gdl.api.hr.get_applicant_documents", { job_applicant: props.jobApplicant });
		documents.value = res?.data?.documents || [];
		otherDocuments.value = res?.data?.other_documents || [];
	} catch (err) {
		error.value = err.messages?.[0] || "Could not load documents.";
	} finally {
		loaded.value = true;
	}
}

onMounted(load);

async function setStatus(row, status) {
	actionInFlight.value = row.key;
	actionError.value = "";
	try {
		await call("gdl.api.hr.set_document_verification_status", {
			job_applicant: props.jobApplicant,
			document_key: row.key,
			status,
			remark: status === "Sent Back" ? sendBackRemark.value.trim() : undefined,
		});
		sendBackTarget.value = "";
		sendBackRemark.value = "";
		await load();
	} catch (err) {
		actionError.value = err.messages?.[0] || "Could not update this document.";
	} finally {
		actionInFlight.value = "";
	}
}

function statusBadgeClass(status) {
	return (
		{
			Verified: "bg-green-100 text-green-700",
			"Sent Back": "bg-red-100 text-red-700",
			Submitted: "bg-gray-100 text-body",
		}[status] || "bg-gray-100 text-body"
	);
}
</script>
