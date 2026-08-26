<template>
	<div v-if="loaded && detail">
		<router-link to="/HR/Vacancies" class="text-sm text-body hover:text-brand-700">← All vacancies</router-link>

		<div class="mt-3 flex items-start justify-between">
			<div>
				<h1 class="text-2xl font-bold text-ink">{{ detail.opening.job_title }}</h1>
				<p class="mt-1 text-sm text-body">
					{{ detail.opening.name }} · {{ detail.opening.department || "—" }}
					<template v-if="detail.opening.gdl_vacancy_category"> · {{ detail.opening.gdl_vacancy_category }}</template>
				</p>
				<div class="mt-2 flex flex-wrap items-center gap-3 text-sm">
					<span class="rounded-full px-3 py-1 text-xs font-semibold" :class="statusBadgeClass(detail.computed_status)">
						{{ detail.computed_status.toUpperCase() }}
					</span>
					<span class="text-body">{{ detail.positions_filled }}/{{ detail.positions_total }} filled</span>
					<span v-if="detail.opening.closes_on" class="text-body">Closes {{ formatDate(detail.opening.closes_on) }}</span>
				</div>
				<a
					v-if="detail.opening.gdl_terms_of_reference"
					:href="detail.opening.gdl_terms_of_reference"
					target="_blank"
					class="mt-3 inline-flex items-center gap-1 text-sm font-medium text-brand-700 hover:underline"
				>
					Terms of Reference
				</a>
			</div>
			<div class="flex shrink-0 items-center gap-2">
				<a
					:href="`/app/job-opening/${detail.opening.name}`"
					class="rounded-md border border-gray-200 px-3 py-2 text-sm font-medium text-ink hover:bg-gray-50"
				>
					Edit
				</a>
				<button
					v-if="detail.computed_status === 'Published'"
					class="rounded-md border border-brand-200 px-3 py-2 text-sm font-medium text-brand-700 hover:bg-brand-50"
					@click="closeApplications"
				>
					Close applications
				</button>
				<button disabled title="Coming soon" class="rounded-md border border-gray-200 px-3 py-2 text-sm text-body/60">
					Duplicate
				</button>
				<button disabled title="Coming soon" class="rounded-md border border-gray-200 px-3 py-2 text-sm text-body/60">
					Delete
				</button>
			</div>
		</div>

		<div class="mt-6 border-b border-gray-200">
			<nav class="flex gap-6 text-sm font-medium">
				<button
					v-for="tab in tabs"
					:key="tab"
					class="border-b-2 px-1 py-3"
					:class="activeTab === tab ? 'border-brand-600 text-brand-700' : 'border-transparent text-body hover:text-ink'"
					@click="selectTab(tab)"
				>
					{{ tab }}
				</button>
			</nav>
		</div>

		<div class="mt-6">
			<div v-if="activeTab === 'Overview'" class="grid gap-6 lg:grid-cols-2">
				<div class="rounded-xl border border-gray-200 p-6">
					<h2 class="mb-4 font-semibold text-ink">Pipeline funnel</h2>
					<div class="space-y-4">
						<div v-for="stage in pipelineStages" :key="stage.key">
							<div class="mb-1 flex items-center justify-between text-sm">
								<span class="text-ink">{{ stage.label }}</span>
								<span class="font-medium text-ink">{{ detail.pipeline[stage.key] }}</span>
							</div>
							<div class="h-1.5 rounded-full bg-gray-100">
								<div
									class="h-1.5 rounded-full bg-brand-500"
									:style="{ width: `${pipelinePercent(stage.key)}%` }"
								></div>
							</div>
						</div>
					</div>
				</div>
				<div class="rounded-xl border border-gray-200 p-6">
					<h2 class="mb-4 font-semibold text-ink">Totals</h2>
					<div class="text-3xl font-bold text-ink">{{ detail.totals.applications }}</div>
					<div class="text-sm text-body">Total applications</div>
				</div>
				<div class="lg:col-span-2">
					<button
						v-if="detail.computed_status === 'Published'"
						class="rounded-md border border-brand-200 px-3 py-2 text-sm font-medium text-brand-700 hover:bg-brand-50"
						@click="closeApplications"
					>
						Close applications
					</button>
				</div>
			</div>

			<div v-else-if="activeTab === 'Applications'">
				<div v-if="!applicationsLoaded" class="space-y-3">
					<div v-for="i in 4" :key="i" class="h-10 animate-pulse rounded-md bg-gray-100"></div>
				</div>
				<p v-else-if="!applications.length" class="text-sm text-body">No applications yet.</p>
				<div v-else class="overflow-x-auto rounded-xl border border-gray-200">
					<table class="w-full text-left text-sm">
						<thead class="border-b border-gray-200 text-xs uppercase tracking-wide text-body">
							<tr>
								<th class="px-4 py-3 font-medium">Applicant</th>
								<th class="px-4 py-3 font-medium">Email</th>
								<th class="px-4 py-3 font-medium">Status</th>
								<th class="px-4 py-3 font-medium">Applied on</th>
							</tr>
						</thead>
						<tbody class="divide-y divide-gray-100">
							<tr v-for="a in applications" :key="a.name">
								<td class="px-4 py-3 font-medium text-ink">{{ a.applicant_name }}</td>
								<td class="px-4 py-3 text-body">{{ a.email_id }}</td>
								<td class="px-4 py-3 text-body">{{ a.status }}</td>
								<td class="px-4 py-3 text-body">{{ formatDate(a.creation) }}</td>
							</tr>
						</tbody>
					</table>
				</div>
			</div>

			<ComingSoonPanel v-else :feature="activeTab" />
		</div>
	</div>

	<div v-else class="space-y-4">
		<div class="h-6 w-40 animate-pulse rounded bg-gray-100"></div>
		<div class="h-24 animate-pulse rounded-xl bg-gray-100"></div>
	</div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import call from "@doppio/controllers/call";
