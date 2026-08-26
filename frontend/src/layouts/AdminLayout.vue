<template>
	<div class="flex min-h-screen bg-white">
		<aside class="flex w-60 shrink-0 flex-col border-r border-gray-200">
			<div class="flex items-center gap-2 border-b border-gray-200 px-5 py-4">
				<span class="text-xl font-extrabold tracking-tight text-brand-600">G•DL</span>
				<span class="text-sm font-semibold text-ink">GreenDigital Limited HR</span>
			</div>
			<nav class="flex-1 space-y-1 p-3">
				<router-link
					v-for="item in navItems"
					:key="item.to"
					:to="item.to"
					class="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium"
					:class="
						isActive(item.to)
							? 'bg-brand-50 text-brand-700'
							: 'text-body hover:bg-gray-50 hover:text-ink'
					"
				>
					<component :is="item.icon" class="h-4 w-4 shrink-0" />
					{{ item.label }}
				</router-link>
			</nav>
		</aside>

		<div class="flex flex-1 flex-col">
			<header class="flex items-center justify-end border-b border-gray-200 px-6 py-4">
				<UserMenu :display-name="boot.full_name || boot.user" :email="boot.user" role-label="HR" />
			</header>
			<main class="flex-1 bg-white px-8 py-8">
				<router-view />
			</main>
		</div>
	</div>
</template>

<script setup>
import { useRoute } from "vue-router";
import DashboardIcon from "../components/icons/DashboardIcon.vue";
import BriefcaseIcon from "../components/icons/BriefcaseIcon.vue";
import UsersIcon from "../components/icons/UsersIcon.vue";
import LetterIcon from "../components/icons/LetterIcon.vue";
import ClipboardIcon from "../components/icons/ClipboardIcon.vue";
import SettingsIcon from "../components/icons/SettingsIcon.vue";
import UserMenu from "../components/shared/UserMenu.vue";

const route = useRoute();
const boot = window.boot || {};

const navItems = [
	{ label: "Dashboard", to: "/HR/Dashboard", icon: DashboardIcon },
	{ label: "Vacancies", to: "/HR/Vacancies", icon: BriefcaseIcon },
	{ label: "Candidates", to: "/HR/Candidates", icon: UsersIcon },
	{ label: "Letters", to: "/HR/Letters", icon: LetterIcon },
	{ label: "Audit log", to: "/HR/Audit-log", icon: ClipboardIcon },
	{ label: "Settings", to: "/HR/Settings", icon: SettingsIcon },
];

// startsWith (not exact match) so /HR/Vacancies/<name> still highlights
// the "Vacancies" nav item.
function isActive(to) {
	return route.path.startsWith(to);
}
</script>
