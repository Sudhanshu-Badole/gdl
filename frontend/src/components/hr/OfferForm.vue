<template>
	<form class="space-y-3 rounded-md border border-gray-200 bg-gray-50 p-4" @submit.prevent="save">
		<div class="grid gap-3 sm:grid-cols-2">
			<div>
				<label class="mb-1 block text-sm font-medium text-ink">Designation</label>
				<select v-model="form.designation" required class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm">
					<option value="" disabled>Select...</option>
					<option v-for="d in designations" :key="d.name" :value="d.name">{{ d.name }}</option>
				</select>
			</div>
			<div>
				<label class="mb-1 block text-sm font-medium text-ink">Department</label>
				<select v-model="form.department" class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm">
					<option value="">None</option>
					<option v-for="d in departments" :key="d.name" :value="d.name">{{ d.name }}</option>
				</select>
			</div>
			<div>
				<label class="mb-1 block text-sm font-medium text-ink">Reporting manager</label>
				<select v-model="form.reporting_manager" class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm">
					<option value="">None</option>
					<option v-for="u in users" :key="u.name" :value="u.name">{{ u.full_name || u.name }}</option>
				</select>
			</div>
			<div>
				<label class="mb-1 block text-sm font-medium text-ink">Company</label>
				<input v-model="form.company" type="text" required class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm" />
			</div>
			<div>
				<label class="mb-1 block text-sm font-medium text-ink">Joining date</label>
				<input v-model="form.joining_date" type="date" required class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm" />
			</div>
			<div>
				<label class="mb-1 block text-sm font-medium text-ink">Response deadline</label>
				<input v-model="form.response_deadline" type="date" class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm" />
				<p class="mt-1 text-xs text-body">Defaults to 5 days from today if left blank.</p>
			</div>
			<div class="sm:col-span-2">
				<label class="mb-1 block text-sm font-medium text-ink">TFMR</label>
				<textarea
					v-model="form.salary"
					rows="3"
					placeholder="Enter TFMR/salary details to print on the offer letter"
					class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm"
				></textarea>
			</div>
		</div>

		<p v-if="error" class="text-sm text-red-600">{{ error }}</p>

		<button
			type="submit"
			:disabled="saving"
			class="rounded-md bg-brand-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
		>
			{{ saving ? "Creating..." : "Create offer" }}
		</button>
	</form>
</template>

<script setup>
import { ref, onMounted } from "vue";
import call from "../../lib/call";

const props = defineProps({
	jobApplication: { type: String, required: true },
});
const emit = defineEmits(["saved"]);

const designations = ref([]);
const departments = ref([]);
const users = ref([]);

const form = ref({
	designation: "",
	department: "",
	reporting_manager: "",
	company: "GreenDigital Ltd",
	salary: null,
	joining_date: "",
	response_deadline: "",
});
const saving = ref(false);
const error = ref("");

onMounted(async () => {
	const [d, dept, u] = await Promise.all([
		call("frappe.client.get_list", { doctype: "Designation", fields: ["name"], limit_page_length: 0, order_by: "name asc" }),
		call("frappe.client.get_list", { doctype: "Department", fields: ["name"], limit_page_length: 0, order_by: "name asc" }),
		call("frappe.client.get_list", { doctype: "User", fields: ["name", "full_name"], filters: { enabled: 1 }, limit_page_length: 0, order_by: "full_name asc" }),
	]);
	designations.value = d || [];
	departments.value = dept || [];
	users.value = u || [];
});

async function save() {
	saving.value = true;
	error.value = "";
	try {
		const res = await call("gdl.api.hr_offer.create_offer", {
			job_application: props.jobApplication,
			designation: form.value.designation,
			company: form.value.company,
			joining_date: form.value.joining_date,
			reporting_manager: form.value.reporting_manager || null,
			department: form.value.department || null,
			response_deadline: form.value.response_deadline || null,
			salary: form.value.salary,
		});
		if (res.success) {
			emit("saved");
		} else {
			error.value = res.message || "Could not create offer.";
		}
	} catch (err) {
		error.value = err.messages?.[0] || "Could not create offer.";
	} finally {
		saving.value = false;
	}
}
</script>
