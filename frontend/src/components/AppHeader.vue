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
				<button
					v-if="installPrompt"
					type="button"
					class="hidden rounded-md border border-brand-600 px-3 py-1.5 text-sm font-medium text-brand-600 hover:bg-brand-50 sm:inline"
					@click="installApp"
				>
					Install app
				</button>
				<template v-if="isGuest">
					<router-link to="/e-recruitment/login" class="text-sm font-medium text-ink hover:text-brand-600">
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
import { computed, onMounted, onBeforeUnmount, ref } from "vue";
import UserMenu from "./shared/UserMenu.vue";
import { getRoleInfo } from "../lib/roles";

// HR-editable Web Page (route: how-to-apply), unchanged - not part of this
// Vue rewrite. Links out to a real page load, not a SPA route.
const userGuideUrl = "/how-to-apply";

const boot = window.boot || {};
const isGuest = computed(() => !boot.user || boot.user === "Guest");
const roleInfo = computed(() => getRoleInfo(boot.roles));

// "Install app" adds a desktop/home-screen shortcut (PWA). Opening it loads
// "/", which the server/router resolves to the user's role dashboard.
const installPrompt = ref(null);
function onBeforeInstall(e) {
	e.preventDefault();
	installPrompt.value = e;
}
async function installApp() {
	if (!installPrompt.value) return;
	installPrompt.value.prompt();
	await installPrompt.value.userChoice;
	installPrompt.value = null;
}
onMounted(() => window.addEventListener("beforeinstallprompt", onBeforeInstall));
onBeforeUnmount(() => window.removeEventListener("beforeinstallprompt", onBeforeInstall));
</script>

