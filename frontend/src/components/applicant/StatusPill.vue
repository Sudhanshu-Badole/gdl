<template>
	<span class="rounded-full px-3 py-1 text-xs font-semibold" :class="colorClass">{{ status }}</span>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	status: { type: String, required: true },
});

const GREEN_STATUSES = ["Selected", "Offer Accepted", "Appointed"];
const RED_STATUSES = [
	"Not Shortlisted",
	"Rejected",
	"Offer Declined",
	"Exam Not Attended",
	"Interview Not Attended",
];

const colorClass = computed(() => {
	if (GREEN_STATUSES.includes(props.status)) return "bg-brand-100 text-brand-700";
	if (RED_STATUSES.includes(props.status)) return "bg-red-100 text-red-700";
	return "bg-blue-100 text-blue-700";
});
</script>
