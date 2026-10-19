#!/usr/bin/env python3
"""Exact search with an arbitrary external integer index k>2. Every digit of n remains in the original right-associated tower; no blocks or permutations are permitted.

Author: Josué Amaro. Python 3.11+; standard library only.
"""
from __future__ import annotations
import argparse
from functools import lru_cache
from itertools import product
import json
from math import gcd
from pathlib import Path
import sys
import time
PRIMITIVE_DIGITS = {2: (2, 1), 3: (3, 1), 4: (2, 2), 5: (5, 1), 6: (6, 1), 7: (7, 1), 8: (2, 3), 9: (3, 2)}

@lru_cache(maxsize=10000)
def prime_factors(n):
    output = []
    p = 2
    while p * p <= n:
        v = 0
        while n % p == 0:
            n //= p
            v += 1
        if v:
            output.append((p, v))
        p += 1
    if n > 1:
        output.append((n, 1))
    return tuple(output)

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

def tower_divisible(digits, q):
    """Decide divisibility of a defined positive tower through prime valuations."""
    if q == 1:
        return True
    if not digits:
        return False
    c = int(digits[0])
    h_minimum = 0
    if c < 2:
        return False
    for p, v in prime_factors(q):
        if c % p:
            return False
        r, w = (c, 0)
        while r % p == 0:
            r //= p
            w += 1
        h_minimum = max(h_minimum, (v + w - 1) // w)
    return capped_tower(digits[1:], max(1, h_minimum)) >= h_minimum

def simplify_tower(digits, limit):
    """Return an exact small value or a symbolic expression for a defined tower."""
    v, expression = (1, '1')
    for character in reversed(digits):
        b = int(character)
        if b == 0:
            if v == 0:
                raise ValueError('0**0 is undefined')
            v, expression = (0, '0')
        elif b == 1 or v == 0:
            v, expression = (1, '1')
        elif v == 1:
            v, expression = (b, str(b))
        elif v is not None and v < exponent_threshold(b, limit):
            v = pow(b, v)
            expression = str(v)
        else:
            v, expression = (None, f'{b}^({expression})')
    return (v, expression)

def tower_text(digits):
    output = digits[-1]
    for c in reversed(digits[:-1]):
        output = f'{c}^({output})'
    return output

def search(max_digits=1000, max_index_digits=60, seconds=60, output='external_run'):
    start = time.monotonic()
    last_progress = start
    tope = 10 ** max_digits
    limit = 10 ** max_index_digits - 1
    records = []
    completed = True
    last_base = 1
    counts = {'candidate_powers': 0, 'compatible_leading_digit': 0, 'defined_towers': 0, 'identities': 0, 'numeric_indices': 0, 'symbolic_indices': 0}
    try:
        for b in (2, 3, 5, 6, 7):
            n, t = (b, 1)
            while n < tope:
                now = time.monotonic()
                if now - start >= seconds:
                    raise TimeoutError
                if now - last_progress >= 10:
                    print(json.dumps({'event': 'progress', 'base': b, 't': t, 'seconds': round(now - start, 3), **counts}), flush=True)
                    last_progress = now
                counts['candidate_powers'] += 1
                text = str(n)
                d = int(text[0])
                data = PRIMITIVE_DIGITS.get(d)
                if len(text) > 1 and data and (data[0] == b):
                    counts['compatible_leading_digit'] += 1
                    g = data[1]
                    tail = text[1:]
                    if '00' not in text:
                        counts['defined_towers'] += 1
                        common = gcd(g, t)
                        p, q = (g // common, t // common)
                        e = capped_tower(tail, max(1, 2 * q // p))
                        if e is not None and p * e > 2 * q and tower_divisible(tail, q):
                            exact, expr = simplify_tower(tail, limit * q // p)
                            r = {'n': text, 'digits': list(text), 'tower': tower_text(text), 'primitive_base': b, 't': t, 'g': g, 'index_coefficient': {'p': p, 'q': q}, 'exponent_tower': tower_text(tail), 'simplified_exponent': expr, 'integer_index_above_two': True, 'verified': True}
                            if exact is not None:
                                assert p * exact % q == 0
                                k = p * exact // q
                                assert k > 2
                                r.update(k=str(k), index_type='numeric')
                                counts['numeric_indices'] += 1
                            else:
                                r.update(symbolic_k=f'({p}*({expr}))/{q}', index_type='symbolic')
                                counts['symbolic_indices'] += 1
                            assert pow(b, t) == n and pow(b, g) == d
                            assert ''.join(r['digits']) == text
                            records.append(r)
                            counts['identities'] += 1
                n *= b
                t += 1
            last_base = b
    except TimeoutError:
        completed = False
    records.sort(key=lambda r: int(r['n']))
    with Path(output + '.jsonl').open('w', encoding='utf-8') as file:
        for r in records:
            file.write(json.dumps(r, ensure_ascii=False) + '\n')
    resumen = {'rule': 'root_k(T(digits(n)))=n; original order; integer k>2; no blocks', 'max_digits': max_digits, 'max_printed_index_digits': max_index_digits, 'unbounded_index': True, 'completed': completed, 'last_completed_base': last_base, 'seconds': round(time.monotonic() - start, 3), 'counts': counts, 'trivial_families': ['root_k(0)=0 for every integer k>=3', 'root_k(1)=1 for every integer k>=3'], 'identities': records}
    Path(output + '.json').write_text(json.dumps(resumen, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'event': 'finished', 'completed': completed, 'seconds': resumen['seconds'], 'counts': counts}), flush=True)
    for r in records[:20]:
        print(f"n={r['n']}; k={r.get('k', r.get('symbolic_k'))}", flush=True)
    return resumen

def self_test():
    for largo in range(1, 4):
        for ds in product('0123', repeat=largo):
            text = ''.join(ds)
            v = 1
            for c in reversed(text):
                b = int(c)
                if b == 0 and v == 0:
                    v = None
                    break
                v = pow(b, v)
            for limit in (1, 2, 10, 100):
                assert capped_tower(text, limit) == (None if v is None else min(v, limit + 1))
            if v is not None and v > 0:
                for q in range(1, 41):
                    assert tower_divisible(text, q) == (v % q == 0)
                exact, expr = simplify_tower(text, 100)
                assert exact == (v if v <= 100 else None)
    assert capped_tower('262144', 262144 ** 2) == 262144 ** 2

if __name__ == '__main__':
    sys.set_int_max_str_digits(0)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--max-digits', type=int, default=10000)
    parser.add_argument('--max-index-digits', type=int, default=60)
    parser.add_argument('--seconds', type=float, default=60)
    parser.add_argument('--output', default='external_run')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.max_digits < 1 or args.max_index_digits < 1 or args.seconds < 0:
        parser.error('Digit limits must be positive and seconds nonnegative.')
    self_test()
    if not args.self_test:
        search(args.max_digits, args.max_index_digits, args.seconds, args.output)

