#!/usr/bin/env python3
# PaycheckNest static site generator — no dependencies, pure stdlib.
import json, os, shutil, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, "dist")
SITE_NAME = "PaycheckNest"
SITE_URL = "https://paychecknest.pages.dev"  # primary: Cloudflare Pages (github.io is mirror)
INDEXNOW_KEY = "8f3e2a1c9b4d6e8f0a2c4e6b8d0f2a4c"
GOOGLE_VERIFY = "F0S3I3ddnvG3z9qdL6rDpwDA6bqNE_50ZbUpa1XoUo8"
YEAR = 2026

with open(os.path.join(ROOT, "data", "states.json"), encoding="utf-8") as f:
    STATES = json.load(f)

# ---------- calc (mirror of assets/calc.js, used for content examples) ----------
FED = {
    "single": [(12400, .10), (50400, .12), (105700, .22), (201775, .24), (256225, .32), (640600, .35), (None, .37)],
    "married": [(24800, .10), (100800, .12), (211400, .22), (403550, .24), (512450, .32), (768700, .35), (None, .37)],
}
STD = {"single": 16100, "married": 32200}

def prog(taxable, brackets):
    if taxable <= 0: return 0.0
    tax, lower = 0.0, 0
    for upper, rate in brackets:
        if upper is None or taxable <= upper:
            return tax + (taxable - lower) * rate
        tax += (upper - lower) * rate
        lower = upper
    return tax

def state_tax(st, agi):
    if st["type"] == "none": return 0.0
    taxable = max(0, agi - st.get("std", 0))
    if st["type"] == "flat": return taxable * st["rate"]
    return prog(taxable, [(u if u is not None else None, r) for u, r in st["brackets"]])

def example_net(st, gross=75000):
    fed = prog(max(0, gross - STD["single"]), FED["single"])
    fica = gross * 0.0765
    st_tax = state_tax(st, gross)
    return gross - fed - fica - st_tax

def money0(n): return "$" + format(round(n), ",")

# ---------- page shell ----------
def header():
    return """<header><div class="wrap">
<a class="logo" href="index">Paycheck<span>Nest</span></a>
<nav>
<a href="index">All States</a>
<a href="overtime-tax-calculator">Overtime Tax</a>
<a href="tips-tax-calculator">Tips Tax</a>
<a href="salary-to-hourly-calculator">Salary→Hourly</a>
</nav></div></header>"""

def footer():
    return """<footer><div class="wrap">
<p>PaycheckNest — free US paycheck &amp; tax calculators. Estimates for planning only; not tax advice.
Federal figures: IRS Rev. Proc. 2025-32 (TY2026), SSA 2026 COLA. State rates: 2025/2026 enacted schedules.</p>
<p>&copy; %d PaycheckNest</p></div></footer>""" % datetime.date.today().year

def page(title, desc, path, body, extra_head=""):
    canonical = SITE_URL + ("/" if path == "index.html" else "/" + path[:-5])
    return """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="google-site-verification" content="%s">
<title>%s</title>
<meta name="description" content="%s">
<link rel="canonical" href="%s">
<meta property="og:title" content="%s">
<meta property="og:description" content="%s">
<meta property="og:type" content="website">
%s
<link rel="stylesheet" href="assets/style.css">
</head><body>
%s
<main class="wrap">
%s
</main>
%s
</body></html>""" % (GOOGLE_VERIFY, title, desc, canonical, title, desc, extra_head, header(), body, footer())

def state_links_html(current_slug=None):
    out = ['<div class="state-links">']
    for s in STATES:
        if s["slug"] == current_slug: continue
        out.append('<a href="%s-paycheck-calculator.html">%s</a>' % (s["slug"], s["abbr"]))
    out.append('</div>')
    return "".join(out)

