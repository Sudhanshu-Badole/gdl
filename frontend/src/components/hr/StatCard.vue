<template>
	<div
		class="flex items-center gap-4 rounded-xl border p-5"
		:class="highlight ? 'border-amber-200 bg-amber-50' : 'border-gray-200'"
	>
		<div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-brand-50 text-brand-700">
			<component :is="icon" class="h-5 w-5" />
		</div>
		<div>
			<div class="text-2xl font-bold text-ink">{{ value }}</div>
			<div class="text-sm text-body">{{ label }}</div>
		</div>
	</div>
</template>

<script setup>
defineProps({
	icon: { type: [Object, Function], required: true },
	value: { type: [Number, String], required: true },
	label: { type: String, required: true },
	highlight: { type: Boolean, default: false },
});
</script>
