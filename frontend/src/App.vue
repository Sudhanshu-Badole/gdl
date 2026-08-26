<template>
	<router-view v-if="route.meta.isAdmin" />
	<div v-else class="flex min-h-screen flex-col bg-white">
		<AppHeader />
		<main class="flex-1">
			<router-view />
		</main>
		<AppFooter />
	</div>
</template>

<script setup>
import { useRoute } from "vue-router";
import AppHeader from "./components/AppHeader.vue";
import AppFooter from "./components/AppFooter.vue";

// /HR/* routes render inside AdminLayout.vue, which owns its own
// header+sidebar - the public site's chrome is skipped entirely for those.
const route = useRoute();
</script>