# ---------- state page ----------
def state_page(st):
    name, slug = st["name"], st["slug"]
    title = "%s Paycheck Calculator %d — Take-Home Pay After Taxes" % (name, YEAR)
    desc = "Free %s paycheck calculator for %d. Estimate your take-home pay after federal, state and FICA taxes. Updated %d tax brackets." % (name, YEAR, YEAR)

    if st["type"] == "none":
        tax_intro = "<strong>%s does not levy a state income tax</strong>, so only federal income tax and FICA (Social Security + Medicare) come out of your paycheck." % name
        rate_line = "0%% state income tax"
    elif st["type"] == "flat":
        tax_intro = "%s has a <strong>flat state income tax of %.2f%%</strong>, applied the same way to all taxable income regardless of how much you earn." % (name, st["rate"] * 100)
        rate_line = "%.2f%% flat state income tax" % (st["rate"] * 100)
    else:
        top = st["brackets"][-1][1] * 100
        tax_intro = "%s uses a <strong>progressive income tax</strong> with multiple brackets and a top marginal rate of about <strong>%.2f%%</strong>." % (name, top)
        rate_line = "progressive, up to %.2f%%" % top

    ex = example_net(st)
    note = ("<div class='note'><strong>Note:</strong> %s</div>" % st["note"]) if st.get("note") else ""

    body = """
<div class="hero">
<h1>%(name)s Paycheck Calculator %(year)d</h1>
<p>Estimate your %(name)s take-home pay after federal income tax, %(abbr)s state tax, Social Security and Medicare. Free, instant, no signup.</p>
</div>

<div class="card">
<div class="row">
<div><label for="salary">Annual gross salary ($)</label><input id="salary" type="number" value="75000" min="0" step="1000"></div>
<div><label for="status">Filing status</label><select id="status">
<option value="single">Single</option><option value="married">Married filing jointly</option><option value="hoh">Head of household</option></select></div>
</div>
<div class="row">
<div><label for="k401">Pre-tax 401(k) contribution (%%)</label><input id="k401" type="number" value="0" min="0" max="75" step="1"></div>
<div><label for="freq">Pay frequency</label><select id="freq">
<option value="biweekly">Every 2 weeks (26 checks)</option><option value="weekly">Weekly (52)</option>
<option value="semimonthly">Twice a month (24)</option><option value="monthly">Monthly (12)</option></select></div>
</div>
<button class="btn" id="calc-btn">Calculate Take-Home Pay</button>

<div class="results" id="results">
<p style="margin-top:8px">Your estimated take-home pay</p>
<div class="big" id="r-net-check"></div>
<p style="color:var(--muted)"><span id="r-period-label"></span> &middot; <b id="r-net-year"></b> per year &middot; you keep <b id="r-pct"></b> of gross</p>
<table>
<tr><th>Deduction (annual)</th><th class="num">Amount</th></tr>
<tr><td>Gross salary</td><td class="num" id="r-gross"></td></tr>
<tr><td>Federal income tax (effective <span id="r-eff"></span>)</td><td class="num" id="r-fed"></td></tr>
<tr><td>%(name)s state income tax</td><td class="num" id="r-state"></td></tr>
<tr><td>Social Security (6.2%%)</td><td class="num" id="r-ss"></td></tr>
<tr><td>Medicare (1.45%%)</td><td class="num" id="r-med"></td></tr>
<tr><td>401(k) contribution</td><td class="num" id="r-401k"></td></tr>
</table>
</div>
</div>

%(note)s

<div class="card content">
<h2>How much tax do you pay in %(name)s?</h2>
<p>%(tax_intro)s</p>
<p>A single filer earning <strong>$75,000</strong> in %(name)s takes home roughly <strong>%(ex)s per year</strong> after federal tax, state tax and FICA (estimate, %(year)d rules, no other deductions).</p>
<h2>%(name)s income tax at a glance</h2>
<ul>
<li>State income tax: <strong>%(rate_line)s</strong></li>
<li>Federal standard deduction (%(year)d): $16,100 single / $32,200 married filing jointly</li>
<li>Social Security: 6.2%% on wages up to $184,500</li>
<li>Medicare: 1.45%% on all wages (+0.9%% over $200,000)</li>
</ul>
<h2>Frequently asked questions</h2>
<h3>Does %(name)s have a state income tax?</h3>
<p>%(tax_intro_faq)s</p>
<h3>How accurate is this calculator?</h3>
<p>It models %(year)d federal brackets, FICA and %(name)s state brackets. Real withholding also depends on W-4 settings, benefits, local taxes and credits, so treat the result as a close planning estimate, not tax advice.</p>
<h3>What is the "no tax on overtime / tips" deduction?</h3>
<p>Under the One Big Beautiful Bill Act (2025&ndash;2028), eligible workers can deduct up to $12,500 of overtime premium pay ($25,000 for joint filers) and up to $25,000 of tips from federal taxable income. Try our <a href="overtime-tax-calculator">overtime tax calculator</a> and <a href="tips-tax-calculator">tips tax calculator</a>.</p>
</div>

<h2 class="section">Paycheck calculators for other states</h2>
%(state_links)s

<script>window.STATE = %(state_json)s;</script>
<script src="assets/calc.js"></script>
<script src="assets/paycheck-page.js"></script>
""" % {
        "name": name, "abbr": st["abbr"], "year": YEAR,
        "tax_intro": tax_intro, "tax_intro_faq": tax_intro,
        "rate_line": rate_line, "ex": money0(ex), "note": note,
        "state_links": state_links_html(slug),
        "state_json": json.dumps(st),
    }

    faq_ld = json.dumps({
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": "Does %s have a state income tax?" % name,
             "acceptedAnswer": {"@type": "Answer", "text": tax_intro.replace("<strong>", "").replace("</strong>", "")}},
            {"@type": "Question", "name": "How accurate is the %s paycheck calculator?" % name,
             "acceptedAnswer": {"@type": "Answer", "text": "It models %d federal brackets, FICA and %s state brackets. Real withholding depends on W-4 settings, benefits, local taxes and credits." % (YEAR, name)}},
        ]})
    extra = '<script type="application/ld+json">%s</script>' % faq_ld
    return ("%s-paycheck-calculator.html" % slug, page(title, desc, "%s-paycheck-calculator.html" % slug, body, extra))

