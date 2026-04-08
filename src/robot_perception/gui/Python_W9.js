const pptxgen = require("pptxgenjs");

const C = {
  dark:"0D1B2A", navy:"1B2A4A", blue:"1E5F8E",
  accent:"00B4D8", accent2:"90E0EF", light:"E8F4F8",
  white:"FFFFFF", gray:"7A8A9A", code_bg:"0A1628",
  green:"06D6A0", red:"EF476F", orange:"F4A261",
  purple:"9B59B6", pyellow:"FFD43B", pblue:"4B8BBE",
};
const FOOTER="Python dla Obliczeń Naukowo-Technicznych  |  Wykład 9: Statystyka i analiza danych";
const W=10, H=5.625;

function ft(s,num){
  s.addShape("rect",{x:0,y:5.42,w:W,h:0.205,fill:{color:C.navy},line:{color:C.navy}});
  s.addText(FOOTER,{x:0.3,y:5.455,w:8.8,h:0.16,fontSize:8.5,color:C.gray,
    align:"left",fontFace:"Calibri",margin:0});
  s.addText(`${num} / 30`,{x:0.3,y:5.455,w:9.4,h:0.16,fontSize:8.5,color:C.gray,
    align:"right",fontFace:"Calibri",margin:0});
}
function hdr(pres,s,title,num){
  s.background={color:C.light};
  s.addShape("rect",{x:0,y:0,w:W,h:0.96,fill:{color:C.navy},line:{color:C.navy}});
  s.addShape("rect",{x:0,y:0.96,w:W*0.55,h:0.055,fill:{color:C.pyellow},line:{color:C.pyellow}});
  s.addShape("rect",{x:W*0.55,y:0.96,w:W*0.45,h:0.055,fill:{color:C.pblue},line:{color:C.pblue}});
  s.addText(title,{x:0.5,y:0.12,w:8.6,h:0.72,fontSize:22,color:C.white,
    bold:true,fontFace:"Calibri",margin:0});
  ft(s,num);
}
function sec(pres,n,title,sub){
  const s=pres.addSlide();
  s.background={color:C.navy};
  s.addShape("rect",{x:0,y:0,w:0.12,h:H,fill:{color:C.pyellow},line:{color:C.pyellow}});
  s.addShape("rect",{x:0.12,y:0,w:0.06,h:H,fill:{color:C.pblue},line:{color:C.pblue}});
  s.addShape("ellipse",{x:4.8,y:-2.2,w:8,h:8,
    fill:{color:C.blue,transparency:72},line:{color:C.blue,transparency:72}});
  s.addText(`0${n}`,{x:0.5,y:0.7,w:1.8,h:1.5,fontSize:80,color:C.pyellow,
    bold:true,fontFace:"Calibri",margin:0});
  s.addText(title,{x:0.5,y:2.35,w:9,h:0.9,fontSize:34,color:C.white,
    bold:true,fontFace:"Calibri",margin:0});
  s.addShape("rect",{x:0.5,y:3.02,w:2,h:0.05,fill:{color:C.pyellow},line:{color:C.pyellow}});
  s.addText(sub,{x:0.5,y:3.15,w:9,h:0.5,fontSize:13,color:C.accent2,
    fontFace:"Calibri Light",margin:0});
}

// COLS3 — max 19 wierszy × 42 znaki, fontSize 8.8
function cols3(s,items){
  items.forEach((col,i)=>{
    const x=0.35+i*3.22;
    s.addShape("rect",{x,y:1.22,w:3.06,h:0.36,fill:{color:col.color},line:{color:col.color}});
    s.addText(col.title,{x:x+0.08,y:1.26,w:2.90,h:0.26,fontSize:10,
      color:col.color===C.pyellow?C.dark:C.white,bold:true,fontFace:"Calibri",margin:0});
    s.addShape("rect",{x,y:1.58,w:3.06,h:3.64,fill:{color:C.code_bg},line:{color:C.navy}});
    s.addText(col.code,{x:x+0.09,y:1.63,w:2.89,h:3.55,fontSize:8.8,
      color:C.white,fontFace:"Consolas",margin:0});
  });
}

// CBL — lewa strona (w=5.4), max 22 wiersze × 65 znaków, fontSize 9.2
function cbL(s,code,y,h,label){
  const x=0.4,w=5.4;
  s.addShape("rect",{x,y,w,h,fill:{color:C.code_bg},line:{color:C.navy}});
  if(label){
    s.addText(label,{x:x+0.12,y:y+0.07,w:w-0.20,h:0.20,fontSize:8.5,
      color:C.pyellow,fontFace:"Calibri",margin:0});
    s.addText(code,{x:x+0.12,y:y+0.30,w:w-0.20,h:h-0.37,fontSize:9.2,
      color:C.white,fontFace:"Consolas",margin:0});
  } else {
    s.addText(code,{x:x+0.12,y:y+0.10,w:w-0.20,h:h-0.16,fontSize:9.2,
      color:C.white,fontFace:"Consolas",margin:0});
  }
}

// CBFULL — pełna szerokość, max 28 wierszy, fontSize 9.0
function cbFull(s,code,y,h,label){
  const x=0.4,w=9.2;
  s.addShape("rect",{x,y,w,h,fill:{color:C.code_bg},line:{color:C.navy}});
  if(label){
    s.addText(label,{x:x+0.12,y:y+0.07,w:w-0.20,h:0.20,fontSize:8.5,
      color:C.pyellow,fontFace:"Calibri",margin:0});
    s.addText(code,{x:x+0.12,y:y+0.30,w:w-0.20,h:h-0.37,fontSize:9.0,
      color:C.white,fontFace:"Consolas",margin:0});
  } else {
    s.addText(code,{x:x+0.12,y:y+0.10,w:w-0.20,h:h-0.16,fontSize:9.0,
      color:C.white,fontFace:"Consolas",margin:0});
  }
}

function banner(s,text,y){
  s.addShape("rect",{x:0.4,y,w:9.2,h:0.48,fill:{color:C.navy},line:{color:C.navy}});
  s.addText(text,{x:0.60,y:y+0.09,w:8.8,h:0.30,fontSize:10.5,color:C.accent2,
    fontFace:"Calibri",margin:0});
}
function strip(s,items,y){
  const w=9.2/items.length;
  items.forEach((it,i)=>{
    const x=0.4+i*w;
    s.addShape("rect",{x,y,w:w-0.06,h:0.28,fill:{color:it.c},line:{color:it.c}});
    s.addText(it.t,{x,y:y+0.04,w:w-0.06,h:0.20,fontSize:9.5,
      color:it.c===C.pyellow?C.dark:C.white,bold:true,align:"center",fontFace:"Calibri",margin:0});
  });
}
function panel(s,title,items,x,y,w,h,ih){
  s.addShape("rect",{x,y,w,h,fill:{color:C.white},line:{color:"E0E8F0"}});
  s.addText(title,{x:x+0.14,y:y+0.09,w:w-0.22,h:0.28,fontSize:11,
    color:C.blue,bold:true,fontFace:"Calibri",margin:0});
  items.forEach((it,i)=>{
    const iy=y+0.44+i*ih;
    s.addShape("rect",{x:x+0.08,y:iy,w:w-0.16,h:ih-0.07,
      fill:{color:"F8FBFE"},line:{color:"E0E8F0"}});
    s.addShape("rect",{x:x+0.08,y:iy,w:0.06,h:ih-0.07,fill:{color:it.c},line:{color:it.c}});
    s.addText(it.t,{x:x+0.20,y:iy+0.04,w:w-0.32,h:0.20,fontSize:10,
      color:C.dark,bold:true,fontFace:"Calibri",margin:0});
    if(it.s) s.addText(it.s,{x:x+0.20,y:iy+0.25,w:w-0.32,h:0.18,fontSize:9,
      color:C.gray,fontFace:"Calibri",margin:0});
  });
}

