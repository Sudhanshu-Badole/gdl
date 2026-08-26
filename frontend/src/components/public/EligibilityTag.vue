<template>
	<div class="rounded-lg border border-gray-200 px-4 py-3">
		<div class="text-sm font-semibold text-ink">{{ title }}</div>
		<div class="text-sm text-body">{{ description }}</div>
	</div>
</template>

<script setup>
defineProps({
	title: { type: String, required: true },
	description: { type: String, required: true },
});
</script>
