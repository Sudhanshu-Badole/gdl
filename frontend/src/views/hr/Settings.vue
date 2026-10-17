<template>
	<div>
		<h1 class="text-2xl font-bold text-ink">Settings</h1>
		<p class="mt-1 text-sm text-body">Organization, offer/appointment policy, and staff accounts.</p>

		<div v-if="loaded" class="mt-6 space-y-6">
			<form class="rounded-xl border border-gray-200 p-6" @submit.prevent="saveSettings">
				<h2 class="mb-4 font-semibold text-ink">Organization &amp; Policy</h2>
				<div class="grid gap-4 sm:grid-cols-2">
					<div>
						<label class="mb-1 block text-sm font-medium text-ink">Organization name</label>
						<input v-model="settings.organization_name" type="text" class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm" />
					</div>
					<div>
						<label class="mb-1 block text-sm font-medium text-ink">Time zone</label>
						<input v-model="settings.time_zone" type="text" placeholder="e.g. Asia/Thimphu" class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm" />
					</div>
					<div>
						<label class="mb-1 block text-sm font-medium text-ink">Organization logo</label>
						<input type="file" accept="image/jpeg,image/png" class="w-full text-sm" @change="onLogoSelected" />
						<p v-if="logoUploading" class="mt-1 text-xs text-body">Uploading...</p>
						<p v-if="logoError" class="mt-1 text-xs text-red-600">{{ logoError }}</p>
						<a v-if="settings.organization_logo" :href="settings.organization_logo" target="_blank" class="mt-1 inline-block text-xs text-brand-700 hover:underline">
							View current logo
						</a>
					</div>
					<div>
						<label class="mb-1 block text-sm font-medium text-ink">Offer response window (days)</label>
						<input v-model.number="settings.offer_response_window_days" type="number" min="1" class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm" />
					</div>
				</div>
				<label class="mt-4 flex items-center gap-2 text-sm text-ink">
					<input v-model="settings.auto_issue_appointment_letter" type="checkbox" />
					Automatically issue the appointment letter when an offer is accepted
				</label>

				<div class="mt-4 max-w-xs">
					<label class="mb-1 block text-sm font-medium text-ink">Test lockdown: auto-submit after N violations</label>
					<input v-model.number="settings.max_exam_violations_before_autosubmit" type="number" min="0" class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm" />
					<p class="mt-1 text-xs text-body">A running test is submitted automatically once it has this many logged full-screen-exit/tab-switch violations. 0 disables auto-submit.</p>
				</div>

				<p v-if="settingsMessage" class="mt-3 text-sm text-brand-700">{{ settingsMessage }}</p>
				<p v-if="settingsError" class="mt-3 text-sm text-red-600">{{ settingsError }}</p>
				<button type="submit" :disabled="savingSettings" class="mt-4 rounded-md bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60">
					{{ savingSettings ? "Saving..." : "Save settings" }}
				</button>
			</form>

			<div v-if="isSystemManager" class="rounded-xl border border-gray-200 p-6">
				<div class="mb-4 flex items-center justify-between">
					<h2 class="font-semibold text-ink">Staff accounts</h2>
					<button
						v-if="!showCreateForm"
						type="button"
						class="rounded-md border border-gray-200 px-3 py-1.5 text-sm font-medium text-ink hover:bg-gray-50"
						@click="showCreateForm = true"
					>
						+ New account
					</button>
				</div>

				<StaffAccountForm v-if="showCreateForm" class="mb-4" @saved="onAccountSaved" @cancel="showCreateForm = false" />

				<EmptyState v-if="!accounts.length" :icon="UsersIcon" title="No staff accounts yet" subtitle="HR Officer and Panel Member accounts appear here." />
				<div v-else class="overflow-x-auto rounded-xl border border-gray-200">
					<table class="w-full text-left text-sm">
						<thead class="border-b border-gray-200 text-xs uppercase tracking-wide text-body">
							<tr>
								<th class="px-4 py-3 font-medium">Name</th>
								<th class="px-4 py-3 font-medium">Email</th>
								<th class="px-4 py-3 font-medium">Role</th>
								<th class="px-4 py-3 font-medium">Status</th>
								<th class="px-4 py-3 text-right font-medium">Action</th>
							</tr>
						</thead>
						<tbody class="divide-y divide-gray-100">
							<template v-for="a in accounts" :key="a.name">
								<tr>
									<td class="px-4 py-3 text-ink">{{ a.full_name }}</td>
									<td class="px-4 py-3 text-body">{{ a.email }}</td>
									<td class="px-4 py-3 text-body">{{ a.role }}</td>
									<td class="px-4 py-3">
										<span class="rounded-full px-2 py-0.5 text-xs font-medium" :class="a.enabled ? 'bg-brand-50 text-brand-700' : 'bg-gray-100 text-body'">
											{{ a.enabled ? "Active" : "Deactivated" }}
										</span>
									</td>
									<td class="px-4 py-3 text-right">
										<div class="flex justify-end gap-3">
											<button type="button" class="text-xs font-medium text-brand-700 hover:underline" @click="editingFor = editingFor === a.name ? null : a.name">
												{{ editingFor === a.name ? "Close" : "Edit" }}
											</button>
											<button type="button" class="text-xs font-medium text-brand-700 hover:underline" @click="resettingFor = resettingFor === a.name ? null : a.name">
												Reset password
											</button>
											<button type="button" class="text-xs font-medium text-red-600 hover:underline" @click="toggleEnabled(a)">
												{{ a.enabled ? "Deactivate" : "Activate" }}
											</button>
										</div>
									</td>
								</tr>
								<tr v-if="editingFor === a.name">
									<td colspan="5" class="px-4 pb-4">
										<StaffAccountForm :existing="a" @saved="onAccountSaved" @cancel="editingFor = null" />
									</td>
								</tr>
								<tr v-if="resettingFor === a.name">
									<td colspan="5" class="px-4 pb-4">
										<div class="flex items-end gap-2 rounded-md border border-gray-200 bg-gray-50 p-4">
											<div>
												<label class="mb-1 block text-sm font-medium text-ink">New password</label>
												<input v-model="newPassword" type="text" class="rounded-md border border-gray-200 px-3 py-2 text-sm" />
											</div>
											<button type="button" class="rounded-md bg-brand-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-brand-700" @click="resetPassword(a.name)">
												Set password
											</button>
										</div>
									</td>
								</tr>
							</template>
						</tbody>
					</table>
				</div>
				<p v-if="accountsError" class="mt-3 text-sm text-red-600">{{ accountsError }}</p>
				<p v-if="accountsMessage" class="mt-3 text-sm text-brand-700">{{ accountsMessage }}</p>
			</div>
		</div>

		<div v-else class="mt-6 space-y-3">
			<div v-for="i in 3" :key="i" class="h-10 animate-pulse rounded-md bg-gray-100"></div>
		</div>
	</div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import call from "../../lib/call";
