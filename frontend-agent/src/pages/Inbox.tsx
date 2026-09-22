import { useEffect, useState } from "react";
import { getJSON, postJSON } from "../api/client";
import type { InboxMessageOut } from "../api/types";

export default function Inbox() {
  const [messages, setMessages] = useState<InboxMessageOut[]>([]);
  const [openId, setOpenId] = useState<number | null>(null);

  const refresh = () => {
    getJSON<InboxMessageOut[]>("/inbox/messages").then(setMessages);
  };

  useEffect(() => {
    refresh();
  }, []);

  const open = async (id: number) => {
    setOpenId(id);
    const message = messages.find((m) => m.id === id);
    if (message && !message.is_read) {
      await postJSON(`/inbox/messages/${id}/read`, {});
      refresh();
    }
  };

  const openMessage = messages.find((m) => m.id === openId) ?? null;

  return (
    <div data-testid="page-inbox">
      <h2>Inbox</h2>
      {messages.length === 0 && <p className="muted">No messages.</p>}
      <table className="data-table">
        <tbody>
          {messages.map((m) => (
            <tr
              key={m.id}
              data-testid={`inbox-message-${m.id}`}
              onClick={() => open(m.id)}
              style={{ cursor: "pointer", fontWeight: m.is_read ? "normal" : "bold" }}
            >
              <td>{m.is_read ? "" : "●"}</td>
              <td>{m.sender}</td>
              <td>{m.subject}</td>
              <td className="muted">Day {m.day}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {openMessage && (
        <section className="card" data-testid="inbox-message-detail">
          <h3>{openMessage.subject}</h3>
          <p className="muted">
            From: {openMessage.sender} · Day {openMessage.day}
          </p>
          <p data-testid="inbox-message-body">{openMessage.body}</p>
        </section>
      )}
    </div>
  );
}
