// Client feedback (Phase 2, HR-f): "Exam" should read as "Test" everywhere a
// user sees it. This is a display-only relabel - Job Application.status,
// Exam/Exam Attempt/Exam Question doctype names, and every gdl.api.hr_exam
// function/route stay "Exam" internally (see the plan's rationale: renaming
// the stored status vocabulary needs a data migration across every function
// that branches on those literal strings, for a client ask that's purely
// about on-screen wording).
export function displayStatus(status) {
	if (!status) return status;
	return status.replace(/\bExam\b/g, "Test");
}
