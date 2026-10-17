<template>
	<form class="space-y-3 rounded-md border border-gray-200 bg-gray-50 p-4" @submit.prevent="save">
		<div class="grid gap-3 sm:grid-cols-2">
			<div>
				<label class="mb-1 block text-sm font-medium text-ink">Email</label>
				<input v-model="form.email" type="email" required :disabled="!!props.existing" class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm disabled:bg-gray-100" />
			</div>
			<div>
				<label class="mb-1 block text-sm font-medium text-ink">Role</label>
				<select v-model="form.role" required class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm">
					<option value="HR Officer">HR Officer</option>
					<option value="Panel Member">Panel Member</option>
				</select>
			</div>
			<div>
				<label class="mb-1 block text-sm font-medium text-ink">First name</label>
				<input v-model="form.first_name" type="text" required class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm" />
			</div>
			<div>
				<label class="mb-1 block text-sm font-medium text-ink">Last name</label>
				<input v-model="form.last_name" type="text" class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm" />
			</div>
			<div v-if="!props.existing">
				<label class="mb-1 block text-sm font-medium text-ink">Initial password</label>
				<input v-model="form.password" type="text" required class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm" />
			</div>
		</div>

		<p v-if="error" class="text-sm text-red-600">{{ error }}</p>

		<div class="flex gap-2">
			<button type="submit" :disabled="saving" class="rounded-md bg-brand-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60">
				{{ props.existing ? "Save account" : "Create account" }}
			</button>
			<button type="button" class="rounded-md border border-gray-200 px-3 py-1.5 text-sm font-medium text-ink hover:bg-white" @click="$emit('cancel')">
				Cancel
			</button>
		</div>
	</form>
</template>

<script setup>
import { ref } from "vue";
import call from "../../lib/call";

const props = defineProps({
	existing: { type: Object, default: null },
});
const emit = defineEmits(["saved", "cancel"]);

function initialForm() {
	if (props.existing) {
		return {
			email: props.existing.email,
			role: props.existing.role,
			first_name: props.existing.full_name?.split(" ")[0] || "",
			last_name: props.existing.full_name?.split(" ").slice(1).join(" ") || "",
			password: "",
		};
	}
	return { email: "", role: "HR Officer", first_name: "", last_name: "", password: "" };
}

const form = ref(initialForm());
const saving = ref(false);
const error = ref("");

async function save() {
	saving.value = true;
	error.value = "";
	try {
		const method = props.existing ? "gdl.api.hr_admin.update_staff_account" : "gdl.api.hr_admin.create_staff_account";
		const args = props.existing
			? { user: props.existing.name, first_name: form.value.first_name, last_name: form.value.last_name, role: form.value.role }
			: { email: form.value.email, first_name: form.value.first_name, last_name: form.value.last_name, role: form.value.role, password: form.value.password };
		const res = await call(method, args);
		if (res.success) {
			emit("saved");
		} else {
			error.value = res.message || "Could not save account.";
		}
	} catch (err) {
		error.value = err.messages?.[0] || "Could not save account.";
	} finally {
		saving.value = false;
	}
}
</script>
