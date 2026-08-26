<template>
	<div class="relative" ref="root">
		<button
			type="button"
			class="flex h-9 w-9 items-center justify-center rounded-full bg-brand-600 text-sm font-semibold text-white"
			@click="open = !open"
		>
			{{ avatarInitial }}
		</button>

		<div
			v-if="open"
			class="absolute right-0 z-10 mt-2 w-64 rounded-md border border-gray-200 bg-white p-4 text-sm shadow-lg"
		>
			<p class="font-semibold text-ink">{{ displayName }}</p>
			<p class="text-body">{{ email }}</p>
			<p v-if="roleLabel" class="mt-1 text-xs font-medium text-brand-700">{{ roleLabel }}</p>

			<router-link
				v-if="homeLink"
				:to="homeLink.to"
				class="mt-3 block text-brand-700 hover:underline"
				@click="open = false"
			>
				{{ homeLink.label }}
			</router-link>

			<button type="button" class="mt-3 flex items-center gap-1 text-body hover:text-ink" @click="signOut">
				<ArrowRightIcon class="h-3.5 w-3.5" />
				Sign out
			</button>
		</div>
	</div>
</template>

<script setup>
import { ref, computed, inject, onMounted, onUnmounted } from "vue";
import ArrowRightIcon from "../icons/ArrowRightIcon.vue";

const props = defineProps({
	displayName: { type: String, required: true },
	email: { type: String, required: true },
	roleLabel: { type: String, default: "" },
	// { label: "My dashboard", to: "/HR/Dashboard" } | null
	homeLink: { type: Object, default: null },
});

const auth = inject("$auth");
const open = ref(false);
const root = ref(null);

const avatarInitial = computed(() => props.displayName?.[0]?.toUpperCase() || "?");

function onClickOutside(e) {
	if (root.value && !root.value.contains(e.target)) {
		open.value = false;
	}
}

onMounted(() => document.addEventListener("click", onClickOutside));
onUnmounted(() => document.removeEventListener("click", onClickOutside));

async function signOut() {
	await auth.logout();
}
</script>
