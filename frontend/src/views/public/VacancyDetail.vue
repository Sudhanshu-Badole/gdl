<template>
	<div v-if="loaded && opening" class="mx-auto max-w-3xl px-6 py-12">
		<router-link to="/jobs" class="text-sm text-body hover:text-brand-700">← Back to jobs</router-link>

		<div class="mb-3 mt-4 flex flex-wrap gap-2">
			<span v-if="opening.gdl_vacancy_category" class="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-ink">
				{{ opening.gdl_vacancy_category }}
			</span>
			<span v-if="opening.gdl_job_type" class="rounded-full border border-brand-200 px-3 py-1 text-xs font-medium text-brand-700">
				{{ opening.gdl_job_type }}
			</span>
		</div>

		<h1 class="text-3xl font-extrabold text-ink">{{ opening.job_title }}</h1>
		<p class="mt-1 text-sm text-body">Ref: {{ opening.name }}</p>

		<div class="mt-6 flex flex-wrap gap-x-8 gap-y-2 rounded-xl border border-gray-200 p-5">
			<div v-if="opening.department" class="flex items-center gap-2 text-sm text-body">
				<BuildingIcon class="h-4 w-4 shrink-0" />
				{{ opening.department }}
			</div>
			<div class="flex items-center gap-2 text-sm text-body">
				<UsersIcon class="h-4 w-4 shrink-0" />
				{{ opening.gdl_number_of_positions || 1 }} position{{ (opening.gdl_number_of_positions || 1) === 1 ? "" : "s" }}
			</div>
			<div v-if="closesText" class="flex items-center gap-2 text-sm text-body">
				<ClockIcon class="h-4 w-4 shrink-0" />
				{{ closesText }}
			</div>
		</div>

		<div v-if="showCriteria" class="mt-6 rounded-xl border border-gray-200 p-6">
			<h2 class="font-semibold text-ink">Application criteria</h2>
			<p class="mt-1 text-sm text-body">You must meet these requirements to apply. Your profile marks and experience are checked automatically.</p>

			<div v-if="eligibilityTags.length" class="mt-4">
				<div class="mb-2 flex items-center gap-2 text-sm font-medium text-ink">
					<GraduationCapIcon class="h-4 w-4 shrink-0" />
					Eligibility
				</div>
				<div class="grid gap-2 sm:grid-cols-2">
					<EligibilityTag v-for="tag in eligibilityTags" :key="tag.title" :title="tag.title" :description="tag.description" />
				</div>
			</div>

			<div v-if="opening.gdl_required_documents?.length" class="mt-5 border-t border-gray-100 pt-4">
				<div class="mb-2 flex items-center gap-2 text-sm font-medium text-ink">
					<DocCheckIcon class="h-4 w-4 shrink-0" />
					Documents required when applying
				</div>
				<ul class="list-disc space-y-1 pl-5 text-sm text-body">
					<li v-for="doc in opening.gdl_required_documents" :key="doc">{{ doc }}</li>
				</ul>
				<p class="mt-2 text-xs text-body">Total work experience is calculated from all experience periods on your profile.</p>
			</div>

			<ApplyCta :job-opening="opening.name" class="mt-5" />
		</div>

		<div v-if="opening.gdl_eligibility_requirements" class="mt-6">
			<h2 class="mb-2 font-semibold text-ink">Requirements</h2>
			<p class="whitespace-pre-wrap text-sm text-body">{{ opening.gdl_eligibility_requirements }}</p>
		</div>

		<div v-if="opening.description" class="mt-6">
			<h2 class="mb-2 font-semibold text-ink">Description</h2>
			<div class="prose prose-sm max-w-none text-body" v-html="opening.description"></div>
		</div>

		<ApplyCta :job-opening="opening.name" class="mt-6" />
	</div>

	<p v-else-if="loaded" class="mx-auto max-w-3xl px-6 py-12 text-sm text-body">
		This vacancy could not be found - it may have been unpublished.
	</p>

	<div v-else class="mx-auto max-w-3xl space-y-4 px-6 py-12">
		<div class="h-8 w-64 animate-pulse rounded bg-gray-100"></div>
		<div class="h-32 animate-pulse rounded-xl bg-gray-100"></div>
	</div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import call from "../../lib/call";
import BuildingIcon from "../../components/icons/BuildingIcon.vue";
import ClockIcon from "../../components/icons/ClockIcon.vue";
import UsersIcon from "../../components/icons/UsersIcon.vue";
import DocCheckIcon from "../../components/icons/DocCheckIcon.vue";
import GraduationCapIcon from "../../components/icons/GraduationCapIcon.vue";
import EligibilityTag from "../../components/public/EligibilityTag.vue";
import ApplyCta from "../../components/public/ApplyCta.vue";
import { closesLabel } from "../../lib/dates";

const props = defineProps({
	name: { type: String, required: true },
});

const opening = ref(null);
const loaded = ref(false);

const closesText = computed(() => (opening.value ? closesLabel(opening.value.closes_on) : null));

const eligibilityTags = computed(() => {
	if (!opening.value) return [];
	const tags = [];
	if (opening.value.gdl_min_experience_years > 0) {
		tags.push({
			title: "Work experience",
			description: `At least ${opening.value.gdl_min_experience_years} year(s) total`,
		});
	}
	if (opening.value.gdl_degree_required) {
		tags.push({
			title: "Degree",
			description: opening.value.gdl_min_degree_score
				? `Required · Minimum ${opening.value.gdl_min_degree_score}% overall score`
				: "Required",
		});
	}
	if (opening.value.gdl_experienced_vacancy) {
		tags.push({
			title: "Experienced vacancy",
			description: "Work experience with certificate uploaded on profile",
		});
	}
	return tags;
});

const showCriteria = computed(() => eligibilityTags.value.length > 0 || opening.value?.gdl_required_documents?.length > 0);

onMounted(async () => {
	try {
		const res = await call("gdl.api.public.get_vacancy_detail", { name: props.name });
		opening.value = res?.data || null;
	} finally {
		loaded.value = true;
	}
});
</script>
