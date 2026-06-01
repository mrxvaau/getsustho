import dayjs from 'dayjs';

const dayIndex = { SUN: 0, MON: 1, TUE: 2, WED: 3, THU: 4, FRI: 5, SAT: 6 };

export function nextAvailableDate(schedule, bookedCount = 0) {
  const target = dayIndex[schedule.day_code];
  if (target === undefined) return null;

  let cursor = dayjs().startOf('day');
  for (let i = 0; i < 60; i += 1) {
    if (cursor.day() === target && bookedCount < schedule.max_patients) {
      return cursor.format('YYYY-MM-DD');
    }
    cursor = cursor.add(1, 'day');
  }
  return null;
}

export function formatDate(value) {
  return value ? dayjs(value).format('MMM D, YYYY') : '';
}
