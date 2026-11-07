export default function Panel({ title, children }) {
  return (
    <section className="panel-shell" aria-label={title}>
      <div className="panel">
        <h2>{title}</h2>
        <div className="panel-body">{children}</div>
      </div>
    </section>
  );
}
