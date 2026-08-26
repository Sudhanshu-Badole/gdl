<template>
	<div>
		<h1 class="text-2xl font-bold text-ink">My applications</h1>

		<div v-if="loaded" class="mt-6">
			<div v-if="applications.length" class="space-y-3">
				<ApplicationCard v-for="app in applications" :key="app.name" :application="app" />
			</div>
			<EmptyState
				v-else
				:icon="SearchIcon"
				title="No applications yet"
				subtitle="Browse open vacancies and submit your first application."
				action-label="Browse jobs"
				action-to="/jobs"
			/>
		</div>

		<div v-else class="mt-6 space-y-3">
			<div v-for="i in 3" :key="i" class="h-16 animate-pulse rounded-xl bg-gray-100"></div>
		</div>
	</div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import call from "@doppio/controllers/call";
import ApplicationCard from "../../components/applicant/ApplicationCard.vue";
import EmptyState from "../../components/applicant/EmptyState.vue";
import SearchIcon from "../../components/icons/SearchIcon.vue";

const applications = ref([]);
const loaded = ref(false);

onMounted(async () => {
	try {
		const res = await call("gdl.api.applicant.get_my_applications");
		applications.value = res?.data || [];
	} finally {
		loaded.value = true;
	}
});
</script>
