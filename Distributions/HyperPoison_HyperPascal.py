"""
fit_lengths.py -- fitting the 1-displaced hyper-Poisson and hyper-Pascal
distributions to length data.

Both models are 1-displaced: the support starts at length 1, not 0.
Both can be fitted right-truncated at n (default) or untruncated.

    hyper-Poisson   P_x  =  C * a^(x-1) / b^(x-1)
    hyper-Pascal    P_x  =  P_1 * C(k+x-2, x-1) / C(m+x-2, x-1) * q^(x-1)

where b^(x) = Gamma(b+x)/Gamma(b) is the rising factorial (Pochhammer) and
the leading constant is whatever makes the probabilities sum to 1:

    truncated at n :  sum over x = 1 ... n
    untruncated    :  sum over x = 1 ... infinity
                      (= 1F1(1; b; a) and 2F1(k, 1; m; q) respectively)

Everything is computed in log space, so large n or large parameters cause
no overflow.

Changes from the earlier version:
  * --no-truncate now works for both models, not only the hyper-Poisson
  * low-expectation classes are pooled before X^2 is computed, and both the
    pooled and the unpooled value are reported
  * an identifiability diagnostic is run on every fit: both models have a
    direction in parameter space along which the likelihood is nearly flat,
    and estimates that sit on it must not be reported as point estimates
  * AIC is reported, so the 3-parameter hyper-Pascal is not credited for
    its extra parameter for free
  * the empirical repeat rate RR is computed
  * parameters are bounded from below as well as above, and non-finite
    probabilities are rejected rather than silently propagated as NaN

Usage:
    python fit_lengths.py lengths.txt --model both
    python fit_lengths.py lengths.txt --model both --no-truncate
    python fit_lengths.py lengths.txt --model both --out fitted.csv
"""

import numpy as np
from scipy.special import gammaln
from scipy.optimize import minimize

# parameters are searched inside these bounds; hitting either end is
# reported, because it means the data do not determine that parameter
PAR_MIN, PAR_MAX = 1e-6, 1e4

# the untruncated norming constant is evaluated by summing the kernel up to
# this length; the omitted remainder is far below machine precision for any
# parameter values that fit length data
INF_N = 4000


# ---------------------------------------------------------------- kernels


def _log_kernel_poisson(x, a, b):
    """log( a^(x-1) / b^(x-1) )."""
    j = np.asarray(x, dtype=float) - 1.0
    return j * np.log(a) - (gammaln(b + j) - gammaln(b))


def _logbinom(n, k):
    return gammaln(n + 1) - gammaln(k + 1) - gammaln(n - k + 1)


def _log_kernel_pascal(x, k, m, q):
    """log( C(k+x-2, x-1) / C(m+x-2, x-1) * q^(x-1) )."""
    j = np.asarray(x, dtype=float) - 1.0
    return _logbinom(k + j - 1, j) - _logbinom(m + j - 1, j) + j * np.log(q)


KERNELS = {"poisson": _log_kernel_poisson, "pascal": _log_kernel_pascal}
NPAR = {"poisson": 2, "pascal": 3}
PARNAMES = {"poisson": ("a", "b"), "pascal": ("k", "m", "q")}


def pmf(x, model, par, n=None):
    """
    Probabilities P_x for the 1-displaced distribution.

    n = int   -> right-truncated at n
    n = None  -> untruncated
    """
    log_kernel = KERNELS[model]
    x = np.atleast_1d(np.asarray(x, dtype=float))
    support = np.arange(1, (n if n is not None else INF_N) + 1, dtype=float)
    ls = log_kernel(support, *par)
    mx = ls.max()
    log_norm = mx + np.log(np.exp(ls - mx).sum())
    return np.exp(log_kernel(x, *par) - log_norm)


# ---------------------------------------------------------------- fitting


def _unpack(theta, model):
    if model == "poisson":
        return tuple(np.exp(theta))
    # k, m positive; q in (0, 1) via the logistic transform
    return (np.exp(theta[0]), np.exp(theta[1]), 1.0 / (1.0 + np.exp(-theta[2])))


def _start_grid(model, mean):
    if model == "poisson":
        return [np.log([a, b]) for a in (0.2, 1.0, max(mean, 0.5), 5.0)
                for b in (0.3, 1.0, 5.0, 20.0)]
    return [[np.log(k), np.log(m), np.log(q / (1 - q))]
            for k in (0.02, 0.2, 1.0, 3.0)
            for m in (0.02, 0.5, 3.0, 10.0)
            for q in (0.2, 0.5, 0.8)]


