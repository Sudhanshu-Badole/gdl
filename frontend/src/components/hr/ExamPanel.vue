<template>
	<div v-if="loaded && !loadError">
		<!-- No test yet -->
		<div v-if="!exam" class="rounded-xl border border-gray-200 p-6">
			<h2 class="mb-1 font-semibold text-ink">Create a test</h2>
			<p class="mb-4 text-sm text-body">
				Candidates already at "Test Invited / Scheduled" will be invited automatically once you publish.
			</p>
			<ExamBuilderForm :job-opening="props.jobOpening" @saved="load" />
		</div>

		<!-- Draft: build questions, then publish -->
		<div v-else-if="exam.status === 'Draft'" class="space-y-6">
			<div class="rounded-xl border border-gray-200 p-6">
				<h2 class="mb-4 font-semibold text-ink">Test details</h2>
				<ExamBuilderForm :job-opening="props.jobOpening" :existing="exam" @saved="load" />
			</div>

			<div class="rounded-xl border border-gray-200 p-6">
				<div class="mb-4 flex items-center justify-between">
					<h2 class="font-semibold text-ink">Questions ({{ questions.length }})</h2>
					<div class="flex gap-2">
						<button
							type="button"
							class="rounded-md border border-gray-200 px-3 py-1.5 text-sm font-medium text-ink hover:bg-gray-50"
							@click="showBankPicker = !showBankPicker"
						>
							{{ showBankPicker ? "Close bank" : "+ Add from bank" }}
						</button>
						<button
							v-if="!addingQuestion"
							type="button"
							class="rounded-md border border-gray-200 px-3 py-1.5 text-sm font-medium text-ink hover:bg-gray-50"
							@click="addingQuestion = true"
						>
							+ Add question
						</button>
					</div>
				</div>

				<QuestionBankPicker v-if="showBankPicker" :exam="exam.name" class="mb-4" @assigned="onQuestionSaved" />

				<ExamQuestionForm
					v-if="addingQuestion"
					:exam="exam.name"
					class="mb-4"
					@saved="onQuestionSaved"
					@cancel="addingQuestion = false"
				/>

				<div class="space-y-3">
					<div v-for="q in questions" :key="q.name">
						<ExamQuestionForm
							v-if="editingQuestion === q.name"
							:exam="exam.name"
							:existing="q"
							@saved="onQuestionSaved"
							@cancel="editingQuestion = null"
						/>
						<div v-else class="flex items-start justify-between gap-3 rounded-md border border-gray-200 p-3">
							<div>
								<p class="text-xs font-semibold uppercase tracking-wide text-body">{{ q.question_type }} · {{ q.marks }} mark(s)</p>
								<p class="mt-1 text-sm text-ink">{{ q.question_text }}</p>
							</div>
							<div class="flex shrink-0 gap-2">
								<button type="button" class="text-xs font-medium text-brand-700 hover:underline" @click="editingQuestion = q.name">
									Edit
								</button>
								<button type="button" class="text-xs font-medium text-red-600 hover:underline" @click="removeQuestion(q.name)">
									Delete
								</button>
							</div>
						</div>
					</div>
				</div>

				<p v-if="questionError" class="mt-4 text-sm text-red-600">{{ questionError }}</p>
				<p v-if="publishError" class="mt-4 text-sm text-red-600">{{ publishError }}</p>
				<button
					type="button"
					:disabled="!questions.length || publishing"
					class="mt-4 rounded-md bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
					@click="publish"
				>
					{{ publishing ? "Publishing..." : "Publish test" }}
				</button>
			</div>
		</div>

		<!-- Published: attempts + grading + advance -->
		<div v-else class="space-y-6">
			<div class="rounded-xl border border-gray-200 p-6">
				<div class="flex items-start justify-between">
					<div>
						<h2 class="font-semibold text-ink">{{ exam.title }}</h2>
						<p class="mt-1 text-sm text-body">
							{{ formatDateTime(exam.opens_on) }} → {{ formatDateTime(exam.closes_on) }}
							· {{ exam.duration_minutes }} min · Pass {{ exam.pass_marks }} / {{ exam.total_marks }}
						</p>
					</div>
					<span class="rounded-full bg-brand-100 px-3 py-1 text-xs font-semibold text-brand-700">Published</span>
				</div>
				<div class="mt-4 flex flex-wrap gap-3">
					<button
						type="button"
						:disabled="publishing"
						class="rounded-md border border-gray-200 px-3 py-2 text-sm font-medium text-ink hover:bg-gray-50 disabled:opacity-60"
						@click="publish"
					>
						{{ publishing ? "Inviting..." : "Invite new candidates" }}
					</button>
					<button
						type="button"
						class="rounded-md border border-gray-200 px-3 py-2 text-sm font-medium text-ink hover:bg-gray-50"
						@click="closeAndMarkAbsent"
					>
						Close & mark absent
					</button>
				</div>
				<p class="mt-2 text-xs text-body">
					"Invite new candidates" re-checks for anyone advanced to "Test Invited / Scheduled" since this test was
					published and invites them - it won't re-invite anyone already invited.
				</p>
				<p v-if="publishMessage" class="mt-2 text-sm text-brand-700">{{ publishMessage }}</p>
				<p v-if="publishError" class="mt-2 text-sm text-red-600">{{ publishError }}</p>
				<p v-if="closeMessage" class="mt-2 text-sm text-brand-700">{{ closeMessage }}</p>
				<p v-if="closeError" class="mt-2 text-sm text-red-600">{{ closeError }}</p>
			</div>

			<div class="rounded-xl border border-gray-200 p-6">
				<h2 class="mb-4 font-semibold text-ink">Attempts</h2>
				<EmptyState v-if="!attempts.length" :icon="UsersIcon" title="No attempts yet" subtitle="Invited candidates will appear here." />
				<div v-else class="overflow-x-auto rounded-xl border border-gray-200">
					<table class="w-full text-left text-sm">
						<thead class="border-b border-gray-200 text-xs uppercase tracking-wide text-body">
							<tr>
								<th class="px-4 py-3 font-medium">Applicant</th>
								<th class="px-4 py-3 font-medium">Status</th>
								<th class="px-4 py-3 font-medium">Attending</th>
								<th class="px-4 py-3 font-medium">Score</th>
								<th class="px-4 py-3 font-medium">Result</th>
								<th class="px-4 py-3 text-right font-medium">Action</th>
							</tr>
						</thead>
						<tbody class="divide-y divide-gray-100">
							<template v-for="a in attempts" :key="a.name">
								<tr>
									<td class="px-4 py-3">
										<p class="font-medium text-ink">{{ a.applicant_name }}</p>
										<p class="text-xs text-body">{{ a.email_id }}</p>
									</td>
									<td class="px-4 py-3">
										<StatusPill :status="a.status" />
									</td>
									<td class="px-4 py-3 text-body">{{ a.attendance_response || "Pending" }}</td>
									<td class="px-4 py-3 text-body">{{ a.total_score ?? "—" }}</td>
									<td class="px-4 py-3 text-body">
										<span v-if="!a.is_fully_graded">Pending</span>
										<span v-else :class="a.is_pass ? 'text-brand-700' : 'text-red-600'">{{ a.is_pass ? "Pass" : "Fail" }}</span>
									</td>
									<td class="px-4 py-3 text-right">
										<button
											v-if="a.has_pending_grading"
											type="button"
											class="text-xs font-medium text-brand-700 hover:underline"
											@click="toggleGrading(a.name)"
										>
											{{ gradingFor === a.name ? "Close" : "Grade" }}
										</button>
									</td>
								</tr>
								<tr v-if="gradingFor === a.name">
									<td colspan="6" class="px-4 pb-4">
										<ExamGradingForm :attempt="a.name" @saved="onGraded" @cancel="gradingFor = null" />
									</td>
								</tr>
							</template>
						</tbody>
					</table>
				</div>
			</div>

			<div class="flex flex-wrap items-center gap-3 rounded-xl border border-gray-200 p-4">
				<span class="text-sm font-medium text-ink">Advance top</span>
				<input v-model.number="cutoff" type="number" min="1" class="w-20 rounded-md border border-gray-200 px-2 py-1.5 text-sm" />
				<span class="text-sm text-body">completed candidate(s) by score to Interview</span>
				<button
					type="button"
					:disabled="advancing"
					class="ml-auto rounded-md bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
					@click="advance"
				>
					Advance
				</button>
			</div>
			<p v-if="advanceMessage" class="text-sm text-brand-700">{{ advanceMessage }}</p>
			<p v-if="advanceError" class="text-sm text-red-600">{{ advanceError }}</p>
		</div>
	</div>

	<p v-else-if="loaded" class="text-sm text-red-600">{{ loadError }}</p>

	<div v-else class="space-y-3">
		<div v-for="i in 3" :key="i" class="h-10 animate-pulse rounded-md bg-gray-100"></div>
	</div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import call from "../../lib/call";
