import { formatWhen } from "./ui";

function describe(event) {
  const data = event.data || {};
  switch (event.verb) {
    case "task.created":
      return `created task "${data.title}"`;
    case "task.moved":
      return `moved a task from ${data.from} to ${data.to}`;
    case "task.updated":
      return `updated ${Object.keys(data).join(", ")}`;
    case "task.commented":
      return `commented: ${data.body}`;
    case "report.created":
      return `filled a report for ${data.work_date} (${data.quantity})`;
    case "report.updated":
      return `updated a report for ${data.work_date} (${data.quantity})`;
    case "stock.received":
      return `received ${data.quantity} ${data.item} at ${data.location}`;
    case "stock.transfer":
      return `transferred ${data.quantity} ${data.item}`;
    case "stock.consume":
      return `used ${data.quantity} ${data.item}`;
    case "stock.adjust":
      return `adjusted ${data.item} by ${data.quantity}`;
    default:
      return event.verb;
  }
}

function ActivityList({ events, showProject = false }) {
  if (events.length === 0) return <p style={{ color: "var(--faint)" }}>No activity yet.</p>;
  return (
    <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "grid", gap: "0.5rem" }}>
      {events.map((event) => (
        <li key={event.id} style={{ fontSize: "0.9rem" }}>
          <strong>{event.actor_email || "Someone"}</strong> {describe(event)}
          {showProject && event.project_name ? ` · ${event.project_name}` : ""}
          <div style={{ color: "var(--faint)", fontSize: "0.78rem" }}>{formatWhen(event.created_at)}</div>
        </li>
      ))}
    </ul>
  );
}

export default ActivityList;
