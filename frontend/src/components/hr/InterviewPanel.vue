<template>
	<div v-if="loaded && !loadError">
		<!-- No interview yet -->
		<div v-if="!interview" class="rounded-xl border border-gray-200 p-6">
			<h2 class="mb-1 font-semibold text-ink">Create an interview</h2>
			<p class="mb-4 text-sm text-body">
				Candidates already at "Interview Invited / Scheduled" will be invited automatically once you publish.
			</p>
			<InterviewBuilderForm :job-opening="props.jobOpening" @saved="load" />
		</div>

		<!-- Draft: build criteria + assign panel, then publish -->
		<div v-else-if="interview.status === 'Draft'" class="space-y-6">
			<div class="rounded-xl border border-gray-200 p-6">
				<h2 class="mb-4 font-semibold text-ink">Interview details</h2>
				<InterviewBuilderForm :job-opening="props.jobOpening" :existing="interview" @saved="load" />
			</div>

			<div v-if="interview.score_entry_mode !== 'Compiled Scores'" class="rounded-xl border border-gray-200 p-6">
				<div class="mb-4 flex items-center justify-between">
					<h2 class="font-semibold text-ink">Scoring criteria ({{ criteria.length }})</h2>
					<div class="flex gap-2">
						<button
							type="button"
							class="rounded-md border border-gray-200 px-3 py-1.5 text-sm font-medium text-ink hover:bg-gray-50"
							@click="loadStandardCriteria"
						>
							Load standard criteria
						</button>
						<button
							v-if="!addingCriterion"
							type="button"
							class="rounded-md border border-gray-200 px-3 py-1.5 text-sm font-medium text-ink hover:bg-gray-50"
							@click="addingCriterion = true"
						>
							+ Add criterion
						</button>
					</div>
				</div>

				<InterviewCriterionForm
					v-if="addingCriterion"
					:interview="interview.name"
					class="mb-4"
					@saved="onCriterionSaved"
					@cancel="addingCriterion = false"
				/>

				<div class="space-y-3">
					<div v-for="c in criteria" :key="c.name">
						<InterviewCriterionForm
							v-if="editingCriterion === c.name"
							:interview="interview.name"
							:existing="c"
							@saved="onCriterionSaved"
							@cancel="editingCriterion = null"
						/>
						<div v-else class="flex items-center justify-between rounded-md border border-gray-200 p-3">
							<div>
								<p class="text-sm text-ink">{{ c.criterion_label }}</p>
								<p v-if="c.description" class="text-xs text-body">{{ c.description }}</p>
								<p class="text-xs text-body">Max {{ c.max_score }}</p>
							</div>
							<div class="flex shrink-0 gap-2">
								<button type="button" class="text-xs font-medium text-brand-700 hover:underline" @click="editingCriterion = c.name">
									Edit
								</button>
								<button type="button" class="text-xs font-medium text-red-600 hover:underline" @click="removeCriterion(c.name)">
									Delete
								</button>
							</div>
						</div>
					</div>
				</div>
				<p v-if="criterionError" class="mt-3 text-sm text-red-600">{{ criterionError }}</p>
			</div>

			<div v-if="interview.score_entry_mode !== 'Compiled Scores'" class="rounded-xl border border-gray-200 p-6">
				<h2 class="mb-4 font-semibold text-ink">Panel members ({{ interview.panel_members.length }})</h2>
				<div class="mb-4 flex flex-wrap items-center gap-2">
					<select v-model="pickedPanelMember" class="rounded-md border border-gray-200 px-3 py-2 text-sm">
						<option value="">Select a panel member...</option>
						<option v-for="u in availablePanelMembers" :key="u.name" :value="u.name">{{ u.full_name }}</option>
					</select>
					<button
						type="button"
						:disabled="!pickedPanelMember"
						class="rounded-md border border-gray-200 px-3 py-1.5 text-sm font-medium text-ink hover:bg-gray-50 disabled:opacity-50"
						@click="assignPanelMember"
					>
						Assign
					</button>
				</div>
				<div v-if="!interview.panel_members.length" class="text-sm text-body">No panel members assigned yet.</div>
				<div v-else class="space-y-2">
					<div
						v-for="row in interview.panel_members"
						:key="row.user"
						class="flex items-center justify-between rounded-md border border-gray-200 px-3 py-2 text-sm"
					>
						<span class="text-ink">{{ panelMemberLabel(row.user) }}</span>
						<button type="button" class="text-xs font-medium text-red-600 hover:underline" @click="removePanelMember(row.user)">
							Remove
						</button>
					</div>
				</div>
				<p v-if="panelError" class="mt-3 text-sm text-red-600">{{ panelError }}</p>
			</div>

			<div>
				<p v-if="publishError" class="mb-3 text-sm text-red-600">{{ publishError }}</p>
				<button
					type="button"
					:disabled="!canPublish || publishing"
					class="rounded-md bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
					@click="publish"
				>
					{{ publishing ? "Publishing..." : "Publish interview" }}
				</button>
			</div>
		</div>

		<!-- Published: sessions + completion + unlock -->
		<div v-else class="space-y-6">
			<div class="rounded-xl border border-gray-200 p-6">
				<div class="flex items-start justify-between">
					<div>
						<h2 class="font-semibold text-ink">{{ interview.title }}</h2>
						<p class="mt-1 text-sm text-body">
							{{ formatDateTime(interview.scheduled_on) }}
							<template v-if="interview.venue_or_link"> &middot; {{ interview.venue_or_link }}</template>
						</p>
					</div>
					<span class="rounded-full bg-brand-100 px-3 py-1 text-xs font-semibold text-brand-700">Published</span>
				</div>
				<button
					type="button"
					:disabled="publishing"
					class="mt-4 rounded-md border border-gray-200 px-3 py-2 text-sm font-medium text-ink hover:bg-gray-50 disabled:opacity-60"
					@click="publish"
				>
					{{ publishing ? "Inviting..." : "Invite new candidates" }}
				</button>
				<p class="mt-2 text-xs text-body">
					Re-checks for anyone advanced to "Interview Invited / Scheduled" since this interview was published and
					invites them - it won't re-invite anyone already invited.
				</p>
				<p v-if="publishMessage" class="mt-2 text-sm text-brand-700">{{ publishMessage }}</p>
				<p v-if="publishError" class="mt-2 text-sm text-red-600">{{ publishError }}</p>
			</div>

			<div class="rounded-xl border border-gray-200 p-6">
				<h2 class="mb-4 font-semibold text-ink">Sessions</h2>
				<EmptyState v-if="!sessions.length" :icon="UsersIcon" title="No sessions yet" subtitle="Invited candidates will appear here." />
				<div v-else class="overflow-x-auto rounded-xl border border-gray-200">
					<table class="w-full text-left text-sm">
						<thead class="border-b border-gray-200 text-xs uppercase tracking-wide text-body">
							<tr>
								<th class="px-4 py-3 font-medium">Applicant</th>
								<th class="px-4 py-3 font-medium">Status</th>
								<th class="px-4 py-3 font-medium">Scheduled</th>
								<th class="px-4 py-3 font-medium">Attending</th>
								<th class="px-4 py-3 font-medium">Score</th>
								<th v-if="interview.score_entry_mode !== 'Compiled Scores'" class="px-4 py-3 font-medium">Feedback</th>
								<th class="px-4 py-3 text-right font-medium">Action</th>
							</tr>
						</thead>
						<tbody class="divide-y divide-gray-100">
							<template v-for="s in sessions" :key="s.name">
								<tr>
									<td class="px-4 py-3">
										<p class="font-medium text-ink">{{ s.applicant_name }}</p>
										<p class="text-xs text-body">{{ s.email_id }}</p>
									</td>
									<td class="px-4 py-3"><StatusPill :status="s.status" /></td>
									<td class="px-4 py-3">
										<input
											type="datetime-local"
											:value="toLocalInput(s.scheduled_on)"
											class="rounded-md border border-gray-200 px-2 py-1 text-xs"
											@change="setSessionSchedule(s.name, $event.target.value)"
										/>
									</td>
									<td class="px-4 py-3 text-body">{{ s.attendance_response || "Pending" }}</td>
									<td class="px-4 py-3 text-body">
										<div v-if="interview.score_entry_mode === 'Compiled Scores' && s.status === 'Invited'" class="flex items-center gap-2">
											<input
												v-model.number="compiledScores[s.name]"
												type="number"
												min="0"
												class="w-20 rounded-md border border-gray-200 px-2 py-1 text-sm"
											/>
											<button type="button" class="text-xs font-medium text-brand-700 hover:underline" @click="saveCompiledScore(s.name)">
												Save score
											</button>
										</div>
										<template v-else>{{ s.status === "Completed" ? (s.total_score ?? "—") : "—" }}</template>
									</td>
									<td v-if="interview.score_entry_mode !== 'Compiled Scores'" class="px-4 py-3 text-body">
										{{ s.submitted_count }} / {{ s.panel_count }} submitted
									</td>
									<td class="px-4 py-3 text-right">
										<div v-if="s.status === 'Invited'" class="flex justify-end gap-3">
											<button
												v-if="interview.score_entry_mode === 'HR Proxy Entry'"
												type="button"
												class="text-xs font-medium text-brand-700 hover:underline"
												@click="toggleProxy(s.name)"
											>
												{{ proxyFor === s.name ? "Close" : "Enter scores" }}
											</button>
											<button type="button" class="text-xs font-medium text-brand-700 hover:underline" @click="complete(s.name)">
												Complete
											</button>
											<button type="button" class="text-xs font-medium text-red-600 hover:underline" @click="markNotAttended(s.name)">
												Not attended
											</button>
										</div>
										<button
											v-else-if="s.status === 'Completed' && isSystemManager"
											type="button"
											class="text-xs font-medium text-body hover:underline"
											@click="toggleUnlock(s.name)"
										>
											{{ unlockFor === s.name ? "Close" : "Unlock" }}
										</button>
									</td>
								</tr>
								<tr v-if="proxyFor === s.name">
									<td :colspan="columnCount" class="px-4 pb-4">
										<div class="rounded-md border border-gray-200 bg-gray-50 p-4">
											<label class="mb-1 block text-sm font-medium text-ink">Panel member</label>
											<select v-model="proxyPanelMember" class="mb-3 w-full rounded-md border border-gray-200 px-3 py-2 text-sm" @change="loadProxyScorecard(s.name)">
												<option value="">Select a panel member...</option>
												<option v-for="row in interview.panel_members" :key="row.user" :value="row.user">{{ panelMemberLabel(row.user) }}</option>
											</select>

											<CandidateDocumentsCard :documents="proxyDocuments" />
											<ExamResultCard :result="proxyExamResult" :checked="true" />

											<div v-if="proxyRows.length" class="mt-3 space-y-3">
												<div v-for="row in proxyRows" :key="row.criterion" class="rounded-md border border-gray-200 bg-white p-3">
													<div class="flex items-center justify-between gap-3">
														<div>
															<span class="text-sm font-medium text-ink">{{ row.criterion_label }}</span>
															<p v-if="row.description" class="mt-0.5 text-xs text-body">{{ row.description }}</p>
														</div>
														<div class="flex items-center gap-2">
															<input
																v-model.number="row.score_given"
																type="number"
																min="0"
																:max="row.max_score"
																class="w-20 rounded-md border border-gray-200 px-2 py-1 text-sm"
															/>
															<span class="text-xs text-body">/ {{ row.max_score }}</span>
														</div>
													</div>
													<textarea
														v-model="row.comments"
														rows="2"
														placeholder="Comments (optional)"
														class="mt-2 w-full rounded-md border border-gray-200 px-3 py-2 text-sm"
													></textarea>
												</div>
												<div class="mt-3">
													<label class="mb-1 block text-sm font-medium text-ink">Overall comments</label>
													<textarea
														v-model="proxyOverallComments"
														rows="2"
														placeholder="Any overall remarks about the candidate (optional)"
														class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm"
													></textarea>
												</div>
												<div class="mt-3 flex gap-2">
													<button
														type="button"
														class="rounded-md bg-brand-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-brand-700"
														@click="saveProxyScorecard(s.name)"
													>
														Save proxy score
													</button>
													<button type="button" class="rounded-md border border-gray-200 px-3 py-1.5 text-sm font-medium text-ink hover:bg-white" @click="toggleProxy(s.name)">
														Cancel
													</button>
												</div>
											</div>
											<p v-if="proxyError" class="mt-2 text-sm text-red-600">{{ proxyError }}</p>
										</div>
									</td>
								</tr>
								<tr v-if="unlockFor === s.name">
									<td :colspan="columnCount" class="px-4 pb-4">
										<div class="rounded-md border border-gray-200 bg-gray-50 p-4">
											<div v-if="unlockLog.length" class="mb-3 space-y-2">
												<p class="text-xs font-semibold uppercase tracking-wide text-body">Previous unlocks</p>
												<div v-for="log in unlockLog" :key="log.unlocked_on" class="rounded-md border border-gray-200 bg-white p-2 text-xs text-body">
													<span class="font-medium text-ink">{{ log.unlocked_by }}</span> on {{ formatDateTime(log.unlocked_on) }} — {{ log.reason }}
												</div>
											</div>
											<label class="mb-1 block text-sm font-medium text-ink">Reason for unlocking</label>
											<textarea v-model="unlockReason" rows="2" class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm"></textarea>
											<div class="mt-2 flex gap-2">
												<button
													type="button"
													class="rounded-md bg-brand-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-brand-700"
													@click="unlock(s.name)"
												>
													Unlock session
												</button>
												<button type="button" class="rounded-md border border-gray-200 px-3 py-1.5 text-sm font-medium text-ink hover:bg-white" @click="unlockFor = null">
													Cancel
												</button>
											</div>
											<p v-if="unlockError" class="mt-2 text-sm text-red-600">{{ unlockError }}</p>
										</div>
									</td>
								</tr>
							</template>
						</tbody>
					</table>
				</div>
				<p v-if="actionError" class="mt-3 text-sm text-red-600">{{ actionError }}</p>
			</div>
		</div>
	</div>

	<p v-else-if="loaded" class="text-sm text-red-600">{{ loadError }}</p>

	<div v-else class="space-y-3">
		<div v-for="i in 3" :key="i" class="h-10 animate-pulse rounded-md bg-gray-100"></div>
	</div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import call from "../../lib/call";
