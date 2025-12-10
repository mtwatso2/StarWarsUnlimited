import re
import unicodedata
import pandas as pd


INPUT_FILES = [
    "jump_to_lightspeed_raw.csv",
    "legends_of_the_force_raw.csv",
    "secrets_of_power_raw.csv",
    "twilight_of_the_republic_raw.csv",
    "shadows_of_the_galaxy_raw.csv",
    "spark_of_rebellion_raw.csv",
]


# ---------- text helpers ----------
def fix_mojibake(text: str) -> str:
    """
    Try to repair mojibake caused by Latin-1 vs UTF-8 decoding issues.

    If `text` is a string, it is re-encoded as Latin-1 and decoded as UTF-8.
    If this fails, the original value is returned unchanged.
    """
    if not isinstance(text, str):
        return text
    try:
        return text.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text


def normalize_punctuation(text: str) -> str:
    """
    Normalize “smart” punctuation to plain ASCII and strip some symbols.

    - Converts curly quotes and dashes to straight quotes and hyphens.
    - Replaces ellipsis with three dots.
    - Removes some currency/trademark symbols.
    - Runs `fix_mojibake` first to repair common encoding issues.
    """
    if not isinstance(text, str):
        return text
    text = fix_mojibake(text)
    repl = {
        "\u2018": "'", "\u2019": "'", "\u201B": "'", "\u201A": "'", "\u2032": "'", "\u02BC": "'",
        "\u201C": '"', "\u201D": '"', "\u201E": '"',
        "\u2013": "-", "\u2014": "-", "\u2015": "-",
        "\u2026": "...",
    }
    for bad, good in repl.items():
        text = text.replace(bad, good)
    # Drop symbols like £, ©, ®, €, ™
    text = re.sub(r"[\u00A3\u00A9\u00AE\u20AC\u2122]", "", text)
    return text


def strip_accents(text: str) -> str:
    """
    Remove diacritic marks from a Unicode string.

    Uses NFKD normalization and then removes combining characters so that
    accented letters compare and sort like their unaccented counterparts.
    """
    if not isinstance(text, str):
        return text
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))


def normalize_name(name: str) -> str:
    """
    Build a canonical version of a card name for grouping and sorting.

    Steps:
    - Normalize punctuation and strip accents.
    - Trim, lowercase, and collapse internal whitespace.
    - Apply a few set-specific text normalizations so near-duplicates
      collapse into the same normalized key.
    """
    name = normalize_punctuation(name)
    name = strip_accents(name)
    n = str(name).strip().lower()
    n = re.sub(r"\s+", " ", n)
    # Manual fixes for known mismatches in source data
    n = n.replace("wisecracking wheelman", "wisecrack wheelman")
    n = n.replace(" razor crest - ride for hire", " razor crest - ride for hire")
    return n


