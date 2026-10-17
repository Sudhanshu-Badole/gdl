<template>
	<div v-if="loaded">
		<EmptyState
			v-if="!rows.length"
			:icon="UsersIcon"
			title="No candidates here yet"
			subtitle="Candidates appear here once marked Selected in the Selection tab."
		/>

		<div v-else class="space-y-4">
			<div v-for="row in rows" :key="row.job_application" class="rounded-xl border border-gray-200 p-5">
				<div class="flex items-start justify-between gap-4">
					<div>
						<p class="font-medium text-ink">{{ row.applicant_name }}</p>
						<p class="text-xs text-body">{{ row.email_id }}</p>
					</div>
					<StatusPill :status="row.status" />
				</div>

				<!-- No offer yet -->
				<OfferForm v-if="!row.offer" class="mt-4" :job-application="row.job_application" @saved="load" />

				<!-- Offer exists -->
				<div v-else class="mt-4 space-y-3 text-sm">
					<div class="grid gap-2 sm:grid-cols-2">
						<p><span class="text-body">Designation:</span> <span class="text-ink">{{ row.offer.designation }}</span></p>
						<p class="sm:col-span-2"><span class="text-body">TFMR:</span> <span class="whitespace-pre-line text-ink">{{ row.offer.gdl_salary || "—" }}</span></p>
						<p><span class="text-body">Joining date:</span> <span class="text-ink">{{ row.offer.gdl_joining_date ?? "—" }}</span></p>
						<p><span class="text-body">Response deadline:</span> <span class="text-ink">{{ row.offer.gdl_response_deadline ?? "—" }}</span></p>
					</div>
					<div class="flex flex-wrap items-center gap-3">
						<a :href="pdfUrl('Job Offer', row.offer.name)" target="_blank" class="text-xs font-medium text-brand-700 hover:underline">
							Download offer PDF
						</a>
						<template v-if="row.offer.status === 'Awaiting Response'">
							<button type="button" class="text-xs font-medium text-brand-700 hover:underline" @click="respond(row.offer.name, 'Accepted')">
								Record: Accepted
							</button>
							<button type="button" class="text-xs font-medium text-red-600 hover:underline" @click="respond(row.offer.name, 'Rejected')">
								Record: Declined
							</button>
						</template>
					</div>

					<template v-if="row.offer.status === 'Accepted'">
						<button
							v-if="!row.appointment_letter"
							type="button"
							class="rounded-md bg-brand-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-brand-700"
							@click="generateLetter(row.offer.name)"
						>
							Generate appointment letter
						</button>
						<a
							v-else
							:href="pdfUrl('Appointment Letter', row.appointment_letter)"
							target="_blank"
							class="text-xs font-medium text-brand-700 hover:underline"
						>
							Download appointment letter PDF
						</a>
					</template>
				</div>
			</div>
		</div>
		<p v-if="actionError" class="mt-3 text-sm text-red-600">{{ actionError }}</p>
	</div>

	<div v-else class="space-y-3">
		<div v-for="i in 3" :key="i" class="h-16 animate-pulse rounded-xl bg-gray-100"></div>
	</div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import call from "../../lib/call";
import EmptyState from "../applicant/EmptyState.vue";
import StatusPill from "../applicant/StatusPill.vue";
import UsersIcon from "../icons/UsersIcon.vue";
import OfferForm from "./OfferForm.vue";

const props = defineProps({
	jobOpening: { type: String, required: true },
});

const rows = ref([]);
const loaded = ref(false);
const actionError = ref("");

async function load() {
	const res = await call("gdl.api.hr_offer.get_letters_queue", { job_opening: props.jobOpening });
	rows.value = res?.data || [];
}

onMounted(async () => {
	try {
		await load();
	} finally {
		loaded.value = true;
	}
});

function pdfUrl(doctype, name) {
	return `/api/method/frappe.utils.print_format.download_pdf?doctype=${encodeURIComponent(doctype)}&name=${encodeURIComponent(name)}`;
}

async function respond(jobOffer, response) {
	actionError.value = "";
	try {
		await call("gdl.api.hr_offer.record_offer_response", { job_offer: jobOffer, response });
		await load();
	} catch (err) {
		actionError.value = err.messages?.[0] || "Could not record response.";
	}
}

async function generateLetter(jobOffer) {
	actionError.value = "";
	try {
		await call("gdl.api.hr_offer.generate_appointment_letter", { job_offer: jobOffer });
		await load();
	} catch (err) {
		actionError.value = err.messages?.[0] || "Could not generate appointment letter.";
	}
}
</script>