import EmptyState from "../applicant/EmptyState.vue";
import StatusPill from "../applicant/StatusPill.vue";
import UsersIcon from "../icons/UsersIcon.vue";
import InterviewBuilderForm from "./InterviewBuilderForm.vue";
import InterviewCriterionForm from "./InterviewCriterionForm.vue";
import ExamResultCard from "../shared/ExamResultCard.vue";
import CandidateDocumentsCard from "../shared/CandidateDocumentsCard.vue";

const props = defineProps({
	jobOpening: { type: String, required: true },
});

const boot = window.boot || {};
const isSystemManager = computed(() => (boot.roles || []).includes("System Manager"));

const loaded = ref(false);
const loadError = ref("");
const interview = ref(null);
const criteria = ref([]);
const sessions = ref([]);
const panelMembers = ref([]);

const addingCriterion = ref(false);
const editingCriterion = ref(null);
const criterionError = ref("");

const pickedPanelMember = ref("");
const panelError = ref("");

const publishing = ref(false);
const publishError = ref("");
const publishMessage = ref("");

const actionError = ref("");
const unlockFor = ref(null);
const unlockReason = ref("");
const unlockError = ref("");
const unlockLog = ref([]);

const compiledScores = ref({});

const proxyFor = ref(null);
const proxyPanelMember = ref("");
const proxyRows = ref([]);
const proxyOverallComments = ref("");
const proxyError = ref("");
const proxyDocuments = ref(null);
const proxyExamResult = ref(null);

