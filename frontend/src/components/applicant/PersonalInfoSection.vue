<template>
	<div id="personal-info-section" class="rounded-xl border border-gray-200 p-6">
		<h2 class="font-semibold text-ink">Personal details</h2>
		<p class="mt-1 text-sm text-body">Update your personal information and CID. These details are snapshotted when you apply for a job.</p>

		<div class="mt-4 flex items-center justify-between rounded-md bg-gray-50 px-4 py-3">
			<div>
				<p class="text-xs text-body">Email</p>
				<p class="font-medium text-ink">{{ applicant.email_id }}</p>
			</div>
			<span v-if="emailVerified" class="rounded-full bg-brand-100 px-3 py-1 text-xs font-semibold text-brand-700">
				Verified
			</span>
		</div>

		<form class="mt-4 space-y-4" @submit.prevent="save">
			<div>
				<label class="mb-1 block text-sm font-medium text-ink">CID / National ID</label>
				<input v-model="form.gdl_cid_number" type="text" class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm" />
				<p class="mt-1 text-xs text-body">If you change your CID number, your uploaded CID document will need HR verification again.</p>
			</div>

			<div class="grid gap-4 sm:grid-cols-2">
				<div>
					<label class="mb-1 block text-sm font-medium text-ink">Date of birth</label>
					<input v-model="form.gdl_date_of_birth" type="date" class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm" />
				</div>
				<div>
					<label class="mb-1 block text-sm font-medium text-ink">Gender</label>
					<select v-model="form.gdl_gender" class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm">
						<option value="">Select...</option>
						<option v-for="g in genders" :key="g" :value="g">{{ g }}</option>
					</select>
				</div>
			</div>

			<div>
				<label class="mb-1 block text-sm font-medium text-ink">Nationality</label>
				<select v-model="form.gdl_nationality" class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm">
					<option value="">Select...</option>
					<option v-for="c in countries" :key="c" :value="c">{{ c }}</option>
				</select>
			</div>

			<div>
				<label class="mb-1 block text-sm font-medium text-ink">Permanent address</label>
				<textarea v-model="form.gdl_permanent_address" rows="2" class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm"></textarea>
			</div>
			<div>
				<label class="mb-1 block text-sm font-medium text-ink">Current address</label>
				<textarea v-model="form.gdl_current_address" rows="2" class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm"></textarea>
			</div>

			<p v-if="error" class="text-sm text-red-600">{{ error }}</p>
			<p v-if="success" class="text-sm text-brand-700">{{ success }}</p>

			<button
				type="submit"
				:disabled="saving"
				class="rounded-md bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
			>
				Save personal details
			</button>
		</form>
	</div>
</template>

<script setup>
import { ref, watch } from "vue";
import call from "../../lib/call";

const props = defineProps({
	applicant: { type: Object, required: true },
});
const emit = defineEmits(["saved"]);

const FIELDS = ["gdl_cid_number", "gdl_date_of_birth", "gdl_gender", "gdl_nationality", "gdl_permanent_address", "gdl_current_address"];

function snapshot() {
	const out = {};
	for (const f of FIELDS) out[f] = props.applicant[f] || "";
	return out;
}

const form = ref(snapshot());
watch(
	() => props.applicant,
	() => {
		form.value = snapshot();
	}
);

const genders = ref([]);
const countries = ref([]);
const emailVerified = ref(false);
const saving = ref(false);
const error = ref("");
const success = ref("");

async function save() {
	saving.value = true;
	error.value = "";
	success.value = "";
	try {
		const res = await call("gdl.api.applicant.update_personal_info", { ...form.value });
		if (res.success) {
			success.value = res.message;
			emit("saved");
		} else {
			error.value = res.message || "Could not save personal information.";
		}
	} catch (err) {
		error.value = err.messages?.[0] || "Something went wrong. Please try again.";
	} finally {
		saving.value = false;
	}
}

async function loadLookups() {
	const [genderRows, countryRows, verified] = await Promise.all([
		call("frappe.client.get_list", { doctype: "Gender", fields: ["name"], limit_page_length: 0, order_by: "name asc" }),
		call("frappe.client.get_list", { doctype: "Country", fields: ["name"], limit_page_length: 0, order_by: "name asc" }),
		call("frappe.client.get_value", {
			doctype: "User",
			fieldname: "gdl_email_verified",
			filters: { name: props.applicant.email_id },
			as_dict: 0,
		}),
	]);
	genders.value = (genderRows || []).map((r) => r.name);
	countries.value = (countryRows || []).map((r) => r.name);
	emailVerified.value = !!verified;
}

loadLookups();
</script>
