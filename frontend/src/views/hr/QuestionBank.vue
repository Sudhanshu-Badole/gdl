<template>
	<div>
		<div class="flex items-start justify-between">
			<div>
				<h1 class="text-2xl font-bold text-ink">Question bank</h1>
				<p class="mt-1 text-sm text-body">A reusable pool of questions you can draw from when building any exam.</p>
			</div>
			<button
				type="button"
				class="rounded-md bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700"
				@click="showForm = !showForm; editing = null"
			>
				{{ showForm && !editing ? "Close" : "+ Add question" }}
			</button>
		</div>

		<div v-if="showForm" class="mt-4 rounded-md border border-gray-200 bg-gray-50 p-4">
			<QuestionBankItemForm :existing="editing" :categories="categories" @saved="onSaved" @cancel="showForm = false; editing = null" />
		</div>

		<div class="mt-6 rounded-md border border-gray-200 bg-gray-50 p-4">
			<h2 class="mb-2 text-sm font-semibold text-ink">Bulk upload (CSV)</h2>
			<p class="text-xs text-body">
				Columns: question_type, question_text, marks, category, tags, option_a, option_b, option_c, option_d, correct_option.
			</p>
			<input type="file" accept=".csv" class="mt-2 text-sm" @change="onCsvChosen" />
			<p v-if="uploadResult" class="mt-2 text-sm text-brand-700">{{ uploadResult }}</p>
			<p v-if="uploadError" class="mt-2 text-sm text-red-600">{{ uploadError }}</p>
		</div>

		<div class="mt-6 flex flex-wrap items-center gap-3">
			<select v-model="filterType" class="rounded-md border border-gray-200 px-2 py-1.5 text-sm" @change="load">
				<option value="">Any type</option>
				<option value="Multiple Choice">Multiple Choice</option>
				<option value="True or False">True or False</option>
				<option value="Short Answer">Short Answer</option>
			</select>
			<select v-model="filterCategory" class="rounded-md border border-gray-200 px-2 py-1.5 text-sm" @change="load">
				<option value="">Any category</option>
				<option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
			</select>
			<input
				v-model="search"
				type="text"
				placeholder="Search question text or tags"
				class="rounded-md border border-gray-200 px-3 py-1.5 text-sm"
				@keyup.enter="load"
			/>
			<button type="button" class="rounded-md border border-gray-200 px-3 py-1.5 text-sm font-medium text-ink hover:bg-gray-50" @click="load">
				Search
			</button>
		</div>

		<div v-if="loaded && questions.length" class="mt-4 space-y-2">
			<div v-for="q in questions" :key="q.name" class="flex items-start justify-between gap-3 rounded-md border border-gray-200 p-3">
				<div>
					<p class="text-xs font-semibold uppercase tracking-wide text-body">
						{{ q.question_type }} · {{ q.marks }} mark(s)
						<template v-if="q.category"> · {{ q.category }}</template>
					</p>
					<p class="mt-1 text-sm text-ink">{{ q.question_text }}</p>
					<p v-if="q.tags" class="mt-1 text-xs text-body">Tags: {{ q.tags }}</p>
				</div>
				<div class="flex shrink-0 gap-2">
					<button type="button" class="text-xs font-medium text-brand-700 hover:underline" @click="edit(q)">Edit</button>
					<button type="button" class="text-xs font-medium text-red-600 hover:underline" @click="remove(q.name)">Delete</button>
				</div>
			</div>
		</div>
		<p v-else-if="loaded" class="mt-4 text-sm text-body">No questions in the bank yet.</p>
	</div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import call from "../../lib/call";
import QuestionBankItemForm from "../../components/hr/QuestionBankItemForm.vue";

const questions = ref([]);
const categories = ref([]);
const filterType = ref("");
const filterCategory = ref("");
const search = ref("");
const loaded = ref(false);
const showForm = ref(false);
const editing = ref(null);
const uploadResult = ref("");
const uploadError = ref("");

async function load() {
	try {
		const res = await call("gdl.api.hr_question_bank.list_bank_questions", {
			question_type: filterType.value || undefined,
			category: filterCategory.value || undefined,
			search: search.value || undefined,
		});
		questions.value = res?.data || [];
	} finally {
		loaded.value = true;
	}
}

onMounted(async () => {
	try {
		const res = await call("gdl.api.hr_question_bank.list_vacancy_categories");
		categories.value = res?.data || [];
	} catch {
		// non-critical
	}
	await load();
});

function edit(q) {
	editing.value = q;
	showForm.value = true;
}

async function onSaved() {
	showForm.value = false;
	editing.value = null;
	await load();
}

async function remove(name) {
	try {
		await call("gdl.api.hr_question_bank.delete_bank_question", { name });
		await load();
	} catch {
		// surfaced implicitly by the row simply staying in place
	}
}

function parseCsv(text) {
	const lines = text.split(/\r?\n/).filter((l) => l.trim().length);
	if (!lines.length) return [];
	const headers = lines[0].split(",").map((h) => h.trim());
	return lines.slice(1).map((line) => {
		const cells = line.split(",").map((c) => c.trim());
		const row = {};
		headers.forEach((h, i) => (row[h] = cells[i] ?? ""));
		return row;
	});
}

async function onCsvChosen(e) {
	const file = e.target.files[0];
	if (!file) return;
	uploadResult.value = "";
	uploadError.value = "";
	try {
		const text = await file.text();
		const rows = parseCsv(text);
		const res = await call("gdl.api.hr_question_bank.bulk_upload_bank_questions", { rows: JSON.stringify(rows) });
		if (res.success) {
			uploadResult.value = res.message;
			await load();
		} else {
			uploadError.value = res.message || "Upload failed.";
		}
	} catch (err) {
		uploadError.value = err.messages?.[0] || "Upload failed.";
	} finally {
		e.target.value = "";
	}
}
</script>