# ---------- main cleaner ----------
def clean_price_guide(path_in: str, path_out: str) -> None:
    """
    Clean a single raw CSV price guide file and write a normalized CSV.

    The function:
    - Normalizes encoding and punctuation in product names.
    - Drops malformed rows and strips extra numbering fragments.
    - Derives display name, rarity, type, and base number.
    - Assigns a shared sort key to variants of the same location/character.
    - Sorts variants by suffix (full text after `//`) and by card type.
    - Outputs a standardized CSV with an empty Quantity column.
    """
    df = pd.read_csv(path_in)
    df["Product Name"] = df["Product Name"].apply(normalize_punctuation)

    # 1) Keep only Product Name, Rarity, Number
    df = df[["Product Name", "Rarity", "Number"]]

    # 1b) Drop rows whose Number does NOT start with a digit
    # (filters out headers, notes, or other non-card rows)
    df = df[df["Number"].astype(str).str.match(r"^\d")].copy()

    # --- Set-specific fix: ensure leading numbers like '020 // T01'
    # become '020/262' or '020/252' for the two large sets.
    if "shadows" in path_in.lower() or "spark" in path_in.lower():
        num_str = df["Number"].astype(str)
        # Only rows that contain '//' and whose numeric prefix is < 100
        mask_has_slash = num_str.str.contains("//", regex=False)
        numeric_prefix = (
            num_str.str.extract(r"^(\d+)", expand=False)
            .astype(float)
        )
        mask_small = numeric_prefix < 100
        fix_mask = mask_has_slash & mask_small

        # Choose total-card suffix by set
        if "spark" in path_in.lower():
            total_suffix = "/252"
        else:  # shadows
            total_suffix = "/262"

        # Replace everything from '//' onward with the correct suffix
        df.loc[fix_mask, "Number"] = (
            numeric_prefix[fix_mask].astype(int).astype(str).str.zfill(3) + total_suffix
        )

    # 1c) For Number values with "//", keep only the part before "//"
    # (drops internal TXX/TYY or similar segments)
    df["Number"] = (
        df["Number"]
        .astype(str)
        .str.split("//", n=1)
        .str[0]
        .str.strip()
    )

    # 2) Type from parentheses, e.g. "Card Name (Hyperspace)"
    # Defaults to "Normal" when no explicit type is present.
    df["Type"] = (
        df["Product Name"]
        .str.extract(r"\(([^()]*)\)", expand=False)
        .fillna("Normal")
    )

    # 3) Clean Name for display: drop the type part in parentheses,
    # normalize punctuation and accents.
    df["Name"] = (
        df["Product Name"]
        .str.replace(r"\([^()]*\)", "", regex=True)
        .str.strip()
        .apply(normalize_punctuation)
        .apply(strip_accents)
    )

    # 3a) Prefix and suffix flag
    # NamePrefix is the part before " // ", used to group variants of a location.
    df["NamePrefix"] = df["Name"].str.split(" // ").str[0]
    df["HasSuffix"] = df["Name"].str.contains(" // ", regex=False)
    df = df.drop(columns=["Product Name"])

    # 3b) GroupName for grouping/sort-number logic (normalized name key)
    df["GroupName"] = df["Name"].apply(normalize_name)

    # 4) BaseNum = numeric before first "/" in cleaned Number
    df["BaseNum"] = (
        df["Number"]
        .astype(str)
        .str.extract(r"^(\d+)", expand=False)
        .astype(float)
    )

    # 5) Initial Sort Number by GroupName
    # Each group (character/location) gets the minimum BaseNum as its sort key.
    def group_sort_number(g: pd.DataFrame) -> pd.DataFrame:
        """Assign a shared 'Sort Number' to all rows in a GroupName group."""
        valid = g["BaseNum"].dropna()
        base = valid.min() if not valid.empty else 1e9
        g["Sort Number"] = base
        return g

    df = df.groupby("GroupName", group_keys=False).apply(group_sort_number)

    # 6) Share Sort Number between base rows and 'NamePrefix // ...' variants
    # Ensures plain locations and their '//' variants sort together.
    prefix_min = (
        df.groupby("NamePrefix")["Sort Number"]
        .min()
        .rename("PrefixSort")
    )
    df = df.merge(prefix_min, left_on="NamePrefix", right_index=True, how="left")
    df["Sort Number"] = df["PrefixSort"]
    df = df.drop(columns=["PrefixSort"])

    # 7) Final ordering
    # Extract the full suffix after "//" for sorting (not just first word),
    # so multi-word variants like "TIE Fighter" sort correctly.
    df["VariantSuffix"] = (
        df["Name"]
        .str.extract(r"//\s*(.+)", expand=False)
        .fillna("")  # Empty string for cards without "//"
    )

    type_order = [
        "Normal",
        "Hyperspace",
        "Foil",
        "Hyperspace Foil",
        "Showcase",
        "Prestige",
        "Prestige Foil",
        "Serialized",
    ]
    # Use an ordered categorical type so card types sort in gameplay order,
    # not alphabetically.
    type_cat = pd.CategoricalDtype(categories=type_order, ordered=True)
    df["Type"] = df["Type"].astype(type_cat)

    df = df.sort_values(
        ["Sort Number", "NamePrefix", "HasSuffix", "VariantSuffix", "Type", "Name"],
        ascending=[True, True, True, True, True, True],
    )

    # 8) Final columns
    df = df[["Name", "Type", "Rarity", "Number"]]

    # 9) Quantity column (left empty for later population)
    df["Quantity"] = ""

    df.to_csv(path_out, index=False)
    print(f"Wrote cleaned file: {path_out}")


if __name__ == "__main__":
    # Process all known input files that follow the *_raw.csv pattern.
    for infile in INPUT_FILES:
        if not infile.endswith("_raw.csv"):
            continue
        outfile = infile.replace("_raw.csv", ".csv")
        clean_price_guide(infile, outfile)
