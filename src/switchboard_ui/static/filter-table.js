/* Filter-table adapter: narrow and reorder a server-rendered table over the bus.
 *
 * The whole table is rendered on the server and every row stays in the DOM; this
 * adapter only hides and reorders, so the page works without it and nothing is
 * fetched to filter. The controls in the bar are ordinary islands publishing on
 * their own topics — the wiring crosses the bus, so the analyzer sees it
 * statically and neither side holds a reference to the other.
 *
 * Filtering matches each row's key (props.keys, aligned with the original tbody
 * row order) against the published value: `substring` lowercases and trims both
 * and asks for containment, `exact` compares as-is. The reserved props.allValue
 * (the empty string by default) restores every row and clears the count.
 *
 * Sorting reads props.sortKeys under the same alignment and reorders the rows in
 * place: "asc" and "desc" sort by key with the original index breaking ties, and
 * the reserved "none" restores the server's order. Hidden state and DOM order are
 * independent properties of a row, so filtering and sorting compose in either
 * order without either having to know about the other. */
window.switchboard.register("filter-table", function (el, props, bus) {
  var rows = Array.prototype.slice.call(el.querySelectorAll("tbody tr"));
  var keys = props.keys || [];
  var sortKeys = props.sortKeys || [];
  var allValue = props.allValue || "";
  var exact = props.match === "exact";
  var count = el.querySelector(".sb-filter-count");
  var body = rows.length ? rows[0].parentNode : null;

  function applyFilter(value) {
    var query = exact ? value : String(value).trim().toLowerCase();
    var reset = query === allValue;
    var shown = 0;
    rows.forEach(function (row, index) {
      var key = keys[index] || "";
      var match = reset || (exact ? key === query : key.indexOf(query) !== -1);
      row.hidden = !match;
      if (match) shown += 1;
    });
    if (count) count.textContent = reset ? "" : shown + " shown";
  }

  function applySort(mode) {
    if (!body) return;
    var order = rows.map(function (row, index) {
      return { row: row, index: index };
    });
    if (mode === "asc" || mode === "desc") {
      order.sort(function (a, b) {
        var left = sortKeys[a.index] || "";
        var right = sortKeys[b.index] || "";
        if (left === right) return a.index - b.index;
        var cmp = left < right ? -1 : 1;
        return mode === "desc" ? -cmp : cmp;
      });
    }
    order.forEach(function (entry) {
      body.appendChild(entry.row);
    });
  }

  var offFilter = bus.subscribe(props.topic, function (value) {
    if (typeof value === "string") applyFilter(value);
  });

  var offSort = null;
  if (props.sortTopic) {
    offSort = bus.subscribe(props.sortTopic, function (value) {
      if (typeof value === "string") applySort(value);
    });
  }

  return function teardown() {
    offFilter();
    if (offSort) offSort();
  };
});
