"""Data layoutu pastviny.

# TODO Lane B
Pastvina jako 2D matice, např. 20x12 dlaždic. Hodnoty:
- 0 = tráva (průchozí)
- 1 = plot (neprůchozí)

Lane B doplní finální layout (a případně další typy dlaždic).
"""

# Placeholder layout 20x12 (jen tráva). Lane B doplní plot a další prvky.
PASTURE_LAYOUT: list[list[int]] = [
    [0] * 20 for _ in range(12)
]
