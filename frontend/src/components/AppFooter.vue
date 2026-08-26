<template>
	<footer class="border-t border-gray-200 bg-gray-50">
		<div class="mx-auto grid max-w-7xl gap-10 px-6 py-12 sm:grid-cols-3">
			<div>
				<span class="text-xl font-extrabold tracking-tight text-brand-600">GDL</span>
				<p class="mt-3 max-w-xs text-sm text-body">
					GreenDigital Limited careers portal - apply online and track your recruitment
					journey from shortlist to appointment.
				</p>
			</div>

			<div>
				<h4 class="text-sm font-semibold text-ink">For applicants</h4>
				<ul class="mt-3 space-y-2 text-sm">
					<li><router-link to="/jobs" class="text-body hover:text-brand-600">Browse jobs</router-link></li>
					<li><router-link to="/register" class="text-body hover:text-brand-600">Register</router-link></li>
					<li><router-link to="/login" class="text-body hover:text-brand-600">Sign in</router-link></li>
				</ul>
			</div>

			<div>
				<h4 class="text-sm font-semibold text-ink">Contact</h4>
				<ul class="mt-3 space-y-2 text-sm">
					<li><a href="mailto:gdl@gdl.bt" class="text-body hover:text-brand-600">gdl@gdl.bt</a></li>
					<li><span class="text-body">Recruitment support</span></li>
				</ul>
			</div>
		</div>

		<div class="border-t border-gray-200">
			<div class="mx-auto flex max-w-7xl flex-col gap-2 px-6 py-4 text-xs text-body sm:flex-row sm:items-center sm:justify-between">
				<span>&copy; {{ year }} GreenDigital Limited. All rights reserved.</span>
				<span>e-Recruitment platform</span>
			</div>
		</div>
	</footer>
</template>

<script setup>
const year = new Date().getFullYear();
</script>
