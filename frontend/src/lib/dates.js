// closes_on is a Date field (no time-of-day), so this stays at day
// granularity ("today"/"tomorrow"/"N days ago"/plain date) rather than the
// hour-precision copy a live reference design might show - deliberate,
// since adding time-of-day to Job Opening is out of scope here.
export function closesLabel(closesOn) {
	if (!closesOn) return null;

	const closesDate = new Date(`${closesOn}T00:00:00`);
	const today = new Date();
	today.setHours(0, 0, 0, 0);
	const daysLeft = Math.round((closesDate - today) / 86400000);

	const formatted = closesDate.toLocaleDateString("en-GB", {
		day: "numeric",
		month: "short",
		year: "numeric",
	});

	if (daysLeft === 0) return `Closes ${formatted} (today)`;
	if (daysLeft === 1) return `Closes ${formatted} (tomorrow)`;
	if (daysLeft < 0) return `Closed ${formatted} (${Math.abs(daysLeft)} day${Math.abs(daysLeft) === 1 ? "" : "s"} ago)`;
	return `Closes ${formatted}`;
}
