<template>
	<div>
		<h1 class="text-2xl font-bold text-ink">Candidates</h1>
		<p class="mt-1 text-sm text-body">Search applicants, review verifications, and open candidate profiles.</p>

		<div class="mt-6 flex gap-6 border-b border-gray-200 text-sm font-medium">
			<button
				class="border-b-2 px-1 py-3"
				:class="activeTab === 'all' ? 'border-brand-600 text-brand-700' : 'border-transparent text-body hover:text-ink'"
				@click="activeTab = 'all'"
			>
				All candidates
			</button>
			<button
				class="border-b-2 px-1 py-3"
				:class="
					activeTab === 'verification' ? 'border-brand-600 text-brand-700' : 'border-transparent text-body hover:text-ink'
				"
				@click="activeTab = 'verification'"
			>
				Verification
			</button>
		</div>

		<div v-if="activeTab === 'all'" class="mt-6">
			<div class="flex flex-wrap items-center gap-3">
				<input
					v-model="search"
					type="text"
					placeholder="Search by name, email, or CID"
					class="w-72 rounded-md border border-gray-200 px-3 py-2 text-sm focus:border-brand-400 focus:outline-none"
					@keyup.enter="loadCandidates"
				/>
				<button
					class="rounded-md bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700"
					@click="loadCandidates"
				>
					Search
				</button>
				<div class="ml-auto flex items-center gap-2 text-sm text-body">
					<span>Sort by date created</span>
					<select v-model="sort" class="rounded-md border border-gray-200 px-2 py-1.5" @change="loadCandidates">
						<option value="creation desc">Newest first</option>
						<option value="creation asc">Oldest first</option>
					</select>
				</div>
			</div>

			<div v-if="loaded && candidates.length" class="mt-6 overflow-x-auto rounded-xl border border-gray-200">
				<table class="w-full text-left text-sm">
					<thead class="border-b border-gray-200 text-xs uppercase tracking-wide text-body">
						<tr>
							<th class="px-4 py-3 font-medium">Name</th>
							<th class="px-4 py-3 font-medium">Email</th>
							<th class="px-4 py-3 font-medium">CID</th>
							<th class="px-4 py-3 font-medium">Date created</th>
							<th class="px-4 py-3 font-medium">Applications</th>
							<th class="px-4 py-3 text-right font-medium">Action</th>
						</tr>
					</thead>
					<tbody class="divide-y divide-gray-100">
						<tr v-for="c in candidates" :key="c.name">
							<td class="px-4 py-3 font-medium text-ink">{{ c.applicant_name }}</td>
							<td class="px-4 py-3 text-body">{{ c.email_id }}</td>
							<td class="px-4 py-3 text-body">{{ c.gdl_cid_number || "—" }}</td>
							<td class="px-4 py-3 text-body">{{ formatDate(c.creation) }}</td>
							<td class="px-4 py-3 text-body">{{ c.applications_count }}</td>
							<td class="px-4 py-3 text-right">
								<a :href="`/app/job-applicant/${c.name}`" class="font-medium text-brand-700 hover:underline">
									View details
								</a>
							</td>
						</tr>
					</tbody>
				</table>
			</div>
			<p v-else-if="loaded && error" class="mt-6 text-sm text-red-600">{{ error }}</p>
			<p v-else-if="loaded" class="mt-6 text-sm text-body">No candidates found.</p>
			<div v-else class="mt-6 space-y-3">
				<div v-for="i in 5" :key="i" class="h-10 animate-pulse rounded-md bg-gray-100"></div>
			</div>
		</div>

		<ComingSoonPanel v-else feature="Document verification" class="mt-6" />
	</div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import call from "../../lib/call";
import ComingSoonPanel from "../../components/hr/ComingSoonPanel.vue";

const activeTab = ref("all");
const search = ref("");
const sort = ref("creation desc");
const candidates = ref([]);
const loaded = ref(false);
const error = ref("");

async function loadCandidates() {
	loaded.value = false;
	error.value = "";
	try {
		const res = await call("gdl.api.hr.list_candidates", {
			search: search.value || undefined,
			sort: sort.value,
		});
		candidates.value = res?.data || [];
	} catch (err) {
		error.value = err.messages?.[0] || "Could not load candidates.";
	} finally {
		loaded.value = true;
	}
}

onMounted(loadCandidates);

function formatDate(value) {
	if (!value) return "—";
	return new Date(value.replace(" ", "T")).toLocaleDateString("en-GB", {
		day: "numeric",
		month: "short",
		year: "numeric",
	});
}
</script>