def fit(x, freq, model="poisson", n=None, truncate=True, method="ml"):
    """
    x      : observed lengths (1, 2, 3, ...)
    freq   : absolute frequencies
    model  : 'poisson' or 'pascal'
    n      : truncation point; defaults to max(x) when truncate=True
    method : 'ml'   -> maximum likelihood (recommended)
             'chi2' -> minimise X^2
             'ls'   -> least squares on relative frequencies (maximises R^2)
    """
    x = np.asarray(x, dtype=float)
    freq = np.asarray(freq, dtype=float)
    N = freq.sum()
    p_emp = freq / N
    if truncate and n is None:
        n = int(x.max())
    if not truncate:
        n = None

    def objective(theta):
        par = _unpack(theta, model)
        bounded = par[:2] if model == "pascal" else par
        if max(bounded) > PAR_MAX or min(bounded) < PAR_MIN:
            return 1e12
        p = pmf(x, model, par, n)
        if not np.all(np.isfinite(p)) or p.min() <= 0.0:
            return 1e12
        if method == "ml":
            return -np.sum(freq * np.log(p))
        if method == "chi2":
            e = np.clip(p * N, 1e-10, None)
            return np.sum((freq - e) ** 2 / e)
        if method == "ls":
            return np.sum((p_emp - p) ** 2)
        raise ValueError(f"unknown method {method!r}: use 'ml', 'chi2' or 'ls'")

    # Nelder-Mead's convergence test on the objective is absolute, so with a
    # log-likelihood of order 1e6 a fixed tolerance of 1e-12 can never be met
    # and every run would be reported as unconverged. Scale it to the problem.
    starts = _start_grid(model, float(np.sum(x * p_emp)))
    scale = abs(objective(starts[0]))
    if not np.isfinite(scale) or scale > 1e11:
        scale = float(N)
    ftol = max(1e-12, 1e-10 * scale)

    best = None
    for start in starts:
        res = minimize(objective, start, method="Nelder-Mead",
                       options={"xatol": 1e-10, "fatol": ftol,
                                "maxiter": 5000, "maxfev": 5000})
        if best is None or res.fun < best.fun:
            best = res

    # polish: restart from the best point until the simplex converges there,
    # so that a start which merely ran out of iterations is not reported as
    # the final answer
    for _ in range(5):
        if best.success:
            break
        res = minimize(objective, best.x, method="Nelder-Mead",
                       options={"xatol": 1e-11, "fatol": ftol * 1e-2,
                                "maxiter": 20000, "maxfev": 20000})
        if res.fun <= best.fun:
            best = res
        else:
            break

    par = _unpack(best.x, model)
    p = pmf(x, model, par, n)
    out = {"model": model, "par": par, "names": PARNAMES[model], "n": n,
           "N": N, "x": x, "freq": freq, "p": p, "expected": p * N,
           "converged": bool(best.success), "method": method}
    out.update(_goodness(x, freq, p, NPAR[model]))
    out.update(_identifiability(x, freq, model, par, n))
    out["RR"] = float(np.sum(p_emp ** 2))
    return out


# ---------------------------------------------------------------- assessment


def pool(freq, expected, min_expected=5.0):
    """
    Merge classes from the top down until every expected frequency reaches
    min_expected. X^2 is unreliable when expected frequencies fall below
    about 5: a cell with an expected frequency of 0.02 and one observation
    contributes 2438 to X^2 on its own. Pooling is standard practice and is
    what earlier published values of C reflect.
    """
    f = list(map(float, freq))
    e = list(map(float, expected))
    while len(e) > 2 and e[-1] < min_expected:
        le, lf = e.pop(), f.pop()
        e[-1] += le
        f[-1] += lf
    return np.array(f), np.array(e)


def _goodness(x, freq, p, npar, min_expected=5.0):
    N = freq.sum()
    expected = p * N
    p_emp = freq / N
    ss_res = np.sum((p_emp - p) ** 2)
    ss_tot = np.sum((p_emp - p_emp.mean()) ** 2)
    chi2_raw = np.sum((freq - expected) ** 2 / expected)
    fo, eo = pool(freq, expected, min_expected)
    chi2 = np.sum((fo - eo) ** 2 / eo)
    logL = np.sum(freq * np.log(p))
    return {
        "R2": 1 - ss_res / ss_tot,
        "chi2": chi2, "chi2_raw": chi2_raw,
        "C": chi2 / N, "C_raw": chi2_raw / N,
        "cells": len(freq), "cells_pooled": len(eo),
        "df": len(eo) - npar - 1,
        "logL": logL, "AIC": 2 * npar - 2 * logL,
    }


