#!/usr/bin/env python3
"""Interactive cover-art generation loop.

For each of three surfaces (wrap, kindle, motif):
  1. Build 3 prompt variants (2 on-palette + 1 wildcard)
  2. Show prompts to user for review before firing zgen
  3. Run zgen SERIALLY — one image at a time, never batched
  4. Contact sheet: user approves or refines
  5. Refinement sub-loop: seed-locked, single image per tweak

Session state in cover-assets/cover-session.json lets you resume.
"""
from pathlib import Path
import random
import sys

from lib.cover_prompts import build_variants
from lib.cover_session import CoverSession, load_session, save_session_atomic
from lib.zgen_runner import run_zgen

SURFACE_DIMS = {
    "wrap":   {"width": 4992, "height": 2624},
    "kindle": {"width": 1600, "height": 2560},
    "motif":  {"width": 1664, "height": 2560},
}
SURFACES = ["wrap", "kindle", "motif"]


def _candidate_path(assets: Path, surface: str, idx: int) -> Path:
    return assets / "candidates" / f"{surface}_v1_candidate_{idx}.png"


def _canonical_path(assets: Path, surface: str) -> Path:
    return assets / f"{surface}_art.png"


def _generate_candidates(surface: str, genre: str, palette: str, assets: Path) -> list[dict]:
    """Build 3 variants, show to user, run zgen serially."""
    variants = build_variants(surface=surface, genre=genre, palette_key=palette)
    print(f"\n=== {surface.upper()} — drafted {len(variants)} prompts ===")
    for i, v in enumerate(variants, 1):
        label = "WILDCARD" if v["is_wildcard"] else "on-palette"
        print(f"\n[{i}] ({label}) {v['composition']}")
        print(f"    PROMPT: {v['prompt']}")
    input("\nPress Enter to start generation (Ctrl-C to bail and re-draft)...")

    results = []
    for i, v in enumerate(variants, 1):
        seed = random.randint(1, 2**31 - 1)
        out = _candidate_path(assets, surface, i)
        print(f"  [{i}/{len(variants)}] {surface} variant {i}  ... running zgen (seed={seed})")
        run_zgen(
            prompt=v["prompt"],
            output=out,
            width=SURFACE_DIMS[surface]["width"],
            height=SURFACE_DIMS[surface]["height"],
            seed=seed,
        )
        print(f"        done → {out.name}")
        results.append({"prompt": v["prompt"], "seed": seed, "file": out})
    return results


def _prompt_approval(surface: str, candidates: list[dict]) -> str:
    """Ask user for W1/K1/M1 style approval or 'refine' / 'reroll'."""
    print(f"\n{surface} candidates:")
    for i, c in enumerate(candidates, 1):
        print(f"  [{i}] {c['file'].name}")
    return input(
        f"  approve/refine/reroll for {surface}? "
        "(e.g. '1' to approve candidate 1, 'refine 1' or 'reroll'): "
    ).strip()


def _refine_loop(
    surface: str, current: dict, assets: Path, first_iteration: bool = True
) -> dict:
    """Seed-locked refinement loop. Returns updated candidate dict on approval."""
    seed = current["seed"]
    prompt = current["prompt"]
    while True:
        tweak = input(
            f"  refine {surface} (seed locked={seed}). What to adjust? "
            "(e.g. 'more muted, less orange'; 'reroll' for new seed; 'done' to approve): "
        ).strip()
        if tweak in ("done", ""):
            current["approved"] = True
            return current
        if tweak == "reroll":
            seed = random.randint(1, 2**31 - 1)
            print(f"  new seed={seed}")
            continue
        # Rewrite prompt: naive append; user can edit full prompt if they want
        new_prompt = prompt + f", {tweak}"
        if first_iteration:
            print(f"  REWRITTEN PROMPT: {new_prompt}")
            confirm = input("  fire? (y/n/edit): ").strip().lower()
            if confirm == "edit":
                new_prompt = input("  edit prompt: ").strip() or new_prompt
            elif confirm == "n":
                continue
        out = current["file"]
        run_zgen(
            prompt=new_prompt, output=out,
            width=SURFACE_DIMS[surface]["width"],
            height=SURFACE_DIMS[surface]["height"],
            seed=seed,
        )
        print(f"  re-rendered → {out}. review, then say 'done' or refine more.")
        prompt = new_prompt
        current.update({"prompt": new_prompt, "seed": seed})
        first_iteration = False


def _promote_candidate(surface: str, candidate: dict, assets: Path) -> None:
    """Copy approved candidate to canonical name."""
    canonical = _canonical_path(assets, surface)
    canonical.write_bytes(candidate["file"].read_bytes())


def generate_cover_art(
    book_config: dict,
    assets_dir: Path,
) -> None:
    """Main entry point."""
    assets_dir.mkdir(parents=True, exist_ok=True)
    (assets_dir / "candidates").mkdir(exist_ok=True)
    session_file = assets_dir / "cover-session.json"

    if session_file.exists():
        session = load_session(session_file)
        print(f"Resuming session for {session.book_title!r}.")
    else:
        session = CoverSession.new(
            book_title=book_config["title"],
            style_preset=book_config.get("style_preset", "navy_gold"),
        )

    genre = book_config.get("genre", "non-fiction")
    palette = book_config.get("style_preset", "navy_gold")

    for surface in SURFACES:
        if surface in session.surfaces and session.surfaces[surface].get("approved_file"):
            print(f"Skipping {surface} — already approved.")
            continue

        candidates = _generate_candidates(surface, genre, palette, assets_dir)
        for c in candidates:
            session.record_iteration(
                surface=surface, prompt=c["prompt"], seed=c["seed"],
                approved=False,
                width=SURFACE_DIMS[surface]["width"],
                height=SURFACE_DIMS[surface]["height"],
            )

        while True:
            choice = _prompt_approval(surface, candidates)
            if choice.isdigit():
                idx = int(choice) - 1
                approved = candidates[idx]
                session.record_iteration(
                    surface=surface, prompt=approved["prompt"],
                    seed=approved["seed"], approved=True,
                    width=SURFACE_DIMS[surface]["width"],
                    height=SURFACE_DIMS[surface]["height"],
                )
                _promote_candidate(surface, approved, assets_dir)
                break
            if choice.startswith("refine"):
                idx = int(choice.split()[1]) - 1 if len(choice.split()) > 1 else 0
                refined = _refine_loop(surface, candidates[idx], assets_dir)
                session.record_iteration(
                    surface=surface, prompt=refined["prompt"],
                    seed=refined["seed"], approved=True,
                    width=SURFACE_DIMS[surface]["width"],
                    height=SURFACE_DIMS[surface]["height"],
                )
                _promote_candidate(surface, refined, assets_dir)
                break
            if choice == "reroll":
                candidates = _generate_candidates(surface, genre, palette, assets_dir)
                continue
            print(f"  unrecognized: {choice!r}")

        save_session_atomic(session, session_file)

    print("\nAll surfaces approved. Canonical art:")
    for s in SURFACES:
        print(f"  {_canonical_path(assets_dir, s)}")


if __name__ == "__main__":
    try:
        from BOOK_CONFIG import BOOK_CONFIG  # noqa
    except ImportError:
        print("ERROR: BOOK_CONFIG.py not found. Copy the template and set your metadata.")
        sys.exit(1)
    project = Path(__file__).parent
    generate_cover_art(book_config=BOOK_CONFIG, assets_dir=project / "cover-assets")
