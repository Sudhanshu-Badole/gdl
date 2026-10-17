<template>
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
		<div class="max-w-md rounded-xl bg-white p-6 text-center">
			<h2 class="text-lg font-bold text-ink">You left the test window</h2>
			<p class="mt-2 text-sm text-body">
				Leaving full-screen or switching tabs/windows during a test is logged.
				<template v-if="maxViolations">
					This attempt has {{ violationCount }} of {{ maxViolations }} recorded - it will be submitted automatically if this keeps
					happening.
				</template>
			</p>
			<button
				type="button"
				class="mt-4 rounded-md bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-700"
				@click="$emit('resume')"
			>
				Return to full screen and continue
			</button>
		</div>
	</div>
</template>

<script setup>
defineProps({
	violationCount: { type: Number, default: 0 },
	maxViolations: { type: Number, default: 0 },
});
defineEmits(["resume"]);
</script>
