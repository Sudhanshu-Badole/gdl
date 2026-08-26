<template>
	<div class="rounded-xl border border-gray-200 p-6">
		<h2 class="font-semibold text-ink">Photo</h2>
		<p class="mt-1 text-sm text-body">A clear headshot helps HR identify you.</p>

		<div class="mt-4 flex items-center gap-4">
			<img v-if="photoUrl" :src="photoUrl" alt="Profile photo" class="h-16 w-16 rounded-full object-cover" />
			<div v-else class="flex h-16 w-16 items-center justify-center rounded-full bg-gray-100 text-body">?</div>

			<label
				class="cursor-pointer rounded-md border border-gray-200 px-4 py-2 text-sm font-medium text-ink hover:bg-gray-50"
			>
				<CameraIcon class="mr-1 inline h-4 w-4" />
				Change photo
				<input type="file" accept="image/jpeg,image/png" class="hidden" @change="onChange" />
			</label>
		</div>

		<p class="mt-2 text-xs text-body">JPG or PNG, up to 2MB. Counts toward profile completeness.</p>
		<p v-if="error" class="mt-2 text-xs text-red-600">{{ error }}</p>
	</div>
</template>

<script setup>
import { ref } from "vue";
import upload from "../../lib/upload";
import CameraIcon from "../icons/CameraIcon.vue";

defineProps({
	photoUrl: { type: String, default: null },
});
const emit = defineEmits(["uploaded"]);

const error = ref("");

async function onChange(e) {
	const file = e.target.files[0];
	if (!file) return;
	error.value = "";
	try {
		const res = await upload("gdl.api.applicant.upload_profile_photo", file);
		if (res.success) {
			emit("uploaded");
		} else {
			error.value = res.message || "Could not upload photo.";
		}
	} catch (err) {
		error.value = err.messages?.[0] || "Could not upload photo.";
	} finally {
		e.target.value = "";
	}
}
</script>
