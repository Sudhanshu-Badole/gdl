<template>
	<div class="flex h-full flex-col rounded-xl border border-gray-200 p-6">
		<div class="mb-3 flex flex-wrap gap-2">
			<span v-if="vacancy.gdl_vacancy_category" class="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-ink">
				{{ vacancy.gdl_vacancy_category }}
			</span>
			<span v-if="vacancy.gdl_job_type" class="rounded-full border border-brand-200 px-3 py-1 text-xs font-medium text-brand-700">
				{{ vacancy.gdl_job_type }}
			</span>
		</div>

		<h3 class="mb-2 text-lg font-semibold text-ink">{{ vacancy.job_title }}</h3>

		<div v-if="vacancy.department" class="mb-1 flex items-center gap-2 text-sm text-body">
			<BuildingIcon class="h-4 w-4 shrink-0" />
			{{ vacancy.department }}
		</div>
		<div v-if="label" class="mb-4 flex items-center gap-2 text-sm text-brand-700">
			<ClockIcon class="h-4 w-4 shrink-0" />
			{{ label }}
		</div>

		<router-link
			:to="`/jobs/${vacancy.name}`"
			class="mt-auto block rounded-md bg-brand-600 px-4 py-2.5 text-center text-sm font-semibold text-white hover:bg-brand-700"
		>
			View &amp; apply
		</router-link>
	</div>
</template>

<script setup>
import { computed } from "vue";
import BuildingIcon from "./icons/BuildingIcon.vue";
import ClockIcon from "./icons/ClockIcon.vue";
import { closesLabel } from "../lib/dates";

const props = defineProps({
	vacancy: { type: Object, required: true },
});

const label = computed(() => closesLabel(props.vacancy.closes_on));
</script>