def _identifiability(x, freq, model, par, n, span=(0.01, 0.1, 10.0, 100.0)):
    """
    Both models have a direction in parameter space along which the shape of
    the distribution barely changes:

      hyper-Poisson  a, b -> t*a, t*b   (the geometric limit as t -> inf)
      hyper-Pascal   k, m -> t*k, t*m   (q fixed)

    Along it only the ratio b/a, or k/m, is determined by the data. The
    diagnostic rescales the fitted values by t and records how much the
    log-likelihood moves. A change of only a few units across four orders of
    magnitude means the individual parameters are not estimable and only the
    ratio may be reported.
    """
    freq = np.asarray(freq, dtype=float)

    def nll(p_):
        pr = pmf(x, model, p_, n)
        if not np.all(np.isfinite(pr)) or pr.min() <= 0:
            return np.nan
        return -np.sum(freq * np.log(pr))

    base = nll(par)
    deltas = []
    for t in span:
        scaled = (par[0] * t, par[1] * t) + tuple(par[2:])
        if max(scaled[:2]) > PAR_MAX * 100 or min(scaled[:2]) < PAR_MIN / 100:
            continue
        d = nll(scaled) - base
        if np.isfinite(d):
            deltas.append(d)
    flat = bool(deltas) and min(deltas) < 2.0
    at_bound = any(v <= PAR_MIN * 1.1 or v >= PAR_MAX * 0.9 for v in par[:2])
    ratio = par[1] / par[0] if model == "poisson" else par[0] / par[1]
    return {"ratio": ratio, "profile": deltas,
            "flat_ridge": flat or at_bound, "at_bound": at_bound}


# ---------------------------------------------------------------- reporting


def report(fit_out, show_table=True):
    f = fit_out
    names = f["names"]
    ps = "   ".join(f"{nm} = {v:.4f}" if 1e-3 <= abs(v) < 1e4 else f"{nm} = {v:.4g}"
                    for nm, v in zip(names, f["par"]))
    label = "hyper-Poisson" if f["model"] == "poisson" else "hyper-Pascal"
    trunc = f"right-truncated at n = {f['n']}" if f["n"] else "untruncated"
    print(f"\n--- {label} ({trunc}, {f['method']}) ---")
    print(ps + f"   N = {f['N']:.0f}")
    ratio_name = "b/a" if f["model"] == "poisson" else "k/m"
    print(f"{ratio_name} = {f['ratio']:.4f}   RR = {f['RR']:.4f}")

    if f["flat_ridge"]:
        print("  ** the likelihood is nearly flat along the direction in which")
        print(f"     {names[0]} and {names[1]} are scaled together. Across four orders of")
        print(f"     magnitude the log-likelihood moves by only "
              f"{min(f['profile']):+.1f} at best.")
        print(f"     {names[0]} and {names[1]} are therefore NOT individually identified here;")
        extra = " together with q" if f["model"] == "pascal" else ""
        print(f"     report the ratio {ratio_name} = {f['ratio']:.4f}{extra} instead.")
        if f["at_bound"]:
            print("     (a parameter has run to the edge of the search region.)")

    verdict = ("very good" if f["C"] <= 0.01 else
               "acceptable" if f["C"] <= 0.02 else "REJECTED (C > 0.02)")
    print(f"R2 = {f['R2']:.4f}   AIC = {f['AIC']:.1f}")
    print(f"X2 = {f['chi2']:.2f}   df = {f['df']}   C = X2/N = {f['C']:.5f}"
          f"   -> {verdict}")
    print(f"  (pooled {f['cells']} classes into {f['cells_pooled']}; "
          f"unpooled C = {f['C_raw']:.5f})")
    if not f["converged"]:
        print("  ** the optimiser did not report convergence.")

    if show_table:
        print(f"{'x':>4} {'f(x)':>12} {'NP(x)':>14} {'P(x)':>12}")
        for xi, fi, ei, pi in zip(f["x"], f["freq"], f["expected"], f["p"]):
            print(f"{xi:>4.0f} {fi:>12.0f} {ei:>14.2f} {pi:>12.6f}")


# ---------------------------------------------------------------- i/o


