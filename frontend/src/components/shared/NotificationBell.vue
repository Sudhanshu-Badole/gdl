<template>
	<div class="relative" ref="root">
		<button
			type="button"
			class="relative flex h-9 w-9 items-center justify-center rounded-full text-body hover:bg-gray-50 hover:text-ink"
			@click="toggle"
		>
			<BellIcon class="h-5 w-5" />
			<span
				v-if="unreadCount"
				class="absolute right-0.5 top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-600 px-1 text-[10px] font-semibold leading-none text-white"
			>
				{{ unreadCount > 9 ? "9+" : unreadCount }}
			</span>
		</button>

		<div v-if="open" class="absolute right-0 z-10 mt-2 w-80 rounded-md border border-gray-200 bg-white shadow-lg">
			<div class="flex items-center justify-between border-b border-gray-100 px-4 py-3">
				<p class="text-sm font-semibold text-ink">Notifications</p>
				<button
					v-if="unreadCount"
					type="button"
					class="text-xs font-medium text-brand-700 hover:underline"
					@click="markAllRead"
				>
					Mark all as read
				</button>
			</div>
			<div class="max-h-96 overflow-y-auto">
				<p v-if="!logs.length" class="px-4 py-6 text-center text-sm text-body">You're all caught up.</p>
				<button
					v-for="log in logs"
					:key="log.name"
					type="button"
					class="flex w-full flex-col gap-0.5 border-b border-gray-50 px-4 py-3 text-left last:border-0 hover:bg-gray-50"
					:class="!log.read ? 'bg-brand-50/40' : ''"
					@click="openLog(log)"
				>
					<span class="text-sm text-ink" :class="!log.read ? 'font-semibold' : ''">{{ log.subject }}</span>
					<span class="text-xs text-body">{{ relativeTime(log.creation) }}</span>
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import call from "../../lib/call";
import BellIcon from "../icons/BellIcon.vue";

const router = useRouter();
const root = ref(null);
const open = ref(false);
const logs = ref([]);

const unreadCount = computed(() => logs.value.filter((l) => !l.read).length);

function relativeTime(value) {
	if (!value) return "";
	const then = new Date(value.replace(" ", "T"));
	const seconds = Math.round((Date.now() - then.getTime()) / 1000);
	if (seconds < 60) return "just now";
	const minutes = Math.round(seconds / 60);
	if (minutes < 60) return `${minutes}m ago`;
	const hours = Math.round(minutes / 60);
	if (hours < 24) return `${hours}h ago`;
	const days = Math.round(hours / 24);
	return `${days}d ago`;
}

async function loadLogs() {
	const res = await call("frappe.desk.doctype.notification_log.notification_log.get_notification_logs");
	logs.value = res?.notification_logs || [];
}

function toggle() {
	open.value = !open.value;
	if (open.value) loadLogs();
}

async function markAllRead() {
	await call("frappe.desk.doctype.notification_log.notification_log.mark_all_as_read");
	logs.value = logs.value.map((l) => ({ ...l, read: 1 }));
}

async function openLog(log) {
	if (!log.read) {
		await call("frappe.desk.doctype.notification_log.notification_log.mark_as_read", { docname: log.name });
		log.read = 1;
	}
	open.value = false;
	if (log.link) router.push(log.link);
}

function onClickOutside(e) {
	if (root.value && !root.value.contains(e.target)) open.value = false;
}

onMounted(() => {
	document.addEventListener("click", onClickOutside);
	loadLogs();
});
onUnmounted(() => document.removeEventListener("click", onClickOutside));
</script>
