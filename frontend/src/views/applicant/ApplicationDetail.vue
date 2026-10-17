<template>
	<div v-if="loaded && detail">
		<h1 class="text-2xl font-bold text-ink">{{ detail.job_opening.job_title }}</h1>
		<p class="text-sm text-body">{{ detail.application.name }}</p>
		<div class="mt-2">
			<StatusPill :status="detail.application.status" />
		</div>

		<div class="mt-6 grid gap-6 lg:grid-cols-3">
			<div class="space-y-6 lg:col-span-2">
				<div class="rounded-xl border border-gray-200 p-6">
					<h2 class="mb-2 font-semibold text-ink">Test</h2>
					<template v-if="detail.exam_schedule">
						<p class="text-sm text-ink">{{ detail.exam_schedule.exam_title }}</p>
						<p class="text-sm text-body">Status: {{ detail.exam_schedule.status }}</p>
						<p v-if="detail.exam_schedule.status !== 'Submitted' && detail.exam_schedule.status !== 'Not Attended'" class="mt-2 text-sm text-body">
							Window: {{ detail.exam_schedule.opens_on }} → {{ detail.exam_schedule.closes_on }}
						</p>
						<router-link
							v-if="detail.exam_schedule.status === 'Invited' || detail.exam_schedule.status === 'In Progress'"
							:to="`/exams/${detail.exam_schedule.attempt}`"
							class="mt-2 inline-block text-sm font-medium text-brand-700 hover:underline"
						>
							{{ detail.exam_schedule.status === "In Progress" ? "Resume test" : "Take test" }}
						</router-link>
						<p v-else-if="detail.exam_schedule.total_score != null" class="mt-2 text-sm">
							Score: {{ detail.exam_schedule.total_score }} ·
							<span :class="detail.exam_schedule.is_pass ? 'text-brand-700' : 'text-red-600'">
								{{ detail.exam_schedule.is_pass ? "Pass" : "Fail" }}
							</span>
						</p>
						<p v-else-if="detail.exam_schedule.status === 'Submitted'" class="mt-2 text-sm text-body">Awaiting results.</p>
						<div v-if="detail.exam_schedule.status === 'Invited' && detail.exam_schedule.attendance_response === 'Pending'" class="mt-3 flex gap-3">
							<button type="button" class="rounded-md bg-brand-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-brand-700" @click="respondToExamAttendance('Confirmed')">
								I'll attend
							</button>
							<button type="button" class="rounded-md border border-gray-200 px-3 py-1.5 text-sm font-medium text-ink hover:bg-gray-50" @click="respondToExamAttendance('Declined')">
								Can't attend
							</button>
						</div>
						<p v-else-if="detail.exam_schedule.attendance_response && detail.exam_schedule.attendance_response !== 'Pending'" class="mt-2 text-xs text-body">
							Attendance: {{ detail.exam_schedule.attendance_response }}
						</p>
						<p v-if="examAttendanceError" class="mt-2 text-sm text-red-600">{{ examAttendanceError }}</p>
					</template>
					<p v-else class="text-sm text-body">Not scheduled yet.</p>
				</div>
				<div class="rounded-xl border border-gray-200 p-6">
					<h2 class="mb-2 font-semibold text-ink">Interview</h2>
					<template v-if="detail.interview_schedule">
						<p class="text-sm text-ink">{{ detail.interview_schedule.interview_title }}</p>
						<p class="text-sm text-body">Status: {{ detail.interview_schedule.status }}</p>
						<p class="mt-2 text-sm text-body">
							When: {{ detail.interview_schedule.scheduled_on }}
							<template v-if="detail.interview_schedule.venue_or_link">
								<br />Where: {{ detail.interview_schedule.venue_or_link }}
							</template>
						</p>
						<a
							v-if="detail.interview_schedule.location_map_link"
							:href="detail.interview_schedule.location_map_link"
							target="_blank"
							class="mt-1 inline-block text-sm font-medium text-brand-700 hover:underline"
						>
							Get directions
						</a>
						<p v-if="detail.interview_schedule.total_score != null" class="mt-2 text-sm text-ink">
							Score: {{ detail.interview_schedule.total_score }}
						</p>
						<div v-if="detail.interview_schedule.status === 'Invited' && detail.interview_schedule.attendance_response === 'Pending'" class="mt-3 flex gap-3">
							<button type="button" class="rounded-md bg-brand-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-brand-700" @click="respondToInterviewAttendance('Confirmed')">
								I'll attend
							</button>
							<button type="button" class="rounded-md border border-gray-200 px-3 py-1.5 text-sm font-medium text-ink hover:bg-gray-50" @click="respondToInterviewAttendance('Declined')">
								Can't attend
							</button>
						</div>
						<p v-else-if="detail.interview_schedule.attendance_response && detail.interview_schedule.attendance_response !== 'Pending'" class="mt-2 text-xs text-body">
							Attendance: {{ detail.interview_schedule.attendance_response }}
						</p>
						<p v-if="interviewAttendanceError" class="mt-2 text-sm text-red-600">{{ interviewAttendanceError }}</p>
					</template>
					<p v-else class="text-sm text-body">Not scheduled yet.</p>
				</div>
				<div class="rounded-xl border border-gray-200 p-6">
					<h2 class="mb-2 font-semibold text-ink">Offer &amp; Appointment</h2>
					<template v-if="detail.offer">
						<p class="text-sm text-ink">{{ detail.offer.designation }}</p>
						<p class="text-sm text-body">Status: {{ detail.offer.status }}</p>
						<p v-if="detail.offer.salary" class="mt-2 whitespace-pre-line text-sm text-body">TFMR: {{ detail.offer.salary }}</p>
						<p v-if="detail.offer.joining_date" class="text-sm text-body">Joining date: {{ detail.offer.joining_date }}</p>
						<p v-if="detail.offer.status === 'Awaiting Response' && detail.offer.response_deadline" class="text-sm text-body">
							Respond by: {{ detail.offer.response_deadline }}
						</p>
						<div v-if="detail.offer.status === 'Awaiting Response'" class="mt-3 flex gap-3">
							<button type="button" class="rounded-md bg-brand-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-brand-700" @click="respondToOffer('Accepted')">
								Accept offer
							</button>
							<button type="button" class="rounded-md border border-gray-200 px-3 py-1.5 text-sm font-medium text-ink hover:bg-gray-50" @click="respondToOffer('Rejected')">
								Decline offer
							</button>
						</div>
						<p v-if="offerError" class="mt-2 text-sm text-red-600">{{ offerError }}</p>
						<a
							v-if="detail.offer.appointment_letter"
							:href="`/api/method/frappe.utils.print_format.download_pdf?doctype=Appointment%20Letter&name=${encodeURIComponent(detail.offer.appointment_letter)}`"
							target="_blank"
							class="mt-3 inline-block text-sm font-medium text-brand-700 hover:underline"
						>
							Download appointment letter
						</a>
					</template>
					<p v-else class="text-sm text-body">No offer issued yet.</p>
				</div>
			</div>

			<div class="space-y-6">
				<div v-if="detail.terms_of_reference" class="rounded-xl border border-gray-200 p-6">
					<h2 class="mb-2 font-semibold text-ink">Terms of Reference</h2>
					<a
						:href="detail.terms_of_reference.file_url"
						target="_blank"
						class="inline-block text-sm font-medium text-brand-700 hover:underline"
					>
						{{ detail.terms_of_reference.filename }}
					</a>
				</div>
				<div class="rounded-xl border border-gray-200 p-6">
					<h2 class="mb-2 font-semibold text-ink">Cover Letter</h2>
					<p class="text-sm text-body">{{ detail.application.cover_letter || "(none provided)" }}</p>
				</div>
				<router-link to="/applications" class="inline-block text-sm font-medium text-brand-700 hover:underline">
					← Back to My Applications
				</router-link>
			</div>
		</div>
	</div>

	<p v-else-if="loaded" class="text-sm text-body">{{ error || "Application not found." }}</p>

	<div v-else class="space-y-4">
		<div class="h-8 w-64 animate-pulse rounded bg-gray-100"></div>
		<div class="h-32 animate-pulse rounded-xl bg-gray-100"></div>
	</div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import call from "../../lib/call";
