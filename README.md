# Self-Referential Identities Involving Decimal Power Towers and Integer Roots

### Algebraic Reductions, Combinatorial Variants, and Certified Computational Searches

**Author:** Josué Amaro — Independent Researcher

This repository contains the complete English LaTeX manuscript and two
self-contained Python search programs. The programs use exact integer
arithmetic, algebraic reductions, and certified interval bounds; they do
not approximate giant towers with floating-point logarithms.

## Motivation

The study was inspired by **[A New Math Meme](https://www.youtube.com/watch?v=Uvy5Cs9FDLg)**,
a **Numberphile** video presented by **Matt Parker together with Brady Haran**.
The motivating identity is

$$
\sqrt{2^{6^{2^{1^{4^4}}}}}=262144.
$$

All exponentiation is right-associated. The original digits are used
exactly once and in order. The manuscript also examines permutations,
consecutive digit blocks, and indices embedded in a decimal prefix.

## The two search models are different

| Program | Root index | Digits in the tower |
|---|---|---|
| `search.py` | The first digit of the result, from 2 to 9 | All remaining individual digits, in their original order |
| `search_external_indices.py` | An arbitrary external integer greater than 2 | Every individual digit of the result, in its original order |

Neither program permits blocks or permutations. Both treat `0**0` as
undefined. The manuscript documents additional variants; these two
programs reproduce the final strict search models, not every historical
block or permutation experiment.

### Algebraic reduction

If the bottom digit is $a=b^g$, with $b$ not a perfect power, then
$a^E=n^k$ forces $n=b^t$ and $kt=gE$.

For the embedded-index model, $n$ begins with the digits $k,a,c$ and
$E=c^h$, hence

$$t=\frac{g c^h}{k}.$$

Divisibility eliminates entire families. The exponent $h$ must itself be
representable as a digit tower. If $n$ has at most $D$ digits, then
$t<4D$ is a sufficient enumeration bound. Leading digits of $b^t$ are
certified with outward-rounded integer intervals.

## Requirements

- **Python 3.11 or later**; no third-party Python packages.
- **pdfLaTeX** for the manuscript, or an Overleaf account.
- **Git** and **GitHub CLI** only for publishing. On Windows, the provided
  publisher attempts to install missing tools with `winget`.

## Run the embedded-index search

From the repository directory:

```bash
python search.py --seconds 600
```

This runs the finite self-checks first, then allocates 600 seconds of
wall-clock time to progressively larger search stages. Self-checks and
final file writing are additional work. Progress is printed as JSON.

For a quick check or a shorter run:

```bash
python search.py --self-test
python search.py --seconds 10 --output quick_run
```

The output prefix controls the generated `.json` summary and `.tsv` stage
table. A repeated prefix overwrites its previous output. Use
`--max-materialize 10000` to control the largest complete number that may
be constructed. Larger surviving candidates are recorded as unresolved;
they are never rejected merely because they exceed this limit.

## Run the external-index search

```bash
python search_external_indices.py --max-digits 10000 --seconds 60
```

The index is derived exactly from divisibility; no upper bound is imposed
on it. Large indices are retained as exact symbolic expressions.

```bash
python search_external_indices.py --self-test
python search_external_indices.py --max-digits 40 --seconds 10 --output external_quick
```

Inspect the `completed` field before claiming coverage of the requested
digit bound. Timings vary between machines.

## Recorded results and their scope

| Model | Completed bound on the number of digits | Nontrivial results |
|---|---|---|
| External square root, strict digit order; historical experiment | $10^{384}$ | Only 262144 |
| Arbitrary external index $k>2$, strict digit order | 10,000 | $4294967296=2^{32}$ and $3433683820292512484657849089281=3^{64}$ |
| Index embedded in the first digit, strict remaining digits | $10^{1536}$ | No solutions |

For the embedded model, the historical 600-second execution resolved
5,419 candidates. The stage at $10^{1536}$ digits was complete; the stage
at $10^{3072}$ digits was **partial**. An astronomical digit bound is not
the numerical value of the bound on $n$.

The two external-index solutions have indices exceeding $10^{100}$.
They are **not** embedded-index solutions. See the manuscript for the
exact symbolic indices and proofs.

The English JSON snapshots in `results/` preserve the recorded numerical
values. The programs are translations and standalone repackagings of the
validated algorithms; their logic is unchanged, while function names,
command-line options, and output keys are in English. Do not expect the
same wall-clock timings on another machine.

None of the bounded searches proves global uniqueness or global
nonexistence without a digit bound.

## Manuscript and Overleaf

`articulo_torres_en.tex` is the full, self-contained English manuscript,
including all appendices, 54 displayed equations, and 15 tables. The
bibliography entries remain in their original language as requested by
the author. No external bibliography or image files are needed.

Upload it to Overleaf, select it as the main document, and use pdfLaTeX.
Locally:

```bash
pdflatex articulo_torres_en.tex
pdflatex articulo_torres_en.tex
```

Compilation could not be confirmed in the preparation environment
because Windows denied access to the local compiler. Structural checks
verified balanced environments and braces, preserved mathematics, and
unchanged table data.

## Publish to your own GitHub account

`publish.ps1` creates a **new public** repository named
`decimal-power-tower-identities` in the authenticated GitHub account.
It installs missing Git/GitHub CLI through Windows Package Manager when
available, starts browser authentication when necessary, makes the initial
commit, and pushes it. Browser sign-in or installation prompts may require
your interaction. It does not overwrite an existing repository.

To inspect the plan without installing, authenticating, committing, or
publishing:

```powershell
.\publish.ps1 -DryRun
```

To choose another repository name after extraction:

```powershell
.\publish.ps1 -RepositoryName another-repository-name
```

The script sets the commit author to Josué Amaro and uses the authenticated
account's GitHub no-reply email address. This configuration is local to
the new repository. Authentication uses the official GitHub CLI; no tokens
are stored in this repository or embedded in the publishing command.

Official documentation: [create a repository](https://cli.github.com/manual/gh_repo_create),
[browser authentication](https://cli.github.com/manual/gh_auth_login),
and [configure Git credentials](https://cli.github.com/manual/gh_auth_setup-git).

## Contents

```text
articulo_torres_en.tex       Complete English manuscript
search.py                   Standalone embedded-index search
search_external_indices.py  Standalone external-index search
results/                    English snapshots of historical results
publish.ps1                 Windows publication assistant
README.md                   This guide
CITATION.cff                Citation metadata
.gitignore                  Python and LaTeX build artifacts
```

## Acknowledgments

The author thanks Matt Parker and the Numberphile team for presenting the
power-tower puzzle. Language-model tools assisted with code optimization,
algebraic exploration, and manuscript organization. The full acknowledgment
and author contribution statement appear in the manuscript.
