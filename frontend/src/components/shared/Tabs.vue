<template>
	<div>
		<div class="flex gap-6 border-b border-gray-200 text-sm font-medium">
			<button
				v-for="tab in tabs"
				:key="tab"
				type="button"
				class="border-b-2 px-1 py-3"
				:class="modelValue === tab ? 'border-brand-600 text-brand-700' : 'border-transparent text-body hover:text-ink'"
				@click="$emit('update:modelValue', tab)"
			>
				{{ tab }}
			</button>
		</div>
		<div class="mt-6">
			<slot />
		</div>
	</div>
</template>

<script setup>
defineProps({
	tabs: { type: Array, required: true },
	modelValue: { type: String, required: true },
});
defineEmits(["update:modelValue"]);
</script>
