export default function PageControls({ pages, selected, onChange, label }) {
  function step(direction) {
    onChange((selected + direction + pages.length) % pages.length);
  }
  return (
    <nav className="page-controls" aria-label={label}>
      <button aria-label={"Previous " + label} onClick={() => step(-1)}>
        ◀
      </button>
      <div className="page-dots">
        {pages.map((page, index) => (
          <button
            key={page}
            className={index === selected ? "dot active" : "dot"}
            aria-label={page}
            aria-current={index === selected ? "page" : undefined}
            onClick={() => onChange(index)}
          />
        ))}
      </div>
      <button aria-label={"Next " + label} onClick={() => step(1)}>
        ▶
      </button>
    </nav>
  );
}
