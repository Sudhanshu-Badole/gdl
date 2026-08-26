<template>
	<router-link
		:to="`/applications/${application.name}`"
		class="flex items-center justify-between rounded-xl border border-gray-200 p-4 hover:border-brand-200"
	>
		<div>
			<p class="font-semibold text-ink">{{ application.job_title || application.job_opening }}</p>
			<p class="text-xs text-body">{{ application.name }} · {{ formatDate(application.creation) }}</p>
		</div>
		<StatusPill :status="application.status" />
	</router-link>
</template>

<script setup>
import StatusPill from "./StatusPill.vue";

defineProps({
	application: { type: Object, required: true },
});

function formatDate(value) {
	if (!value) return "";
	return new Date(value.replace(" ", "T")).toLocaleDateString("en-GB", {
		day: "numeric",
		month: "short",
		year: "numeric",
	});
}
</script>