# ---------- homepage ----------
def home_page():
    tiles = []
    for s in STATES:
        if s["type"] == "none": tag = "No state income tax"
        elif s["type"] == "flat": tag = "%.2f%% flat" % (s["rate"] * 100)
        else: tag = "Up to %.1f%%" % (s["brackets"][-1][1] * 100)
        tiles.append('<a class="tile" href="%s-paycheck-calculator.html"><b>%s</b><small>%s</small></a>' % (s["slug"], s["name"], tag))

    body = """
<div class="hero">
<h1>US Paycheck Calculators — %(year)d Tax Year</h1>
<p>Free take-home pay calculators for all 50 states + DC. Federal %(year)d brackets (Rev. Proc. 2025-32), state income tax, Social Security and Medicare — computed instantly in your browser.</p>
</div>

<h2 class="section">Popular tools</h2>
<div class="grid">
<a class="tile" href="overtime-tax-calculator"><b>Overtime Tax Calculator</b><small>"No tax on overtime" deduction — up to $12,500 / $25,000</small></a>
<a class="tile" href="tips-tax-calculator"><b>Tips Tax Calculator</b><small>"No tax on tips" deduction — up to $25,000</small></a>
<a class="tile" href="salary-to-hourly-calculator"><b>Salary to Hourly Converter</b><small>Convert annual salary to hourly rate &amp; back</small></a>
<a class="tile" href="california-paycheck-calculator"><b>California Paycheck</b><small>Progressive, up to 12.3%%</small></a>
<a class="tile" href="texas-paycheck-calculator"><b>Texas Paycheck</b><small>No state income tax</small></a>
<a class="tile" href="new-york-paycheck-calculator"><b>New York Paycheck</b><small>Progressive, up to 10.9%%</small></a>
</div>

<h2 class="section">Choose your state</h2>
<div class="grid">%(tiles)s</div>

<div class="card content">
<h2>What's new for %(year)d taxes?</h2>
<ul>
<li><strong>Higher standard deduction:</strong> $16,100 (single) / $32,200 (married filing jointly) under the One Big Beautiful Bill Act.</li>
<li><strong>No tax on overtime:</strong> deduct up to $12,500 ($25,000 joint) of overtime premium pay, 2025&ndash;2028.</li>
<li><strong>No tax on tips:</strong> deduct up to $25,000 of qualified tips, 2025&ndash;2028.</li>
<li><strong>Social Security wage base:</strong> up to $184,500 in %(year)d (from $176,100).</li>
</ul>
<p>All calculators run 100%% in your browser — your numbers never leave your device. Estimates are for planning only and are not tax advice.</p>
</div>

<script src="assets/calc.js"></script>
""" % {"year": YEAR, "tiles": "".join(tiles)}

    return ("index.html", page("Paycheck Calculator %(year)d — Take-Home Pay for All 50 States | PaycheckNest" % {"year": YEAR},
                               "Free paycheck calculators for all 50 states + DC. Estimate %(year)d take-home pay after federal, state, Social Security and Medicare taxes. No signup, runs in your browser." % {"year": YEAR},
                               "index.html", body))

