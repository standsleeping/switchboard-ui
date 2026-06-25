/* Modal adapter: open a focus-trapping <dialog> from its trigger.
 *
 * Opening uses the native dialog.showModal(), so the browser owns the top layer,
 * the ::backdrop scrim, the focus trap, Esc-to-close, and the inert background;
 * this adapter only wires the open button, the close button, and an optional bus
 * echo of {open: bool}. Every close path (Esc or the close button) funnels through
 * the dialog's native `close` event, where aria-expanded is reset and the close is
 * echoed once. Dismissal is deliberately not a backdrop click, so the modal is not
 * lost to an accidental outside click. */
window.switchboard.register("modal", function (el, props, bus) {
  var topic = props.topic || null;
  var trigger = el.querySelector(".sb-modal-trigger");
  var dialog = el.querySelector(".sb-modal-dialog");
  var closeBtn = el.querySelector(".sb-modal-close");

  function onOpen() {
    dialog.showModal();
    trigger.setAttribute("aria-expanded", "true");
    if (topic) bus.publish(topic, { open: true });
  }

  function onClose() {
    trigger.setAttribute("aria-expanded", "false");
    if (topic) bus.publish(topic, { open: false });
  }

  function onCloseClick() {
    dialog.close();
  }

  trigger.addEventListener("click", onOpen);
  closeBtn.addEventListener("click", onCloseClick);
  dialog.addEventListener("close", onClose);

  return function teardown() {
    trigger.removeEventListener("click", onOpen);
    closeBtn.removeEventListener("click", onCloseClick);
    dialog.removeEventListener("close", onClose);
    if (dialog.open) dialog.close();
  };
});
