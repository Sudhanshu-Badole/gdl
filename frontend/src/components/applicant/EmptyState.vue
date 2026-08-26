<template>
	<div class="flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-300 py-16 text-center">
		<div class="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-gray-100 text-body">
			<component :is="icon" class="h-5 w-5" />
		</div>
		<p class="font-semibold text-ink">{{ title }}</p>
		<p class="mt-1 max-w-sm text-sm text-body">{{ subtitle }}</p>
		<router-link
			v-if="actionTo"
			:to="actionTo"
			class="mt-4 rounded-md bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700"
		>
			{{ actionLabel }}
		</router-link>
	</div>
</template>

<script setup>
defineProps({
	icon: { type: [Object, Function], required: true },
	title: { type: String, required: true },
	subtitle: { type: String, default: "" },
	actionLabel: { type: String, default: "" },
	actionTo: { type: String, default: "" },
});
</script>
