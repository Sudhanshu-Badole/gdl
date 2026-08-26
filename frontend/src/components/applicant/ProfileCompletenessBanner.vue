<template>
	<div
		v-if="value < 80"
		class="mb-8 flex items-center justify-between rounded-xl border border-amber-200 bg-amber-50 px-5 py-4"
	>
		<div class="flex items-center gap-2 text-sm text-ink">
			<UsersIcon class="h-4 w-4 shrink-0 text-amber-600" />
			Your profile is {{ value }}% complete. Reach 80% to apply.
		</div>
		<router-link
			to="/complete-profile"
			class="shrink-0 rounded-md border border-gray-200 bg-white px-4 py-2 text-sm font-semibold text-ink hover:bg-gray-50"
		>
			Complete profile
		</router-link>
	</div>
</template>

<script setup>
import UsersIcon from "../icons/UsersIcon.vue";

defineProps({
	value: { type: Number, required: true },
});
</script>