const availablePanelMembers = computed(() => {
	const assigned = new Set((interview.value?.panel_members || []).map((row) => row.user));
	return panelMembers.value.filter((u) => !assigned.has(u.name));
});

const canPublish = computed(() => {
	if (interview.value?.score_entry_mode === "Compiled Scores") return true;
	return criteria.value.length > 0 && interview.value?.panel_members?.length > 0;
});

const columnCount = computed(() => (interview.value?.score_entry_mode === "Compiled Scores" ? 6 : 7));

function panelMemberLabel(user) {
	const found = panelMembers.value.find((u) => u.name === user);
	return found ? found.full_name : user;
}

async function load() {
	loadError.value = "";
	try {
		const [interviewRes, panelRes] = await Promise.all([
			call("gdl.api.hr_interview.get_interview", { job_opening: props.jobOpening }),
			call("gdl.api.hr_interview.list_panel_members"),
		]);
		const data = interviewRes?.data;
		interview.value = data?.interview || null;
		criteria.value = data?.criteria || [];
		panelMembers.value = panelRes?.data || [];
		addingCriterion.value = false;
		editingCriterion.value = null;

		if (interview.value?.status === "Published") {
			await loadQueue();
		}
	} catch (err) {
		loadError.value = err.messages?.[0] || "Could not load interview.";
	}
}