import ComingSoonPanel from "../../components/hr/ComingSoonPanel.vue";

const props = defineProps({
	name: { type: String, required: true },
});

const tabs = ["Overview", "Applications", "Shortlist", "Exams", "Interviews", "Selection", "Letters"];
const activeTab = ref("Overview");

const pipelineStages = [
	{ key: "submitted_under_review", label: "Submitted / under review" },
	{ key: "shortlisted", label: "Shortlisted" },
	{ key: "exam_stage", label: "Exam stage" },
	{ key: "interview_stage", label: "Interview stage" },
	{ key: "selected", label: "Selected" },
	{ key: "offer_appointed", label: "Offer / appointed" },
];

const detail = ref(null);
const loaded = ref(false);

const applications = ref([]);
const applicationsLoaded = ref(false);

onMounted(async () => {
	try {
		const res = await call("gdl.api.hr.get_vacancy", { name: props.name });
		detail.value = res?.data || null;
	} finally {
		loaded.value = true;
	}
});

function selectTab(tab) {
	activeTab.value = tab;
	if (tab === "Applications" && !applicationsLoaded.value) {
		loadApplications();
	}
}

async function loadApplications() {
	try {
		const res = await call("gdl.api.hr.get_vacancy_applications", { job_opening: props.name });
		applications.value = res?.data || [];
	} finally {
		applicationsLoaded.value = true;
	}
}

async function closeApplications() {
	await call("gdl.api.hr.close_vacancy_applications", { name: props.name });
	const res = await call("gdl.api.hr.get_vacancy", { name: props.name });
	detail.value = res?.data || null;
}

function pipelinePercent(key) {
	const total = detail.value.totals.applications;
	if (!total) return 0;
	return Math.round((detail.value.pipeline[key] / total) * 100);
}

function formatDate(value) {
	if (!value) return "—";
	// Datetime strings come back "YYYY-MM-DD HH:MM:SS" from Frappe - the space
	// separator isn't reliably parsed by every browser's Date constructor.
	return new Date(value.replace(" ", "T")).toLocaleDateString("en-GB", {
		day: "numeric",
		month: "short",
		year: "numeric",
	});
}

function statusBadgeClass(status) {
	return (
		{
			Published: "bg-brand-100 text-brand-700",
			Closed: "bg-gray-200 text-body",
			Filled: "bg-gray-100 text-body",
			Draft: "bg-gray-100 text-body italic",
		}[status] || "bg-gray-100 text-body"
	);
}
</script>