import EmptyState from "../applicant/EmptyState.vue";
import StatusPill from "../applicant/StatusPill.vue";
import UsersIcon from "../icons/UsersIcon.vue";
import ExamBuilderForm from "./ExamBuilderForm.vue";
import ExamQuestionForm from "./ExamQuestionForm.vue";
import ExamGradingForm from "./ExamGradingForm.vue";
import QuestionBankPicker from "./QuestionBankPicker.vue";

const props = defineProps({
	jobOpening: { type: String, required: true },
});

const loaded = ref(false);
const loadError = ref("");
const exam = ref(null);
const questions = ref([]);
const attempts = ref([]);

const addingQuestion = ref(false);
const showBankPicker = ref(false);
const editingQuestion = ref(null);
const questionError = ref("");
const publishing = ref(false);
const publishError = ref("");
const publishMessage = ref("");

const gradingFor = ref(null);
const closeMessage = ref("");
const closeError = ref("");

const cutoff = ref(1);
const advancing = ref(false);
const advanceMessage = ref("");
const advanceError = ref("");

async function load() {
	loadError.value = "";
	try {
		const res = await call("gdl.api.hr_exam.get_exam", { job_opening: props.jobOpening });
		const data = res?.data;
		exam.value = data?.exam || null;
		questions.value = data?.questions || [];
		addingQuestion.value = false;
		editingQuestion.value = null;

		if (exam.value?.status === "Published") {
			await loadQueue();
		}
	} catch (err) {
		loadError.value = err.messages?.[0] || "Could not load test.";
	}
}

