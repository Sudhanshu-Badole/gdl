<template>
	<div>
		<div class="flex items-start justify-between">
			<div>
				<h1 class="text-2xl font-bold text-ink">Vacancies</h1>
				<p class="mt-1 text-sm text-body">Create, publish, and manage recruitment for each position.</p>
			</div>
			<a
				href="/app/job-opening/new"
				class="rounded-md bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700"
			>
				+ New vacancy
			</a>
		</div>

		<div v-if="loaded && vacancies.length" class="mt-8 overflow-x-auto rounded-xl border border-gray-200">
			<table class="w-full min-w-[900px] text-left text-sm">
				<thead class="border-b border-gray-200 text-xs uppercase tracking-wide text-body">
					<tr>
						<th class="px-4 py-3 font-medium">Title</th>
						<th class="px-4 py-3 font-medium">Ref</th>
						<th class="px-4 py-3 font-medium">Office</th>
						<th class="px-4 py-3 font-medium">Open date</th>
						<th class="px-4 py-3 font-medium">Applications</th>
						<th class="px-4 py-3 font-medium">Positions</th>
						<th class="px-4 py-3 font-medium">Deadline</th>
						<th class="px-4 py-3 font-medium">Status</th>
						<th class="px-4 py-3 text-right font-medium">Actions</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-gray-100">
					<tr v-for="v in vacancies" :key="v.name">
						<td class="px-4 py-4 font-semibold text-ink">
							<router-link :to="`/HR/Vacancies/${v.name}`" class="hover:text-brand-700">
								{{ v.job_title }}
							</router-link>
						</td>
						<td class="px-4 py-4 text-body">{{ v.name }}</td>
						<td class="px-4 py-4 text-body">{{ v.department || "—" }}</td>
						<td class="px-4 py-4 text-body">{{ formatDate(v.posted_on) }}</td>
						<td class="px-4 py-4 text-body">{{ v.applications_count }}</td>
						<td class="px-4 py-4 text-body">{{ v.positions_filled }}/{{ v.positions_total }}</td>
						<td class="px-4 py-4 text-body">{{ formatDate(v.closes_on) }}</td>
						<td class="px-4 py-4">
							<span class="rounded-full px-3 py-1 text-xs font-semibold" :class="statusBadgeClass(v.computed_status)">
								{{ statusLabel(v.computed_status).toUpperCase() }}
							</span>
						</td>
						<td class="px-4 py-4 text-right">
							<button
								v-if="v.computed_status === 'Published'"
								class="rounded-md border border-brand-200 px-3 py-1.5 text-sm font-medium text-brand-700 hover:bg-brand-50"
								:disabled="closingName === v.name"
								@click="closeApplications(v)"
							>
								Close applications
							</button>
							<span v-else class="rounded-md border border-gray-200 px-3 py-1.5 text-sm text-body/70">
								{{ v.computed_status === "Filled" ? "Closed" : "Open for applications" }}
							</span>
						</td>
					</tr>
				</tbody>
			</table>
		</div>

		<p v-else-if="loaded && error" class="mt-8 text-sm text-red-600">{{ error }}</p>

		<p v-else-if="loaded" class="mt-8 text-sm text-body">No vacancies yet.</p>

		<div v-else class="mt-8 space-y-3">
			<div v-for="i in 5" :key="i" class="h-12 animate-pulse rounded-md bg-gray-100"></div>
		</div>

		<p v-if="actionError" class="mt-3 text-sm text-red-600">{{ actionError }}</p>
	</div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import call from "../../lib/call";

const vacancies = ref([]);
const loaded = ref(false);
const error = ref("");
const closingName = ref(null);
const actionError = ref("");

async function loadVacancies() {
	try {
		const res = await call("gdl.api.hr.list_vacancies");
		vacancies.value = res?.data || [];
	} catch (err) {
		error.value = err.messages?.[0] || "Could not load vacancies.";
	}
}

onMounted(async () => {
	try {
		await loadVacancies();
	} finally {
		loaded.value = true;
	}
});

async function closeApplications(vacancy) {
	closingName.value = vacancy.name;
	actionError.value = "";
	try {
		await call("gdl.api.hr.close_vacancy_applications", { name: vacancy.name });
		await loadVacancies();
	} catch (err) {
		actionError.value = err.messages?.[0] || "Could not close applications.";
	} finally {
		closingName.value = null;
	}
}

function formatDate(value) {
	if (!value) return "—";
	// posted_on comes back as a Datetime ("YYYY-MM-DD HH:MM:SS"); closes_on as
	// a plain Date ("YYYY-MM-DD") - normalize both to something Date() parses.
	const isoish = value.includes(" ") ? value.replace(" ", "T") : `${value}T00:00:00`;
	return new Date(isoish).toLocaleDateString("en-GB", {
		day: "numeric",
		month: "short",
		year: "numeric",
	});
}

function statusLabel(status) {
	// Client feedback: "Vacancy Filled" should read as "Closed" - the
	// underlying computed_status value ("Filled") stays as-is since other
	// code (statusBadgeClass, the button v-if above) still keys off it.
	return status === "Filled" ? "Closed" : status;
}

function statusBadgeClass(status) {
	return (
		{
			Published: "bg-brand-100 text-brand-700",
			Closed: "bg-gray-200 text-body",
			Filled: "bg-gray-100 text-body",
			Draft: "bg-gray-100 text-body italic",
		}[status] || "bg-gray-100 text-body"
	);
}
</script>
