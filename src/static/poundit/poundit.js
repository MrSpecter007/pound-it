/* Progressive enhancement. Navigation and all schedule days work without JS. */
(() => {
  'use strict';
  const toggle = document.querySelector('.pi-menu-toggle');
  const nav = document.getElementById('primary-navigation');
  const mobile = window.matchMedia('(max-width: 800px)');

  if (toggle && nav) {
    const closeGroups = () => nav.querySelectorAll('details[open]').forEach(group => { group.open = false; });
    const setOpen = (open, restoreFocus = false) => {
      toggle.setAttribute('aria-expanded', String(open));
      nav.hidden = mobile.matches && !open;
      if (!open) closeGroups();
      if (restoreFocus) toggle.focus();
    };
    const syncViewport = () => {
      const focusWillHide = mobile.matches && nav.contains(document.activeElement);
      toggle.hidden = !mobile.matches;
      setOpen(false, focusWillHide);
    };
    syncViewport();
    mobile.addEventListener('change', syncViewport);
    toggle.addEventListener('click', () => setOpen(toggle.getAttribute('aria-expanded') !== 'true'));
    nav.addEventListener('click', event => {
      if (event.target.closest('a') && mobile.matches) setOpen(false, true);
    });
    nav.querySelectorAll('details').forEach(group => {
      group.addEventListener('toggle', () => {
        if (group.open) nav.querySelectorAll('details[open]').forEach(other => { if (other !== group) other.open = false; });
      });
    });
    document.addEventListener('keydown', event => {
      if (event.key !== 'Escape') return;
      if (mobile.matches && toggle.getAttribute('aria-expanded') === 'true') {
        setOpen(false, true);
      } else {
        const openGroup = nav.querySelector('details[open]');
        if (openGroup) { openGroup.open = false; openGroup.querySelector('summary').focus(); }
      }
    });
    document.addEventListener('click', event => {
      if (!nav.contains(event.target) && !toggle.contains(event.target)) setOpen(false);
    });
  }

  document.querySelectorAll('[data-schedule]').forEach(schedule => {
    const select = schedule.querySelector('[data-day-filter]');
    const filters = schedule.querySelector('.pi-schedule__filters');
    const days = [...schedule.querySelectorAll('[data-day]')];
    const status = schedule.querySelector('[data-schedule-status]');
    if (!select || !filters || !days.length) return;
    filters.hidden = false;
    const filterDays = () => {
      days.forEach(day => { day.hidden = select.value !== 'all' && day.dataset.day !== select.value; });
      const visibleDays = days.filter(day => !day.hidden);
      const classCount = visibleDays.reduce((count, day) => count + day.querySelectorAll('.pi-session').length, 0);
      status.textContent = `${select.selectedOptions[0].textContent}: ${classCount} ${classCount === 1 ? 'class' : 'classes'} shown.`;
    };
    select.addEventListener('change', filterDays);
    // Keep both studios in view; all days remain available without JavaScript.
    select.value = days[0].dataset.day;
    filterDays();
  });

  const errors = document.querySelector('.pi-form-errors');
  if (errors) errors.focus();
})();
