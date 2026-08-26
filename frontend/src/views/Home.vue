<template>
	<div>
		<!-- Hero -->
		<section class="bg-gradient-to-b from-brand-50 to-white">
			<div class="mx-auto grid max-w-7xl gap-10 px-6 py-16 lg:grid-cols-2 lg:items-center lg:py-24">
				<div>
					<span class="mb-4 inline-flex items-center gap-1.5 rounded-full bg-brand-100 px-3 py-1 text-xs font-semibold text-brand-700">
						<SparkleIcon class="h-3.5 w-3.5" />
						{{ openCount }} open position{{ openCount === 1 ? "" : "s" }}
					</span>

					<h1 class="text-4xl font-extrabold leading-tight text-ink sm:text-5xl">
						Grow your career with
						<span class="text-brand-600">GreenDigital Limited</span>
					</h1>

					<p class="mt-4 max-w-xl text-body">
						Register once, get your documents verified by HR, and apply online to roles that
						match your skills. Track your journey from application to appointment in one place.
					</p>

					<ul class="mt-6 grid gap-2 sm:grid-cols-2">
						<li v-for="item in checklist" :key="item" class="flex items-center gap-2 text-sm text-body">
							<CheckCircleIcon class="h-4 w-4 shrink-0 text-brand-600" />
							{{ item }}
						</li>
					</ul>

					<div class="mt-8 flex flex-wrap items-center gap-3">
						<router-link
							to="/jobs"
							class="inline-flex items-center gap-2 rounded-md bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-700"
						>
							Browse open jobs
							<ArrowRightIcon class="h-4 w-4" />
						</router-link>
						<router-link
							to="/register"
							class="rounded-md border border-gray-300 px-5 py-2.5 text-sm font-semibold text-ink hover:border-brand-400"
						>
							Create applicant account
						</router-link>
					</div>
					<a :href="userGuideUrl" class="mt-4 inline-block text-sm font-medium text-ink hover:text-brand-600">
						User guide
					</a>

					<dl class="mt-10 grid grid-cols-3 gap-6 border-t border-gray-200 pt-6">
						<div>
							<dt class="text-2xl font-extrabold text-ink">{{ openCount }}</dt>
							<dd class="text-xs text-body">Open roles</dd>
						</div>
						<div>
							<dt class="text-2xl font-extrabold text-ink">2-3 days</dt>
							<dd class="text-xs text-body">Typical verification</dd>
						</div>
						<div>
							<dt class="text-2xl font-extrabold text-ink">100%</dt>
							<dd class="text-xs text-body">Online applications</dd>
						</div>
					</dl>
				</div>

				<div class="rounded-2xl border-t-4 border-brand-500 bg-white p-8 text-center shadow-lg shadow-brand-900/5">
					<div class="text-2xl font-extrabold tracking-tight text-brand-600">GDL</div>
					<p class="mt-6 text-xs font-semibold uppercase tracking-wide text-brand-600">New applicant?</p>
					<h3 class="mt-1 text-lg font-bold text-ink">Complete your profile first</h3>
					<p class="mt-3 text-sm text-body">
						Upload your CID and certificates, then allow 2-3 days (up to 5 business days) for HR
						verification before you apply.
					</p>
					<router-link
						to="/register"
						class="mt-6 block rounded-md bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-brand-700"
					>
						Get started
					</router-link>
					<a :href="userGuideUrl" class="mt-3 block text-sm font-medium text-brand-700 hover:text-brand-800">
						Read the full user guide
					</a>
				</div>
			</div>
		</section>

		<div class="mx-auto max-w-7xl px-6 py-12">
			<IntentionNotice />
		</div>

		<!-- Featured openings -->
		<section class="mx-auto max-w-7xl px-6 pb-16">
			<div class="mb-6 flex flex-wrap items-end justify-between gap-4">
				<div>
					<div class="mb-1 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-brand-600">
						<BriefcaseIcon class="h-4 w-4" />
						Latest opportunities
					</div>
					<h2 class="text-2xl font-bold text-ink">Featured openings</h2>
					<p class="mt-1 max-w-xl text-sm text-body">
						Review each role carefully and apply only when you are confident it is right for you.
						Deadlines and department details are shown on every listing.
					</p>
				</div>
				<router-link
					to="/jobs"
					class="inline-flex shrink-0 items-center gap-1.5 rounded-md border border-gray-300 px-4 py-2 text-sm font-semibold text-ink hover:border-brand-400"
				>
					View all {{ openCount }} job{{ openCount === 1 ? "" : "s" }}
					<ArrowRightIcon class="h-4 w-4" />
				</router-link>
			</div>

			<p v-if="loaded && !vacancies.length" class="text-sm text-body">
				No open vacancies right now - check back soon.
			</p>
			<div v-else class="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
				<VacancyCard v-for="v in vacancies" :key="v.name" :vacancy="v" />
			</div>
		</section>

		<!-- How it works -->
		<section class="bg-gray-50">
			<div class="mx-auto max-w-7xl px-6 py-16">
				<div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
					<div v-for="step in steps" :key="step.title" class="rounded-xl bg-white p-6">
						<span class="text-xs font-semibold uppercase tracking-wide text-brand-600">
							Step {{ step.number }}
						</span>
						<div class="my-3 flex h-10 w-10 items-center justify-center rounded-lg bg-brand-100 text-brand-700">
							<component :is="step.icon" class="h-5 w-5" />
						</div>
						<h3 class="mb-2 font-bold text-ink">{{ step.title }}</h3>
						<p class="text-sm text-body">{{ step.description }}</p>
					</div>
				</div>

				<div class="mt-8 flex flex-col items-start gap-4 rounded-xl bg-white p-6 sm:flex-row sm:items-center sm:justify-between">
					<div class="flex items-start gap-3">
						<div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-brand-100 text-brand-700">
							<ClipboardIcon class="h-5 w-5" />
						</div>
						<div>
							<h3 class="font-bold text-ink">Need more detail?</h3>
							<p class="text-sm text-body">
								The applicant user guide explains profiles, verification, applying, and tracking
								your recruitment stages.
							</p>
						</div>
					</div>
					<a
						:href="userGuideUrl"
						class="inline-flex shrink-0 items-center gap-1.5 rounded-md border border-gray-300 px-4 py-2 text-sm font-semibold text-ink hover:border-brand-400"
					>
						Open user guide
						<ArrowRightIcon class="h-4 w-4" />
					</a>
				</div>

				<div class="mt-8">
					<IntentionNotice />
				</div>
			</div>
		</section>

		<!-- Bottom CTA -->
		<section class="bg-gradient-to-br from-brand-600 to-brand-800">
			<div class="mx-auto max-w-3xl px-6 py-20 text-center text-white">
				<UsersIcon class="mx-auto mb-4 h-8 w-8" />
				<h2 class="text-3xl font-extrabold">Ready to take the next step?</h2>
				<p class="mx-auto mt-4 max-w-xl text-brand-50">
					Join GreenDigital Limited's talent pool. Build your profile, get verified, and apply
					thoughtfully to roles where you can succeed and grow.
				</p>
				<div class="mt-8 flex flex-wrap items-center justify-center gap-3">
					<router-link
						to="/register"
						class="rounded-md bg-white px-5 py-2.5 text-sm font-semibold text-brand-700 hover:bg-brand-50"
					>
						Register as applicant
					</router-link>
					<router-link
						to="/jobs"
						class="rounded-md border border-white/60 px-5 py-2.5 text-sm font-semibold text-white hover:bg-white/10"
					>
						Browse jobs
					</router-link>
					<a
						:href="userGuideUrl"
						class="rounded-md border border-white/60 px-5 py-2.5 text-sm font-semibold text-white hover:bg-white/10"
					>
						User guide
					</a>
				</div>
			</div>
		</section>
	</div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import call from "@doppio/controllers/call";

