#!/usr/bin/env python3
"""Exact staged search: the first decimal digit is the root index, and all remaining digits form a right-associated tower in their original order. No blocks; 0**0 is undefined.

Author: Josué Amaro. Python 3.11+; standard library only.
"""
import argparse
from functools import lru_cache
from math import gcd
from pathlib import Path
import json
import sys
import time
PRIMITIVE_DIGITS = {2: (2, 1), 3: (3, 1), 4: (2, 2), 5: (5, 1), 6: (6, 1), 7: (7, 1), 8: (2, 3), 9: (3, 2)}

@lru_cache(maxsize=10000)
def exponent_threshold(b, limit):
    power, h = (1, 0)
    while power <= limit:
        power *= b
        h += 1
    return h

def capped_tower(digits, limit):
    """Return min(T, limit+1), or None if any subtower contains undefined 0**0."""
    v = 1
    for character in reversed(digits):
        b = int(character)
        if b == 0:
            if v == 0:
                return None
            v = 0
        elif b == 1 or v == 0:
            v = 1
        else:
            v = limit + 1 if v >= exponent_threshold(b, limit) else pow(b, v)
    return v

def prefix_compatible(prefix, target):
    """Necessary condition for completing a digit tower with this prefix."""
    for character in prefix:
        c = int(character)
        if c == 0:
            return target == 0
        if c == 1:
            return target == 1
        if target == 0:
            return False
        exponent = 0
        while target > 1 and target % c == 0:
            target //= c
            exponent += 1
        if target != 1:
            return False
        target = exponent
    return True

def tower_text(digits):
    output = digits[-1]
    for c in reversed(digits[:-1]):
        output = f'{c}^({output})'
    return output

@lru_cache(maxsize=32)
def representable_exponents(limit):
    """All attainable digit-tower values at most limit. Values above one have base 2..9 and an attainable exponent at most floor(log2(limit)). The recursion is exhaustive."""
    if limit <= 1:
        return tuple(range(limit + 1))
    values = {0, 1}
    for e in representable_exponents(limit.bit_length() - 1):
        for b in range(2, 10):
            v = pow(b, e)
            if v <= limit:
                values.add(v)
    return tuple(sorted(values))

def minimum_h(k, g, c):
    """Return the first h>=1 with k dividing g*c**h, or None if impossible."""
    q = k // gcd(k, g)
    h = 0
    while q > 1:
        divisor = gcd(q, c)
        if divisor == 1:
            return None
        q //= divisor
        h += 1
    return max(1, h)

def certified_prefix(b, t, width, check_deadline):
    """Certify leading digits and length using outward-rounded integer intervals."""
    precision = max(32, len(str(t)) + width + 10)
    while True:

        def multiply(x, y):
            lo, hi, scale = (x[0] * y[0], x[1] * y[1], x[2] + y[2])
            trim = max(0, len(str(hi)) - precision)
            if trim:
                divisor = 10 ** trim
                lo //= divisor
                hi = (hi + divisor - 1) // divisor
                scale += trim
            return (lo, hi, scale)
        result, factor, e = ((1, 1, 0), (b, b, 0), t)
        steps = 0
        while e:
            if steps % 32 == 0:
                check_deadline()
            if e & 1:
                result = multiply(result, factor)
            e >>= 1
            if e:
                factor = multiply(factor, factor)
            steps += 1
        lo, hi, scale = result
        lower_text, upper_text = (str(lo), str(hi))
        if len(lower_text) == len(upper_text) and lower_text[:width] == upper_text[:width]:
            return (lower_text[:width], len(lower_text) + scale)
        precision *= 2

def self_test():

    def representable(v):
        if v <= 9:
            return True
        for b in range(2, 10):
            r, e = (v, 0)
            while r > 1 and r % b == 0:
                r //= b
                e += 1
            if r == 1 and representable(e):
                return True
        return False
    assert set(representable_exponents(5000)) == {h for h in range(5001) if representable(h)}
    for k in range(2, 10):
        for g in (1, 2, 3):
            for c in range(2, 10):
                minimum = minimum_h(k, g, c)
                for h in range(1, 20):
                    assert (g * pow(c, h) % k == 0) == (minimum is not None and h >= minimum)
    for b in (2, 3, 5, 6, 7):
        for t in (1, 2, 13, 100, 1000):
            text = str(pow(b, t))
            for width in (3, 48):
                assert certified_prefix(b, t, width, lambda: None) == (text[:width], len(text))
    direct_solutions = []
    for n in range(20, 10000):
        s = str(n)
        k = int(s[0])
        if k >= 2 and capped_tower(s[1:], n ** k) == n ** k:
            direct_solutions.append(n)
    assert direct_solutions == []
    print(json.dumps({'event': 'self_tests', 'checked_up_to': 9999, 'solutions': direct_solutions, 'status': 'passed'}), flush=True)