# ---------- simple tool pages ----------
def tool_page(filename, title, desc, h1, sub, form_html, js, content_html):
    body = """
<div class="hero"><h1>%s</h1><p>%s</p></div>
<div class="card">%s
<div class="results" id="results"></div>
</div>
<div class="card content">%s</div>
<script src="assets/calc.js"></script>
<script>%s</script>
""" % (h1, sub, form_html, content_html, js)
    return (filename, page(title, desc, filename, body))

def overtime_page():
    form = """
<div class="row">
<div><label for="wage">Regular hourly wage ($)</label><input id="wage" type="number" value="25" min="0" step="0.5"></div>
<div><label for="hours">Overtime hours per week</label><input id="hours" type="number" value="8" min="0" step="1"></div>
</div>
<div class="row">
<div><label for="status">Filing status</label><select id="status">
<option value="single">Single</option><option value="married">Married filing jointly</option></select></div>
<div><label for="salary">Other annual income ($)</label><input id="salary" type="number" value="0" min="0" step="1000"></div>
</div>
<button class="btn" id="go">Calculate Savings</button>"""
    js = """
document.getElementById("go").addEventListener("click", function(){
  var wage=+document.getElementById("wage").value||0, hours=+document.getElementById("hours").value||0,
      status=document.getElementById("status").value, other=+document.getElementById("salary").value||0;
  var premium = wage*0.5*hours*52;           // deductible part: the 0.5x premium
  var ded = Math.min(premium, PN.OT_DED_MAX[status]);
  var gross = wage*40*52 + wage*1.5*hours*52 + other;
  var r0 = PN.calc({gross:gross, status:status, overtimePay:0});
  var r1 = PN.calc({gross:gross, status:status, overtimePay:ded});
  var save = r0.fed - r1.fed;
  var box = document.getElementById("results");
  box.innerHTML = "<p style='margin-top:8px'>Deductible overtime premium (annual)</p><div class='big'>"+PN.money0(ded)+"</div>"+
    "<p>Estimated federal tax saved: <b>"+PN.money0(save)+"</b></p>"+
    "<table><tr><th>Item</th><th class='num'>Amount</th></tr>"+
    "<tr><td>Annual overtime premium (0.5x portion)</td><td class='num'>"+PN.money0(premium)+"</td></tr>"+
    "<tr><td>Deduction cap ("+status+")</td><td class='num'>"+PN.money0(PN.OT_DED_MAX[status])+"</td></tr>"+
    "<tr><td>Estimated federal tax saved</td><td class='num'>"+PN.money0(save)+"</td></tr></table>";
  box.classList.add("show");
});"""
    content = """
<h2>How the "no tax on overtime" deduction works</h2>
<p>Under the One Big Beautiful Bill Act (tax years 2025&ndash;2028), eligible workers can deduct the <strong>overtime premium portion</strong> of their pay — the extra "half" of time-and-a-half — from federal taxable income.</p>
<ul>
<li>Maximum deduction: <strong>$12,500</strong> (single) or <strong>$25,000</strong> (married filing jointly)</li>
<li>Only the premium portion (0.5x) qualifies, not your full overtime pay</li>
<li>Reduces <strong>federal income tax only</strong> — Social Security and Medicare still apply</li>
<li>Phases out at higher incomes ($150,000 single / $300,000 joint, modified AGI)</li>
</ul>
<p>Example: at $25/hour with 8 overtime hours a week, your annual deductible premium is $25 &times; 0.5 &times; 8 &times; 52 = <strong>$5,200</strong>. In the 22% bracket that saves about $1,144 in federal tax.</p>"""
    return tool_page("overtime-tax-calculator.html",
        "Overtime Tax Calculator %d — No Tax on Overtime Deduction" % YEAR,
        "Calculate how much the 2025-2028 'no tax on overtime' deduction saves you. Up to $12,500 single / $25,000 married of overtime premium is deductible from federal tax.",
        "Overtime Tax Calculator (%d)" % YEAR,
        "The One Big Beautiful Bill lets you deduct the overtime premium from federal taxable income. See your savings.",
        form, js, content)

