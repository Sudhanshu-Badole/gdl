<template>
	<div>
		<router-link to="/jobs" class="text-sm text-body hover:text-brand-700">← Back to jobs</router-link>

		<div v-if="!jobOpening" class="mt-6 rounded-xl border border-gray-200 p-6 text-sm text-body">
			No vacancy specified.
		</div>

		<div v-else-if="!loaded" class="mt-6 space-y-4">
			<div class="h-6 w-64 animate-pulse rounded bg-gray-100"></div>
			<div class="h-40 animate-pulse rounded-xl bg-gray-100"></div>
		</div>

		<div v-else-if="loadError" class="mt-6 rounded-xl border border-gray-200 p-6 text-sm text-red-600">
			{{ loadError }}
		</div>

		<div v-else class="mt-6 max-w-2xl space-y-6">
			<div>
				<h1 class="text-2xl font-bold text-ink">Apply for {{ context.job_opening.job_title }}</h1>
				<p class="mt-1 text-sm text-body">
					{{ context.job_opening.name }}
					<template v-if="closesOn"> · {{ closesOn }}</template>
				</p>
			</div>

			<div class="rounded-xl border border-gray-200 p-6">
				<div class="mb-1 flex items-center justify-between">
					<h2 class="font-semibold text-ink">Your profile</h2>
					<router-link to="/complete-profile" class="text-sm font-medium text-brand-700 hover:underline">
						Edit profile
					</router-link>
				</div>
				<dl class="mt-3 space-y-1 text-sm">
					<div class="flex justify-between">
						<dt class="text-body">Name</dt>
						<dd class="text-ink">{{ context.applicant.applicant_name }}</dd>
					</div>
					<div class="flex justify-between">
						<dt class="text-body">Email</dt>
						<dd class="text-ink">{{ context.applicant.email_id }}</dd>
					</div>
					<div class="flex justify-between">
						<dt class="text-body">Profile completeness</dt>
						<dd :class="context.applicant.gdl_profile_completeness >= 80 ? 'text-brand-700' : 'text-amber-600'">
							{{ context.applicant.gdl_profile_completeness || 0 }}%
						</dd>
					</div>
				</dl>
			</div>

			<div v-if="!context.can_apply" class="rounded-xl border border-amber-200 bg-amber-50 p-6">
				<h2 class="mb-2 flex items-center gap-2 font-semibold text-ink">
					<InfoIcon class="h-4 w-4 shrink-0 text-amber-600" />
					You can't apply yet
				</h2>
				<ul class="list-inside list-disc space-y-1 text-sm text-ink">
					<li v-for="(blocker, i) in context.blockers" :key="i">{{ blocker }}</li>
				</ul>
			</div>

			<form v-else class="space-y-4 rounded-xl border border-gray-200 p-6" @submit.prevent="submit">
				<div>
					<label class="mb-1 block text-sm font-medium text-ink">Cover letter (optional)</label>
					<textarea
						v-model="coverLetter"
						rows="6"
						class="w-full rounded-md border border-gray-200 px-3 py-2 text-sm"
						placeholder="Tell us why you're a good fit for this role..."
					></textarea>
				</div>
				<p v-if="submitError" class="text-sm text-red-600">{{ submitError }}</p>
				<button
					type="submit"
					:disabled="submitting"
					class="rounded-md bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
				>
					{{ submitting ? "Submitting..." : "Submit application" }}
				</button>
			</form>
		</div>
	</div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import call from "../../lib/call";
import { closesLabel } from "../../lib/dates";
import InfoIcon from "../../components/icons/InfoIcon.vue";

const route = useRoute();
const router = useRouter();

const jobOpening = computed(() => route.query.job_title || "");

const loaded = ref(false);
const loadError = ref("");
const context = ref(null);

const coverLetter = ref("");
const submitting = ref(false);
const submitError = ref("");

const closesOn = computed(() => (context.value ? closesLabel(context.value.job_opening.closes_on) : null));

onMounted(async () => {
	if (!jobOpening.value) return;
	try {
		const res = await call("gdl.api.applicant.get_apply_context", { job_opening: jobOpening.value });
		context.value = res?.data || null;
	} catch (err) {
		loadError.value = err.messages?.[0] || "This vacancy is not open for applications.";
	} finally {
		loaded.value = true;
	}
});

async function submit() {
	submitting.value = true;
	submitError.value = "";
	try {
		const res = await call("gdl.api.applicant.submit_application", {
			job_opening: jobOpening.value,
			cover_letter: coverLetter.value,
		});
		if (res.success) {
			router.push("/applications");
		} else {
			submitError.value = res.message || "Could not submit application.";
		}
	} catch (err) {
		submitError.value = err.messages?.[0] || "Something went wrong. Please try again.";
	} finally {
		submitting.value = false;
	}
}
</script>
