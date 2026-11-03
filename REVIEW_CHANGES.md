# Revision 9 — one saved row per field

Addresses the next-fixes review at 32260a9. The 308-test sample catalog, existing storage key, one-row-per-test worklist, and separate choose/save/approve/download steps are retained.

1. Saved fields appear once under Ready for approval, Approved, or Your saved choices. Each row shows In OLSD now and After import/Kept, the note, and one Change button. Approve follows the rows. Edit and Send back are removed from this saved section; Send back remains on the To approve list. Other fields omits fields already displayed above.
2. Matched exported changes show Confirmed in OLSD with the snapshot date and no Change button. Edit can start a new change requiring approval. Confirmation remains a dated observation, not proof of live publication.
3. Change cards replace the saved row. Cancel restores that field, preserving other unsaved work. Accepted navigation away closes reopened cards. The heading uses the field name directly.
4. Saved wording equal to Epic no longer creates a duplicate third card or suppresses normal inline choices.
5. Any open field can offer Keep my saved wording when its saved value differs from both Epic and OLSD. This survives reload after an OLSD update. The note says You saved; Epic context appears only for a real Epic value change.
6. Walk endings count both saved tests and tests still needing a choice. Save and finish does not duplicate Save and exit.
7. Opening a row carries its staged choice into the editor without a dialog only when it is the sole unsaved test. Other cases retain the save/discard warning.
8. Lab fields use a central-management note for editors and a Lab mappings link for administrators. Set-aside fields use Decide now without an extra Review now link. Navigation buttons say Go to approvals/downloads. Kept summaries include Epic's value; Set aside appears only once per list row.

Each requested item 1–5 has a browser regression case. Additional cases cover skipped walks, staged-choice carry-over, navigation warnings, and the smaller wording/role controls. Prior grouping, saved-choice editing, approval warning, source invalidation, Excel, focus, back-link, and phone checks remain. See verification.json for the full-suite result and exact tested source/test hashes.

Release validation: 336 browser checks passed, with no JavaScript errors. Measured save/single-download/32-name paths remain 2/5/7 clicks.