async function loadQueue() {
	try {
		const res = await call("gdl.api.hr_interview.get_interview_queue", { job_opening: props.jobOpening });
		sessions.value = res?.data?.sessions || [];
		const scores = {};
		for (const s of sessions.value) scores[s.name] = s.total_score ?? 0;
		compiledScores.value = scores;
	} catch (err) {
		loadError.value = err.messages?.[0] || "Could not load interview sessions.";
	}
}

onMounted(async () => {
	try {
		await load();
	} finally {
		loaded.value = true;
	}
});

function onCriterionSaved() {
	addingCriterion.value = false;
	editingCriterion.value = null;
	load();
}

async function loadStandardCriteria() {
	criterionError.value = "";
	try {
		await call("gdl.api.hr_interview.add_standard_criteria", { interview: interview.value.name });
		await load();
	} catch (err) {
		criterionError.value = err.messages?.[0] || "Could not load standard criteria.";
	}
}

async function removeCriterion(name) {
	criterionError.value = "";
	try {
		await call("gdl.api.hr_interview.delete_criterion", { name });
		await load();
	} catch (err) {
		criterionError.value = err.messages?.[0] || "Could not remove criterion.";
	}
}

async function assignPanelMember() {
	panelError.value = "";
	try {
		await call("gdl.api.hr_interview.add_panel_member", { interview: interview.value.name, user: pickedPanelMember.value });
		pickedPanelMember.value = "";
		await load();
	} catch (err) {
		panelError.value = err.messages?.[0] || "Could not assign panel member.";
	}
}

