# Independent-review changes

## Wrong results (browser regressions 1–11)

1. Approval requires explicit decisions; it never invents Use Epic. The approval dialog shows all three values and records the exact source basis.
2. Group review includes open Epic differences even if OLSD and proposed match. Boxes start unticked, the button counts chosen approvals, and already approved records cannot be reapproved.
3. Open source changes and mapping blockers are independent of selected export columns.
4. Discard restores the working copy on role-switch and reset routes; Stay restores the visible role selection.
5. Unsaved approved edits disable downloading and explain that saving withdraws approval.
6. Exported and Confirmed in snapshot states show dates/files; Ready to export excludes downloaded revisions. Progress follows the actual stage.
7. An export record is created per file only when its download action is used. Merely opening/closing a chooser creates no record.
8. Each draft/approval captures its source basis. Unexpected OLSD or Epic changes preserve drafts, invalidate affected approvals, and return fields to review, including unselected fields. An expected match to an exported value is recorded as observed confirmation.
9. Keep current OLSD value uses current observed OLSD. Use my wording is explicit; typing selects it and retained custom differences remain discoverable.
10. Performing-laboratory line breaks are preserved.
11. Needs a decision, Decided, Approved changes, and Other fields are separate. Keep choices stay visible. Mapping saves report approval only when something was approved.

Item 12 was absent by request.

## Usability (13–20)

Global search includes all statuses and clears hidden selections. Edit actions include the field. The nightly summary, change/lab filters, sorting, and paging operate on 306 sample records. Added/removed text is highlighted in comparisons, group review, approval, and exact unsaved-change dialogs. Optional decision notes, per-test history, and prior-kept source context are visible. Pure keeps finish on save. Blocked editors can note a clearly simulated administrator request. Mapping changes appear in the table and have a return link. Notifications appear away from the action bar.

## Wording and accessibility (21–29)

Removed promotional copy and developer terms. Use consistent Demo editor/administrator labels, full time-zone dates, age, and overdue indicators. Restore focus after rendering and dialogs. Comparisons use real table semantics; one live region reports feedback. Worklist filters use plain buttons. Essential small text and contrast were improved. Category removal cancellation, expanded category choices, URL navigation/Back/refresh, and mobile role/reset controls are covered by browser tests.

## Documentation and limits

The reviewer guide includes a glossary, Reset demo first, exact CBCND identity, explicit saving/discard instructions, phone controls, and a category-reconciliation scenario. Verification includes a date, the exact tested code commit, test-script URL, and file hashes. Production gaps explicitly include vendor control-column handling and approval source snapshots.

The sample-data banner, visual design, exact unsaved-value comparison, prominent blocker position, deliberate name editing, named Excel downloads, approval/publication distinction, snapshot observation limits, and category-removal explanation remain.
