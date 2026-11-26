/* Shared page logic for state paycheck calculator pages */
(function () {
  "use strict";
  var $ = function (id) { return document.getElementById(id); };

  function run() {
    var salary = parseFloat(($("salary").value || "").replace(/[^0-9.]/g, "")) || 0;
    var status = $("status").value;
    var k401 = parseFloat($("k401").value) || 0;
    var freq = $("freq").value;
    var periods = { weekly: 52, biweekly: 26, semimonthly: 24, monthly: 12 }[freq];

    var r = PN.calc({ gross: salary, status: status, state: window.STATE, k401Pct: k401 });

    $("r-net-year").textContent = PN.money0(r.net);
    $("r-net-check").textContent = PN.money(r.net / periods);
    $("r-gross").textContent = PN.money0(r.gross);
    $("r-fed").textContent = PN.money0(r.fed);
    $("r-state").textContent = PN.money0(r.state);
    $("r-ss").textContent = PN.money0(r.ss);
    $("r-med").textContent = PN.money0(r.medicare);
    $("r-401k").textContent = PN.money0(r.k401);
    $("r-total").textContent = PN.money0(r.total);
    $("r-pct").textContent = (r.takeHomePct * 100).toFixed(1) + "%";
    $("r-eff").textContent = (r.gross > 0 ? (r.fed / r.gross * 100) : 0).toFixed(1) + "%";
    $("r-period-label").textContent = { weekly: "per week", biweekly: "per paycheck (every 2 weeks)", semimonthly: "per paycheck (twice a month)", monthly: "per month" }[freq];

    $("results").classList.add("show");
  }

  document.addEventListener("DOMContentLoaded", function () {
    $("calc-btn").addEventListener("click", run);
    ["salary", "status", "k401", "freq"].forEach(function (id) {
      $(id).addEventListener("change", run);
      $(id).addEventListener("input", run);
    });
  });
})();
