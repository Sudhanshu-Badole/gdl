<template>
	<header class="border-b border-gray-200 bg-white">
		<div class="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
			<router-link to="/e-recruitment" class="flex items-center gap-2">
				<span class="text-2xl font-extrabold tracking-tight text-brand-600">GDL</span>
				<span class="hidden text-sm font-semibold text-ink sm:inline">GreenDigital Limited Careers</span>
			</router-link>

			<nav class="flex items-center gap-6">
				<router-link to="/jobs" class="hidden text-sm font-medium text-ink hover:text-brand-600 sm:inline">
					Browse jobs
				</router-link>
				<a :href="userGuideUrl" class="hidden text-sm font-medium text-ink hover:text-brand-600 sm:inline">
					User guide
				</a>
				<template v-if="isGuest">
					<router-link to="/login" class="text-sm font-medium text-ink hover:text-brand-600">
						Sign in
					</router-link>
					<router-link
						to="/register"
						class="rounded-md bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700"
					>
						Register
					</router-link>
				</template>
				<UserMenu
					v-else
					:display-name="boot.full_name || boot.user"
					:email="boot.user"
					:role-label="roleInfo?.label"
					:home-link="roleInfo && { label: 'My dashboard', to: roleInfo.homePath }"
				/>
			</nav>
		</div>
	</header>
</template>

<script setup>
import { computed } from "vue";
import UserMenu from "./shared/UserMenu.vue";
import { getRoleInfo } from "../lib/roles";

// HR-editable Web Page (route: how-to-apply), unchanged - not part of this
// Vue rewrite. Links out to a real page load, not a SPA route.
const userGuideUrl = "/how-to-apply";

const boot = window.boot || {};
const isGuest = computed(() => !boot.user || boot.user === "Guest");
const roleInfo = computed(() => getRoleInfo(boot.roles));
</script>
