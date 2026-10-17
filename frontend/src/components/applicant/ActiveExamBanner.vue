<template>
	<div class="mb-8 flex items-center justify-between rounded-xl border border-brand-200 bg-brand-50 px-5 py-4">
		<div class="text-sm text-ink">
			<span class="font-semibold">Test open: {{ exam.exam_title }}</span>
			<span class="text-body"> — {{ exam.job_title }}. Closes {{ formatDateTime(exam.closes_on) }}.</span>
		</div>
		<router-link
			:to="`/exams/${exam.attempt}`"
			class="shrink-0 rounded-md bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700"
		>
			Take Test Now
		</router-link>
	</div>
</template>

<script setup>
defineProps({
	exam: { type: Object, required: true },
});

function formatDateTime(value) {
	if (!value) return "—";
	return new Date(value.replace(" ", "T")).toLocaleString("en-GB", {
		day: "numeric",
		month: "short",
		hour: "2-digit",
		minute: "2-digit",
	});
}
</script>