import upload from "../../lib/upload";
import EmptyState from "../../components/applicant/EmptyState.vue";
import UsersIcon from "../../components/icons/UsersIcon.vue";
import StaffAccountForm from "../../components/hr/StaffAccountForm.vue";

const boot = window.boot || {};
const isSystemManager = computed(() => (boot.roles || []).includes("System Manager"));

const loaded = ref(false);
const settings = ref({});
const savingSettings = ref(false);
const settingsMessage = ref("");
const settingsError = ref("");
const logoUploading = ref(false);
const logoError = ref("");

const accounts = ref([]);
const showCreateForm = ref(false);
const editingFor = ref(null);
const resettingFor = ref(null);
const newPassword = ref("");
const accountsError = ref("");
const accountsMessage = ref("");

async function loadSettings() {
	const res = await call("gdl.api.hr_settings.get_recruitment_settings");
	settings.value = res?.data || {};
}

async function loadAccounts() {
	if (!isSystemManager.value) return;
	const res = await call("gdl.api.hr_admin.list_staff_accounts");
	accounts.value = res?.data || [];
}

onMounted(async () => {
	try {
		await Promise.all([loadSettings(), loadAccounts()]);
	} finally {
		loaded.value = true;
	}
});

async function onLogoSelected(e) {
	const file = e.target.files[0];
	if (!file) return;
	logoUploading.value = true;
	logoError.value = "";
	try {
		const res = await upload("gdl.api.hr_settings.upload_organization_logo", file);
		settings.value.organization_logo = res.data.file_url;
	} catch (err) {
		logoError.value = err.messages?.[0] || "Could not upload logo.";
	} finally {
		logoUploading.value = false;
	}
}

async function saveSettings() {
	savingSettings.value = true;
	settingsMessage.value = "";
	settingsError.value = "";
	try {
		const res = await call("gdl.api.hr_settings.update_recruitment_settings", {
			organization_name: settings.value.organization_name,
			time_zone: settings.value.time_zone,
			offer_response_window_days: settings.value.offer_response_window_days,
			auto_issue_appointment_letter: settings.value.auto_issue_appointment_letter ? 1 : 0,
			max_exam_violations_before_autosubmit: settings.value.max_exam_violations_before_autosubmit,
		});
		if (res.success) {
			settingsMessage.value = res.message;
		} else {
			settingsError.value = res.message || "Could not save settings.";
		}
	} catch (err) {
		settingsError.value = err.messages?.[0] || "Could not save settings.";
	} finally {
		savingSettings.value = false;
	}
}

function onAccountSaved() {
	showCreateForm.value = false;
	editingFor.value = null;
	loadAccounts();
}

async function toggleEnabled(account) {
	accountsError.value = "";
	accountsMessage.value = "";
	try {
		const res = await call("gdl.api.hr_admin.set_account_enabled", { user: account.name, enabled: account.enabled ? 0 : 1 });
		accountsMessage.value = res.message;
		await loadAccounts();
	} catch (err) {
		accountsError.value = err.messages?.[0] || "Could not update account.";
	}
}

async function resetPassword(user) {
	accountsError.value = "";
	accountsMessage.value = "";
	try {
		const res = await call("gdl.api.hr_admin.reset_staff_password", { user, new_password: newPassword.value });
		accountsMessage.value = res.message;
		resettingFor.value = null;
		newPassword.value = "";
	} catch (err) {
		accountsError.value = err.messages?.[0] || "Could not reset password.";
	}
}
</script>
