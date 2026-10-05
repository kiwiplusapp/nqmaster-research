exec(open("pullday_eval2.py").read().split("for scale in (1, 2):")[0])
import sys
for scale, maxpos in ((1, 1), (1, 2), (1, 3), (2, 1), (2, 2), (3, 1), (3, 2)):
    T_ = apply_dll(scale, 0, maxpos)
    daily = T_.groupby("date").usd.sum().reindex(days, fill_value=0.0)
    eq = daily.cumsum(); mdd = (eq.cummax() - eq).max()
    wk = daily.groupby(pd.to_datetime(daily.index.astype(str)).to_period("W")).sum()
    u = T_.usd
    yrs = " ".join(f"{pf(u[T_.date//10000==y]):.2f}" for y in range(2020, 2027))
    print(f"\nx{scale} maxpos {maxpos}: trades/wk {len(u)/350:.2f} WR {100*(u>0).mean():.1f}% PF {pf(u):.2f} | IS {pf(u[T_.date<20240101]):.2f} OOS {pf(u[T_.date>=20240101]):.2f} | yrs {yrs} | net/yr ${daily.sum()/6.73:,.0f} avg wk ${wk.mean():,.0f} weeks>0 {100*(wk>0).mean():.0f}% maxDD ${mdd:,.0f} worst day ${daily.min():,.0f}")
    for nm, a, b in (("25K 1500/1500", 1500, 1500), ("50K 3000/2000", 3000, 2000), ("50K 3000/2500", 3000, 2500)):
        s = ""
        for md in (20, 30, 60):
            p, f, med = evalsim(daily, a, b, md); s += f" {md}d pass {p:.0f}%/bust {f:.0f}% med {med:.0f}d |"
        print(f"  {nm}:{s}")
    sys.stdout.flush()