async function removePanelMember(user) {
	panelError.value = "";
	try {
		await call("gdl.api.hr_interview.remove_panel_member", { interview: interview.value.name, user });
		await load();
	} catch (err) {
		panelError.value = err.messages?.[0] || "Could not remove panel member.";
	}
}

async function publish() {
	publishing.value = true;
	publishError.value = "";
	publishMessage.value = "";
	try {
		const res = await call("gdl.api.hr_interview.publish_interview", { name: interview.value.name });
		if (res.success) {
			publishMessage.value = res.message;
			await load();
		} else {
			publishError.value = res.message || "Could not publish interview.";
		}
	} catch (err) {
		publishError.value = err.messages?.[0] || "Could not publish interview.";
	} finally {
		publishing.value = false;
	}
}

async function complete(session) {
	actionError.value = "";
	try {
		await call("gdl.api.hr_interview.complete_session", { session });
		await loadQueue();
	} catch (err) {
		actionError.value = err.messages?.[0] || "Could not complete session.";
	}
}

async function markNotAttended(session) {
	actionError.value = "";
	try {
		await call("gdl.api.hr_interview.mark_not_attended", { session });
		await loadQueue();
	} catch (err) {
		actionError.value = err.messages?.[0] || "Could not update session.";
	}
}

async function toggleUnlock(session) {
	unlockFor.value = unlockFor.value === session ? null : session;
	unlockReason.value = "";
	unlockError.value = "";
	unlockLog.value = [];
	if (unlockFor.value) {
		try {
			const res = await call("gdl.api.hr_interview.get_unlock_log", { session });
			unlockLog.value = res?.data || [];
		} catch {
			// non-critical - just skip showing history if this fails
		}
	}
}