import IntentionNotice from "../components/IntentionNotice.vue";
import VacancyCard from "../components/VacancyCard.vue";
import SparkleIcon from "../components/icons/SparkleIcon.vue";
import CheckCircleIcon from "../components/icons/CheckCircleIcon.vue";
import ArrowRightIcon from "../components/icons/ArrowRightIcon.vue";
import BriefcaseIcon from "../components/icons/BriefcaseIcon.vue";
import ClipboardIcon from "../components/icons/ClipboardIcon.vue";
import UsersIcon from "../components/icons/UsersIcon.vue";
import GraduationCapIcon from "../components/icons/GraduationCapIcon.vue";
import DocCheckIcon from "../components/icons/DocCheckIcon.vue";
import SearchIcon from "../components/icons/SearchIcon.vue";
import TrophyIcon from "../components/icons/TrophyIcon.vue";

const userGuideUrl = "/how-to-apply";

const checklist = [
	"Step-by-step applicant user guide",
	"HR document verification with notifications",
	"Transparent recruitment stages",
	"Secure online applications",
];

const steps = [
	{
		number: "01",
		icon: GraduationCapIcon,
		title: "Register & complete your profile",
		description:
			"Create your account, verify your email if required, and add personal details, CID, education, and experience with PDF certificates.",
	},
	{
		number: "02",
		icon: DocCheckIcon,
		title: "HR verifies your documents",
		description:
			"Our team reviews your CID and certificates. This usually takes 2-3 days and may take up to 5 business days when volumes are high. We notify you when approved or if updates are needed.",
	},
	{
		number: "03",
		icon: SearchIcon,
		title: "Apply to the right roles",
		description:
			"Browse open vacancies and apply only to positions you genuinely want. Applications are final and cannot be withdrawn.",
	},
	{
		number: "04",
		icon: TrophyIcon,
		title: "Track every stage",
		description:
			"Follow shortlisting, exams, interviews, offers, and appointment from your dashboard with email and portal updates.",
	},
];

const vacancies = ref([]);
const openCount = ref(0);
const loaded = ref(false);

onMounted(async () => {
	try {
		const res = await call("gdl.api.public.get_home_vacancies");
		vacancies.value = res?.data?.vacancies || [];
		openCount.value = res?.data?.total || 0;
	} finally {
		loaded.value = true;
	}
});
</script>
