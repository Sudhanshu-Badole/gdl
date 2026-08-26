<template>
	<div class="rounded-xl border border-dashed border-gray-300 p-10 text-center text-sm text-body">
		{{ feature }} isn't available yet — this is planned for a later phase of the HR Portal rollout.
	</div>
</template>

<script setup>
defineProps({
	feature: { type: String, required: true },
});
</script>
