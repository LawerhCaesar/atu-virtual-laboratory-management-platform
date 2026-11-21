/* ATU academic choices and index guidance; the server validates every selection. */
(() => {
  const form = document.getElementById('registration-form');
  if (!form) return;
  const field = name => document.getElementById('id_' + name);
  const course = field('qualification'), index = field('index_number'), role = field('role');
  const faculty = field('faculty'), department = field('department'), programme = field('programme');
  const status = document.getElementById('registration-index-status');
  const programmeStatus = document.getElementById('registration-programme-status');
  const catalogue = JSON.parse(document.getElementById('registration-academic-catalogue').textContent);
  const suffixes = {HND: 'D', BTECH: 'B', MTECH: 'M'};
  let previous = course.value;
  index.closest('.atu-form-field').append(status);
  index.setAttribute('aria-describedby', ((index.getAttribute('aria-describedby') || '') + ' ' + status.id).trim());
  programme.closest('.atu-form-field').append(programmeStatus);
  programme.setAttribute('aria-describedby', ((programme.getAttribute('aria-describedby') || '') + ' ' + programmeStatus.id).trim());

  function replaceOptions(select, items, placeholder) {
    const selected = select.value;
    select.replaceChildren(new Option(placeholder, ''));
    for (const item of items) {
      const label = item.name + (item.aliases?.length ? ' — also listed as ' + item.aliases.join(', ') : '') +
        (item.department_confirmed === false ? ' (department confirmation needed)' : '');
      select.append(new Option(label, item.id));
    }
    if (items.some(item => item.id === selected)) select.value = selected;
  }

  function updateAcademics() {
    const student = role.value === 'STUDENT';
    replaceOptions(department, catalogue.departments.filter(d => d.faculty === faculty.value),
      faculty.value ? 'Select your department' : 'Select your faculty first');
    department.disabled = !faculty.value;
    const choices = catalogue.programmes.filter(p =>
      faculty.value && department.value && course.value &&
      (!course.value || p.qualification === course.value) &&
      (!faculty.value || !p.faculty || p.faculty === faculty.value) &&
      (!department.value || !p.department || p.department === department.value));
    replaceOptions(programme, choices, 'Select your programme');
    programme.disabled = !student || !faculty.value || !department.value || !course.value;
    programme.required = student;
    programme.closest('.atu-form-field').hidden = !student;
    const selected = choices.find(p => p.id === programme.value);
    programmeStatus.textContent = !student ? 'Choose the faculty and department where you teach.' :
      selected?.department_confirmed === false ?
        'ATU lists this programme, but its department needs confirmation. An administrator will check your selection.' :
      selected ? 'Your selection will be reviewed before your account is activated.' :
      !faculty.value ? 'Choose your faculty or school, then your department and programme.' :
      !course.value ? 'Choose your course level to see matching programmes.' :
      'Choose your programme from the matching ' + course.value + ' options.';
  }

  function updateIndex(courseChanged = false) {
    const student = role.value === 'STUDENT', suffix = suffixes[course.value];
    for (const control of [course, index]) {
      control.disabled = !student;
      control.required = student;
      control.closest('.atu-form-field').hidden = !student;
    }
    if (!student) { index.setCustomValidity(''); status.hidden = true; return; }
    status.hidden = false;
    const uppercase = index.value.replace(/[a-z]/g, c => c.toUpperCase());
    if (index.value !== uppercase) {
      const start = index.selectionStart, end = index.selectionEnd;
      index.value = uppercase; index.setSelectionRange(start, end);
    }
    if (courseChanged && suffix && /^[0-9]{8}[DBM]$/.test(index.value)) {
      index.value = index.value.slice(0, 8) + suffix;
      status.textContent = 'Course changed: your index ending is now ' + suffix + '. ';
    } else status.textContent = '';
    index.placeholder = suffix ? '01181429' + suffix : 'Select a course first';
    index.pattern = suffix ? '[0-9]{8}' + suffix : '[0-9]{8}[DBM]';
    const valid = suffix && new RegExp('^[0-9]{8}' + suffix + '$').test(index.value);
    index.setCustomValidity(index.value && !valid ? 'Use exactly 8 digits followed by ' + (suffix || 'the letter for your selected course') + '.' : '');
    status.textContent += (suffix ? course.value + ' uses 8 digits followed by ' + suffix + '. ' : 'Choose HND, BTECH or MTECH. ') + index.value.length + '/9 characters.';
  }
  course.addEventListener('change', () => { updateIndex(previous !== course.value); previous = course.value; updateAcademics(); });
  role.addEventListener('change', () => { updateIndex(); updateAcademics(); });
  faculty.addEventListener('change', updateAcademics);
  department.addEventListener('change', updateAcademics);
  programme.addEventListener('change', updateAcademics);
  index.addEventListener('input', () => updateIndex());
  updateIndex(); updateAcademics();
})();
