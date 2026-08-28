<template>
	<div>
		<div class="flex items-start justify-between">
			<div>
				<h1 class="text-2xl font-bold text-ink">HR dashboard</h1>
				<p class="mt-1 text-sm text-body">Recruitment activity and items that need your attention.</p>
			</div>
			<a
				href="/app"
				class="shrink-0 rounded-md border border-gray-200 px-4 py-2 text-sm font-medium text-ink hover:bg-gray-50"
			>
				Go to Desk
			</a>
		</div>

		<template v-if="loaded && stats">
			<section class="mt-8">
				<h2 class="mb-3 text-xs font-semibold uppercase tracking-wide text-body">Overview</h2>
				<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
					<StatCard :icon="BriefcaseIcon" :value="stats.overview.open_vacancies" label="Open vacancies" />
					<StatCard :icon="SendIcon" :value="stats.overview.applications_this_week" label="Applications this week" />
					<StatCard :icon="ClockIcon" :value="stats.overview.upcoming_exams_14d" label="Upcoming exams (14d)" />
					<StatCard :icon="ClockIcon" :value="stats.overview.upcoming_interviews_14d" label="Upcoming interviews (14d)" />
				</div>
			</section>

			<section class="mt-8">
				<h2 class="mb-3 text-xs font-semibold uppercase tracking-wide text-body">Needs action</h2>
				<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
					<StatCard
						:icon="DocCheckIcon"
						:value="stats.needs_action.pending_document_review"
						label="Pending document review"
						:highlight="stats.needs_action.pending_document_review > 0"
					/>
					<StatCard :icon="SendIcon" :value="stats.needs_action.ready_to_publish_exam" label="Ready to publish exam" />
					<StatCard
						:icon="SendIcon"
						:value="stats.needs_action.ready_to_publish_interview"
						label="Ready to publish interview"
					/>
					<StatCard :icon="DocCheckIcon" :value="stats.needs_action.exam_grades_pending" label="Exam grades pending" />
					<StatCard
						:icon="TrophyIcon"
						:value="stats.needs_action.offers_awaiting_response"
						label="Offers awaiting response"
					/>
					<StatCard
						:icon="LetterIcon"
						:value="stats.needs_action.appointment_letters_to_issue"
						label="Appointment letters to issue"
					/>
					<StatCard
						:icon="UsersIcon"
						:value="stats.needs_action.repeat_applicants_this_month"
						label="Repeat applicants this month"
					/>
				</div>
			</section>

			<section class="mt-8 rounded-xl border border-gray-200 p-6">
				<div class="mb-4 flex items-center gap-2 text-ink">
					<ClockIcon class="h-4 w-4 text-amber-600" />
					<h2 class="font-semibold">Vacancies closing soon</h2>
				</div>
				<p v-if="!stats.closing_soon.length" class="text-sm text-body">No vacancies closing in the next few days.</p>
				<div v-else class="divide-y divide-gray-100">
					<div v-for="v in stats.closing_soon" :key="v.name" class="flex items-center justify-between py-3">
						<span class="font-medium text-ink">{{ v.job_title }}</span>
						<span class="text-sm text-body">{{ closingLabel(v.closes_on) }}</span>
					</div>
				</div>
			</section>
		</template>

		<p v-else-if="loaded" class="mt-8 text-sm text-red-600">{{ error }}</p>

		<div v-else class="mt-8 space-y-4">
			<div v-for="i in 4" :key="i" class="h-20 animate-pulse rounded-xl bg-gray-100"></div>
		</div>
	</div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import call from "../../lib/call";
import StatCard from "../../components/hr/StatCard.vue";
import BriefcaseIcon from "../../components/icons/BriefcaseIcon.vue";
import SendIcon from "../../components/icons/SendIcon.vue";
import ClockIcon from "../../components/icons/ClockIcon.vue";
import DocCheckIcon from "../../components/icons/DocCheckIcon.vue";
import TrophyIcon from "../../components/icons/TrophyIcon.vue";
import LetterIcon from "../../components/icons/LetterIcon.vue";
import UsersIcon from "../../components/icons/UsersIcon.vue";

const stats = ref(null);
const loaded = ref(false);
const error = ref("");

onMounted(async () => {
	try {
		const res = await call("gdl.api.hr.get_dashboard_stats");
		stats.value = res?.data || null;
	} catch (err) {
		error.value = err.messages?.[0] || "Could not load dashboard.";
	} finally {
		loaded.value = true;
	}
});

// closes_on is a Date (no time-of-day), so "in N hours" is computed against
// end-of-day (23:59:59) on the closing date - same manual-math approach as
// VacancyCard.vue's closesLabel, no date library.
function closingLabel(closesOn) {
	const target = new Date(`${closesOn}T23:59:59`);
	const now = new Date();
	const diffHours = Math.round((target - now) / 3600000);
	const formatted = new Date(`${closesOn}T00:00:00`).toLocaleDateString("en-GB", {
		day: "numeric",
		month: "short",
		year: "numeric",
	});

	if (diffHours <= 0) return `Closes ${formatted}`;
	if (diffHours < 24) return `Closes ${formatted} (in ${diffHours} hour${diffHours === 1 ? "" : "s"})`;

	const diffDays = Math.round(diffHours / 24);
	if (diffDays === 1) return `Closes ${formatted} (tomorrow)`;
	return `Closes ${formatted} (in ${diffDays} days)`;
}
</script>
