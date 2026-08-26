<template>
	<div v-if="loaded && data">
		<h1 class="text-2xl font-bold text-ink">Welcome, {{ data.applicant_name }}</h1>
		<p class="mt-1 text-sm text-body">Track your applications and complete any pending actions.</p>

		<ProfileCompletenessBanner :value="data.profile_completeness" />

		<div class="grid gap-6 lg:grid-cols-3">
			<div class="lg:col-span-2">
				<div class="rounded-xl border border-gray-200 p-6">
					<h2 class="mb-4 font-semibold text-ink">Active applications</h2>
					<div v-if="data.applications.length" class="space-y-3">
						<ApplicationCard v-for="app in data.applications" :key="app.name" :application="app" />
					</div>
					<EmptyState
						v-else
						:icon="SearchIcon"
						title="No active applications"
						subtitle="Browse open vacancies and submit your first application."
						action-label="Browse jobs"
						action-to="/jobs"
					/>
				</div>
			</div>

			<div class="space-y-6">
				<div class="rounded-xl border border-gray-200 p-6">
					<h2 class="mb-3 flex items-center gap-2 font-semibold text-ink">
						<BellIcon class="h-4 w-4" />
						Notifications
					</h2>
					<p v-if="!data.notifications.length" class="text-sm text-body">No notifications yet.</p>
					<div v-else class="space-y-2">
						<p v-for="(n, i) in data.notifications" :key="i" class="text-sm text-body">{{ n.message }}</p>
					</div>
				</div>

				<div class="rounded-xl border border-gray-200 p-6">
					<h2 class="mb-3 font-semibold text-ink">Your documents</h2>
					<div class="space-y-1.5 text-sm">
						<div v-for="row in fixedDocumentRows" :key="row.label" class="flex items-center justify-between">
							<span class="text-body">{{ row.label }}</span>
							<span :class="row.uploaded ? 'text-brand-700' : 'text-body'">{{ row.uploaded ? "✓" : "Missing" }}</span>
						</div>
					</div>
					<div v-if="data.documents.other.length" class="mt-3 space-y-2 border-t border-gray-100 pt-3">
						<DocumentRow
							v-for="doc in data.documents.other"
							:key="doc.name"
							:label="doc.document_type"
							:url="doc.attachment"
						/>
					</div>
					<router-link to="/complete-profile" class="mt-3 inline-block text-sm font-medium text-brand-700 hover:underline">
						Manage documents
					</router-link>
				</div>

				<router-link
					to="/complete-profile"
					class="block rounded-md border border-gray-200 px-4 py-2.5 text-center text-sm font-medium text-ink hover:bg-gray-50"
				>
					Edit profile
				</router-link>
				<router-link
					to="/applications"
					class="block rounded-md border border-gray-200 px-4 py-2.5 text-center text-sm font-medium text-ink hover:bg-gray-50"
				>
					All applications
				</router-link>
			</div>
		</div>
	</div>

	<p v-else-if="loaded" class="text-sm text-body">{{ error }}</p>

	<div v-else class="space-y-4">
		<div class="h-8 w-64 animate-pulse rounded bg-gray-100"></div>
		<div class="h-32 animate-pulse rounded-xl bg-gray-100"></div>
	</div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import call from "@doppio/controllers/call";
import ProfileCompletenessBanner from "../../components/applicant/ProfileCompletenessBanner.vue";
import ApplicationCard from "../../components/applicant/ApplicationCard.vue";
import EmptyState from "../../components/applicant/EmptyState.vue";
import DocumentRow from "../../components/applicant/DocumentRow.vue";
import SearchIcon from "../../components/icons/SearchIcon.vue";
import BellIcon from "../../components/icons/BellIcon.vue";

const data = ref(null);
const loaded = ref(false);
const error = ref("");

const fixedDocumentRows = computed(() => {
	if (!data.value) return [];
	const d = data.value.documents;
	return [
		{ label: "CV", uploaded: d.cv },
		{ label: "National ID", uploaded: d.national_id },
		{ label: "Academic Certificate", uploaded: d.academic_certificate },
		{ label: "Experience Letter", uploaded: d.experience_letter },
	];
});

onMounted(async () => {
	try {
		const res = await call("gdl.api.applicant.get_dashboard_data");
		if (res.success) {
			data.value = res.data;
		} else {
			error.value = res.message || "Could not load dashboard.";
		}
	} catch (err) {
		error.value = err.messages?.[0] || "Could not load dashboard.";
	} finally {
		loaded.value = true;
	}
});
</script>