import StatusPill from "../../components/applicant/StatusPill.vue";

const props = defineProps({
	name: { type: String, required: true },
});

const detail = ref(null);
const loaded = ref(false);
const error = ref("");
const offerError = ref("");
const examAttendanceError = ref("");
const interviewAttendanceError = ref("");

async function load() {
	try {
		const res = await call("gdl.api.applicant.get_application_detail", { name: props.name });
		if (res.success) {
			detail.value = res.data;
		} else {
			error.value = res.message;
		}
	} catch (err) {
		error.value = err.messages?.[0] || "Application not found.";
	} finally {
		loaded.value = true;
	}
}

onMounted(load);

async function respondToOffer(response) {
	offerError.value = "";
	try {
		await call("gdl.api.applicant.respond_to_offer", { job_offer: detail.value.offer.job_offer, response });
		await load();
	} catch (err) {
		offerError.value = err.messages?.[0] || "Could not record your response.";
	}
}

async function respondToExamAttendance(response) {
	examAttendanceError.value = "";
	try {
		await call("gdl.api.applicant.confirm_exam_attendance", { attempt: detail.value.exam_schedule.attempt, response });
		await load();
	} catch (err) {
		examAttendanceError.value = err.messages?.[0] || "Could not record your response.";
	}
}

async function respondToInterviewAttendance(response) {
	interviewAttendanceError.value = "";
	try {
		await call("gdl.api.applicant.confirm_interview_attendance", { session: detail.value.interview_schedule.session, response });
		await load();
	} catch (err) {
		interviewAttendanceError.value = err.messages?.[0] || "Could not record your response.";
	}
}
</script>
