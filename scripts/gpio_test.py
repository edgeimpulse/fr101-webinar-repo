#!/usr/bin/env python3
import argparse
import subprocess
import time


def physical_value(logical_on: bool, active_low: bool) -> int:
    if active_low:
        return 0 if logical_on else 1
    return 1 if logical_on else 0


def set_gpio(chip: str, line: int, logical_on: bool, active_low: bool, dry_run: bool):
    value = physical_value(logical_on, active_low)
    if dry_run:
        print(f"[DRY_RUN] gpioset {chip} {line}={value}")
        return
    subprocess.run(["gpioset", chip, f"{line}={value}"], check=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--chip", default="gpiochip5")
    p.add_argument("--line", type=int, default=0)
    p.add_argument("--seconds", type=float, default=2.0)
    p.add_argument("--active-low", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    print(f"ON {args.chip} line {args.line}")
    set_gpio(args.chip, args.line, True, args.active_low, args.dry_run)
    time.sleep(args.seconds)
    print(f"OFF {args.chip} line {args.line}")
    set_gpio(args.chip, args.line, False, args.active_low, args.dry_run)

if __name__ == "__main__":
    main()
