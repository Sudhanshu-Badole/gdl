<template>
	<div v-if="documents" class="mt-4 rounded-xl border border-gray-200 p-4">
		<h2 class="mb-2 text-sm font-semibold text-ink">Candidate documents</h2>
		<div class="flex flex-wrap gap-3 text-sm">
			<a v-if="documents.resume_attachment" :href="documents.resume_attachment" target="_blank" class="font-medium text-brand-700 hover:underline">CV</a>
			<a v-if="documents.gdl_national_id" :href="documents.gdl_national_id" target="_blank" class="font-medium text-brand-700 hover:underline">National ID</a>
			<a v-if="documents.gdl_academic_certificate" :href="documents.gdl_academic_certificate" target="_blank" class="font-medium text-brand-700 hover:underline">Academic Certificate</a>
		</div>
	</div>
</template>

<script setup>
defineProps({
	documents: { type: Object, default: null },
});
</script>