async function unlock(session) {
	unlockError.value = "";
	try {
		await call("gdl.api.hr_interview.unlock_session", { session, reason: unlockReason.value });
		unlockFor.value = null;
		await loadQueue();
	} catch (err) {
		unlockError.value = err.messages?.[0] || "Could not unlock session.";
	}
}

async function saveCompiledScore(session) {
	actionError.value = "";
	try {
		await call("gdl.api.hr_interview.set_compiled_score", { session, score: compiledScores.value[session] || 0 });
		await loadQueue();
	} catch (err) {
		actionError.value = err.messages?.[0] || "Could not save score.";
	}
}

function toggleProxy(session) {
	proxyFor.value = proxyFor.value === session ? null : session;
	proxyPanelMember.value = "";
	proxyRows.value = [];
	proxyOverallComments.value = "";
	proxyError.value = "";
	proxyDocuments.value = null;
	proxyExamResult.value = null;
}

async function loadProxyScorecard(session) {
	proxyError.value = "";
	proxyRows.value = [];
	proxyOverallComments.value = "";
	proxyDocuments.value = null;
	proxyExamResult.value = null;
	if (!proxyPanelMember.value) return;
	try {
		const res = await call("gdl.api.hr_interview.get_proxy_scorecard", { session, panel_member: proxyPanelMember.value });
		const data = res?.data;
		const existingByCriterion = {};
		for (const s of data.existing_scores) existingByCriterion[s.criterion] = s;
		proxyRows.value = data.criteria.map((c) => {
			const existing = existingByCriterion[c.name];
			return {
				criterion: c.name,
				criterion_label: c.criterion_label,
				description: c.description,
				max_score: c.max_score,
				score_given: existing?.score_given ?? 0,
				comments: existing?.comments ?? "",
			};
		});
		proxyOverallComments.value = data.existing_overall_comments || "";
		proxyDocuments.value = data.documents || null;
		proxyExamResult.value = data.exam_result || null;
	} catch (err) {
		proxyError.value = err.messages?.[0] || "Could not load this scorecard.";
	}
}

async function saveProxyScorecard(session) {
	proxyError.value = "";
	try {
		const res = await call("gdl.api.hr_interview.save_proxy_scorecard", {
			session,
			panel_member: proxyPanelMember.value,
			criterion_scores: proxyRows.value,
			overall_comments: proxyOverallComments.value,
		});
		if (res.success) {
			proxyFor.value = null;
			await loadQueue();
		} else {
			proxyError.value = res.message || "Could not save score.";
		}
	} catch (err) {
		proxyError.value = err.messages?.[0] || "Could not save score.";
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

function toLocalInput(value) {
	if (!value) return "";
	return value.slice(0, 16).replace(" ", "T");
}

async function setSessionSchedule(session, value) {
	const scheduledOn = value ? `${value.replace("T", " ")}:00` : "";
	try {
		await call("gdl.api.hr_interview.set_session_schedule", { session, scheduled_on: scheduledOn });
		await loadQueue();
	} catch (err) {
		proxyError.value = err.messages?.[0] || "Could not update the interview time.";
	}
}
</script>