// ══════════════════════════════════════════════════════════════════════════
async function build(){
  const pres=new pptxgen();
  pres.layout="LAYOUT_16x9";
  pres.title="Python dla ONT — Wykład 9: Statystyka i analiza danych";

  // ── SLAJD 1 — TYTUŁ ───────────────────────────────────────────────────
  {
    const s=pres.addSlide();
    s.background={color:C.dark};
    s.addShape("rect",{x:0,y:0,w:W*0.55,h:0.09,fill:{color:C.pyellow},line:{color:C.pyellow}});
    s.addShape("rect",{x:W*0.55,y:0,w:W*0.45,h:0.09,fill:{color:C.pblue},line:{color:C.pblue}});
    s.addShape("rect",{x:0,y:0,w:0.06,h:H,fill:{color:C.pblue},line:{color:C.pblue}});
    s.addShape("ellipse",{x:5.5,y:-1.3,w:6.4,h:6.4,
      fill:{color:C.navy,transparency:55},line:{color:C.navy,transparency:55}});
    // Dekoracja: słupki histogramu
    [0.4,0.72,1.0,0.82,0.55].forEach((ht,i)=>{
      s.addShape("rect",{x:7.5+i*0.38,y:1.85-ht*0.85,w:0.32,h:ht*0.85,
        fill:{color:i===2?C.pyellow:C.pblue,transparency:25},line:{color:C.navy}});
    });
    s.addText("OBLICZENIA NAUKOWO-TECHNICZNE  •  STUDIA MAGISTERSKIE",
      {x:0.4,y:0.28,w:9.2,h:0.38,fontSize:9,color:C.accent,bold:true,
        charSpacing:3,fontFace:"Calibri",margin:0});
    s.addShape("rect",{x:0.4,y:0.78,w:1.4,h:0.42,fill:{color:C.pyellow},line:{color:C.pyellow}});
    s.addText("Wykład 9 / PY",{x:0.4,y:0.84,w:1.4,h:0.30,fontSize:10,color:C.dark,
      bold:true,align:"center",fontFace:"Calibri",margin:0});
    s.addText("Statystyka",{x:0.4,y:1.36,w:6.0,h:0.72,fontSize:30,
      color:C.white,fontFace:"Calibri Light",margin:0});
    s.addText("i analiza danych",{x:0.4,y:2.04,w:7.0,h:0.80,fontSize:42,
      color:C.pyellow,bold:true,fontFace:"Calibri",margin:0,charSpacing:1});
    s.addText("scipy.stats · testy hipotez · regresja · bootstrap · Bayes",
      {x:0.4,y:2.96,w:9,h:0.34,fontSize:13,color:C.accent2,fontFace:"Calibri Light",margin:0});
    s.addText("Wykład 9 z 12  |  120 minut",{x:0.4,y:3.38,w:6,h:0.34,
      fontSize:13,color:C.accent2,fontFace:"Calibri",margin:0});
    s.addShape("rect",{x:0.4,y:3.82,w:3.4,h:0.04,fill:{color:C.pblue},line:{color:C.pblue}});
    ["Statystyki opisowe i rozkłady — scipy.stats, miary, QQ-plot",
     "Testy hipotez — t-test, ANOVA, Mann-Whitney, chi-kwadrat",
     "Regresja liniowa i wieloraka — statsmodels OLS, diagnostyka",
     "Bootstrap i permutacje — CI bez założeń, test permutacyjny",
     "Wnioskowanie bayesowskie — PyMC, MCMC, posteriori, LOO"].forEach((t,i)=>{
      s.addShape("ellipse",{x:0.42,y:3.95+i*0.28,w:0.10,h:0.10,
        fill:{color:C.pyellow},line:{color:C.pyellow}});
      s.addText(t,{x:0.62,y:3.93+i*0.28,w:8.8,h:0.25,fontSize:10.5,
        color:C.accent2,fontFace:"Calibri",margin:0});
    });
    s.addShape("rect",{x:0,y:5.42,w:W,h:0.205,fill:{color:C.navy},line:{color:C.navy}});
    s.addText("Katedra Inżynierii  •  2024/2025",{x:0.3,y:5.455,w:9.4,h:0.16,
      fontSize:9,color:C.gray,fontFace:"Calibri",margin:0});
  }

  // ── SLAJD 2 — PLAN ────────────────────────────────────────────────────
  {
    const s=pres.addSlide();
    s.background={color:C.light};
    s.addShape("rect",{x:0,y:0,w:W,h:1.08,fill:{color:C.navy},line:{color:C.navy}});
    s.addShape("rect",{x:0,y:1.08,w:W*0.55,h:0.05,fill:{color:C.pyellow},line:{color:C.pyellow}});
    s.addShape("rect",{x:W*0.55,y:1.08,w:W*0.45,h:0.05,fill:{color:C.pblue},line:{color:C.pblue}});
    s.addText("Plan wykładu — Wykład 9",{x:0.5,y:0.20,w:9,h:0.68,fontSize:28,
      color:C.white,bold:true,fontFace:"Calibri",margin:0});
    [["01","Statystyki opisowe i rozkłady","scipy.stats, miary, dopasowanie MLE, QQ-plot"],
     ["02","Testowanie hipotez","t-test, ANOVA, Mann-Whitney, chi-kwadrat, moc"],
     ["03","Regresja liniowa","statsmodels OLS, VIF, diagnostyka reszt, GLM"],
     ["04","Bootstrap i permutacje","CI bez założeń, jackknife, test permutacyjny"],
     ["05","Wnioskowanie bayesowskie","PyMC, NUTS, ArviZ, posteriori, LOO-CV"],
     ["06","Zastosowania inżynierskie","SPC, DOE, analiza przeżycia, niezawodność"],
    ].forEach((b,i)=>{
      const col=i<3?0:1, row=i%3, x=0.4+col*4.9, y=1.22+row*1.34;
      s.addShape("rect",{x,y,w:4.55,h:1.2,fill:{color:C.white},
        shadow:{type:"outer",color:"000000",blur:8,offset:2,angle:135,opacity:0.09}});
      s.addShape("rect",{x,y,w:0.56,h:1.2,
        fill:{color:i<3?C.pyellow:C.pblue},line:{color:i<3?C.pyellow:C.pblue}});
      s.addText(b[0],{x,y:y+0.36,w:0.56,h:0.50,fontSize:18,
        color:i<3?C.dark:C.white,bold:true,align:"center",fontFace:"Calibri",margin:0});
      s.addText(b[1],{x:x+0.66,y:y+0.10,w:3.75,h:0.38,fontSize:12,
        color:C.dark,bold:true,fontFace:"Calibri",margin:0});
      s.addText(b[2],{x:x+0.66,y:y+0.54,w:3.75,h:0.38,fontSize:10,
        color:C.gray,fontFace:"Calibri",margin:0});
    });
    ft(s,2);
  }

  // ══ SEKCJA 01 ═════════════════════════════════════════════════════════
  sec(pres,1,"Statystyki opisowe i rozkłady","scipy.stats: miary, dopasowanie MLE, QQ-plot, CI");

  // SLAJD 4 — miary opisowe
  {
    const s=pres.addSlide();
    hdr(pres,s,"Miary opisowe i dopasowanie rozkładu",4);
    banner(s,"scipy.stats ma ponad 90 rozkładów z jednolitym API: rvs, pdf, cdf, ppf, fit. Zawsze zacznij od wizualizacji: histogram + KDE + wykres QQ ujawnią skośność, outliery i wielomodalność.",1.14);
    cols3(s,[
      {title:"Miary tendencji i zmienności",color:C.pyellow,code:
`import numpy as np
from scipy import stats

rng = np.random.default_rng(0)
x = rng.normal(235, 20, 80)

# Miary tendencji centralnej
print(f"Średnia:  {x.mean():.2f}")
print(f"Mediana:  {np.median(x):.2f}")

# Miary zmienności
print(f"Std:      {x.std(ddof=1):.2f}")
print(f"IQR:      {stats.iqr(x):.2f}")
print(f"MAD:      "
      f"{stats.median_abs_deviation(x):.2f}")

# Kształt rozkładu
print(f"Skośność: {stats.skew(x):.3f}")
print(f"Kurtoza:  {stats.kurtosis(x):.3f}")

# CI dla średniej (95%)
ci = stats.t.interval(
    0.95, df=len(x)-1,
    loc=x.mean(),
    scale=stats.sem(x))
print(f"CI 95%: [{ci[0]:.2f}, {ci[1]:.2f}]")`},
      {title:"Dopasowanie rozkładu — MLE",color:C.pblue,code:
`from scipy import stats
import numpy as np

rng = np.random.default_rng(1)
# Czas życia [h] — rozkład Weibulla
dane = stats.weibull_min.rvs(
    c=2.5, scale=1000,
    size=100, random_state=1)

# Porównanie AIC dla kandydatów
for nazwa in ["weibull_min","lognorm",
              "expon","gamma"]:
    rozk = getattr(stats, nazwa)
    par  = rozk.fit(dane, floc=0)
    ll   = rozk.logpdf(dane, *par).sum()
    aic  = 2*len(par) - 2*ll
    print(f"{nazwa:12s} AIC={aic:.1f}")

# Test KS dla najlepszego
par_w = stats.weibull_min.fit(
    dane, floc=0)
ks, p = stats.kstest(
    dane, "weibull_min", par_w)
print(f"KS: stat={ks:.4f} p={p:.4f}")
# p > 0.05 → brak podstaw do odrzucenia`},
      {title:"Wykres QQ i normalność",color:C.green,code:
`from scipy import stats
import numpy as np
import matplotlib.pyplot as plt

rng = np.random.default_rng(2)
x_n = rng.normal(0, 1, 80)
x_h = rng.exponential(1, 80)

fig, axes = plt.subplots(
    1, 2, figsize=(6, 3))
for ax, x, tyt in zip(
    axes, [x_n, x_h],
    ["Normalny", "Wykładniczy"]):
    (osm,osr),(sl,ic,r) = stats.probplot(
        x, dist="norm", fit=True)[:2]
    ax.plot(osm, osr, "o",
            ms=4, alpha=0.6)
    ax.plot(osm, sl*osm+ic,
            "r-", lw=1.5)
    ax.set_title(f"{tyt}  r={r:.3f}",
                 fontsize=9)
    ax.grid(True, alpha=0.3)
plt.tight_layout(); plt.show()

# Shapiro-Wilk (n < 5000)
_, p_n = stats.shapiro(x_n)
_, p_h = stats.shapiro(x_h)
print(f"SW norm: p={p_n:.3f}")
print(f"SW wykł: p={p_h:.4f}")`},
    ]);
  }

  // SLAJD 5 — rozkłady
  {
    const s=pres.addSlide();
    hdr(pres,s,"Rozkłady prawdopodobieństwa — API scipy.stats",5);
    banner(s,"Każdy rozkład: rvs() losuje, pdf/pmf() oblicza gęstość, cdf() daje dystrybuantę, ppf() — kwantyl (odwrotność cdf), fit() dopasowuje przez MLE. Rozkłady ciągłe: 90+; dyskretne: 20+.",1.14);

    cbL(s,
`from scipy import stats
import numpy as np
import matplotlib.pyplot as plt

x = np.linspace(0, 600, 300)

fig, axes = plt.subplots(
    2, 3, figsize=(6, 4))

for ax, (rozk, par, tyt) in zip(
    axes[0], [
    (stats.norm,        (235, 20),
     "Normal(235,20)"),
    (stats.weibull_min, (2.5, 0, 400),
     "Weibull(c=2.5)"),
    (stats.lognorm,     (0.3, 0, 200),
     "LogNormal"),
]):
    ax.plot(x, rozk.pdf(x, *par), lw=2)
    ax.fill_between(x,
        rozk.pdf(x, *par), alpha=0.2)
    ax.set_title(tyt, fontsize=9)
    ax.grid(True, alpha=0.3)

for ax, (rozk, par, tyt) in zip(
    axes[1], [
    (stats.poisson, (5,),    "Poisson(5)"),
    (stats.binom,   (20,.3), "Binom(20,0.3)"),
    (stats.geom,    (0.3,),  "Geom(0.3)"),
]):
    k = np.arange(0, 20)
    ax.bar(k, rozk.pmf(k, *par),
           alpha=0.7, width=0.8)
    ax.set_title(tyt, fontsize=9)
    ax.grid(True, alpha=0.3)

plt.tight_layout(); plt.show()`,
    1.74,3.36,"pdf/pmf, fill_between — 3 ciągłe i 3 dyskretne na 6-panelowym wykresie");

    panel(s,"Przydatne rozkłady w inżynierii",[
      {t:"Normal — tolerancje, błędy",  s:"stats.norm; zakres 3σ obejmuje 99.73%.",c:C.pyellow},
      {t:"Weibull — trwałość komponentów",s:"stats.weibull_min; c < 1 → wczesne awarie.",c:C.pblue},
      {t:"Lognormal — wytrzymałość",    s:"stats.lognorm; modeluje dane prawostronnie skośne.",c:C.green},
      {t:"Poisson — defekty, zdarzenia",s:"stats.poisson; mu = średnia zdarzeń/jednostkę.",c:C.orange},
      {t:"t-Studenta — małe próbki",    s:"stats.t(df=n-1); CI dla średniej przy n < 30.",c:C.purple},
    ],6.0,1.74,3.62,3.36,0.60);
  }

  // ══ SEKCJA 02 ═════════════════════════════════════════════════════════
  sec(pres,2,"Testowanie hipotez","t-test, ANOVA, Mann-Whitney, chi-kwadrat, moc testu");

  // SLAJD 7
  {
    const s=pres.addSlide();
    hdr(pres,s,"Testy parametryczne — t-test i ANOVA",7);
    banner(s,"Schemat: (1) sprawdź normalność — Shapiro-Wilk; (2) sprawdź jednorodność wariancji — Levene; (3) wybierz test. Dla k > 2 grup: ANOVA + post-hoc Tukey HSD. Zawsze podaj rozmiar efektu (Cohen d).",1.14);
    cols3(s,[
      {title:"Shapiro-Wilk i t-test Welcha",color:C.pyellow,code:
`from scipy import stats
import numpy as np

rng = np.random.default_rng(0)
g1 = rng.normal(235, 15, 35)
g2 = rng.normal(248, 18, 35)

# 1. Normalność
_, p1 = stats.shapiro(g1)
_, p2 = stats.shapiro(g2)
print(f"Shapiro p1={p1:.3f}")
print(f"Shapiro p2={p2:.3f}")

# 2. Jednorodność wariancji
_, p_lev = stats.levene(g1, g2)
print(f"Levene  p={p_lev:.3f}")

# 3. t-test Welcha (różne wariancje)
t, p_t = stats.ttest_ind(
    g1, g2, equal_var=False)
print(f"t={t:.3f}  p={p_t:.4f}")

# Rozmiar efektu (Cohen d)
sp = np.sqrt((g1.var(ddof=1) +
              g2.var(ddof=1)) / 2)
d  = (g2.mean()-g1.mean()) / sp
print(f"Cohen d = {d:.3f}")`},
      {title:"ANOVA + post-hoc Tukey",color:C.pblue,code:
`from scipy import stats
import numpy as np
from statsmodels.stats.multicomp \
    import pairwise_tukeyhsd

rng = np.random.default_rng(1)
grupy = {
    "S235": rng.normal(235,15,30),
    "S355": rng.normal(355,20,30),
    "AL":   rng.normal(270,18,30),
}

# ANOVA jednoczynnikowa
F, p = stats.f_oneway(
    *grupy.values())
print(f"ANOVA F={F:.2f} p={p:.4f}")

if p < 0.05:
    vals   = np.concatenate(
        list(grupy.values()))
    labels = np.repeat(
        list(grupy.keys()),[30]*3)
    wynik  = pairwise_tukeyhsd(
        vals, labels, alpha=0.05)
    print(wynik.summary())

# Kruskal-Wallis (nieparametryczna)
H, p_kw = stats.kruskal(
    *grupy.values())
print(f"KW H={H:.2f} p={p_kw:.4f}")`},
      {title:"Testy nieparametryczne",color:C.green,code:
`from scipy import stats
import numpy as np

rng = np.random.default_rng(2)
x1 = rng.exponential(10, 40)
x2 = rng.exponential(13, 40)

# Mann-Whitney U
U, p_mw = stats.mannwhitneyu(
    x1, x2, alternative="two-sided")
print(f"Mann-Whitney p={p_mw:.4f}")

# Wilcoxon (pary)
przed = rng.normal(100, 15, 25)
po    = przed + rng.normal(5, 12, 25)
W, p_w = stats.wilcoxon(
    przed, po,
    alternative="less")
print(f"Wilcoxon p={p_w:.4f}")

# Chi-kwadrat (kontyngencja)
tab = np.array([[45,30],[15,60]])
chi2, p_chi, df, _ = (
    stats.chi2_contingency(tab))
print(f"Chi2={chi2:.2f} p={p_chi:.4f}")

# Proporcje (z-test)
z, p_z = stats.proportions_ztest(
    [180,160],[200,200])
print(f"Proporcje p={p_z:.4f}")`},
    ]);
  }

  // SLAJD 8 — korekta i moc
  {
    const s=pres.addSlide();
    hdr(pres,s,"Korekta wielokrotna i moc testu",8);
    banner(s,"Przy k testach błąd I rodzaju rośnie: P(≥1 FP) = 1−(1−α)^k. Przy k=20 i α=0.05 prawdopodobieństwo fałszywego odkrycia wynosi 64%. Korekta Benjamini-Hochberg (FDR) jest łagodniejsza niż Bonferroni.",1.14);

    cbL(s,
`from scipy import stats
import numpy as np
from statsmodels.stats.multitest \
    import multipletests
from statsmodels.stats.power \
    import tt_ind_solve_power

rng = np.random.default_rng(3)
k = 20  # liczba testów

# Symulacja: 3 prawdziwe efekty, 17 H0
p_vals = []
for i in range(k):
    mu = 108 if i < 3 else 100
    g1 = rng.normal(100, 10, 30)
    g2 = rng.normal(mu,  10, 30)
    _, p = stats.ttest_ind(g1, g2)
    p_vals.append(p)

p_arr = np.array(p_vals)
p_bonf = np.minimum(p_arr * k, 1.0)

rej, p_bh, _, _ = multipletests(
    p_arr, alpha=0.05, method="fdr_bh")

print(f"Nominalne  p<0.05: {(p_arr<0.05).sum()}")
print(f"Bonferroni p<0.05: {(p_bonf<0.05).sum()}")
print(f"BH  odkrycia:      {rej.sum()}")

# Analiza mocy — dobór n przed exp.
n_min = tt_ind_solve_power(
    effect_size=0.5,  # Cohen d (średni)
    alpha=0.05,
    power=0.80,
    alternative="two-sided")
print(f"Min. n/grupę: {n_min:.0f}")`,
    1.74,3.36,"Bonferroni vs BH/FDR przy 20 testach; tt_ind_solve_power — dobór n");

    panel(s,"Korekty wielokrotne i moc",[
      {t:"Bonferroni α* = α/k",    s:"Konserwatywna; kontroluje FWER. Dla k<10.",c:C.pyellow},
      {t:"Holm-Bonferroni",         s:"Sekwencyjna; lepsza moc niż Bonferroni.",c:C.pblue},
      {t:"Benjamini-Hochberg (FDR)",s:"Kontroluje odsetek fałszywych odkryć.",c:C.green},
      {t:"Moc testu (1−β)",         s:"power_solve → minimalne n przed exp.",c:C.orange},
      {t:"Rozmiar efektu",          s:"Cohen d, η², r — niezależny od n; zawsze podaj.",c:C.purple},
    ],6.0,1.74,3.62,3.36,0.60);
  }

  // ══ SEKCJA 03 ═════════════════════════════════════════════════════════
  sec(pres,3,"Regresja liniowa","statsmodels OLS, VIF, diagnostyka reszt, GLM Logit");

  // SLAJD 10
  {
    const s=pres.addSlide();
    hdr(pres,s,"Regresja OLS i wieloraka — statsmodels",10);
    banner(s,"statsmodels.OLS daje pełne podsumowanie: t, p, SE, CI, R², F. Zawsze sprawdź: normalność reszt (Jarque-Bera), heteroskedastyczność (Breusch-Pagan), autokorelację (Durbin-Watson), wielokoliniearność (VIF).",1.14);
    cols3(s,[
      {title:"OLS — regresja prosta",color:C.pyellow,code:
`import statsmodels.api as sm
import numpy as np

rng = np.random.default_rng(0)
n   = 60
T   = rng.uniform(20, 300, n)
y   = 300-0.5*T + 15*rng.standard_normal(n)

X = sm.add_constant(T)
res = sm.OLS(y, X).fit()
print(res.summary().tables[1])

# R² i F-test
print(f"R²={res.rsquared:.4f}")
print(f"F ={res.fvalue:.2f} "
      f"p={res.f_pvalue:.4f}")

# Przedziały ufności β
ci = res.conf_int(0.05)
print("CI 95%:")
print(ci)

# Predykcja z PI
T_new = sm.add_constant([150, 250])
pred  = res.get_prediction(T_new)
print(pred.summary_frame(alpha=0.05)
    [["mean","obs_ci_lower","obs_ci_upper"]])`},
      {title:"Wieloraka + VIF",color:C.pblue,code:
`import statsmodels.api as sm
from statsmodels.stats.outliers_influence \
    import variance_inflation_factor
import numpy as np

rng = np.random.default_rng(1)
n   = 80
T   = rng.uniform(20, 300, n)
t   = rng.uniform(1, 24, n)
C   = rng.uniform(0.1, 0.8, n)
y   = (200-0.3*T+5*t+80*C
       +10*rng.standard_normal(n))

X = sm.add_constant(
    np.column_stack([T,t,C]))
res = sm.OLS(y, X).fit()
print(f"R²={res.rsquared:.3f}")
print(f"F ={res.fvalue:.1f}")

# VIF — wielokoliniearność
nms = ["const","T","t","C"]
for i, nm in enumerate(nms):
    v = variance_inflation_factor(X,i)
    print(f"VIF({nm}) = {v:.2f}")
# VIF > 10 → problem`},
      {title:"Diagnostyka reszt",color:C.green,code:
`import statsmodels.api as sm
from scipy import stats
import numpy as np
import matplotlib.pyplot as plt

rng = np.random.default_rng(2)
n   = 70
x   = np.sort(rng.uniform(0,10,n))
y   = 3*x+x**1.5*0.5 \
      +rng.normal(0,2,n)

X   = sm.add_constant(x)
res = sm.OLS(y,X).fit()
r   = res.resid

fig,axes=plt.subplots(2,2,figsize=(6,4))
axes[0,0].scatter(
    res.fittedvalues,r,s=10,alpha=0.6)
axes[0,0].axhline(0,color="r",lw=1)
axes[0,0].set_title("Reszty vs Ŷ")
axes[0,1].hist(r,bins=12,
    edgecolor="k",lw=0.3)
axes[0,1].set_title("Histogram reszt")
stats.probplot(r,plot=axes[1,0])
axes[1,0].set_title("QQ reszt")
axes[1,1].scatter(res.fittedvalues,
    np.sqrt(np.abs(r)),s=10,alpha=0.6)
axes[1,1].set_title("Scale-Location")
for ax in axes.flat:
    ax.grid(True,alpha=0.3)
plt.tight_layout()`},
    ]);
  }

  // SLAJD 11 — GLM Logit
  {
    const s=pres.addSlide();
    hdr(pres,s,"Regresja logistyczna i GLM — modele uogólnione",11);
    banner(s,"GLM uogólnia OLS na rozkłady z rodziny wykładniczej. Regresja logistyczna (Binomial + logit) klasyfikuje wynik binarny — wynik to iloraz szans (OR = exp(β)). Dla danych zliczeniowych: Poisson z funkcją log.",1.14);

    cbL(s,
`import statsmodels.api as sm
from sklearn.metrics import roc_auc_score
import numpy as np

rng = np.random.default_rng(4)
n   = 150
g   = rng.uniform(1, 10, n)   # grubość
t   = rng.uniform(50, 200, n) # twardość
p_d = 1/(1+np.exp(
    -(-3 + 0.4*g - 0.02*t)))
y   = rng.binomial(1, p_d)

X   = sm.add_constant(
    np.column_stack([g, t]))
log_res = sm.Logit(y, X).fit(disp=0)
print(log_res.summary().tables[1])

# Ilorazy szans (Odds Ratios)
OR = np.exp(log_res.params)
CI = np.exp(log_res.conf_int())
for nm, o, c in zip(
    ["const","g","t"], OR, CI.values):
    print(f"{nm}: OR={o:.3f} "
          f"[{c[0]:.3f},{c[1]:.3f}]")

# AUC-ROC
y_hat = log_res.predict(X)
auc   = roc_auc_score(y, y_hat)
print(f"AUC-ROC = {auc:.4f}")`,
    1.74,3.36,"GLM Logit: OR + CI, AUC-ROC — klasyfikacja defektów na podstawie grubości i twardości");

    panel(s,"Rodziny GLM — statsmodels",[
      {t:"OLS — Normal + identity",   s:"sm.OLS(y,X). Dane ciągłe, addytywny błąd.",c:C.pyellow},
      {t:"Logit — Binomial + logit",  s:"sm.Logit(y,X). Wynik 0/1; OR = exp(β).",c:C.pblue},
      {t:"Poisson — Poisson + log",   s:"sm.Poisson(y,X). Zliczenia; exp(β) = IRR.",c:C.green},
      {t:"Gamma — Gamma + log",       s:"sm.GLM(y,X,family=Gamma()). Skośne dane.",c:C.orange},
      {t:"NegBinomial",               s:"Overdispersion w danych zliczeniowych.",c:C.purple},
    ],6.0,1.74,3.62,3.36,0.60);
  }

  // ══ SEKCJA 04 ═════════════════════════════════════════════════════════
  sec(pres,4,"Bootstrap i permutacje","CI bez założeń, jackknife, test permutacyjny");

  // SLAJD 13
  {
    const s=pres.addSlide();
    hdr(pres,s,"Bootstrap — przedziały ufności bez założeń",13);
    banner(s,"Bootstrap: losuj N obserwacji ze zwracaniem, oblicz statystykę, powtórz B=5000 razy → rozkład bootstrapowy. BCa (bias-corrected accelerated) jest preferowane dla skośnych danych — koryguje asymetrię CI.",1.14);
    cols3(s,[
      {title:"Bootstrap BCa — scipy",color:C.pyellow,code:
`from scipy.stats import bootstrap
import numpy as np

rng = np.random.default_rng(5)
dane = rng.lognormal(
    np.log(210), 0.08, 40)

# scipy.stats.bootstrap (>=1.7)
wynik = bootstrap(
    (dane,),
    statistic=np.mean,
    n_resamples=5000,
    confidence_level=0.95,
    method="BCa",
    random_state=0)

lo = wynik.confidence_interval.low
hi = wynik.confidence_interval.high
print(f"Średnia: {dane.mean():.2f}")
print(f"CI BCa: [{lo:.2f}, {hi:.2f}]")

# Ręczny bootstrap dla mediany
B   = 4000
med = np.array([
    np.median(rng.choice(
        dane,len(dane),replace=True))
    for _ in range(B)])
ci_med = np.percentile(
    med, [2.5, 97.5])
print(f"Mediana CI: {ci_med.round(2)}")`},
      {title:"Bootstrap dla regresji",color:C.pblue,code:
`import numpy as np

rng = np.random.default_rng(6)
n   = 50
x   = rng.uniform(0, 10, n)
y   = 2.5 + 1.8*x + rng.normal(0,2,n)

def fit_ols(xd, yd):
    X  = np.column_stack(
        [np.ones(len(xd)), xd])
    b, *_ = np.linalg.lstsq(
        X, yd, rcond=None)
    return b

B   = 3000
b0s = np.empty(B)
b1s = np.empty(B)

for i in range(B):
    idx = rng.integers(0, n, n)
    b   = fit_ols(x[idx], y[idx])
    b0s[i], b1s[i] = b

b_or = fit_ols(x, y)
print(f"b0={b_or[0]:.3f} "
      f"b1={b_or[1]:.3f}")

for nm, bs in [("b0",b0s),("b1",b1s)]:
    lo,hi = np.percentile(bs,[2.5,97.5])
    print(f"{nm}: [{lo:.3f},{hi:.3f}] "
          f"SE={bs.std():.4f}")`},
      {title:"Test permutacyjny",color:C.green,code:
`from scipy.stats import permutation_test
import numpy as np

rng = np.random.default_rng(7)
g1  = rng.normal(235, 20, 30)
g2  = rng.normal(248, 22, 30)

def roznica_median(x, y):
    return np.median(x)-np.median(y)

wynik = permutation_test(
    (g1, g2),
    statistic=roznica_median,
    permutation_type="independent",
    n_resamples=9999,
    alternative="two-sided",
    random_state=0)

print(f"Statyst.: {wynik.statistic:.3f}")
print(f"p-wartość:{wynik.pvalue:.4f}")

# Jackknife — SE i bias statystyki
dane = np.concatenate([g1,g2])
n    = len(dane)
thta = np.std(dane, ddof=1)
psi  = np.array([
    np.std(np.delete(dane,i),ddof=1)
    for i in range(n)])
se_j = np.sqrt((n-1)/n *
    np.sum((psi-psi.mean())**2))
print(f"Std SE_jack={se_j:.4f}")`},
    ]);
  }

  // SLAJD 14 — jackknife detail
  {
    const s=pres.addSlide();
    hdr(pres,s,"Jackknife i porównanie metod resamplingu",14);
    banner(s,"Jackknife (leave-one-out) szacuje SE i bias statystyki wykluczając kolejne obserwacje. Jest szybszy niż bootstrap gdy B jest duże. Pseudo-wartości Quenouille'a pozwalają budować CI bez założeń o rozkładzie.",1.14);

    cbL(s,
`import numpy as np
from scipy import stats

rng  = np.random.default_rng(8)
dane = rng.lognormal(5, 0.3, 40)

def jackknife(data, fn):
    n    = len(data)
    thta = fn(data)
    psi  = np.array([
        fn(np.delete(data, i))
        for i in range(n)])
    # Pseudo-wartości Quenouille'a
    jvals = n*thta - (n-1)*psi
    se    = np.sqrt(
        np.var(jvals, ddof=1) / n)
    bias  = (n-1)*(psi.mean()-thta)
    return {"ocena":thta,
            "SE":se, "bias":bias}

# Dla odchylenia standardowego
res = jackknife(dane, np.std)
print(f"Std:  {res['ocena']:.4f}")
print(f"SE:   {res['SE']:.4f}")
print(f"Bias: {res['bias']:.4f}")

# Korelacja — jackknife vs bootstrap
x_j = rng.normal(0,1,40)
y_j = 0.6*x_j + rng.normal(0,0.8,40)
r   = np.corrcoef(x_j,y_j)[0,1]
res_r = jackknife(
    np.column_stack([x_j,y_j]),
    lambda d: np.corrcoef(
        d[:,0],d[:,1])[0,1])
print(f"r={r:.4f}  SE_jack={res_r['SE']:.4f}")`,
    1.74,3.36,"Jackknife: pseudo-wartości, SE i bias dla std i korelacji; porównanie metod");

    panel(s,"Metody resamplingu — porównanie",[
      {t:"Bootstrap percentylowy",   s:"Prosty; dobre dla rozkładów symetrycznych.",c:C.pyellow},
      {t:"Bootstrap BCa",            s:"Poprawiony; preferowany przy skośności danych.",c:C.pblue},
      {t:"Jackknife",                s:"LOO; SE i bias; szybszy niż bootstrap.",c:C.green},
      {t:"Test permutacyjny",        s:"Brak założeń o rozkładzie; dokładna p-wartość.",c:C.orange},
      {t:"Cross-val bootstrap",      s:"632+ rule — dokładne oszacowanie błędu pred.",c:C.purple},
    ],6.0,1.74,3.62,3.36,0.60);
  }

  // ══ SEKCJA 05 ═════════════════════════════════════════════════════════
  sec(pres,5,"Wnioskowanie bayesowskie","PyMC, MCMC, NUTS, ArviZ, posteriori, LOO-CV");

  // SLAJD 16
  {
    const s=pres.addSlide();
    hdr(pres,s,"PyMC — modelowanie probabilistyczne",16);
    banner(s,"PyMC używa NUTS (No-U-Turn Sampler) — automatyczne dostrajanie kroku. Model definiuje się deklaratywnie: priori → wiarygodność → pm.sample(). ArviZ obsługuje diagnostykę: R-hat < 1.01 i ESS > 400 to sygnały zbieżności.",1.14);
    cols3(s,[
      {title:"Regresja bayesowska — PyMC",color:C.pyellow,code:
`import pymc as pm
import numpy as np
import arviz as az

rng = np.random.default_rng(0)
n   = 50
x   = rng.uniform(20, 300, n)
y_o = 250-0.4*x + rng.normal(0,15,n)

with pm.Model() as model:
    a = pm.Normal("a",mu=250,sigma=50)
    b = pm.Normal("b",mu=0, sigma=1)
    s = pm.HalfNormal("s",sigma=20)
    mu = a + b * x
    pm.Normal("y",mu=mu,sigma=s,
              observed=y_o)
    idata = pm.sample(
        1000, tune=1000, chains=4,
        random_seed=0,
        progressbar=False)

print(az.summary(
    idata,
    var_names=["a","b","s"],
    round_to=3))`},
      {title:"Diagnostyka łańcuchów MCMC",color:C.pblue,code:
`import arviz as az

# idata — wynik pm.sample()
# R-hat < 1.01 i ESS > 400 → OK

rhat = az.rhat(idata)
ess  = az.ess(idata)
print("R-hat:\n", rhat)
print("ESS:\n",   ess)

# HDI (Highest Density Interval)
hdi = az.hdi(idata, hdi_prob=0.94)
print("HDI 94%:", hdi)

# Wizualizacja (matplotlib)
# az.plot_trace(idata)
# az.plot_posterior(idata)
# az.plot_pair(idata)

# Predykcja a posteriori (PPC)
with model:
    ppc = pm.sample_posterior_predictive(
        idata, random_seed=0)

# az.plot_ppc(ppc, observed=True)
# Sprawdź kalibrację modelu`},
      {title:"Selekcja modeli — LOO-CV",color:C.green,code:
`import pymc as pm
import numpy as np
import arviz as az

rng = np.random.default_rng(1)
n   = 40
x   = rng.uniform(0, 10, n)
y_o = 2+1.5*x+rng.normal(0,2,n)

# Model liniowy
with pm.Model() as m_lin:
    a = pm.Normal("a",0,10)
    b = pm.Normal("b",0,5)
    s = pm.HalfNormal("s",5)
    pm.Normal("y",a+b*x,s,
              observed=y_o)
    id1 = pm.sample(
        500,tune=500,
        progressbar=False)
    pm.compute_log_likelihood(id1)

# Model kwadratowy
with pm.Model() as m_qd:
    a = pm.Normal("a",0,10)
    b = pm.Normal("b",0,5)
    c = pm.Normal("c",0,2)
    s = pm.HalfNormal("s",5)
    pm.Normal("y",a+b*x+c*x**2,
              s, observed=y_o)
    id2 = pm.sample(
        500,tune=500,
        progressbar=False)
    pm.compute_log_likelihood(id2)

cmp = az.compare(
    {"lin":id1,"qd":id2})
print(cmp[["rank","elpd_loo","dse"]])`},
    ]);
  }

  // SLAJD 17
  {
    const s=pres.addSlide();
    hdr(pres,s,"Bayesowska estymacja z danymi cenzurowanymi",17);
    banner(s,"Dane cenzurowane (ang. censored): wiemy że komponent przeżył do czasu t_obs, ale nie wiemy kiedy dokładnie ulegnie awarii. PyMC obsługuje to naturalnie przez pm.Potential — log-przeżywalność.",1.14);

    cbL(s,
`import pymc as pm
import numpy as np
import arviz as az

rng = np.random.default_rng(9)
# Czas życia [h] — Weibull(c=2, scale=1000)
c_t = 2.0; sc_t = 1000
t_obs  = np.sort(
    rng.weibull(c_t,30)*sc_t)
t_cens = np.full(10, 1200.0)

with pm.Model() as wb_model:
    c_w  = pm.HalfNormal("c",  sigma=3)
    sc_w = pm.HalfNormal("sc",
                          sigma=2000)
    # Wiarygodność — zaobserwowane awarie
    pm.Weibull("t_obs",
        alpha=c_w, beta=sc_w,
        observed=t_obs)
    # Cenzurowane — przeżyły do t_cens
    pm.Potential("t_cens",
        pm.Weibull.dist(
            alpha=c_w,
            beta=sc_w).logcdf(t_cens))
    idata_w = pm.sample(
        800, tune=800, chains=2,
        random_seed=1,
        progressbar=False)

print(az.summary(idata_w,
    var_names=["c","sc"],
    round_to=3))

c_p  = idata_w.posterior["c"].values.ravel()
sc_p = idata_w.posterior["sc"].values.ravel()
surv = np.exp(-(1500/sc_p)**c_p)
print(f"P(t>1500h) = {surv.mean():.4f} "
      f"± {surv.std():.4f}")`,
    1.74,3.36,"Weibull bayesowski z cenzurą: pm.Potential + logcdf; P(t>1500) z posteriori");

    panel(s,"Zalety wnioskowania bayesowskiego",[
      {t:"Pełna niepewność",       s:"Posteriori = rozkład, nie punkt; HDI zamiast CI.",c:C.pyellow},
      {t:"Dane cenzurowane",       s:"pm.Potential — naturalna obsługa przeżyć.",c:C.pblue},
      {t:"Wiedza a priori",        s:"Priori informatywne z literatury lub inżynierii.",c:C.green},
      {t:"Małe próbki",            s:"Stabilny przy n<30 dzięki regularyzcji przez priori.",c:C.orange},
      {t:"Selekcja modeli (LOO)",  s:"az.compare — ELPD, nie AIC/BIC.",c:C.purple},
    ],6.0,1.74,3.62,3.36,0.60);
  }

  // ══ SEKCJA 06 ═════════════════════════════════════════════════════════
  sec(pres,6,"Zastosowania inżynierskie","SPC, DOE, krzywa Wöhlera, analiza przeżycia");

  // SLAJD 19 — SPC
  {
    const s=pres.addSlide();
    hdr(pres,s,"Statystyczna kontrola procesu — karty SPC i Cp/Cpk",19);
    banner(s,"Karta X̄ i R: linie kontrolne ±A₂·R̄ od X̄̄. Zasada wykrycia: punkt poza UCL/LCL lub 8 kolejnych punktów po jednej stronie CL. Cp i Cpk mierzą zdolność procesu — Cpk ≥ 1.33 oznacza proces zdolny.",1.14);
    cols3(s,[
      {title:"Karta X̄ i R",color:C.pyellow,code:
`import numpy as np
import matplotlib.pyplot as plt

rng = np.random.default_rng(0)
k = 25; n = 5  # podgrupy
dane = rng.normal(100,2,(k,n))

X_bar = dane.mean(axis=1)
R     = dane.ptp(axis=1)
Xbb   = X_bar.mean()
Rbar  = R.mean()

A2, D3, D4 = 0.577, 0, 2.114
UCL_x = Xbb + A2*Rbar
LCL_x = Xbb - A2*Rbar

fig,axes=plt.subplots(2,1,figsize=(6,4))
for ax,y,ucl,lcl,cl,tyt in zip(
    axes,[X_bar,R],
    [UCL_x,D4*Rbar],
    [LCL_x,D3*Rbar],
    [Xbb,Rbar],
    ["Karta X̄","Karta R"]
):
    ax.plot(y,"bo-",ms=5,lw=1)
    ax.axhline(ucl,color="r",ls="--")
    ax.axhline(lcl,color="r",ls="--")
    ax.axhline(cl, color="g",ls="-")
    ax.set_title(tyt,fontsize=10)
    ax.grid(True,alpha=0.3)
plt.tight_layout(); plt.show()`},
      {title:"Zdolność procesu Cp/Cpk",color:C.pblue,code:
`import numpy as np
from scipy import stats

rng = np.random.default_rng(1)
LSL = 49.95  # dolna granica spec.
USL = 50.05  # górna granica spec.

x     = rng.normal(50.01,0.015,100)
mu    = x.mean()
sigma = x.std(ddof=1)

Cp  = (USL-LSL) / (6*sigma)
Cpu = (USL-mu)  / (3*sigma)
Cpl = (mu-LSL)  / (3*sigma)
Cpk = min(Cpu, Cpl)

print(f"μ={mu:.4f}  σ={sigma:.5f}")
print(f"Cp  = {Cp:.3f}")
print(f"Cpk = {Cpk:.3f}")

# Frakcja niezgodna (DPM)
p_nok = (
    stats.norm.cdf(LSL,mu,sigma) +
    1-stats.norm.cdf(USL,mu,sigma))
print(f"DPM = {p_nok*1e6:.0f}")

# Poziom Sigma
z_s = min((USL-mu)/sigma,
           (mu-LSL)/sigma)
print(f"Sigma-poziom = {z_s:.2f}")`},
      {title:"Analiza Weibulla — czas życia",color:C.green,code:
`from scipy import stats
import numpy as np
import matplotlib.pyplot as plt

rng = np.random.default_rng(2)
t   = stats.weibull_min.rvs(
    2.0, scale=5000,
    size=40, random_state=2)

c_f,loc_f,sc_f = stats.weibull_min.fit(
    t, floc=0)
print(f"c={c_f:.3f}  scale={sc_f:.0f}")

# Papier Weibulla
t_s  = np.sort(t)
n_t  = len(t_s)
F    = (np.arange(1,n_t+1)-0.3)/(n_t+0.4)
y_w  = np.log(-np.log(1-F))
x_w  = np.log(t_s)
t_f  = np.linspace(t_s.min(),t_s.max(),200)
y_f  = c_f*(np.log(t_f)-np.log(sc_f))

fig,ax=plt.subplots(figsize=(5,3.5))
ax.scatter(x_w,y_w,s=18,alpha=0.7)
ax.plot(np.log(t_f),y_f,"r-",lw=2)
ax.set_xlabel("ln(t)")
ax.set_ylabel("ln(−ln(1−F))")
ax.set_title("Papier Weibulla")
ax.grid(True,alpha=0.3)
plt.tight_layout()`},
    ]);
  }

  // SLAJD 20 — DOE i krzywa Wöhlera
  {
    const s=pres.addSlide();
    hdr(pres,s,"DOE i krzywa Wöhlera — statystyczna analiza zmęczenia",20);
    banner(s,"Plan 2^k: k czynników × 2 poziomy (−1, +1). Efekt główny = (śr. przy +1) − (śr. przy −1). Krzywa Wöhlera: log₁₀(N) = log₁₀(C) − m·log₁₀(σ_a). Regresja log-log wyznacza C i m z CI.",1.14);

    cbFull(s,
`from scipy import stats
import numpy as np
import matplotlib.pyplot as plt
from itertools import product

# ── Plan 2^3 — trzy czynniki: T, t, C ──────────────────────────
import pandas as pd
plan = pd.DataFrame(
    list(product([-1,1],repeat=3)),
    columns=["T","t","C"])
rng  = np.random.default_rng(10)
plan["y"] = (250 + 20*plan["T"] - 10*plan["t"]
             + 15*plan["C"] + rng.normal(0,5,8))
for cz in ["T","t","C"]:
    ef = (plan[plan[cz]==1]["y"].mean() -
          plan[plan[cz]==-1]["y"].mean())
    print(f"Efekt {cz}: {ef:+.2f} MPa")

# ── Krzywa Wöhlera (S-N) ────────────────────────────────────────
sig = np.array([300,280,260,240,220,200,180,160])
log_N_true = 14.5 - 4.5*np.log10(sig)
log_N_obs  = np.concatenate([
    log_N_true+rng.normal(0,0.15,8)
    for _ in range(3)])
sig_rep = np.repeat(sig,3)

sl,ic,r,p,se = stats.linregress(
    np.log10(sig_rep), log_N_obs)
print(f"log₁₀(N) = {ic:.2f} + ({sl:.2f})·log₁₀(σ)")
print(f"R² = {r**2:.4f}")

# ── Wykres z CI i PI ────────────────────────────────────────────
s_plot = np.linspace(150,320,200)
log_sp = np.log10(s_plot)
n_d    = len(log_N_obs)
ls_bar = np.log10(sig_rep).mean()
SSx    = np.sum((np.log10(sig_rep)-ls_bar)**2)
se_e   = np.sqrt(
    np.sum((log_N_obs-(ic+sl*np.log10(sig_rep)))**2)/(n_d-2))
se_fit = se_e*np.sqrt(1/n_d+(log_sp-ls_bar)**2/SSx)
se_pred= se_e*np.sqrt(1+1/n_d+(log_sp-ls_bar)**2/SSx)
t90    = stats.t.ppf(0.95, df=n_d-2)
yhat   = ic + sl*log_sp

fig,ax = plt.subplots(figsize=(9.2,3.2))
ax.scatter(sig_rep,log_N_obs,s=12,alpha=0.5,color="gray",label="Dane")
ax.plot(s_plot,yhat,"b-",lw=2,label="Regresja")
ax.fill_between(s_plot,yhat-t90*se_fit,yhat+t90*se_fit,
    alpha=0.25,label="CI 90%")
ax.fill_between(s_plot,yhat-t90*se_pred,yhat+t90*se_pred,
    alpha=0.12,color="orange",label="PI 90%")
ax.set_xlabel("σ_a [MPa]"); ax.set_ylabel("log₁₀(N)")
ax.legend(fontsize=8); ax.grid(True,alpha=0.3)
ax.set_title(f"Wöhler: log₁₀(N) = {ic:.2f} + ({sl:.2f})·log₁₀(σ)")
plt.tight_layout(); plt.show()`,
    1.74,3.88,"Plan 2^3: efekty T/t/C; Wöhler log-log z CI 90% i PI 90%");
    strip(s,[
      {t:"Plan 2^3: efekty",c:C.pyellow},{t:"linregress log-log",c:C.pblue},
      {t:"se_fit ≠ se_pred",c:C.green},{t:"t.ppf(0.95,df=n-2)",c:C.orange},
      {t:"fill_between CI/PI",c:C.purple}],5.30);
  }

  // SLAJD 21 — analiza przeżycia
  {
    const s=pres.addSlide();
    hdr(pres,s,"Analiza przeżycia — Kaplan-Meier i regresja Coxa",21);
    banner(s,"Analiza przeżycia modeluje czas do zdarzenia (awarii) z danymi cenzurowanymi. Kaplan-Meier: nieparametryczna krzywa przeżycia. Test log-rank: porównuje dwie krzywe. Cox PH: wpływ zmiennych na hazard.",1.14);

    cbL(s,
`from lifelines import (
    KaplanMeierFitter, CoxPHFitter)
import pandas as pd
import numpy as np

rng = np.random.default_rng(11)
n   = 60
df  = pd.DataFrame({
    "T": np.concatenate([
        rng.weibull(2.0,30)*2000,
        rng.weibull(2.2,30)*2800]),
    "E": np.concatenate([
        rng.binomial(1,.85,30),
        rng.binomial(1,.75,30)]),
    "gr":["A"]*30+["B"]*30,
    "ob":rng.uniform(.5,1.5,60),
})

import matplotlib.pyplot as plt
fig,ax=plt.subplots(figsize=(5,3.5))

for gr,col in [("A","tab:blue"),
               ("B","tab:orange")]:
    sub = df[df["gr"]==gr]
    kmf = KaplanMeierFitter()
    kmf.fit(sub["T"],sub["E"],label=gr)
    kmf.plot_survival_function(
        ax=ax, ci_show=True,
        color=col)

ax.set_title("Kaplan-Meier")
ax.set_xlabel("Czas [h]")
ax.set_ylabel("P(przeżycie)")
ax.grid(True,alpha=0.3)
plt.tight_layout(); plt.show()

# Cox Proportional Hazard
cph = CoxPHFitter()
cph.fit(df,"T","E",
        formula="ob+gr")
print(cph.summary[
    ["coef","exp(coef)","p"]])`,
    1.74,3.36,"KaplanMeierFitter z CI dla 2 grup; CoxPHFitter: HR i p-wartość");

    panel(s,"Biblioteka lifelines — API",[
      {t:"KaplanMeierFitter",   s:"kmf.fit(T,E). Nieparametryczna krzywa przeżycia.",c:C.pyellow},
      {t:"NelsonAalenFitter",   s:"Skumulowany hazard; alternatywa dla KM.",c:C.pblue},
      {t:"WeibullFitter",       s:"Parametryczny; MLE dla c i scale.",c:C.green},
      {t:"CoxPHFitter",         s:"HR = exp(coef); semiparametryczny.",c:C.orange},
      {t:"logrank_test",        s:"Porównanie dwóch krzywych KM; p-wartość.",c:C.purple},
    ],6.0,1.74,3.62,3.36,0.60);
  }

  // SLAJDY 22–28 — dodatkowe treści
  {
    const s=pres.addSlide();
    hdr(pres,s,"Korelacja i analiza kowariancji",22);
    banner(s,"Pearson mierzy liniową zależność; Spearman — monotoniczną (odporny na outliery i skośność); Kendall — konkordancję rang. ZAWSZE rysuj scatter plot — identyczne r=0.816 daje kwartet Anscombe'a z różnymi strukturami.",1.14);
    cols3(s,[
      {title:"Pearson, Spearman, Kendall",color:C.pyellow,code:
`from scipy import stats
import numpy as np

rng = np.random.default_rng(0)
x   = rng.uniform(0, 10, 60)
y   = 2*x + rng.normal(0, 3, 60)
y[[0,1,2]] = [50,55,48]  # outliery

r_p, p_p = stats.pearsonr(x, y)
r_s, p_s = stats.spearmanr(x, y)
r_k, p_k = stats.kendalltau(x, y)

print(f"Pearson  r={r_p:.3f} p={p_p:.4f}")
print(f"Spearman r={r_s:.3f} p={p_s:.4f}")
print(f"Kendall  τ={r_k:.3f} p={p_k:.4f}")

# Korelacja częściowa x,y | z
z   = rng.normal(0,1,60)
r1  = stats.linregress(z,x)
r2  = stats.linregress(z,y)
rx  = x-(r1.slope*z+r1.intercept)
ry  = y-(r2.slope*z+r2.intercept)
r_pc,p_pc = stats.pearsonr(rx,ry)
print(f"Częściowa r={r_pc:.3f} "
      f"p={p_pc:.4f}")`},
      {title:"Macierz korelacji — heatmapa",color:C.pblue,code:
`import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt

rng = np.random.default_rng(1)
n   = 80
df  = pd.DataFrame({
    "T_C":   rng.uniform(20,300,n),
    "czas":  rng.uniform(1,24,n),
    "sigma": rng.normal(235,20,n),
    "HB":    rng.normal(150,15,n),
})
corr,pv = stats.spearmanr(df)
mask = pv > 0.05
cs   = np.where(mask, 0, corr)

fig,ax = plt.subplots(figsize=(5,4))
im = ax.imshow(cs,cmap="RdBu_r",
    vmin=-1,vmax=1)
nms = df.columns.tolist()
ax.set_xticks(range(4))
ax.set_yticks(range(4))
ax.set_xticklabels(nms,rotation=25,
    ha="right",fontsize=9)
ax.set_yticklabels(nms,fontsize=9)
plt.colorbar(im,ax=ax,shrink=0.8)
for i in range(4):
    for j in range(4):
        ax.text(j,i,f"{cs[i,j]:.2f}",
            ha="center",va="center",
            fontsize=7)
plt.tight_layout(); plt.show()`},
      {title:"PCA — redukcja wymiarowości",color:C.green,code:
`from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import numpy as np
import matplotlib.pyplot as plt

rng = np.random.default_rng(2)
n   = 150
# Dane z 2 ukrytymi wymiarami
Z   = rng.normal(0,1,(n,2))
A   = rng.uniform(-1,1,(2,6))
X   = Z@A + 0.3*rng.normal(0,1,(n,6))

sc  = StandardScaler()
X_s = sc.fit_transform(X)

pca = PCA(n_components=6)
pca.fit(X_s)
var = pca.explained_variance_ratio_
cum = np.cumsum(var)
n95 = np.argmax(cum>=0.95)+1
print(f"PC do 95% wariancji: {n95}")

fig,axes=plt.subplots(1,2,figsize=(6,3))
axes[0].bar(range(1,7),var)
axes[0].set_title("Wykres osypiska")
axes[0].set_xlabel("Składowa PC")
axes[0].grid(True,alpha=0.3)
X2 = pca.transform(X_s)[:,:2]
axes[1].scatter(X2[:,0],X2[:,1],
    s=10,alpha=0.6)
axes[1].set_title("PC1 vs PC2")
axes[1].grid(True,alpha=0.3)
plt.tight_layout()`},
    ]);
  }

  {
    const s=pres.addSlide();
    hdr(pres,s,"Analiza szeregów czasowych — ADF, ARIMA i STL",23);
    banner(s,"Schemat ARIMA: (1) test ADF → rząd różnicowania d; (2) ACF/PACF → p i q; (3) dopasuj ARIMA; (4) sprawdź reszty testem Ljunga-Boxa (brak autokorelacji = biały szum). STL dekompozycja jest odporna na outliery.",1.14);

    cbL(s,
`from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.seasonal import STL
from statsmodels.stats.diagnostic \
    import acorr_ljungbox
import numpy as np

rng = np.random.default_rng(0)
T   = 200

# Random walk — niestacjonarny
x_rw = np.cumsum(rng.normal(0,1,T))
# AR(1) — stacjonarny
x_st = np.zeros(T)
for i in range(1,T):
    x_st[i]=0.7*x_st[i-1]+rng.normal()

for lbl,x in [("RW",x_rw),("AR1",x_st)]:
    adf_s,p,*_ = adfuller(x,autolag="AIC")
    stan = "niestac." if p>0.05 else "stac."
    print(f"{lbl}: ADF p={p:.4f} {stan}")

# ARIMA(1,1,1) — dopasowanie
x_ar = x_rw  # niestacjonarny → d=1
res  = ARIMA(x_ar,order=(1,1,1)).fit()
lb   = acorr_ljungbox(res.resid,
    lags=[10],return_df=True)
print(f"Ljung-Box p={lb.lb_pvalue.values[0]:.4f}")
# p > 0.05 → reszty to biały szum

# Prognoza 15 kroków
prog = res.get_forecast(steps=15)
print(prog.predicted_mean[:3].round(2))`,
    1.74,3.36,"ADF (stacjonarność), ARIMA(1,1,1) + Ljung-Box + prognoza 15 kroków");

    panel(s,"Analiza szeregów czasowych",[
      {t:"adfuller(x)",         s:"Test ADF: p<0.05 → stacjonarny (H0: niestac.).",c:C.pyellow},
      {t:"ARIMA(p,d,q).fit()",  s:"Dobierz d z ADF, p z PACF, q z ACF.",c:C.pblue},
      {t:"STL(x,period).fit()", s:"Trend + sezonowość + reszty; robust=True.",c:C.green},
      {t:"acorr_ljungbox",      s:"Reszty = biały szum (p>0.05) → model OK.",c:C.orange},
      {t:"Prophet (Facebook)",  s:"pip install prophet; interfejs ds/y; proste API.",c:C.purple},
    ],6.0,1.74,3.62,3.36,0.60);
  }

  {
    const s=pres.addSlide();
    hdr(pres,s,"Symulacja Monte Carlo — niezawodność struktury",24);
    banner(s,"Niezawodność: P_f = P(G ≤ 0) gdzie G = R − S (wytrzymałość minus obciążenie). Symulacja MC daje dokładne P_f dla dowolnych rozkładów. Metoda FORM jest szybsza analitycznie dla normalnych/lognormalnych zmiennych.",1.14);
    cols3(s,[
      {title:"MC — P_f i indeks β",color:C.pyellow,code:
`from scipy import stats
import numpy as np

rng = np.random.default_rng(0)
N   = 1_000_000

# R: Lognormal (wytrzymałość)
mu_R = 300; cov_R = 0.12
R    = rng.lognormal(
    mean=np.log(mu_R)-0.5*np.log(
        1+cov_R**2),
    sigma=np.sqrt(np.log(1+cov_R**2)),
    size=N)

# S: Normal (obciążenie)
mu_S = 200; cov_S = 0.20
S    = rng.normal(mu_S,
                  mu_S*cov_S, N)

G  = R - S         # funkcja graniczna
Pf = (G<=0).mean()
bt = stats.norm.ppf(1-Pf)

print(f"P_f  = {Pf:.2e}")
print(f"beta = {bt:.3f}")
print(f"Niezaw.: {(1-Pf)*100:.4f}%")

ci = stats.proportion_confint(
    int(Pf*N), N, alpha=0.05)
print(f"CI Pf: [{ci[0]:.2e},{ci[1]:.2e}]")`},
      {title:"FORM — analityczny indeks β",color:C.pblue,code:
`from scipy import stats
import numpy as np

# FORM dla Normal-Normal:
# β = (μ_R - μ_S)/sqrt(σ_R²+σ_S²)
mu_R = 300; sig_R = 36
mu_S = 200; sig_S = 40

beta_F = (mu_R-mu_S) / np.sqrt(
    sig_R**2 + sig_S**2)
Pf_F   = stats.norm.cdf(-beta_F)
print(f"FORM β={beta_F:.4f}")
print(f"FORM Pf={Pf_F:.4e}")

# Kierunki wrażliwości (cosines)
a_R = sig_R / np.sqrt(sig_R**2+sig_S**2)
a_S = sig_S / np.sqrt(sig_R**2+sig_S**2)
print(f"α_R={a_R:.3f}  α_S={a_S:.3f}")
# α²: udział zmiennej w niepewności

# Punkt obliczeniowy (design point)
R_star = mu_R - a_R*beta_F*sig_R
S_star = mu_S + a_S*beta_F*sig_S
print(f"R*={R_star:.1f}  S*={S_star:.1f}")`},
      {title:"Analiza wrażliwości Sobola",color:C.green,code:
`from scipy.stats import qmc
import numpy as np

N  = 8192  # musi być 2^k dla Sobola

# Model: y = x1² + x2*x3 + x4
def model(X):
    return (X[:,0]**2
            + X[:,1]*X[:,2]
            + X[:,3])

samp = qmc.Sobol(d=4,scramble=True,
                 seed=0)
A = 2*samp.random_base2(m=13) - 1
samp.reset()
B = 2*samp.random_base2(m=13) - 1

yA  = model(A); yB = model(B)
VAR = np.var(np.concatenate([yA,yB]))

# Indeksy Sobola I rzędu (S1)
S1  = np.zeros(4)
for i in range(4):
    AB_i = A.copy(); AB_i[:,i]=B[:,i]
    S1[i] = (yB*(model(AB_i)-yA)).mean()/VAR

for i,s in enumerate(S1):
    print(f"S1[x{i+1}] = {s:.4f}")`},
    ]);
  }

  {
    const s=pres.addSlide();
    hdr(pres,s,"Zestawienie metod statystycznych",25);
    banner(s,"Schemat wyboru: dane ilościowe + 2 grupy + normalność → t-test; bez normalności → Mann-Whitney; k grup → ANOVA + Tukey; kategorialne → chi-kwadrat; zależność ciągła → regresja OLS lub GLM.",1.14);
    s.addShape("rect",{x:0.4,y:1.74,w:9.2,h:0.34,fill:{color:C.navy},line:{color:C.navy}});
    ["Cel analizy","Metoda","Funkcja Python","Uwaga"].forEach((h,i)=>{
      const ws=[2.2,1.9,2.8,2.3]; let xc=0.52;
      for(let j=0;j<i;j++) xc+=ws[j];
      s.addText(h,{x:xc,y:1.80,w:ws[i],h:0.22,fontSize:10,color:C.accent,
        bold:true,fontFace:"Calibri",margin:0});
    });
    const rows=[
      ["Porównanie 2 grup","t-test Welcha","stats.ttest_ind(equal_var=False)","Shapiro + Levene przed testem",C.pyellow],
      ["Porównanie 2 grup (niep.)","Mann-Whitney U","stats.mannwhitneyu(alt='two-sided')","Skala porządkowa; outliery",C.pblue],
      ["Porównanie k grup","ANOVA 1-czynnikowa","stats.f_oneway(*grupy)","Normalność + równe wariancje",C.green],
      ["Post-hoc po ANOVA","Tukey HSD","pairwise_tukeyhsd(y,labels)","Korekcja wielokrotna built-in",C.orange],
      ["Normalność","Shapiro-Wilk","stats.shapiro(x)","n < 5000; Kolmogorov-Smirnov dla n≥",C.purple],
      ["Tabela kontyngencji","Chi-kwadrat","stats.chi2_contingency(tab)","Oczekiwane częstości > 5",C.pyellow],
      ["Regresja ciągła","OLS statsmodels","sm.OLS(y,X).fit()","Sprawdź diagnostykę reszt",C.pblue],
      ["Regresja 0/1","Logistyczna","sm.Logit(y,X).fit()","OR = exp(β); AUC-ROC",C.green],
      ["CI bez założeń","Bootstrap BCa","stats.bootstrap((x,),fn,'BCa')","B ≥ 5000; scipy ≥ 1.7",C.orange],
      ["Bayesowska estymacja","PyMC + NUTS","pm.sample(1000,tune=1000)","R-hat<1.01 i ESS>400",C.purple],
    ];
    rows.forEach((row,r)=>{
      const bg=r%2===0?C.white:"EEF5FB";
      const ws=[2.2,1.9,2.8,2.3]; let xc=0.4;
      row.slice(0,4).forEach((cell,c)=>{
        s.addShape("rect",{x:xc,y:2.16+r*0.27,w:ws[c]-0.02,h:0.25,
          fill:{color:bg},line:{color:"D8E8F0",width:0.5}});
        const fc=c===0?row[4]:(c===2?C.pblue:C.dark);
        const ff=c===2?"Consolas":"Calibri";
        s.addText(cell,{x:xc+0.05,y:2.18+r*0.27,w:ws[c]-0.10,h:0.21,
          fontSize:8.5,color:fc,fontFace:ff,margin:0});
        xc+=ws[c];
      });
    });
  }

  {
    const s=pres.addSlide();
    hdr(pres,s,"Dobre praktyki analizy statystycznej",26);
    cbFull(s,
`# ════════════════════════════════════════════════════════════════════
# 10 ZASAD RZETELNEJ ANALIZY STATYSTYCZNEJ
# ════════════════════════════════════════════════════════════════════

# 1. ZAWSZE wizualizuj dane przed testowaniem
#    histogram + boxplot + scatter — wykryj outliery i strukturę

# 2. SPRAWDŹ założenia testu PRZED jego zastosowaniem
#    Shapiro-Wilk (normalność), Levene (jednorodność wariancji)

# 3. Podaj rozmiar efektu — nie tylko p-wartość
#    Cohen d, η², r; małe/średnie/duże: d = 0.2/0.5/0.8

# 4. Stosuj korektę przy wielokrotnym testowaniu
#    Benjamini-Hochberg (FDR) — dla wielu hipotez jednocześnie

# 5. Dobierz n PRZED eksperymentem (analiza mocy)
from statsmodels.stats.power import tt_ind_solve_power
n_min = tt_ind_solve_power(effect_size=0.5, alpha=0.05,
                           power=0.80, alternative="two-sided")
print(f"Minimalne n/grupę: {n_min:.0f}")

# 6. Nie interpretuj p > 0.05 jako "brak efektu"
#    CI i ESS podają zakres plausybilnych wartości

# 7. Dla małych n (< 30) użyj metod permutacyjnych lub bootstrap
#    mniej założeń niż klasyczne testy asymptotyczne

# 8. Przy regresji — zawsze sprawdź reszty
#    QQ-plot, Scale-Location, Durbin-Watson, Breusch-Pagan

# 9. Pre-registration: określ H0, metodę i n PRZED zebraniem danych
#    zapobiega p-hackingowi i HARKing (Hypothesis After Results Known)

# 10. Reprodukowalność — ustaw ziarno i zapisz wersje pakietów
import numpy as np; np.random.seed(42)
import scipy, statsmodels
print(f"scipy={scipy.__version__}  statsmodels={statsmodels.__version__}")`,
    1.74,3.80,"10 zasad: wizualizacja, założenia, Cohen d, FDR, moc, CI, permutacje, reprodukowalność");
  }

  {
    const s=pres.addSlide();
    hdr(pres,s,"Analiza głównych składowych i wykrywanie anomalii",27);
    banner(s,"IsolationForest z scikit-learn wykrywa anomalie bez nadzoru: izoluje punkty rzadkie przez losowe partycjonowanie. LocalOutlierFactor (LOF) porównuje gęstość lokalną punktu z sąsiadami — anomalie mają niższą gęstość.",1.14);
    cols3(s,[
      {title:"IsolationForest — anomalie",color:C.pyellow,code:
`from sklearn.ensemble import (
    IsolationForest)
from sklearn.neighbors import (
    LocalOutlierFactor)
import numpy as np

rng  = np.random.default_rng(0)
n    = 200
# Normalne dane + 10 anomalii
X_n  = rng.normal(0,1,(n,3))
X_an = rng.uniform(5,8,(10,3))
X    = np.vstack([X_n, X_an])

# IsolationForest
ifor = IsolationForest(
    contamination=0.05,
    random_state=0)
ifor_pred = ifor.fit_predict(X)
# -1=anomalia, 1=normalny

# LOF
lof      = LocalOutlierFactor(
    n_neighbors=20,
    contamination=0.05)
lof_pred = lof.fit_predict(X)

n_if = (ifor_pred==-1).sum()
n_lf = (lof_pred==-1).sum()
print(f"IForest: {n_if} anomalii")
print(f"LOF:     {n_lf} anomalii")`},
      {title:"One-Class SVM",color:C.pblue,code:
`from sklearn.svm import OneClassSVM
from sklearn.preprocessing import (
    StandardScaler)
import numpy as np
import matplotlib.pyplot as plt

rng  = np.random.default_rng(1)
n    = 150
X_tr = rng.normal(0,1,(n,2))
X_te = np.vstack([
    rng.normal(0,1,(50,2)),
    rng.uniform(3,6,(15,2))
])

sc   = StandardScaler()
X_tr_s = sc.fit_transform(X_tr)
X_te_s = sc.transform(X_te)

ocsvm = OneClassSVM(
    kernel="rbf", nu=0.05,
    gamma="scale")
ocsvm.fit(X_tr_s)
y_pred = ocsvm.predict(X_te_s)

n_an = (y_pred==-1).sum()
print(f"OneClass SVM: {n_an} anomalii")

fig,ax=plt.subplots(figsize=(5,3.5))
ax.scatter(*X_te_s[y_pred==1].T,
    s=20,label="Normal",alpha=0.6)
ax.scatter(*X_te_s[y_pred==-1].T,
    s=50,marker="x",color="r",
    label="Anomalia",linewidths=2)
ax.legend(fontsize=9)
ax.set_title("One-Class SVM")
ax.grid(True,alpha=0.3)
plt.tight_layout()`},
      {title:"Autoencoder — anomalie",color:C.green,code:
`import torch
import torch.nn as nn
import numpy as np

rng = np.random.default_rng(2)
n   = 300

# Normalne dane
X_n = rng.normal(0,1,(n,10))
X_a = rng.normal(5,1,(20,10))
X   = np.vstack([X_n,X_a]).astype("f")

ae  = nn.Sequential(
    nn.Linear(10,4), nn.ReLU(),
    nn.Linear(4,2),  nn.ReLU(),
    nn.Linear(2,4),  nn.ReLU(),
    nn.Linear(4,10)
)
opt = torch.optim.Adam(
    ae.parameters(), lr=1e-3)

X_t = torch.from_numpy(X_n.astype("f"))
for ep in range(200):
    out  = ae(X_t)
    loss = nn.MSELoss()(out, X_t)
    opt.zero_grad(); loss.backward()
    opt.step()

# Błąd rekonstrukcji
with torch.no_grad():
    X_all = torch.from_numpy(X)
    err   = (ae(X_all)-X_all).pow(2).mean(1)

thr = torch.quantile(err[:n],0.95)
an  = (err>thr).sum().item()
print(f"Autoencoder: {an} anomalii")`},
    ]);
  }

  {
    const s=pres.addSlide();
    hdr(pres,s,"Miary zgodności i kalibracja modeli predykcyjnych",28);
    banner(s,"Kalibracja: czy prawdopodobieństwo 70% oznacza, że zdarzenie zachodzi w 70% przypadków? Reliability diagram i Expected Calibration Error (ECE) oceniają kalibrację. CalibratedClassifierCV (sklearn) koryguje model.",1.14);

    cbFull(s,
`from sklearn.calibration import (
    CalibratedClassifierCV, calibration_curve)
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import brier_score_loss
import numpy as np
import matplotlib.pyplot as plt

rng = np.random.default_rng(0)
n   = 500
X   = rng.normal(0, 1, (n, 8))
p   = 1/(1+np.exp(-0.5*X[:,0]+0.3*X[:,1]))
y   = rng.binomial(1, p)

X_tr,X_te,y_tr,y_te = train_test_split(
    X, y, test_size=0.3, random_state=0)

# Model nieskalibrowny (RF)
rf = RandomForestClassifier(
    n_estimators=100, random_state=0)
rf.fit(X_tr, y_tr)
p_rf = rf.predict_proba(X_te)[:,1]

# Model skalibrowany (Platt / isotonic)
for meth in ["sigmoid","isotonic"]:
    ccv = CalibratedClassifierCV(
        rf, method=meth, cv="prefit")
    ccv.fit(X_tr, y_tr)
    p_cal = ccv.predict_proba(X_te)[:,1]
    bs    = brier_score_loss(y_te, p_cal)
    print(f"{meth:10s}: Brier={bs:.4f}")

# Reliability diagram
fig,ax = plt.subplots(figsize=(5,4))
ax.plot([0,1],[0,1],"k--",lw=1,label="Idealna")
for p_pred, lbl, ls in [
    (p_rf,     "RF (raw)",        "-"),
    (p_cal,    "RF (isotonic)",   "--"),
]:
    frac_pos, mean_pred = calibration_curve(
        y_te, p_pred, n_bins=8)
    ax.plot(mean_pred, frac_pos,
            marker="o",ms=6,
            ls=ls, label=lbl)
ax.set_xlabel("Przewid. prawdopodob.")
ax.set_ylabel("Frakcja pozytywnych")
ax.legend(fontsize=9); ax.grid(True,alpha=0.3)
ax.set_title("Reliability diagram (kalibracja)")
plt.tight_layout(); plt.show()`,
    1.74,3.80,"Calibration: RF nieskal. vs CalibratedClassifierCV Platt/isotonic; Brier score; diagram");
  }

  // ── SLAJD 29 — PODSUMOWANIE ──────────────────────────────────────────
  {
    const s=pres.addSlide();
    hdr(pres,s,"Podsumowanie — Wykład 9",29);
    s.addShape("rect",{x:0.4,y:1.16,w:9.2,h:0.34,fill:{color:C.pblue},line:{color:C.pblue}});
    s.addText("Co opanowaliśmy w Wykładzie 9:",{x:0.6,y:1.20,w:9,h:0.26,fontSize:12,
      color:C.white,bold:true,fontFace:"Calibri",margin:0});
    [
      {n:"1",t:"Miary opisowe — scipy.stats: skośność, kurtoza, CI, dopasowanie MLE z AIC, test KS i Shapiro-Wilk, wykres QQ.",c:C.pyellow},
      {n:"2",t:"Testy hipotez — t-test Welcha, Levene, ANOVA + Tukey HSD, Kruskal-Wallis, chi-kwadrat, korekta BH/FDR, moc.",c:C.pblue},
      {n:"3",t:"Regresja — statsmodels OLS (VIF, diagnostyka reszt, PI), GLM Logit (OR, AUC-ROC), analiza mocy tt_ind_solve.",c:C.green},
      {n:"4",t:"Bootstrap i permutacje — BCa CI, bootstrap dla regresji (SE współczynników), jackknife, test permutacyjny.",c:C.orange},
      {n:"5",t:"Bayes — PyMC NUTS, R-hat/ESS (ArviZ), Weibull z danymi cenzurowanymi, LOO-CV az.compare, P(t>T) z posteriori.",c:C.purple},
      {n:"6",t:"Zastosowania — SPC (Cp/Cpk, karta X̄ i R), DOE 2^3, krzywa Wöhlera, Kaplan-Meier, Cox PH, MC niezawodności.",c:C.accent},
    ].forEach((it,i)=>{
      const y=1.60+i*0.52;
      s.addShape("rect",{x:0.4,y,w:9.2,h:0.46,fill:{color:C.white},line:{color:"E0E8F0"}});
      s.addShape("ellipse",{x:0.46,y:y+0.10,w:0.26,h:0.26,fill:{color:it.c},line:{color:it.c}});
      s.addText(it.n,{x:0.46,y:y+0.07,w:0.26,h:0.30,fontSize:11,
        color:it.c===C.pyellow?C.dark:C.white,bold:true,align:"center",fontFace:"Calibri",margin:0});
      s.addText(it.t,{x:0.80,y:y+0.09,w:8.72,h:0.30,fontSize:10.5,
        color:C.dark,fontFace:"Calibri",margin:0});
    });
    s.addShape("rect",{x:0.4,y:4.76,w:9.2,h:0.30,fill:{color:C.navy},line:{color:C.navy}});
    s.addText("Wykład 10 (następny): Przetwarzanie obrazów — OpenCV, scikit-image, segmentacja, transformacje, CNN dla wizji.",
      {x:0.6,y:4.80,w:9.0,h:0.22,fontSize:10,color:C.accent2,fontFace:"Calibri",margin:0});
    ft(s,29);
  }

  // ── SLAJD 30 — ZADANIA I LITERATURA ─────────────────────────────────
  {
    const s=pres.addSlide();
    s.background={color:C.dark};
    s.addShape("rect",{x:0,y:0,w:W*0.55,h:0.09,fill:{color:C.pyellow},line:{color:C.pyellow}});
    s.addShape("rect",{x:W*0.55,y:0,w:W*0.45,h:0.09,fill:{color:C.pblue},line:{color:C.pblue}});
    s.addShape("rect",{x:0,y:0,w:0.06,h:H,fill:{color:C.pblue},line:{color:C.pblue}});
    s.addShape("ellipse",{x:5.6,y:-0.9,w:5.8,h:5.8,
      fill:{color:C.navy,transparency:55},line:{color:C.navy,transparency:55}});
    s.addText("Zadania i literatura",{x:0.4,y:0.22,w:9,h:0.56,fontSize:28,
      color:C.white,bold:true,fontFace:"Calibri",margin:0});
    s.addShape("rect",{x:0.4,y:0.84,w:9.2,h:0.04,fill:{color:C.pblue},line:{color:C.pblue}});

    // Lewa — zadania
    s.addShape("rect",{x:0.4,y:1.00,w:4.42,h:2.56,fill:{color:C.navy},line:{color:C.navy}});
    s.addShape("rect",{x:0.4,y:1.00,w:4.42,h:0.36,fill:{color:C.pblue},line:{color:C.pblue}});
    s.addText("Zadania do wykonania",{x:0.55,y:1.05,w:4.1,h:0.26,fontSize:12,
      color:C.white,bold:true,fontFace:"Calibri",margin:0});
    ["Porównaj wytrzymałość 4 stopów: ANOVA + Tukey HSD + wykres violin z CI (bootstrap BCa 95%).",
     "Regresja wieloraka (T, czas, skład → σ): OLS, VIF, diagnostyka reszt — Jarque-Bera i Breusch-Pagan.",
     "Model bayesowski (PyMC) dla krzywej Wöhlera — posteriori log(C) i m, predykcja HDI 94%.",
     "Analiza przeżycia KM dla danych Weibulla (dwie grupy): test log-rank + Cox PH z jedną zmienną.",
     "MC niezawodności: P_f i β dla R~Lognormal(300,0.12) i S~Normal(200,0.20) — CI dla P_f.",
    ].forEach((item,i)=>{
      s.addShape("ellipse",{x:0.55,y:1.44+i*0.40,w:0.13,h:0.13,
        fill:{color:C.pyellow},line:{color:C.pyellow}});
      s.addText(item,{x:0.75,y:1.43+i*0.40,w:3.96,h:0.36,fontSize:9.5,
        color:C.accent2,fontFace:"Calibri",margin:0});
    });
  }