def load(path, fill_gaps=True, verbose=True):
    """
    Read the first two columns of a file of lengths and frequencies.

    Accepts tab, comma, semicolon or whitespace separation, blank lines,
    lines starting with '#', an optional header row, and extra columns
    after the first two (so a previously written fitted table can be fed
    straight back in).

    With fill_gaps=True any integer length between the smallest and largest
    observed value that is absent from the file is inserted with a frequency
    of 0. The support of the model runs over every integer from 1 to n, so an
    absent length is a zero-frequency class, not a class that does not exist.
    Dropping it silently removes its contribution to X^2 and changes the class
    count used by R^2.
    """
    x, freq = [], []
    with open(path, encoding="utf-8-sig") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = (line.replace(",", " ").replace(";", " ")
                     .replace("\t", " ").split())
            if len(parts) < 2:
                continue
            try:
                xi, fi = float(parts[0]), float(parts[1])
            except ValueError:
                continue  # header row
            x.append(xi)
            freq.append(fi)
    if not x:
        raise ValueError(f"no numeric rows found in {path}")
    x, freq = np.array(x), np.array(freq)
    order = np.argsort(x)
    x, freq = x[order], freq[order]

    if fill_gaps:
        full = np.arange(x.min(), x.max() + 1)
        missing = np.setdiff1d(full, x)
        if missing.size:
            lookup = dict(zip(x, freq))
            x = full.astype(float)
            freq = np.array([lookup.get(v, 0.0) for v in full])
            if verbose:
                print(f"note: lengths {', '.join(str(int(v)) for v in missing)} "
                      f"were absent from the file and have been inserted with "
                      f"frequency 0.")
    if x.min() != 1 and verbose:
        print(f"note: the smallest length in the file is {x.min():.0f}, not 1. "
              f"The 1-displaced model assumes the support starts at 1.")
    return x, freq


def write_csv(path, x, freq, fits):
    cols = {"poisson": "hyperPoisson", "pascal": "hyperPascal"}
    with open(path, "w", encoding="utf-8") as fh:
        head = ["x", "f_x"]
        for f in fits:
            head += [f"NP_x_{cols[f['model']]}", f"P_x_{cols[f['model']]}"]
        fh.write(",".join(head) + "\n")
        for i, (xi, fi) in enumerate(zip(x, freq)):
            row = [f"{xi:.0f}", f"{fi:.0f}"]
            for f in fits:
                row += [f"{f['expected'][i]:.6f}", f"{f['p'][i]:.8f}"]
            fh.write(",".join(row) + "\n")


# ---------------------------------------------------------------- cli


def main():
    import argparse

    ap = argparse.ArgumentParser(
        description="Fit the 1-displaced hyper-Poisson and/or hyper-Pascal "
                    "distribution to a two-column length/frequency file.")
    ap.add_argument("file", help="two-column file: length <sep> frequency")
    ap.add_argument("--model", choices=["poisson", "pascal", "both"],
                    default="both", help="which distribution to fit")
    ap.add_argument("--method", choices=["ml", "chi2", "ls"], default="ml",
                    help="ml = maximum likelihood (default); "
                         "chi2 = minimise X^2; "
                         "ls = least squares on relative frequencies")
    ap.add_argument("--n", type=int, default=None,
                    help="truncation point (default: largest observed length)")
    ap.add_argument("--no-truncate", action="store_true",
                    help="fit the untruncated models instead")
    ap.add_argument("--min-expected", type=float, default=5.0,
                    help="pool classes from the top down until every expected "
                         "frequency reaches this value (default 5)")
    ap.add_argument("--no-table", action="store_true",
                    help="print the summary only, not the fitted table")
    ap.add_argument("--out", default=None,
                    help="optional path to write the fitted table as CSV")
    args = ap.parse_args()

    if args.no_truncate and args.n is not None:
        ap.error("--n and --no-truncate cannot be combined")

    x, freq = load(args.file)
    print(f"file   : {args.file}")
    print(f"method : {args.method}")

    models = ["poisson", "pascal"] if args.model == "both" else [args.model]
    fits = []
    for model in models:
        f = fit(x, freq, model=model, n=args.n,
                truncate=not args.no_truncate, method=args.method)
        if args.min_expected != 5.0:
            f.update(_goodness(x, freq, f["p"], NPAR[model], args.min_expected))
        fits.append(f)
        report(f, show_table=not args.no_table)

    if len(fits) == 2:
        print("\n--- summary ---")
        print(f"{'model':<16}{'R2':>10}{'C':>10}{'AIC':>14}   verdict")
        for f in fits:
            name = "hyper-Poisson" if f["model"] == "poisson" else "hyper-Pascal"
            v = "acceptable" if f["C"] <= 0.02 else "rejected"
            if f["flat_ridge"]:
                v += ", flat ridge"
            print(f"{name:<16}{f['R2']:>10.4f}{f['C']:>10.5f}"
                  f"{f['AIC']:>14.1f}   {v}")
        d = fits[1]["AIC"] - fits[0]["AIC"]
        print(f"\ndelta AIC (Pascal - Poisson) = {d:+.1f}; negative favours the")
        print("hyper-Pascal after charging it for its third parameter.")
        print("C = X2/N with the threshold 0.02 (Macutek & Wimmer 2013).")
        print("R2 is reported for comparability with earlier work but is")
        print("dominated by the first length class and rarely discriminates.")

    if args.out:
        write_csv(args.out, x, freq, fits)
        print(f"\nfitted table written to {args.out}")


if __name__ == "__main__":
    main()

