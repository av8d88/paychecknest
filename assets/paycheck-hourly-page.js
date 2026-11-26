/* Shared page logic for state HOURLY paycheck calculator pages */
(function () {
  "use strict";
  var $ = function (id) { return document.getElementById(id); };

  function run() {
    var wage = parseFloat($("wage").value) || 0;
    var hours = parseFloat($("hours").value) || 40;
    var status = $("status").value;
    var k401 = parseFloat($("k401").value) || 0;
    var freq = $("freq").value;
    var periods = { weekly: 52, biweekly: 26, semimonthly: 24, monthly: 12 }[freq];

    var gross = wage * hours * 52;
    var r = PN.calc({ gross: gross, status: status, state: window.STATE, k401Pct: k401 });

    $("r-gross-year").textContent = PN.money0(gross);
    $("r-net-check").textContent = PN.money(r.net / periods);
    $("r-net-year").textContent = PN.money0(r.net);
    $("r-net-hour").textContent = "$" + (hours * 52 > 0 ? (r.net / (hours * 52)).toFixed(2) : "0.00");
    $("r-fed").textContent = PN.money0(r.fed);
    $("r-state").textContent = PN.money0(r.state);
    $("r-ss").textContent = PN.money0(r.ss);
    $("r-med").textContent = PN.money0(r.medicare);
    $("r-total").textContent = PN.money0(r.total + r.k401);
    $("r-pct").textContent = (r.takeHomePct * 100).toFixed(1) + "%";
    $("r-period-label").textContent = { weekly: "per week", biweekly: "per paycheck (every 2 weeks)", semimonthly: "per paycheck (twice a month)", monthly: "per month" }[freq];

    $("results").classList.add("show");
  }

  document.addEventListener("DOMContentLoaded", function () {
    $("calc-btn").addEventListener("click", run);
    ["wage", "hours", "status", "k401", "freq"].forEach(function (id) {
      $(id).addEventListener("change", run);
      $(id).addEventListener("input", run);
    });
  });
})();