def tips_page():
    form = """
<div class="row">
<div><label for="tips">Annual tips received ($)</label><input id="tips" type="number" value="15000" min="0" step="500"></div>
<div><label for="salary">Other annual income ($)</label><input id="salary" type="number" value="30000" min="0" step="1000"></div>
</div>
<div class="row">
<div><label for="status">Filing status</label><select id="status">
<option value="single">Single</option><option value="married">Married filing jointly</option></select></div>
</div>
<button class="btn" id="go">Calculate Savings</button>"""
    js = """
document.getElementById("go").addEventListener("click", function(){
  var tips=+document.getElementById("tips").value||0, other=+document.getElementById("salary").value||0,
      status=document.getElementById("status").value;
  var ded = Math.min(tips, PN.TIPS_DED_MAX);
  var gross = tips + other;
  var r0 = PN.calc({gross:gross, status:status, tips:0});
  var r1 = PN.calc({gross:gross, status:status, tips:ded});
  var save = r0.fed - r1.fed;
  var box = document.getElementById("results");
  box.innerHTML = "<p style='margin-top:8px'>Deductible tips (annual)</p><div class='big'>"+PN.money0(ded)+"</div>"+
    "<p>Estimated federal tax saved: <b>"+PN.money0(save)+"</b></p>"+
    "<table><tr><th>Item</th><th class='num'>Amount</th></tr>"+
    "<tr><td>Tips reported</td><td class='num'>"+PN.money0(tips)+"</td></tr>"+
    "<tr><td>Deduction cap</td><td class='num'>"+PN.money0(PN.TIPS_DED_MAX)+"</td></tr>"+
    "<tr><td>Estimated federal tax saved</td><td class='num'>"+PN.money0(save)+"</td></tr></table>";
  box.classList.add("show");
});"""
    content = """
<h2>How the "no tax on tips" deduction works</h2>
<p>Under the One Big Beautiful Bill Act (tax years 2025&ndash;2028), workers in tipped occupations can deduct up to <strong>$25,000</strong> of qualified tips from federal taxable income.</p>
<ul>
<li>Applies to voluntarily paid tips (cash, card, or tip-sharing)</li>
<li>Reduces <strong>federal income tax only</strong> — FICA still applies to all tips</li>
<li>Phases out above $150,000 single / $300,000 joint modified AGI</li>
<li>Available whether or not you itemize deductions</li>
</ul>
<p>Example: $15,000 of tips in the 12% bracket saves about <strong>$1,800</strong> in federal tax.</p>"""
    return tool_page("tips-tax-calculator.html",
        "Tips Tax Calculator %d — No Tax on Tips Deduction" % YEAR,
        "Calculate savings from the 2025-2028 'no tax on tips' deduction — up to $25,000 of qualified tips deductible from federal income tax.",
        "Tips Tax Calculator (%d)" % YEAR,
        "Up to $25,000 of qualified tips is now deductible. See what that saves you.",
        form, js, content)

