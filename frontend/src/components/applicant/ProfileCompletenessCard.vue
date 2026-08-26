<template>
	<div class="rounded-xl border border-gray-200 p-6">
		<div class="mb-1 flex items-center justify-between">
			<h2 class="font-semibold text-ink">Profile completeness</h2>
			<span class="font-semibold" :class="completeness >= 80 ? 'text-brand-700' : 'text-amber-600'">{{ completeness }}%</span>
		</div>
		<div class="mb-3 h-2 rounded-full bg-gray-100">
			<div
				class="h-2 rounded-full"
				:class="completeness >= 80 ? 'bg-brand-600' : 'bg-amber-500'"
				:style="{ width: `${completeness}%` }"
			></div>
		</div>
		<p class="mb-4 text-xs text-body">
			Reach at least 80% to apply. Complete the items below - each section adds to your score.
		</p>

		<p class="mb-2 text-xs font-semibold uppercase tracking-wide text-body">What to complete</p>
		<div class="mb-4 space-y-2">
			<button
				v-for="section in incomplete"
				:key="section.key"
				type="button"
				class="flex w-full items-center justify-between rounded-md border border-gray-200 px-3 py-2 text-left text-sm hover:border-brand-200"
				@click="$emit('continue', section.anchor)"
			>
				<span>
					<span class="font-medium text-ink">{{ section.label }}</span>
					<span class="ml-1 text-xs text-body">({{ section.weight }}%)</span>
				</span>
				<ArrowRightIcon class="h-3.5 w-3.5 shrink-0 text-body" />
			</button>
			<p v-if="!incomplete.length" class="text-sm text-brand-700">All sections complete.</p>
		</div>

		<button
			v-if="incomplete.length"
			type="button"
			class="w-full rounded-md bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700"
			@click="$emit('continue', incomplete[0].anchor)"
		>
			Continue: {{ incomplete[0].label }}
		</button>
	</div>
</template>

<script setup>
import { computed } from "vue";
import ArrowRightIcon from "../icons/ArrowRightIcon.vue";
import { CHECKLIST_SECTIONS } from "../../lib/completeness";

const props = defineProps({
	completeness: { type: Number, required: true },
	applicant: { type: Object, required: true },
});

defineEmits(["continue"]);

const incomplete = computed(() => CHECKLIST_SECTIONS.filter((section) => !section.isDone(props.applicant)));
</script>
