<template>
	<div v-if="loaded && data" class="mx-auto max-w-2xl">
		<!-- Not (or no longer) in progress -->
		<div v-if="data.attempt.status === 'Submitted'" class="rounded-xl border border-gray-200 p-6 text-center">
			<h1 class="text-xl font-bold text-ink">Exam already submitted</h1>
			<p class="mt-2 text-sm text-body">You've already submitted this exam. Track its result from your applications.</p>
			<router-link to="/applications" class="mt-4 inline-block text-sm font-medium text-brand-700 hover:underline">
				Go to My Applications
			</router-link>
		</div>

		<div v-else-if="data.attempt.status === 'Not Attended'" class="rounded-xl border border-gray-200 p-6 text-center">
			<h1 class="text-xl font-bold text-ink">Exam window closed</h1>
			<p class="mt-2 text-sm text-body">This exam's window closed before it was submitted.</p>
			<router-link to="/applications" class="mt-4 inline-block text-sm font-medium text-brand-700 hover:underline">
				Go to My Applications
			</router-link>
		</div>

		<!-- Instructions gate -->
		<div v-else-if="data.attempt.status === 'Invited'" class="rounded-xl border border-gray-200 p-6">
			<h1 class="text-2xl font-bold text-ink">{{ data.exam.title }}</h1>
			<p class="mt-1 text-sm text-body">{{ data.job_title }}</p>
			<p v-if="data.exam.instructions" class="mt-4 whitespace-pre-wrap text-sm text-ink">{{ data.exam.instructions }}</p>
			<dl class="mt-4 space-y-1 text-sm">
				<div class="flex justify-between"><dt class="text-body">Duration</dt><dd class="text-ink">{{ data.exam.duration_minutes }} minutes</dd></div>
				<div class="flex justify-between"><dt class="text-body">Questions</dt><dd class="text-ink">{{ data.questions.length }}</dd></div>
				<div class="flex justify-between"><dt class="text-body">Closes</dt><dd class="text-ink">{{ formatDateTime(data.exam.closes_on) }}</dd></div>
			</dl>
			<p class="mt-4 text-xs text-body">
				Once started, the timer cannot be paused. Your answers are saved automatically as you go.
			</p>
			<p v-if="startError" class="mt-3 text-sm text-red-600">{{ startError }}</p>
			<button
				type="button"
				:disabled="starting"
				class="mt-4 rounded-md bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
				@click="start"
			>
				{{ starting ? "Starting..." : "Start exam" }}
			</button>
		</div>

		<!-- In progress -->
		<div v-else>
			<div class="sticky top-0 z-10 mb-6 flex items-center justify-between rounded-xl border border-gray-200 bg-white/95 px-5 py-3 backdrop-blur">
				<div>
					<h1 class="font-semibold text-ink">{{ data.exam.title }}</h1>
					<p class="text-xs text-body">{{ data.job_title }}</p>
				</div>
				<div class="text-right">
					<p class="text-xs uppercase tracking-wide text-body">Time remaining</p>
					<p class="font-mono text-lg font-semibold" :class="remainingSeconds < 60 ? 'text-red-600' : 'text-ink'">
						{{ formattedRemaining }}
					</p>
				</div>
			</div>

			<div class="space-y-4">
				<div v-for="(q, i) in data.questions" :key="q.name" class="rounded-xl border border-gray-200 p-5">
					<p class="mb-3 text-sm font-medium text-ink">{{ i + 1 }}. {{ q.question_text }} <span class="text-xs text-body">({{ q.marks }} mark{{ q.marks === 1 ? "" : "s" }})</span></p>

					<div v-if="q.question_type === 'Short Answer'">
						<textarea
							v-model="answers[q.name].short_answer_text"
							rows="3"
							class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm"
							@input="scheduleSave(q.name)"
						></textarea>
					</div>
					<div v-else class="space-y-2">
						<label
							v-for="opt in optionsFor(q)"
							:key="opt.value"
							class="flex cursor-pointer items-center gap-2 rounded-md border border-gray-200 px-3 py-2 text-sm hover:bg-gray-50"
						>
							<input
								type="radio"
								:name="q.name"
								:value="opt.value"
								v-model="answers[q.name].selected_option"
								@change="saveNow(q.name)"
							/>
							{{ opt.label }}
						</label>
					</div>
				</div>
			</div>

			<p v-if="submitError" class="mt-4 text-sm text-red-600">{{ submitError }}</p>
			<button
				type="button"
				:disabled="submitting"
				class="mt-6 rounded-md bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
				@click="submit"
			>
				{{ submitting ? "Submitting..." : "Submit exam" }}
			</button>
		</div>
	</div>

	<div v-else-if="loaded" class="mx-auto max-w-2xl rounded-xl border border-gray-200 p-6 text-sm text-red-600">
		{{ loadError }}
	</div>

	<div v-else class="mx-auto max-w-2xl space-y-4">
		<div class="h-8 w-64 animate-pulse rounded bg-gray-100"></div>
		<div class="h-40 animate-pulse rounded-xl bg-gray-100"></div>
	</div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from "vue";
