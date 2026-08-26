<template>
	<a
		v-if="url"
		:href="url"
		target="_blank"
		class="flex items-center justify-between rounded-md border border-gray-200 px-3 py-2 text-sm hover:border-brand-200"
	>
		<span class="text-ink">{{ label }}</span>
		<ExternalLinkIcon class="h-3.5 w-3.5 shrink-0 text-body" />
	</a>
</template>

<script setup>
import ExternalLinkIcon from "../icons/ExternalLinkIcon.vue";

defineProps({
	label: { type: String, required: true },
	url: { type: String, default: null },
});
</script>
