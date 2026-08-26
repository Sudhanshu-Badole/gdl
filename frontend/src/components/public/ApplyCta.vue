<template>
	<div class="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-gray-200 bg-gray-50 px-5 py-4">
		<span class="text-sm font-medium text-ink">Ready to apply for this position?</span>
		<a
			:href="`/apply/new?job_title=${jobOpening}`"
			class="rounded-md bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-700"
		>
			Apply now
		</a>
	</div>
</template>

<script setup>
defineProps({
	jobOpening: { type: String, required: true },
});
</script>
