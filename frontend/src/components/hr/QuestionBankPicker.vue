<template>
	<div class="rounded-md border border-gray-200 bg-gray-50 p-4">
		<div class="flex flex-wrap items-end gap-3">
			<div>
				<label class="mb-1 block text-xs text-body">Question type</label>
				<select v-model="filterType" class="rounded-md border border-gray-200 px-2 py-1.5 text-sm" @change="load">
					<option value="">Any</option>
					<option value="Multiple Choice">Multiple Choice</option>
					<option value="True or False">True or False</option>
					<option value="Short Answer">Short Answer</option>
				</select>
			</div>
			<div>
				<label class="mb-1 block text-xs text-body">Category</label>
				<select v-model="filterCategory" class="rounded-md border border-gray-200 px-2 py-1.5 text-sm" @change="load">
					<option value="">Any</option>
					<option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
				</select>
			</div>
			<a href="/HR/Question-bank" target="_blank" class="text-sm font-medium text-brand-700 hover:underline">Manage bank</a>
		</div>

		<div v-if="loaded && !questions.length" class="mt-3 text-sm text-body">No matching questions in the bank.</div>

		<div v-else class="mt-3 max-h-64 space-y-1 overflow-y-auto">
			<label
				v-for="q in questions"
				:key="q.name"
				class="flex items-start gap-2 rounded-md border border-gray-200 bg-white p-2 text-sm"
			>
				<input type="checkbox" class="mt-1" :value="q.name" v-model="selected" />
				<span>
					<span class="text-xs font-semibold uppercase tracking-wide text-body">{{ q.question_type }} · {{ q.marks }} mark(s)</span>
					<br />
					{{ q.question_text }}
				</span>
			</label>
		</div>

		<div class="mt-3 flex flex-wrap items-center gap-2">
			<button
				type="button"
				:disabled="!selected.length || assigning"
				class="rounded-md bg-brand-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
				@click="assignSelected"
			>
				Assign selected ({{ selected.length }})
			</button>
			<span class="text-xs text-body">or</span>
			<input
				v-model.number="randomCount"
				type="number"
				min="1"
				class="w-16 rounded-md border border-gray-200 px-2 py-1 text-sm"
			/>
			<button
				type="button"
				:disabled="assigning"
				class="rounded-md border border-gray-200 px-3 py-1.5 text-sm font-medium text-ink hover:bg-gray-50 disabled:opacity-60"
				@click="assignRandom"
			>
				Add random (matching filters above)
			</button>
		</div>
		<p v-if="error" class="mt-2 text-sm text-red-600">{{ error }}</p>
	</div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import call from "../../lib/call";

const props = defineProps({
	exam: { type: String, required: true },
});
const emit = defineEmits(["assigned"]);

const questions = ref([]);
const categories = ref([]);
const filterType = ref("");
const filterCategory = ref("");
const selected = ref([]);
const randomCount = ref(5);
const loaded = ref(false);
const assigning = ref(false);
const error = ref("");

async function load() {
	selected.value = [];
	try {
		const res = await call("gdl.api.hr_question_bank.list_bank_questions", {
			question_type: filterType.value || undefined,
			category: filterCategory.value || undefined,
		});
		questions.value = res?.data || [];
	} catch (err) {
		error.value = err.messages?.[0] || "Could not load the question bank.";
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

async function assignSelected() {
	assigning.value = true;
	error.value = "";
	try {
		const res = await call("gdl.api.hr_question_bank.assign_manual", {
			exam: props.exam,
			bank_question_names: JSON.stringify(selected.value),
		});
		if (res.success) {
			emit("assigned");
		} else {
			error.value = res.message || "Could not assign questions.";
		}
	} catch (err) {
		error.value = err.messages?.[0] || "Could not assign questions.";
	} finally {
		assigning.value = false;
	}
}

async function assignRandom() {
	assigning.value = true;
	error.value = "";
	try {
		const res = await call("gdl.api.hr_question_bank.assign_random_sample", {
			exam: props.exam,
			count: randomCount.value,
			question_type: filterType.value || undefined,
			category: filterCategory.value || undefined,
		});
		if (res.success) {
			emit("assigned");
		} else {
			error.value = res.message || "Could not assign questions.";
		}
	} catch (err) {
		error.value = err.messages?.[0] || "Could not assign questions.";
	} finally {
		assigning.value = false;
	}
}
</script>
