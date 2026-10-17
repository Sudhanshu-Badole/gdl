<template>
	<div>
		<h1 class="text-2xl font-bold text-ink">Audit log</h1>
		<p class="mt-1 text-sm text-body">Track status changes and administrative actions.</p>

		<div class="mt-6 flex items-center gap-3">
			<label class="text-sm font-medium text-ink">Filter</label>
			<select v-model="referenceDoctype" class="rounded-md border border-gray-200 px-3 py-1.5 text-sm" @change="loadRows">
				<option value="">All record types</option>
				<option v-for="dt in referenceDoctypes" :key="dt" :value="dt">{{ dt }}</option>
			</select>
		</div>

		<div v-if="loaded" class="mt-4">
			<EmptyState v-if="!rows.length" :icon="ClipboardIcon" title="No audit entries yet" subtitle="Status changes and administrative actions will appear here." />
			<div v-else class="overflow-x-auto rounded-xl border border-gray-200">
				<table class="w-full text-left text-sm">
					<thead class="border-b border-gray-200 text-xs uppercase tracking-wide text-body">
						<tr>
							<th class="px-4 py-3 font-medium">Time</th>
							<th class="px-4 py-3 font-medium">User</th>
							<th class="px-4 py-3 font-medium">Action</th>
							<th class="px-4 py-3 font-medium">Record</th>
							<th class="px-4 py-3 font-medium">Change</th>
						</tr>
					</thead>
					<tbody class="divide-y divide-gray-100">
						<tr v-for="row in rows" :key="row.name">
							<td class="whitespace-nowrap px-4 py-3 text-body">{{ formatTimestamp(row.timestamp) }}</td>
							<td class="px-4 py-3 text-body">{{ row.user }}</td>
							<td class="px-4 py-3 text-ink">{{ row.action }}</td>
							<td class="px-4 py-3 text-body">{{ row.reference_doctype }} - {{ row.reference_name }}</td>
							<td class="px-4 py-3 text-body">
								<span v-if="row.previous_value || row.new_value">{{ row.previous_value || "—" }} &rarr; {{ row.new_value || "—" }}</span>
								<span v-else-if="row.details">{{ row.details }}</span>
							</td>
						</tr>
					</tbody>
				</table>
			</div>
		</div>
		<div v-else class="mt-6 space-y-3">
			<div v-for="i in 5" :key="i" class="h-10 animate-pulse rounded-md bg-gray-100"></div>
		</div>
	</div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import call from "../../lib/call";
import EmptyState from "../../components/applicant/EmptyState.vue";
import ClipboardIcon from "../../components/icons/ClipboardIcon.vue";

const loaded = ref(false);
const rows = ref([]);
const referenceDoctypes = ref([]);
const referenceDoctype = ref("");

function formatTimestamp(value) {
	if (!value) return "";
	return new Date(value.replace(" ", "T")).toLocaleString("en-GB", {
		day: "numeric",
		month: "short",
		year: "numeric",
		hour: "2-digit",
		minute: "2-digit",
	});
}

async function loadRows() {
	loaded.value = false;
	try {
		const res = await call("gdl.api.hr_audit.list_audit_log", {
			reference_doctype: referenceDoctype.value || undefined,
		});
		rows.value = res?.data?.rows || [];
		referenceDoctypes.value = res?.data?.reference_doctypes || [];
	} finally {
		loaded.value = true;
	}
}

onMounted(loadRows);
</script>
