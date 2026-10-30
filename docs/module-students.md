# Module student profiles

Every registered module page automatically receives a student attribution card from the shared base template and catalogue context processor. The card provides a name, short biography and portrait space, with accessible placeholders when details are missing. Catalogue and non-module pages do not receive it.

Approved content lives in `apps/core/module_students.py`. Add `bio` and a `portrait` path relative to `static/` for each route. Portraits should be supplied with the student's approval; add the image under `static/images/students/` and set the corresponding local path. Django escapes all text. No remote tracking image or fabricated biography is used. Portraits are cropped to 4:5 with object-fit; mobile cards stack vertically.

Full names currently documented: David Amachie (ECT), Edward Selorm (motor drive), Lawrence Andoh (P2), Abass Moro (microhybrid, earlier uploaded model filename). Partial source names: Bless (FCEV), Bernard (battery energy), Desmond (series-parallel). Full names for these and names for the remaining six modules await confirmation. Bless Kofi Atisu is documented as the platform project author; that does not establish ownership of the separate FCEV project, so the surname was not inferred.

All biographies and portraits await supplied content. This change adds presentation slots; it does not add an account-profile editor or alter identity records. Future modules automatically get the shared profile card; add attribution to the central mapping when confirmed.

Verification: `pytest tests/test_module_students.py` checks all registered routes and catalogue exclusion. `pytest -m e2e tests/e2e/test_module_students_ui.py` checks desktop/mobile rendering, no overflow and axe WCAG contrast/semantics.

Profile update, 30 October 2026: Emmanuel Yankson Sackey has name/module attribution only, with `show_bio=False` and `show_portrait=False`; the biography heading, text and portrait placeholder are omitted entirely. Lawrence Andoh's user-supplied biography appears verbatim on P2 Full-Parallel Hybrid. Ebenezer Wilson's supplied biography awaits a confirmed module association and is not attached to an inferred project.