def search(seconds=600, output='search_run', max_materialize=10000):
    start = time.monotonic()
    deadline = start + seconds
    last_progress = start
    stages, solutions, pending = ([], [], [])
    counts = {name: 0 for name in ('evaluated', 'prefix_mismatch', 'exponent_mismatch', 'undefined_tower', 'tower_mismatch', 'solutions', 'pending')}
    families = [(k, a, b, g, c, minimum_h(k, g, c)) for k in range(2, 10) for a, (b, g) in PRIMITIVE_DIGITS.items() for c in range(2, 10)]
    impossible = sum((f[-1] is None for f in families))
    families = [f for f in families if f[-1] is not None]
    previous_limit, q, position = (0, 4, None)

    def check_deadline():
        nonlocal last_progress
        now = time.monotonic()
        if now >= deadline:
            raise TimeoutError
        if now - last_progress >= 10:
            print(json.dumps({'event': 'progress', 'seconds': round(now - start, 2), 'stage_power_of_10': q, 'position': position, 'counts': counts}), flush=True)
            last_progress = now

    def save(final=False):
        data = {'rule': 'n=k a c ...; 2<=k<=9; T(a,c,...)=n**k; individual digits', 'zero_to_zero_convention': 'undefined', 'time_budget_seconds': seconds, 'seconds': round(time.monotonic() - start, 3), 'finished': final, 'total_families': 512, 'families_eliminated_by_factors': impossible, 'stages': stages, 'counts': counts, 'last_position': position, 'solutions': solutions, 'pending': pending, 'note': 'Each new stage examines t above the preceding bound; candidates longer than D are also resolved so that no gaps remain between stages.'}
        Path(output + '.json').write_text(json.dumps(data, indent=2), encoding='utf-8')
        return data
    try:
        while True:
            check_deadline()
            D, before, stage_start = (10 ** q, counts['evaluated'], time.monotonic())
            limit = 4 * D
            hs = representable_exponents((36 * D).bit_length() - 1)
            complete = False
            try:
                for k, a, b, g, c, minimum in families:
                    for h in hs:
                        check_deadline()
                        if h < minimum:
                            continue
                        e = pow(c, h)
                        numerator = g * e
                        if numerator > k * limit:
                            break
                        if numerator <= k * previous_limit:
                            continue
                        assert numerator % k == 0
                        t = numerator // k
                        if t <= g:
                            continue
                        position = {'k': k, 'a': a, 'c': c, 'h': h, 'exponent_t_digits': len(str(t))}
                        prefix, digit_count = certified_prefix(b, t, 3, check_deadline)
                        if not prefix.startswith(f'{k}{a}{c}'):
                            reason = 'prefix_mismatch'
                        else:
                            prefix, digit_count = certified_prefix(b, t, 48, check_deadline)
                            if '00' in prefix:
                                reason = 'undefined_tower'
                            elif not prefix_compatible(prefix[3:], h):
                                reason = 'exponent_mismatch'
                            else:
                                undefined = False
                                for width in (128, 1024, 8192):
                                    check_deadline()
                                    if digit_count <= width:
                                        break
                                    tail = str(pow(b, t, 10 ** width)).zfill(width)
                                    if '00' in tail:
                                        undefined = True
                                        break
                                if undefined:
                                    reason = 'undefined_tower'
                                elif digit_count > max_materialize:
                                    pending.append({'b': b, 't': str(t), 'k': k, 'a': a, 'c': c, 'h': h, 'digits': str(digit_count)})
                                    reason = 'pending'
                                else:
                                    n = pow(b, t)
                                    s = str(n)
                                    if capped_tower(s[2:], e) == e:
                                        assert int(s[0]) == k
                                        assert capped_tower(s[1:], n ** k) == n ** k
                                        r = {'n': s, 'k': k, 'tower': tower_text(s[1:]), 'b': b, 't': str(t), 'g': g, 'c': c, 'h': h}
                                        solutions.append(r)
                                        print(json.dumps({'event': 'solution', **r}), flush=True)
                                        reason = 'solutions'
                                    else:
                                        reason = 'tower_mismatch'
                        counts[reason] += 1
                        counts['evaluated'] += 1
                complete = True
            finally:
                stage = {'q': q, 'digit_bound': f'10^{q}', 'stage_seconds': round(time.monotonic() - stage_start, 3), 'cumulative_seconds': round(time.monotonic() - start, 3), 'new_candidates': counts['evaluated'] - before, 'cumulative_candidates': counts['evaluated'], 'complete': complete, 'exhaustive': complete and (not pending), 'cumulative_solutions': len(solutions), 'cumulative_pending': len(pending)}
                stages.append(stage)
                print(json.dumps({'event': 'stage', **stage}), flush=True)
                save()
            previous_limit = limit
            q = 12 if q == 4 else q * 2
    except TimeoutError:
        pass
    data = save(final=True)
    with Path(output + '.tsv').open('w', encoding='utf-8') as f:
        columns = list(stages[0]) if stages else []
        f.write('\t'.join(columns) + '\n')
        for stage in stages:
            f.write('\t'.join((str(stage[c]) for c in columns)) + '\n')
    print(json.dumps({'event': 'finished', 'seconds': data['seconds'], 'counts': counts}), flush=True)
    return data

if __name__ == '__main__':
    sys.set_int_max_str_digits(0)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds', type=float, default=600)
    parser.add_argument('--output', default='search_run')
    parser.add_argument('--max-materialize', type=int, default=10000)
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.seconds < 0 or args.max_materialize < 1:
        parser.error('Use nonnegative seconds and a positive materialization limit.')
    self_test()
    if not args.self_test:
        search(args.seconds, args.output, args.max_materialize)

