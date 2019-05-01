import functools
import math
import operator as op
from collections import defaultdict

from pandemic import constants as c


def ncr(n, r):
    r = min(r, n - r)
    if r < 0:
        return 0.0

    numer = functools.reduce(op.mul, range(n, n - r, -1), 1)
    denom = math.factorial(r)

    return numer / denom


def hg_pmf(k, M, n, N):
    N = min(N, M)  # allows for infection rate > stack size
    return ncr(n, k) * ncr(M - n, N - k) / ncr(M, N)


def inf_risks(stack, infection_rate, cond_p):
    inf_risk = defaultdict(list)

    for i in range(1, max(stack) + 1):
        if infection_rate > 0:
            stack_n = sum(stack[i].values())
            for city in stack[i]:
                inf_risk[city].extend(
                    cond_p * hg_pmf(j, stack_n, stack[i][city], infection_rate)
                    for j in range(1, stack[i][city] + 1)
                )

            infection_rate -= stack_n
        else:
            break

    return inf_risk


def trim_risk_dict(inf_risk, max_len):
    for city in c.cities:
        inf_risk[city].extend(0.0 for _ in range(len(inf_risk[city]), max_len))

    return defaultdict(list, {city: inf_risk[city][:max_len] for city in inf_risk})


def infection_risk(stack, infection_rate, p_no_epi):
    inf_risk = inf_risks(stack, infection_rate, p_no_epi)

    for i in (-1, 0):
        for city in stack[i]:
            inf_risk[city].extend(0.0 for _ in range(stack[i][city]))

    return trim_risk_dict(inf_risk, min(infection_rate, c.max_inf))


def epi_infection_risk(stack, infection_rate, p_epi, p_city_epi):
    p_inf0 = lambda j, n, cs, ir: (
        p_city_epi[c] * hg_pmf(j, n + 1, cs + 1, ir)
        + (1 - p_city_epi[c]) * hg_pmf(j, n + 1, cs, ir)
    )

    inf_risk = defaultdict(list)

    stack_n = sum(stack[0].values())
    for city in stack[0]:
        inf_risk[city].extend(
            p_epi * p_inf0(j, stack_n, stack[0][city], infection_rate)
            for j in range(1, stack[0][city] + 1)
        )

    for city, risks in inf_risks(stack, infection_rate - stack_n, p_epi).items():
        inf_risk[city].extend(risks)

    return trim_risk_dict(inf_risk, min(infection_rate, c.max_inf))
