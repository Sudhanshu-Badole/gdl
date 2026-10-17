<template>
	<div v-if="loaded && applicant">
		<h1 class="text-2xl font-bold text-ink">My profile</h1>
		<p class="mt-1 text-sm text-body">Keep your profile up to date - it is snapshotted each time you apply.</p>

		<div class="mt-6 grid gap-6 lg:grid-cols-3">
			<div class="space-y-6 lg:col-span-1">
				<ProfileCompletenessCard
					:completeness="applicant.gdl_profile_completeness || 0"
					:applicant="applicant"
					@continue="scrollToSection"
				/>
			</div>

			<div class="space-y-6 lg:col-span-2">
				<PhotoCard :photo-url="applicant.gdl_profile_photo" @uploaded="reload" />
				<PersonalInfoSection :applicant="applicant" @saved="reload" />
				<DocumentUploadCard
					title="CID / National ID"
					description="Upload one PDF with the front and back of your CID clearly visible."
					accept="application/pdf"
					hint="PDF only"
					:required="true"
					:file-url="applicant.gdl_national_id"
					upload-method="gdl.api.applicant.upload_national_id"
					v-bind="docStatus('national_id')"
					@uploaded="reload"
				/>
				<DocumentUploadCard
					title="Medical Certificate"
					:required="true"
					:file-url="applicant.custom_medical_certificate"
					upload-method="gdl.api.applicant.upload_medical_certificate"
					v-bind="docStatus('medical_certificate')"
					@uploaded="reload"
				/>
				<DocumentUploadCard
					title="Security Clearance"
					:required="true"
					:file-url="applicant.custom_security_clearance"
					upload-method="gdl.api.applicant.upload_security_clearance"
					v-bind="docStatus('security_clearance')"
					@uploaded="reload"
				/>
				<EducationSection
					:rows="applicant.gdl_education || []"
					:academic-certificate-url="applicant.gdl_academic_certificate"
					:doc-status="docStatus('academic_certificate')"
					@changed="reload"
				/>
				<EmploymentSection
					:rows="applicant.gdl_employment_history || []"
					:experience-letter-url="applicant.gdl_experience_letter"
					:doc-status="docStatus('experience_letter')"
					@changed="reload"
				/>
				<DocumentsSection :applicant="applicant" @changed="reload" />
			</div>
		</div>
	</div>

	<p v-else-if="loaded" class="text-sm text-body">{{ error }}</p>

	<div v-else class="space-y-4">
		<div class="h-8 w-64 animate-pulse rounded bg-gray-100"></div>
		<div class="h-40 animate-pulse rounded-xl bg-gray-100"></div>
	</div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import call from "../../lib/call";
import ProfileCompletenessCard from "../../components/applicant/ProfileCompletenessCard.vue";
import PhotoCard from "../../components/applicant/PhotoCard.vue";
import PersonalInfoSection from "../../components/applicant/PersonalInfoSection.vue";
import DocumentUploadCard from "../../components/applicant/DocumentUploadCard.vue";
import EducationSection from "../../components/applicant/EducationSection.vue";
import EmploymentSection from "../../components/applicant/EmploymentSection.vue";
import DocumentsSection from "../../components/applicant/DocumentsSection.vue";

const applicant = ref(null);
const loaded = ref(false);
const error = ref("");

function docStatus(key) {
	const row = applicant.value?.custom_document_verifications?.find((r) => r.document_key === key);
	return { status: row?.status || "Submitted", remark: row?.remark || null };
}

async function reload() {
	try {
		const res = await call("gdl.api.applicant.get_profile");
		if (res.success) {
			applicant.value = res.data;
		} else {
			error.value = res.message || "Could not load profile.";
		}
	} catch (err) {
		error.value = err.messages?.[0] || "Could not load profile.";
	} finally {
		loaded.value = true;
	}
}

function scrollToSection(anchor) {
	document.getElementById(anchor)?.scrollIntoView({ behavior: "smooth", block: "start" });
}

onMounted(reload);
</script>
