import { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";

function Counter({ bus, start }) {
  const [count, setCount] = useState(start);

  // The click is the cause, so the publish lives in the handler. Publishing
  // from inside the state updater would be wrong: updaters must be pure, and
  // React may run them more than once (StrictMode, concurrent renders).
  function increment() {
    const next = count + 1;
    setCount(next);
    bus.publish("react:count", next);
  }

  return (
    <div className="sb-demo-pad">
      <button className="sb-demo-btn" type="button" onClick={increment}>
        count: {count}
      </button>
    </div>
  );
}

function Readout({ bus }) {
  const [message, setMessage] = useState("waiting for a click...");

  // Subscribing is a synchronization concern, so it lives in an effect that
  // returns bus.subscribe's unsubscribe as cleanup. The cleanup is what makes
  // this safe under StrictMode and on unmount.
  useEffect(
    () =>
      bus.subscribe("react:count", (count) => {
        setMessage("latest count: " + count);
      }),
    [bus],
  );

  return <div className="sb-demo-readout">{message}</div>;
}

window.switchboard.register("react-counter", (el, props, bus) => {
  const root = createRoot(el);
  root.render(<Counter bus={bus} start={props.start || 0} />);
  return () => root.unmount();
});

window.switchboard.register("react-readout", (el, props, bus) => {
  const root = createRoot(el);
  root.render(<Readout bus={bus} />);
  return () => root.unmount();
});