def salary_hourly_page():
    form = """
<div class="row">
<div><label for="salary">Annual salary ($)</label><input id="salary" type="number" value="75000" min="0" step="1000"></div>
<div><label for="hours">Hours per week</label><input id="hours" type="number" value="40" min="1" max="80" step="1"></div>
</div>
<div class="row">
<div><label for="weeks">Weeks worked per year</label><input id="weeks" type="number" value="52" min="1" max="52" step="1"></div>
<div><label for="hourly">Or convert hourly → salary ($/hr)</label><input id="hourly" type="number" placeholder="e.g. 30" min="0" step="0.25"></div>
</div>
<button class="btn" id="go">Convert</button>"""
    js = """
document.getElementById("go").addEventListener("click", function(){
  var h=+document.getElementById("hours").value||40, w=+document.getElementById("weeks").value||52,
      s=+document.getElementById("salary").value||0, hr=+document.getElementById("hourly").value;
  var box=document.getElementById("results"), html="";
  if(s>0){ var rate=s/(h*w);
    html+="<p style='margin-top:8px'>"+PN.money0(s)+" per year = </p><div class='big'>$"+rate.toFixed(2)+" / hour</div>"+
    "<table><tr><th>Breakdown</th><th class='num'>Amount</th></tr>"+
    "<tr><td>Hourly</td><td class='num'>$"+rate.toFixed(2)+"</td></tr>"+
    "<tr><td>Daily (8h)</td><td class='num'>"+PN.money0(rate*8)+"</td></tr>"+
    "<tr><td>Weekly</td><td class='num'>"+PN.money0(rate*h)+"</td></tr>"+
    "<tr><td>Monthly</td><td class='num'>"+PN.money0(s/12)+"</td></tr></table>"; }
  if(hr>0){ var annual=hr*h*w;
    html+="<p style='margin-top:12px'>$"+hr.toFixed(2)+" per hour = </p><div class='big'>"+PN.money0(annual)+" / year</div>"; }
  box.innerHTML=html; box.classList.add("show");
});"""
    content = """
<h2>Salary to hourly conversion table (40 hrs/week)</h2>
<table>
<tr><th>Annual salary</th><th class="num">Hourly rate</th></tr>
<tr><td>$40,000</td><td class="num">$19.23</td></tr>
<tr><td>$50,000</td><td class="num">$24.04</td></tr>
<tr><td>$60,000</td><td class="num">$28.85</td></tr>
<tr><td>$75,000</td><td class="num">$36.06</td></tr>
<tr><td>$80,000</td><td class="num">$38.46</td></tr>
<tr><td>$100,000</td><td class="num">$48.08</td></tr>
<tr><td>$120,000</td><td class="num">$57.69</td></tr>
</table>
<p>The standard full-time assumption is <strong>2,080 hours per year</strong> (40 hours &times; 52 weeks). If you take unpaid time off, lower the "weeks worked" value above.</p>"""
    return tool_page("salary-to-hourly-calculator.html",
        "Salary to Hourly Calculator %d — Convert Annual Pay to Hourly Rate" % YEAR,
        "Convert annual salary to hourly rate (and back) with adjustable hours per week and weeks per year. Includes quick conversion table.",
        "Salary to Hourly Calculator", "Convert between annual salary and hourly wage instantly.",
        form, js, content)

# ---------- build ----------
def main():
    os.makedirs(DIST, exist_ok=True)
    shutil.copytree(os.path.join(ROOT, "assets"), os.path.join(DIST, "assets"), dirs_exist_ok=True)

    pages = [home_page(), overtime_page(), tips_page(), salary_hourly_page()]
    for st in STATES:
        pages.append(state_page(st))

    for filename, html in pages:
        with open(os.path.join(DIST, filename), "w", encoding="utf-8") as f:
            f.write(html)

    urls = [SITE_URL + ("/" if fn == "index.html" else "/" + fn[:-5]) for fn, _ in pages]
    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        sitemap.append("<url><loc>%s</loc></url>" % u)
    sitemap.append("</urlset>")
    with open(os.path.join(DIST, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write("\n".join(sitemap))
    with open(os.path.join(DIST, "robots.txt"), "w", encoding="utf-8") as f:
        f.write("User-agent: *\nAllow: /\nSitemap: %s/sitemap.xml\n" % SITE_URL)

    # IndexNow key file (Bing instant indexing)
    with open(os.path.join(DIST, INDEXNOW_KEY + ".txt"), "w", encoding="utf-8") as f:
        f.write(INDEXNOW_KEY)

    print("Built %d pages -> %s" % (len(pages), DIST))

if __name__ == "__main__":
    main()
