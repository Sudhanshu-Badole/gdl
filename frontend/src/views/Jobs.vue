<template>
	<div class="mx-auto max-w-7xl px-6 py-16">
		<div class="mb-6">
			<h1 class="text-3xl font-extrabold text-ink">Open positions</h1>
			<p class="mt-1 text-sm text-body">{{ vacancies.length }} vacanc{{ vacancies.length === 1 ? "y" : "ies" }} available</p>
		</div>

		<IntentionNotice class="mb-6" />

		<div class="mb-8 rounded-xl border border-gray-200 p-4">
			<div class="flex flex-wrap items-center gap-3">
				<input
					v-model="searchInput"
					type="text"
					placeholder="Search by title or keyword"
					class="min-w-[220px] flex-1 rounded-md border border-gray-200 px-3 py-2 text-sm focus:border-brand-400 focus:outline-none"
					@keyup.enter="applyFilters"
				/>
				<select v-model="categoryInput" class="rounded-md border border-gray-200 px-3 py-2 text-sm">
					<option value="">All categories</option>
					<option v-for="c in categoryOptions" :key="c" :value="c">{{ c }}</option>
				</select>
				<select v-model="typeInput" class="rounded-md border border-gray-200 px-3 py-2 text-sm">
					<option value="">All types</option>
					<option v-for="t in typeOptions" :key="t" :value="t">{{ t }}</option>
				</select>
				<button
					type="button"
					class="rounded-md bg-brand-600 px-5 py-2 text-sm font-semibold text-white hover:bg-brand-700"
					@click="applyFilters"
				>
					Filter
				</button>
			</div>
			<label class="mt-3 flex items-center gap-2 text-sm text-body">
				<input v-model="includeRecentInput" type="checkbox" @change="applyFilters" />
				Include recently closed or filled positions (last 90 days)
			</label>
		</div>

		<p v-if="loaded && error" class="text-sm text-red-600">{{ error }}</p>
		<p v-else-if="loaded && !vacancies.length" class="text-sm text-body">
			No open vacancies right now - check back soon.
		</p>
		<div v-else class="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
			<VacancyCard v-for="v in vacancies" :key="v.name" :vacancy="v" />
		</div>
	</div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import call from "../lib/call";
import IntentionNotice from "../components/IntentionNotice.vue";
import VacancyCard from "../components/VacancyCard.vue";

const allVacancies = ref([]);
const loaded = ref(false);
const error = ref("");

// Local inputs vs. applied filters - filtering only happens on "Filter"
// click (or Enter in the search box), not live-as-you-type, matching the
// reference design's explicit Filter button.
const searchInput = ref("");
const categoryInput = ref("");
const typeInput = ref("");
const includeRecentInput = ref(false);

const appliedFilters = ref({ search: "", category: "", type: "" });

const categoryOptions = computed(() =>
	[...new Set(allVacancies.value.map((v) => v.gdl_vacancy_category).filter(Boolean))].sort()
);
const typeOptions = computed(() => [...new Set(allVacancies.value.map((v) => v.gdl_job_type).filter(Boolean))].sort());

const vacancies = computed(() => {
	const { search, category, type } = appliedFilters.value;
	return allVacancies.value.filter((v) => {
		if (search && !v.job_title?.toLowerCase().includes(search.toLowerCase())) return false;
		if (category && v.gdl_vacancy_category !== category) return false;
		if (type && v.gdl_job_type !== type) return false;
		return true;
	});
});

async function loadVacancies() {
	error.value = "";
	try {
		const res = await call("gdl.api.public.get_open_vacancies", {
			include_recent: includeRecentInput.value ? 1 : 0,
		});
		allVacancies.value = res?.data || [];
	} catch (err) {
		error.value = err.messages?.[0] || "Could not load vacancies.";
	}
}

function applyFilters() {
	appliedFilters.value = { search: searchInput.value, category: categoryInput.value, type: typeInput.value };
	loadVacancies();
}

onMounted(async () => {
	try {
		await loadVacancies();
	} finally {
		loaded.value = true;
	}
});
</script>
