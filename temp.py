def _prefix_function(s: str) -> list[int]:
    pi = [0] * len(s)
    j = 0
    for i in range(1, len(s)):
        while j and s[i] != s[j]:
            j = pi[j - 1]
        if s[i] == s[j]:
            j += 1
            pi[i] = j
    return pi

def overlap_ab(A: str, B: str, min_overlap: int = 2):
    if not A or not B:
        return None
    t = B + "#" + A
    L = _prefix_function(t)[-1]
    print(L)
    if L < min_overlap:
        return None
    return {
        "direction": "A->B",
        "overlap_len": L,
        "a_span": (len(A) - L, len(A)),
        "b_span": (0, L),
        "overlap_text": A[-L:],
        "merged": A + B[L:],
    }

# 예시
res = overlap_ab("transmission", "missioncritical", min_overlap=3)
print(res)