async function loadQueue() {
	try {
		const res = await call("gdl.api.hr_exam.get_exam_queue", { job_opening: props.jobOpening });
		attempts.value = res?.data?.attempts || [];
	} catch (err) {
		loadError.value = err.messages?.[0] || "Could not load test attempts.";
	}
}

onMounted(async () => {
	try {
		await load();
	} finally {
		loaded.value = true;
	}
});

function onQuestionSaved() {
	addingQuestion.value = false;
	editingQuestion.value = null;
	load();
}

async function removeQuestion(name) {
	questionError.value = "";
	try {
		await call("gdl.api.hr_exam.delete_question", { name });
		await load();
	} catch (err) {
		questionError.value = err.messages?.[0] || "Could not remove question.";
	}
}

async function publish() {
	publishing.value = true;
	publishError.value = "";
	publishMessage.value = "";
	try {
		const res = await call("gdl.api.hr_exam.publish_exam", { name: exam.value.name });
		if (res.success) {
			publishMessage.value = res.message;
			await load();
		} else {
			publishError.value = res.message || "Could not publish test.";
		}
	} catch (err) {
		publishError.value = err.messages?.[0] || "Could not publish test.";
	} finally {
		publishing.value = false;
	}
}

function toggleGrading(name) {
	gradingFor.value = gradingFor.value === name ? null : name;
}

async function onGraded() {
	gradingFor.value = null;
	await loadQueue();
}

async function closeAndMarkAbsent() {
	closeMessage.value = "";
	closeError.value = "";
	try {
		const res = await call("gdl.api.hr_exam.close_and_mark_absent", { exam: exam.value.name });
		closeMessage.value = res.message;
		await loadQueue();
	} catch (err) {
		closeError.value = err.messages?.[0] || "Could not close test.";
	}
}

async function advance() {
	advancing.value = true;
	advanceMessage.value = "";
	advanceError.value = "";
	try {
		const res = await call("gdl.api.hr_exam.advance_from_exam", { job_opening: props.jobOpening, cutoff: cutoff.value });
		if (res.success) {
			advanceMessage.value = res.message;
			await loadQueue();
		} else {
			advanceError.value = res.message || "Could not advance candidates.";
		}
	} catch (err) {
		advanceError.value = err.messages?.[0] || "Could not advance candidates.";
	} finally {
		advancing.value = false;
	}
}

function formatDateTime(value) {
	if (!value) return "—";
	return new Date(value.replace(" ", "T")).toLocaleString("en-GB", {
		day: "numeric",
		month: "short",
		hour: "2-digit",
		minute: "2-digit",
	});
}
</script>