import { useRoute, useRouter, onBeforeRouteLeave } from "vue-router";
import call from "../../lib/call";

const route = useRoute();
const router = useRouter();

const loaded = ref(false);
const loadError = ref("");
const data = ref(null);
const answers = ref({});

const starting = ref(false);
const startError = ref("");
const submitting = ref(false);
const submitError = ref("");

const remainingSeconds = ref(0);
let timerHandle = null;
const saveTimers = {};

function optionsFor(q) {
	if (q.question_type === "True or False") {
		return [
			{ value: "A", label: "True" },
			{ value: "B", label: "False" },
		];
	}
	return ["a", "b", "c", "d"]
		.map((letter, i) => ({ value: String.fromCharCode(65 + i), label: q[`option_${letter}`] }))
		.filter((opt) => opt.label);
}

function seedAnswers() {
	const seeded = {};
	for (const q of data.value.questions) {
		seeded[q.name] = {
			selected_option: q.answer?.selected_option || "",
			short_answer_text: q.answer?.short_answer_text || "",
		};
	}
	answers.value = seeded;
}

async function load() {
	try {
		const res = await call("gdl.api.applicant.get_exam_attempt", { name: route.params.name });
		if (res.success) {
			data.value = res.data;
			seedAnswers();
			if (data.value.attempt.status === "In Progress") {
				startTimer();
			}
		} else {
			loadError.value = res.message || "This exam is not available.";
		}
	} catch (err) {
		loadError.value = err.messages?.[0] || "This exam is not available.";
	} finally {
		loaded.value = true;
	}
}

function isInProgress() {
	return data.value?.attempt.status === "In Progress";
}

function handleBeforeUnload(e) {
	if (!isInProgress()) return;
	e.preventDefault();
	e.returnValue = "";
}

onMounted(() => {
	load();
	window.addEventListener("beforeunload", handleBeforeUnload);
});
onBeforeUnmount(() => {
	if (timerHandle) clearInterval(timerHandle);
	window.removeEventListener("beforeunload", handleBeforeUnload);
});
onBeforeRouteLeave(() => {
	if (!isInProgress()) return true;
	return window.confirm("Your exam is still in progress. Are you sure you want to leave?");
});

async function start() {
	starting.value = true;
	startError.value = "";
	try {
		const res = await call("gdl.api.applicant.start_exam_attempt", { name: route.params.name });
		if (res.success) {
			await load();
		} else {
			startError.value = res.message || "Could not start the exam.";
		}
	} catch (err) {
		startError.value = err.messages?.[0] || "Could not start the exam.";
	} finally {
		starting.value = false;
	}
}

function startTimer() {
	const opensClose = new Date(data.value.exam.closes_on.replace(" ", "T")).getTime();
	const startedAt = new Date((data.value.attempt.started_on || data.value.exam.opens_on).replace(" ", "T")).getTime();
	const durationEnd = startedAt + data.value.exam.duration_minutes * 60 * 1000;
	const deadline = Math.min(opensClose, durationEnd);

	const tick = () => {
		remainingSeconds.value = Math.max(0, Math.round((deadline - Date.now()) / 1000));
		if (remainingSeconds.value <= 0) {
			clearInterval(timerHandle);
			submit();
		}
	};
	tick();
	timerHandle = setInterval(tick, 1000);
}

const formattedRemaining = computed(() => {
	const total = remainingSeconds.value;
	const h = Math.floor(total / 3600);
	const m = Math.floor((total % 3600) / 60);
	const s = total % 60;
	const pad = (n) => String(n).padStart(2, "0");
	return h > 0 ? `${h}:${pad(m)}:${pad(s)}` : `${pad(m)}:${pad(s)}`;
});

function scheduleSave(questionName) {
	clearTimeout(saveTimers[questionName]);
	saveTimers[questionName] = setTimeout(() => saveNow(questionName), 600);
}

async function saveNow(questionName) {
	const answer = answers.value[questionName];
	try {
		await call("gdl.api.applicant.save_exam_answer", {
			attempt: route.params.name,
			question: questionName,
			selected_option: answer.selected_option || null,
			short_answer_text: answer.short_answer_text || null,
		});
	} catch {
		// Autosave is best-effort - the final submit still works off whatever
		// was last saved; a transient failure here shouldn't interrupt typing.
	}
}

async function submit() {
	if (submitting.value) return;
	submitting.value = true;
	submitError.value = "";
	if (timerHandle) clearInterval(timerHandle);
	try {
		const res = await call("gdl.api.applicant.submit_exam_attempt", { name: route.params.name });
		if (res.success) {
			router.push("/applications");
		} else {
			submitError.value = res.message || "Could not submit the exam.";
		}
	} catch (err) {
		submitError.value = err.messages?.[0] || "Could not submit the exam.";
	} finally {
		submitting.value = false;
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
