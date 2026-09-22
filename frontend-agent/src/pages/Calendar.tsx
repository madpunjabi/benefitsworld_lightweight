import { useEffect, useState } from "react";
import { getJSON } from "../api/client";
import type { CalendarEventOut } from "../api/types";

export default function Calendar() {
  const [events, setEvents] = useState<CalendarEventOut[]>([]);

  useEffect(() => {
    getJSON<CalendarEventOut[]>("/calendar/events").then(setEvents);
  }, []);

  const byDay = new Map<number, CalendarEventOut[]>();
  for (const event of events) {
    byDay.set(event.day, [...(byDay.get(event.day) ?? []), event]);
  }
  const days = [...byDay.keys()].sort((a, b) => a - b);

  return (
    <div data-testid="page-calendar">
      <h2>Household Calendar</h2>
      {events.length === 0 && <p className="muted">No appointments on file.</p>}
      {days.map((day) => (
        <section className="card" key={day} data-testid={`calendar-day-${day}`}>
          <h3>Day {day}</h3>
          <table className="data-table">
            <tbody>
              {byDay.get(day)!.map((event, idx) => (
                <tr key={idx}>
                  <td>
                    {event.start_time}–{event.end_time}
                  </td>
                  <td>{event.label}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ))}
    </div>
  );
}
