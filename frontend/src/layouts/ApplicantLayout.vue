<template>
	<div class="flex min-h-screen bg-white">
		<aside class="flex w-60 shrink-0 flex-col border-r border-gray-200">
			<div class="flex items-center gap-2 border-b border-gray-200 px-5 py-4">
				<span class="text-xl font-extrabold tracking-tight text-brand-600">G•DL</span>
				<span class="text-sm font-semibold text-ink">GreenDigital Limited Careers</span>
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
				<!-- User guide is a separate, non-Vue web page - real navigation. -->
				<a
					href="/how-to-apply"
					class="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-body hover:bg-gray-50 hover:text-ink"
				>
					<GraduationCapIcon class="h-4 w-4 shrink-0" />
					User guide
				</a>
			</nav>
		</aside>

		<div class="flex flex-1 flex-col">
			<header class="flex items-center justify-end border-b border-gray-200 px-6 py-4">
				<UserMenu :display-name="boot.full_name || boot.user" :email="boot.user" role-label="Applicant" />
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
import ClipboardIcon from "../components/icons/ClipboardIcon.vue";
import UsersIcon from "../components/icons/UsersIcon.vue";
import BriefcaseIcon from "../components/icons/BriefcaseIcon.vue";
import GraduationCapIcon from "../components/icons/GraduationCapIcon.vue";
import UserMenu from "../components/shared/UserMenu.vue";

const route = useRoute();
const boot = window.boot || {};

const navItems = [
	{ label: "Dashboard", to: "/dashboard", icon: DashboardIcon },
	{ label: "Applications", to: "/applications", icon: ClipboardIcon },
	{ label: "Profile", to: "/complete-profile", icon: UsersIcon },
	{ label: "Browse jobs", to: "/jobs", icon: BriefcaseIcon },
];

function isActive(to) {
	return route.path === to || route.path.startsWith(to + "/");
}
</script>
