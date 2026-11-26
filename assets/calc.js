/* PaycheckNest calculation engine — 2026 tax year estimates */
(function (global) {
  "use strict";

  var FED_BRACKETS = {
    single: [[12400, .10], [50400, .12], [105700, .22], [201775, .24], [256225, .32], [640600, .35], [null, .37]],
    married: [[24800, .10], [100800, .12], [211400, .22], [403550, .24], [512450, .32], [768700, .35], [null, .37]],
    hoh: [[17700, .10], [67450, .12], [105700, .22], [201750, .24], [256200, .32], [640600, .35], [null, .37]]
  };
  var STD_DED = { single: 16100, married: 32200, hoh: 24150 };
  var SS_RATE = 0.062, SS_WAGE_BASE = 184500;
  var MED_RATE = 0.0145, MED_EXTRA = 0.009, MED_EXTRA_THRESHOLD = { single: 200000, married: 250000, hoh: 200000 };
  // OBBBA (2025-2028): above-the-line deductions
  var TIPS_DED_MAX = 25000;          // no tax on tips
  var OT_DED_MAX = { single: 12500, married: 25000, hoh: 12500 }; // no tax on overtime

  function progressive(taxable, brackets) {
    if (taxable <= 0) return 0;
    var tax = 0, lower = 0;
    for (var i = 0; i < brackets.length; i++) {
      var upper = brackets[i][0], rate = brackets[i][1];
      if (upper === null || taxable <= upper) {
        tax += (taxable - lower) * rate;
        return tax;
      }
      tax += (upper - lower) * rate;
      lower = upper;
    }
    return tax;
  }

  function stateTax(state, gross, filingStatus) {
    if (!state || state.type === "none") return 0;
    var taxable = Math.max(0, gross - (state.std || 0));
    if (state.type === "flat") return taxable * state.rate;
    return progressive(taxable, state.brackets);
  }

  // Annual paycheck breakdown.
  // opts: {gross, status, state, k401Pct, overtimePay, tips}
  function calc(opts) {
    var gross = opts.gross || 0;
    var status = opts.status || "single";
    var k401 = Math.min(Math.max(0, (opts.k401Pct || 0) / 100), 0.75) * gross;

    var agi = gross - k401;

    // OBBBA deductions (federal income tax only, not FICA)
    var otDed = Math.min(Math.max(0, opts.overtimePay || 0), OT_DED_MAX[status]);
    var tipsDed = Math.min(Math.max(0, opts.tips || 0), TIPS_DED_MAX);

    var taxable = Math.max(0, agi - STD_DED[status] - otDed - tipsDed);
    var fedTax = progressive(taxable, FED_BRACKETS[status]);

    var ss = Math.min(gross, SS_WAGE_BASE) * SS_RATE;
    var med = gross * MED_RATE;
    var extraMed = Math.max(0, gross - MED_EXTRA_THRESHOLD[status]) * MED_EXTRA;

    var stTax = stateTax(opts.state, agi, status);

    var total = fedTax + ss + med + extraMed + stTax;
    var net = gross - total - k401;

    return {
      gross: gross, k401: k401, agi: agi, taxable: taxable,
      fed: fedTax, ss: ss, medicare: med + extraMed,
      state: stTax, total: total, net: net,
      takeHomePct: gross > 0 ? net / gross : 0
    };
  }

  function money(n) {
    return "$" + n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }
  function money0(n) {
    return "$" + Math.round(n).toLocaleString("en-US");
  }

  global.PN = { calc: calc, money: money, money0: money0, progressive: progressive,
    FED_BRACKETS: FED_BRACKETS, STD_DED: STD_DED, TIPS_DED_MAX: TIPS_DED_MAX, OT_DED_MAX: OT_DED_MAX };
})(window);
